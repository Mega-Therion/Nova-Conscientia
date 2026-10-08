"""Tests for the benchmark harness: reproducibility and the stability result."""

from __future__ import annotations

import json
import math
import sys
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
for _p in (_REPO_ROOT / "core", _REPO_ROOT / "verification", _REPO_ROOT / "benchmarks"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from drift_model import CallableBackend, DeterministicBackend, random_unit  # type: ignore
from run_benchmark import (  # type: ignore
    BASE_SEED,
    DEFAULT_DIM,
    DEFAULT_STEPS,
    DEFAULT_TRIALS,
    run_baseline_trial,
    run_benchmark,
    run_swarm_trial,
)
from sovereign_clipping_gate import MEASURED_TAU  # type: ignore


class TestDriftModel(unittest.TestCase):
    """The seeded proposal backends."""

    def test_deterministic_reproducibility(self):
        """The same seed reproduces the same proposal stream exactly."""
        a = DeterministicBackend(dim=8, seed=42)
        b = DeterministicBackend(dim=8, seed=42)
        stream_a = [a.propose(c) for c in range(20)]
        stream_b = [b.propose(c) for c in range(20)]
        self.assertEqual(stream_a, stream_b)
        c = DeterministicBackend(dim=8, seed=43)
        stream_c = [c.propose(x) for x in range(20)]
        self.assertNotEqual(stream_a, stream_c)

    def test_random_unit_norms(self):
        """random_unit returns unit vectors."""
        import random

        rng = random.Random(7)
        for _ in range(20):
            v = random_unit(16, rng)
            self.assertAlmostEqual(math.sqrt(sum(x * x for x in v)), 1.0, places=12)

    def test_callable_backend_contract(self):
        """The live-model adapter validates output shape and finiteness."""
        backend = CallableBackend(propose_fn=lambda cycle, dim: [0.1] * dim, dim=4)
        self.assertEqual(backend.propose(0), [0.1, 0.1, 0.1, 0.1])
        bad_len = CallableBackend(propose_fn=lambda c, d: [0.1] * (d - 1), dim=4)
        with self.assertRaises(ValueError):
            bad_len.propose(0)
        bad_val = CallableBackend(propose_fn=lambda c, d: [float("nan")] * d, dim=4)
        with self.assertRaises(ValueError):
            bad_val.propose(0)

    def test_fail_closed_configuration(self):
        """Degenerate backends are refused at construction."""
        with self.assertRaises(ValueError):
            DeterministicBackend(dim=0, seed=1)
        with self.assertRaises(ValueError):
            DeterministicBackend(dim=2, seed=1, drift_gain=-0.5)
        with self.assertRaises(ValueError):
            DeterministicBackend(dim=2, seed=1, momentum=1.0)


class TestBenchmarkArms(unittest.TestCase):
    """The two arms and their stability verdict."""

    def test_baseline_arm_collapses_without_control(self):
        """Unconstrained integration leaves the acceptance cone (arm A)."""
        record = run_baseline_trial(seed=BASE_SEED, steps=DEFAULT_STEPS, dim=DEFAULT_DIM)
        self.assertLess(record["final_similarity"], MEASURED_TAU)
        self.assertTrue(record["collapsed"])

    def test_swarm_arm_stays_inside_the_cone(self):
        """The dual-channel swarm holds the anchor across the whole trial (arm B)."""
        record = run_swarm_trial(seed=BASE_SEED, steps=DEFAULT_STEPS, dim=DEFAULT_DIM,
                                 swarm=4, cohesion_rate=0.05)
        # By construction: arm B applies the gate last, at MEASURED_TAU, so these two
        # assertions can fail only through a REJECT or a HALT.  The non-circular
        # comparison is arm B' (test_projection_removed_arm_beats_baseline).
        self.assertGreaterEqual(record["final_similarity"], MEASURED_TAU)
        self.assertFalse(record["collapsed"])
        self.assertEqual(record["halts"], 0)
        # The gate holds exploration inside the cone: agents are not identical.
        self.assertLess(record["pairwise_cosine"], 1.0)
        self.assertGreater(record["pairwise_cosine"], -1.0)

    def test_projection_removed_arm_beats_baseline(self):
        """Arm B' (projection removed, verdicts tallied) still reduces drift.

        This is the claim the in-cone result cannot make by itself: with the
        gate's projection switched off, the dual channel, correction force and
        cohesion alone keep the swarm closer to the anchor than raw integration.
        """
        base = run_baseline_trial(seed=BASE_SEED, steps=DEFAULT_STEPS, dim=DEFAULT_DIM)
        record = run_swarm_trial(seed=BASE_SEED, steps=DEFAULT_STEPS, dim=DEFAULT_DIM,
                                 swarm=4, cohesion_rate=0.05, project=False)
        self.assertGreater(record["final_similarity"], base["final_similarity"])
        self.assertEqual(record["gate_evaluations"], 4 * DEFAULT_STEPS * 2)
        self.assertGreater(record["gate_clips"], 0)

    def test_full_harness_receipt(self):
        """The receipt is deterministic, well-formed, and shows the mechanism."""
        receipt = run_benchmark(trials=8, steps=20, dim=8, swarm=3,
                                cohesion_rate=0.05, base_seed=BASE_SEED)
        baseline = receipt["metrics"]["baseline_unconstrained"]
        swarm = receipt["metrics"]["dual_channel_swarm"]
        self.assertGreater(baseline["collapse_fraction"], 0.0)
        self.assertEqual(swarm["collapse_fraction"], 0.0)  # by construction (arm B)
        self.assertGreater(swarm["mean_final_similarity"],
                           baseline["mean_final_similarity"])
        unprojected = receipt["metrics"]["swarm_projection_removed"]
        self.assertGreater(unprojected["mean_final_similarity"],
                           baseline["mean_final_similarity"])
        for arm in (swarm, unprojected):
            self.assertGreaterEqual(arm["gate_clip_fraction"], 0.0)
            self.assertLessEqual(arm["gate_clip_fraction"], 1.0)
        self.assertIn("provenance", receipt)
        self.assertIn("parameters", receipt)
        # Determinism: a second identical run reproduces the receipt bit-for-bit
        # (modulo nothing: no timestamps are embedded).
        again = run_benchmark(trials=8, steps=20, dim=8, swarm=3,
                              cohesion_rate=0.05, base_seed=BASE_SEED)
        self.assertEqual(
            json.dumps(receipt, sort_keys=True), json.dumps(again, sort_keys=True)
        )

    def test_full_harness_default_shape(self):
        """The committed default configuration runs and reports both arms."""
        receipt = run_benchmark(trials=DEFAULT_TRIALS, steps=DEFAULT_STEPS,
                                dim=DEFAULT_DIM)
        self.assertEqual(len(receipt["per_trial"]["baseline"]), DEFAULT_TRIALS)
        self.assertEqual(len(receipt["per_trial"]["swarm_projection_removed"]),
                         DEFAULT_TRIALS)
        self.assertEqual(receipt["metrics"]["baseline_unconstrained"]
                         ["collapse_fraction"], 1.0)

    def test_invalid_parameters_fail_closed(self):
        """Bad harness parameters raise instead of producing a receipt."""
        with self.assertRaises(ValueError):
            run_benchmark(trials=0)
        with self.assertRaises(ValueError):
            run_benchmark(cohesion_rate=1.5)


if __name__ == "__main__":
    unittest.main()

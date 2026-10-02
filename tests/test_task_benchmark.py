"""Tests for the task benchmark (benchmarks/run_task_benchmark.py).

Covers the geometry, the simulated constraint signal, stream alignment across
arms, determinism, and the two documented results: with an informative signal
the dual channel rejects drift and beats gate-only on task error; with an
uninformative signal it prefers large drift moves over small useful ones.
"""

from __future__ import annotations

import math
import random
import sys
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
for _p in (_REPO_ROOT / "core", _REPO_ROOT / "benchmarks"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from run_task_benchmark import (  # type: ignore
    ARMS,
    BASE_SEED,
    GOAL_ANGLE_DEG,
    SIGNAL_SENSITIVITY,
    TaskProposalStream,
    constraint_signal,
    frozen_task_error,
    run_task_benchmark,
    run_trial,
    task_frame,
)
from sovereign_clipping_gate import MEASURED_TAU, cosine_similarity  # type: ignore

TRIALS = 10
STEPS = 40
DIM = 16


def _mean_metric(arm, metric, sigma, sensitivity=SIGNAL_SENSITIVITY):
    """Mean of one per-trial metric over TRIALS seeded trials."""
    values = [run_trial(arm, BASE_SEED + k, STEPS, DIM, sigma, sensitivity)[metric]
              for k in range(TRIALS)]
    return sum(values) / len(values)


class TestGeometryAndSignal(unittest.TestCase):
    """Task frame and the simulated invariant checker."""

    def test_goal_inside_acceptance_cone(self):
        """The goal sits GOAL_ANGLE_DEG from the anchor, inside the gate's cone."""
        anchor, goal = task_frame(DIM)
        cos = cosine_similarity(anchor, goal)
        self.assertAlmostEqual(cos, math.cos(math.radians(GOAL_ANGLE_DEG)), places=12)
        self.assertGreater(cos, MEASURED_TAU)
        self.assertAlmostEqual(frozen_task_error(), 1.0 - cos, places=12)

    def test_signal_ignores_in_plane_moves(self):
        """A move inside span(anchor, goal) draws zero pressure from a noiseless checker."""
        move = [0.3, -0.2] + [0.0] * (DIM - 2)
        self.assertEqual(constraint_signal(move, 0.0, random.Random(1)), 0.0)

    def test_signal_scales_off_plane_norm(self):
        """Off-plane norm m gives pressure SIGNAL_SENSITIVITY * m at sigma 0."""
        move = [0.0, 0.0, 0.3, 0.4] + [0.0] * (DIM - 4)
        p = constraint_signal(move, 0.0, random.Random(1))
        self.assertAlmostEqual(p, SIGNAL_SENSITIVITY * 0.5, places=12)

    def test_signal_draws_once_whatever_sigma(self):
        """sigma 0 and sigma > 0 advance the RNG identically (streams stay aligned)."""
        a, b = random.Random(7), random.Random(7)
        constraint_signal([0.0] * DIM, 0.0, a)
        constraint_signal([0.0] * DIM, 1.0, b)
        self.assertEqual(a.random(), b.random())

    def test_signal_rejects_negative_parameters(self):
        """Negative sigma or sensitivity fails closed."""
        with self.assertRaises(ValueError):
            constraint_signal([0.0] * DIM, -0.1, random.Random(1))
        with self.assertRaises(ValueError):
            constraint_signal([0.0] * DIM, 0.1, random.Random(1), sensitivity=-1.0)


class TestStreamAndDeterminism(unittest.TestCase):
    """Every arm sees the same proposal kinds; runs are reproducible."""

    def test_proposal_kinds_independent_of_state(self):
        """Two streams with one seed but different states agree on kinds and drift moves."""
        _, goal = task_frame(DIM)
        s1 = TaskProposalStream(DIM, 123, goal)
        s2 = TaskProposalStream(DIM, 123, goal)
        state_a = [1.0] + [0.0] * (DIM - 1)
        state_b = [0.5, 0.5] + [0.1] * (DIM - 2)
        for cycle in range(STEPS):
            move_a, on_a = s1.propose(cycle, state_a)
            move_b, on_b = s2.propose(cycle, state_b)
            self.assertEqual(on_a, on_b)
            if not on_a:
                self.assertEqual(move_a, move_b)

    def test_trial_is_deterministic(self):
        """The same arm, seed and sigma give identical metrics."""
        for arm in ARMS:
            self.assertEqual(run_trial(arm, BASE_SEED, STEPS, DIM, 0.1),
                             run_trial(arm, BASE_SEED, STEPS, DIM, 0.1))

    def test_receipt_shape(self):
        """The receipt carries both sweeps, every arm at every sigma."""
        receipt = run_task_benchmark(trials=2, steps=5, dim=4, sigmas=[0.0, 0.5])
        for key in ("sweep", "control_sweep"):
            self.assertEqual(set(receipt[key]), {"0.0", "0.5"})
            for per_sigma in receipt[key].values():
                self.assertEqual(set(per_sigma), set(ARMS))

    def test_invalid_inputs_fail_closed(self):
        """Bad sizes, sweeps and arm names raise ValueError."""
        with self.assertRaises(ValueError):
            run_task_benchmark(trials=1, steps=1, dim=2)
        with self.assertRaises(ValueError):
            run_task_benchmark(trials=1, steps=1, dim=4, sigmas=[-0.1])
        with self.assertRaises(ValueError):
            run_task_benchmark(trials=1, steps=1, dim=4, sigmas=[])
        with self.assertRaises(ValueError):
            run_trial("no_such_arm", BASE_SEED, 1, DIM, 0.0)


class TestDocumentedResults(unittest.TestCase):
    """Regression guards for the results recorded in PROVENANCE.md."""

    def test_unscored_arms_accept_everything(self):
        """Arms without dual-channel scoring accept every proposal."""
        for arm in ("unconstrained", "gate_only", "gate_correction"):
            self.assertEqual(_mean_metric(arm, "accept_on", 0.0), 1.0)
            self.assertEqual(_mean_metric(arm, "accept_off", 0.0), 1.0)

    def test_gated_arms_never_collapse_but_unconstrained_does(self):
        """The gate holds every gated arm inside the cone; without it the state leaves."""
        self.assertGreater(_mean_metric("unconstrained", "collapsed", 0.0), 0.5)
        for arm in ("gate_only", "gate_dual_channel", "gate_correction", "full"):
            self.assertEqual(_mean_metric(arm, "collapsed", 0.0), 0.0)

    def test_informative_signal_beats_gate_only(self):
        """At sigma 0 the dual channel rejects all drift and ends closer to the goal."""
        self.assertEqual(_mean_metric("gate_dual_channel", "accept_off", 0.0), 0.0)
        self.assertGreater(_mean_metric("gate_dual_channel", "accept_on", 0.0), 0.0)
        dual = _mean_metric("gate_dual_channel", "final_task_error", 0.0)
        self.assertLess(dual, _mean_metric("gate_only", "final_task_error", 0.0))
        self.assertLess(dual, frozen_task_error())

    def test_uninformative_signal_prefers_large_drift_moves(self):
        """With a pure-noise signal the dual channel admits drift more often than
        useful moves, and does worse than gate-only on task error (scale bias of
        the quadratic credit H(x) = x^2 / 2)."""
        on = _mean_metric("gate_dual_channel", "accept_on", 0.1, sensitivity=0.0)
        off = _mean_metric("gate_dual_channel", "accept_off", 0.1, sensitivity=0.0)
        self.assertGreater(off, on)
        dual = _mean_metric("gate_dual_channel", "final_task_error", 0.1, sensitivity=0.0)
        self.assertGreater(dual, _mean_metric("gate_only", "final_task_error", 0.1))


if __name__ == "__main__":
    unittest.main()

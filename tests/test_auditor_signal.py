"""Tests for the auditor-signal benchmark (benchmarks/run_auditor_signal.py).

Covers the critic panel's rubrics, the pressure mapping, input validation, and
guards for the documented results: unanimous consensus freezes the agent
(the anchor-only critic rejects every move), classic credit never beats the
frozen agent, and running_reference credit does at 0.1 pressure per rejection.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
for _p in (_REPO_ROOT / "core", _REPO_ROOT / "benchmarks", _REPO_ROOT / "verification"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from run_auditor_signal import (  # type: ignore
    FROZEN_TOLERANCE,
    auditor_pressure_fn,
    build_panel,
    deliberate,
    run_arm,
    run_auditor_benchmark,
)
from run_task_benchmark import BASE_SEED, frozen_task_error, task_frame  # type: ignore

DIM = 16
STEPS = 40
TRIALS = 10


def _mean_err(arm, pressure):
    """Mean final task error of an arm over TRIALS seeded trials."""
    return sum(run_arm(arm, BASE_SEED + k, STEPS, DIM, pressure)["final_task_error"]
               for k in range(TRIALS)) / TRIALS


class TestPanel(unittest.TestCase):
    """The three rubric critics and the pressure mapping."""

    def setUp(self):
        self.panel = build_panel(DIM, BASE_SEED)
        self.anchor, self.goal = task_frame(DIM)

    def test_in_plane_move_toward_anchor_is_admitted(self):
        """A move inside the task plane that raises anchor cosine passes every critic."""
        state = list(self.goal)
        move = [0.05 * (a - g) for a, g in zip(self.anchor, self.goal)]
        admitted, rejected = deliberate(self.panel, move, state)
        self.assertTrue(admitted)
        self.assertEqual(set(rejected.values()), {False})

    def test_off_plane_move_is_rejected_by_plane_critics(self):
        """A move entirely off the task plane is rejected by the plane and subspace critics."""
        move = [0.0, 0.0] + [0.1] * (DIM - 2)
        admitted, rejected = deliberate(self.panel, move, self.anchor)
        self.assertFalse(admitted)
        self.assertTrue(rejected["plane-critic"])
        self.assertTrue(rejected["subspace-critic"])

    def test_anchor_critic_rejects_progress_toward_goal(self):
        """The anchor-only critic rejects an in-plane step toward the goal (its blind spot)."""
        move = [0.2 * (g - a) for g, a in zip(self.goal, self.anchor)]
        _, rejected = deliberate(self.panel, move, self.anchor)
        self.assertTrue(rejected["anchor-critic"])
        self.assertFalse(rejected["plane-critic"])

    def test_pressure_counts_rejections(self):
        """Pressure = per-rejection pressure x number of rejecting critics."""
        fn = auditor_pressure_fn(self.panel, 0.1)
        move = [0.0, 0.0] + [0.1] * (DIM - 2)
        _, rejected = deliberate(build_panel(DIM, BASE_SEED), move, self.anchor)
        self.assertAlmostEqual(fn(move, self.anchor), 0.1 * sum(rejected.values()), places=12)

    def test_negative_pressure_fails_closed(self):
        """A negative per-rejection pressure raises ValueError."""
        with self.assertRaises(ValueError):
            auditor_pressure_fn(self.panel, -0.1)


class TestHarness(unittest.TestCase):
    """Receipt shape and input validation."""

    def test_receipt_shape(self):
        """The receipt carries critics, every arm and the summary for each seed."""
        r = run_auditor_benchmark(trials=2, steps=5, dim=4, seeds=[BASE_SEED], pressures=[0.1])
        seed = r["results"][str(BASE_SEED)]
        self.assertEqual(set(seed["critics"]), {"plane-critic", "anchor-critic", "subspace-critic"})
        self.assertEqual(set(seed["dual"]["0.1"]), {"dual_classic", "dual_running_reference"})
        self.assertIn("dual_running_reference@0.1", r["summary"])

    def test_invalid_inputs_fail_closed(self):
        """Bad sizes, sweeps and arms raise ValueError."""
        with self.assertRaises(ValueError):
            run_auditor_benchmark(trials=1, steps=1, dim=2)
        with self.assertRaises(ValueError):
            run_auditor_benchmark(trials=1, steps=1, dim=4, pressures=[])
        with self.assertRaises(ValueError):
            run_arm("nope", BASE_SEED, 1, DIM, 0.1)


class TestDocumentedResults(unittest.TestCase):
    """Regression guards for the results recorded in PROVENANCE.md."""

    def test_unanimous_consensus_freezes(self):
        """The anchor-only critic rejects every move, so consensus never admits one."""
        for k in range(3):
            r = run_arm("consensus_gate", BASE_SEED + k, STEPS, DIM, 0.0)
            self.assertEqual(r["accept_on"], 0.0)
            self.assertEqual(r["accept_off"], 0.0)
            self.assertAlmostEqual(r["final_task_error"], frozen_task_error(), places=9)

    def test_classic_credit_does_not_beat_frozen(self):
        """With auditor pressure, classic credit ends no closer to the goal than a frozen agent."""
        self.assertGreater(_mean_err("dual_classic", 0.1), frozen_task_error() - FROZEN_TOLERANCE)

    def test_running_reference_beats_frozen(self):
        """running_reference at 0.1 per rejection ends closer to the goal than a frozen agent."""
        self.assertLess(_mean_err("dual_running_reference", 0.1), frozen_task_error() - 0.005)


if __name__ == "__main__":
    unittest.main()

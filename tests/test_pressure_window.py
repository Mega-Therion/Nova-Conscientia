"""Tests for the pressure-window sweep (benchmarks/run_pressure_window.py).

Covers the derivation (L_corr inverse, the separating window, and agreement
with DualChannelAction's running_reference verdicts at the window's edges),
the uninformative control, input validation, and guards for the documented
results: running_reference credit beats a frozen agent and the control at
every grid point of the item-4 window, and not at 0.4.
"""

from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
for _p in (_REPO_ROOT / "core", _REPO_ROOT / "benchmarks", _REPO_ROOT / "verification"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from dual_channel_action import DualChannelAction, h_kinetic, l_corr  # type: ignore
from run_pressure_window import (  # type: ignore
    DOCUMENTED_WINDOW,
    control_pressure_fn,
    derived_window,
    l_corr_inverse,
    max_admissible_pressure,
    measure_trial,
    run_pressure_window,
    run_window_arm,
)
from run_task_benchmark import BASE_SEED, frozen_task_error  # type: ignore

DIM = 16
STEPS = 40
TRIALS = 10


def _admits(x_ref, pressure):
    """running_reference verdict for a proposal scored after one of momentum x_ref."""
    action = DualChannelAction(credit_mode="running_reference")
    action.evaluate(momentum=x_ref, constraint_pressure=0.0)
    return action.evaluate(momentum=x_ref, constraint_pressure=pressure).accepted


def _mean_err(arm, pressure):
    """Mean final task error of a sweep arm over TRIALS seeded trials."""
    total = 0.0
    for k in range(TRIALS):
        rates = measure_trial(BASE_SEED + k, STEPS, DIM)["critic_rates"]
        total += run_window_arm(arm, BASE_SEED + k, STEPS, DIM, pressure, rates)["final_task_error"]
    return total / TRIALS


class TestDerivation(unittest.TestCase):
    """The window follows from the running_reference acceptance rule."""

    def test_l_corr_inverse_round_trip(self):
        """L_corr(L_corr^-1(y)) = y across six decades."""
        for y in (0.0, 1e-6, 1e-3, 0.0102, 0.5, 3.0):
            self.assertAlmostEqual(l_corr(l_corr_inverse(y)), y, places=12)

    def test_l_corr_inverse_rejects_bad_input(self):
        """Negative or non-finite input fails closed."""
        for y in (-1e-9, math.inf, math.nan):
            with self.assertRaises(ValueError):
                l_corr_inverse(y)

    def test_window_matches_dual_channel_verdicts(self):
        """Just inside each edge the verdict is as derived; just outside it flips."""
        eps = 1e-9
        for x_ref in (0.11, 0.1427, 0.19):
            lo, hi = derived_window(x_ref, 1, 3)
            self.assertTrue(_admits(x_ref, 1 * (hi - eps)))
            self.assertFalse(_admits(x_ref, 1 * (hi + eps)))
            self.assertTrue(_admits(x_ref, 3 * (lo - eps)))
            self.assertFalse(_admits(x_ref, 3 * (lo + eps)))

    def test_w_star_close_to_x_ref_for_small_moves(self):
        """For small x, L_corr(w) ~ w^2/2, so w* ~ x_ref (slightly above it)."""
        w = max_admissible_pressure(0.1427)
        self.assertGreater(w, 0.1427)
        self.assertLess(w, 0.1427 * 1.1)
        self.assertAlmostEqual(l_corr(w), h_kinetic(0.1427), places=12)

    def test_no_window_without_separation(self):
        """k_off must exceed k_on >= 1."""
        with self.assertRaises(ValueError):
            derived_window(0.14, 2, 2)
        with self.assertRaises(ValueError):
            derived_window(0.14, 0, 3)


class TestControl(unittest.TestCase):
    """The uninformative control ignores the move."""

    def test_control_ignores_move(self):
        """Two controls with the same seed give the same pressures for different moves."""
        rates = {"plane-critic": 0.5, "anchor-critic": 1.0, "subspace-critic": 0.4}
        a = control_pressure_fn(rates, 0.1, BASE_SEED)
        b = control_pressure_fn(rates, 0.1, BASE_SEED)
        on_plane, off_plane = [0.1, 0.0, 0.0], [0.0, 0.0, 5.0]
        self.assertEqual([a(on_plane, on_plane) for _ in range(50)],
                         [b(off_plane, off_plane) for _ in range(50)])

    def test_control_bad_inputs_fail_closed(self):
        """A negative pressure or an out-of-range rate raises ValueError."""
        rates = {"plane-critic": 0.5, "anchor-critic": 1.0, "subspace-critic": 0.4}
        with self.assertRaises(ValueError):
            control_pressure_fn(rates, -0.1, BASE_SEED)
        with self.assertRaises(ValueError):
            control_pressure_fn(dict(rates, **{"plane-critic": 1.5}), 0.1, BASE_SEED)

    def test_unknown_arm_and_missing_rates(self):
        """Unknown arms and a control without rates raise ValueError."""
        with self.assertRaises(ValueError):
            run_window_arm("nope", BASE_SEED, 1, DIM, 0.1)
        with self.assertRaises(ValueError):
            run_window_arm("control_running_reference", BASE_SEED, 1, DIM, 0.1)


class TestHarness(unittest.TestCase):
    """Receipt shape and input validation."""

    def test_receipt_shape(self):
        """The receipt carries the derivation, every arm, flags and the summary."""
        seeds = [BASE_SEED, BASE_SEED + 100, BASE_SEED + 200]
        r = run_pressure_window(trials=2, steps=5, dim=4, seeds=seeds, pressures=[0.1])
        self.assertIn("derived_window", r["derivation"])
        self.assertEqual(set(r["results"][str(BASE_SEED)]["sweep"]["0.1"]),
                         {"dual_running_reference", "control_running_reference", "dual_classic"})
        self.assertIn("running_reference_claim_constant_inside_documented_window", r["summary"])

    def test_invalid_inputs_fail_closed(self):
        """Bad sizes, too few seeds and bad sweeps raise ValueError."""
        with self.assertRaises(ValueError):
            run_pressure_window(trials=1, steps=1, dim=2)
        with self.assertRaises(ValueError):
            run_pressure_window(trials=1, steps=1, dim=4, seeds=[BASE_SEED])
        with self.assertRaises(ValueError):
            run_pressure_window(trials=1, steps=1, dim=4, pressures=[-0.1])


class TestDocumentedResults(unittest.TestCase):
    """Regression guards for the results recorded in PROVENANCE.md caveat 9."""

    def test_running_reference_beats_frozen_and_control_across_window(self):
        """At both window edges running_reference beats the frozen agent and the control."""
        for p in DOCUMENTED_WINDOW:
            err = _mean_err("dual_running_reference", p)
            self.assertLess(err, frozen_task_error() - 0.001)
            self.assertLess(err, _mean_err("control_running_reference", p))

    def test_high_pressure_freezes(self):
        """At 0.4 per rejection running_reference ends at the frozen agent's error."""
        self.assertAlmostEqual(_mean_err("dual_running_reference", 0.4), frozen_task_error(), places=6)


if __name__ == "__main__":
    unittest.main()

"""Tests for the ablation sweep harness.

Verifies that the constraint-pressure sweep produces non-trivial acceptance
rates: no arm should have acceptance_rate == 0 at every pressure (the regression
that motivated the sweep — at a single pressure of 0.5 the dual channel
rejected 2000/2000 proposals and the arm never moved).
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
for _p in (_REPO_ROOT / "core", _REPO_ROOT / "benchmarks"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from run_ablation import SWEEP_PRESSURES, run_ablation  # type: ignore


class TestAblationSweep(unittest.TestCase):
    """The ablation sweep must produce non-trivial acceptance rates."""

    @classmethod
    def setUpClass(cls):
        cls.receipt = run_ablation(
            trials=5, steps=20, dim=8,
            pressures=SWEEP_PRESSURES, base_seed=20260906,
        )

    def test_sweep_covers_all_pressures(self):
        """Every pressure in SWEEP_PRESSURES appears in the receipt."""
        sweep = self.receipt["sweep"]
        for p in SWEEP_PRESSURES:
            self.assertIn(str(p), sweep, f"pressure {p} missing from sweep")

    def test_all_arms_present_at_each_pressure(self):
        """All four arms appear at every pressure."""
        arms = {"gate_only", "gate_dual_channel", "gate_correction", "full"}
        sweep = self.receipt["sweep"]
        for p in SWEEP_PRESSURES:
            self.assertEqual(set(sweep[str(p)].keys()), arms)

    def test_no_arm_has_zero_acceptance_at_every_pressure(self):
        """No arm should reject 100% of proposals at every pressure in the sweep.

        This is the regression test requested in the PR review: at a single
        pressure of 0.5 the dual channel rejected 2000/2000 proposals and the
        arm never moved.  The sweep must include pressures where the dual
        channel does accept proposals, so the acceptance rate is non-zero at
        at least one pressure for every arm.
        """
        arm_names = self.receipt["sweep"][str(SWEEP_PRESSURES[0])].keys()
        for arm in arm_names:
            rates = [
                self.receipt["sweep"][str(p)][arm]["acceptance_rate"]
                for p in SWEEP_PRESSURES
            ]
            self.assertGreater(
                max(rates), 0.0,
                f"arm '{arm}' has acceptance_rate 0 at every pressure; "
                f"the dual channel rejects all proposals across the sweep"
            )

    def test_dual_channel_accepts_at_low_pressure(self):
        """At pressure 0 the dual-channel arms accept all proposals."""
        sweep = self.receipt["sweep"]
        p0 = sweep[str(0.0)]
        for arm in ("gate_dual_channel", "full"):
            self.assertGreater(
                p0[arm]["acceptance_rate"], 0.0,
                f"arm '{arm}' should accept proposals at pressure 0"
            )

    def test_gate_only_always_accepts(self):
        """gate_only and gate_correction have no scoring; acceptance is always 1.0."""
        sweep = self.receipt["sweep"]
        for p in SWEEP_PRESSURES:
            for arm in ("gate_only", "gate_correction"):
                self.assertEqual(
                    sweep[str(p)][arm]["acceptance_rate"], 1.0,
                    f"arm '{arm}' should always accept (no scoring) at pressure {p}"
                )

    def test_movement_tracks_acceptance(self):
        """When acceptance_rate is 0, mean_movement should also be 0
        (the state never leaves the anchor)."""
        sweep = self.receipt["sweep"]
        for p in SWEEP_PRESSURES:
            for arm in ("gate_dual_channel", "full"):
                m = sweep[str(p)][arm]
                if m["acceptance_rate"] == 0.0:
                    self.assertEqual(
                        m["mean_movement"], 0.0,
                        f"arm '{arm}' at pressure {p}: acceptance is 0 but "
                        f"movement is non-zero"
                    )


if __name__ == "__main__":
    unittest.main()

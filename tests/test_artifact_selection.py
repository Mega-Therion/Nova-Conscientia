"""Tests for the SAMO section 4 artifact selection function (core/).

The witness feeds below are hand-built fixtures in the exact schema MVPC-X
``mvpc.witness_feed`` emits (``mvpc-x/samo-v-mech-feed/1``); the yield must
be recomputed from the per-witness entries, never trusted from the feed.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
for _p in (_REPO_ROOT / "core", _REPO_ROOT / "verification"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from artifact_selection import (  # type: ignore
    FEED_SCHEMA,
    artifact_selection_score,
    hard_veto,
    mechanical_verification_yield,
)


def _entry(passed, total, integrity=True, unavailable=()):
    """One witness-feed entry, shaped like MVPC-X witness_feed output."""
    return {
        "witness_id": "W-TEST",
        "witness_hash": "b" * 64,
        "claim_id": "claim-1",
        "artifact_hash": "a" * 64,
        "attestation_state": "VERIFIED",
        "integrity_ok": integrity,
        "checks_performed": [],
        "checks_unavailable": list(unavailable),
        "violation_count": 0,
        "checks_passed": passed,
        "checks_total": total,
    }


def _feed(entries, stated=0.0):
    """A witness feed whose stated yield defaults to a wrong value."""
    return {"schema": FEED_SCHEMA, "v_mech": stated, "witnesses": entries}


class TestMechanicalVerificationYield(unittest.TestCase):
    """V_mech recomputation from MVPC-X witness feeds."""

    def test_all_checks_passed_yields_one(self):
        """A fully passed feed yields 1.0 regardless of its stated value."""
        v_mech, detail = mechanical_verification_yield(
            _feed([_entry(2, 2), _entry(3, 3)], stated=0.25)
        )
        self.assertEqual(v_mech, 1.0)
        self.assertEqual(detail["checks_passed"], 5)
        self.assertEqual(detail["checks_total"], 5)
        self.assertEqual(detail["feed_stated_v_mech"], 0.25)

    def test_partial_yield_is_the_check_ratio(self):
        """Yield is passed/total over all witness entries."""
        v_mech, _ = mechanical_verification_yield(
            _feed([_entry(2, 2), _entry(1, 2)])
        )
        self.assertEqual(v_mech, 0.75)

    def test_unavailable_checks_are_named_and_counted(self):
        """Checks that could not run surface by name and earn no yield."""
        v_mech, detail = mechanical_verification_yield(
            _feed([_entry(1, 2, unavailable=("Native Verification",))])
        )
        self.assertEqual(v_mech, 0.5)
        self.assertEqual(detail["checks_unavailable"], ["Native Verification"])

    def test_failed_integrity_earns_no_passed_checks(self):
        """A witness whose integrity flag is false contributes 0 passed."""
        v_mech, detail = mechanical_verification_yield(
            _feed([_entry(2, 2, integrity=False), _entry(1, 1)])
        )
        self.assertEqual(detail["checks_passed"], 1)
        self.assertEqual(detail["checks_total"], 3)
        self.assertAlmostEqual(v_mech, 1.0 / 3.0)

    def test_empty_feed_yields_zero(self):
        """No witnesses is no mechanical evidence: yield 0.0, fail closed."""
        v_mech, _ = mechanical_verification_yield(_feed([]))
        self.assertEqual(v_mech, 0.0)

    def test_wrong_schema_is_rejected(self):
        """A feed in any other schema is refused, not scored."""
        with self.assertRaises(ValueError):
            mechanical_verification_yield({"schema": "other/9", "witnesses": []})

    def test_inconsistent_counts_are_rejected(self):
        """passed > total is a malformed entry and fails closed."""
        with self.assertRaises(ValueError):
            mechanical_verification_yield(_feed([_entry(3, 2)]))


class TestArtifactSelectionScore(unittest.TestCase):
    """The multiplicative F(x) = V_hard * V_mech * B_bridge * H_local."""

    def test_full_product(self):
        """All axes at their maxima score 1.0."""
        score = artifact_selection_score(
            v_hard=1, b_bridge=1.0, h_local=1.0,
            witness_feed=_feed([_entry(4, 4)]),
        )
        self.assertEqual(score.score, 1.0)
        self.assertEqual(score.v_mech, 1.0)
        self.assertEqual(score.checks_total, 4)

    def test_hard_veto_zeroes_everything(self):
        """V_hard = 0 cannot be bought back by the other axes."""
        score = artifact_selection_score(
            v_hard=0, b_bridge=1.0, h_local=1.0,
            witness_feed=_feed([_entry(4, 4)]),
        )
        self.assertEqual(score.score, 0.0)

    def test_witness_feed_wires_into_v_mech(self):
        """The MVPC-X feed drives V_mech and hence the product."""
        score = artifact_selection_score(
            v_hard=1, b_bridge=0.5, h_local=0.5,
            witness_feed=_feed([_entry(1, 2, unavailable=("Z3",))]),
        )
        self.assertEqual(score.v_mech, 0.5)
        self.assertEqual(score.score, 0.125)
        self.assertEqual(score.checks_unavailable, ("Z3",))

    def test_explicit_v_mech_path(self):
        """An explicit yield scores without inventing check coverage."""
        score = artifact_selection_score(
            v_hard=1, b_bridge=0.5, h_local=1.0, v_mech=0.5
        )
        self.assertEqual(score.score, 0.25)
        self.assertEqual(score.checks_total, 0)

    def test_exactly_one_yield_source(self):
        """Both or neither yield source is a configuration error."""
        with self.assertRaises(ValueError):
            artifact_selection_score(v_hard=1, b_bridge=1.0, h_local=1.0)
        with self.assertRaises(ValueError):
            artifact_selection_score(
                v_hard=1, b_bridge=1.0, h_local=1.0,
                witness_feed=_feed([]), v_mech=0.5,
            )

    def test_out_of_range_axes_are_rejected(self):
        """Axes outside [0, 1] (and a non-bit veto) fail closed."""
        with self.assertRaises(ValueError):
            artifact_selection_score(
                v_hard=1, b_bridge=1.5, h_local=1.0, v_mech=0.5
            )
        with self.assertRaises(ValueError):
            artifact_selection_score(
                v_hard=2, b_bridge=1.0, h_local=1.0, v_mech=0.5
            )

    def test_receipt_is_deterministic(self):
        """Identical inputs produce identical receipts."""
        kwargs = dict(v_hard=1, b_bridge=0.5, h_local=0.5, v_mech=0.5)
        first = artifact_selection_score(**kwargs)
        second = artifact_selection_score(**kwargs)
        self.assertEqual(first.receipt_hexdigest(), second.receipt_hexdigest())


class TestHardVeto(unittest.TestCase):
    """V_hard composition from the Ring-0 pre-scoring checks."""

    def test_all_checks_hold(self):
        """Schema + signature + anti-fabrication + gate pass give 1."""
        self.assertEqual(
            hard_veto(
                schema_valid=True, signature_valid=True,
                antifabrication_ok=True, gate_verdict="PASS",
            ),
            1,
        )

    def test_any_failed_check_vetoes(self):
        """Each Ring-0 check is individually non-purchasable."""
        base = dict(
            schema_valid=True, signature_valid=True, antifabrication_ok=True
        )
        for key in base:
            broken = dict(base, **{key: False})
            self.assertEqual(hard_veto(**broken), 0, key)

    def test_gate_reject_vetoes(self):
        """A sovereign clipping gate REJECT is a hard veto on its own."""
        self.assertEqual(
            hard_veto(
                schema_valid=True, signature_valid=True,
                antifabrication_ok=True, gate_verdict="REJECT",
            ),
            0,
        )

    def test_unknown_gate_verdict_fails_closed(self):
        """A verdict outside PASS/CLIP/REJECT is not a gate result: veto."""
        for verdict in ("PAS", "reject", "UNKNOWN", "", "PASS "):
            self.assertEqual(
                hard_veto(
                    schema_valid=True, signature_valid=True,
                    antifabrication_ok=True, gate_verdict=verdict,
                ),
                0,
                verdict,
            )

    def test_gate_clip_does_not_veto(self):
        """A clipped (boundary-projected) state is not a veto."""
        self.assertEqual(
            hard_veto(
                schema_valid=True, signature_valid=True,
                antifabrication_ok=True, gate_verdict="CLIP",
            ),
            1,
        )


if __name__ == "__main__":
    unittest.main()

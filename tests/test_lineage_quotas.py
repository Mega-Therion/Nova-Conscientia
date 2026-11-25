"""Tests for the SAMO section 5.3 Layer-0 lineage quotas in the auditor.

Rule under test: with a cap of N, no single base-model lineage may hold
more than a 1/N share of an AdversarialConsensus panel.  Over-quota panels
are refused at construction (fail closed); at-quota panels deliberate
normally; with no cap configured, behavior is unchanged.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
for _p in (_REPO_ROOT / "core", _REPO_ROOT / "verification"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from adversarial_auditor import (  # type: ignore
    AdversarialConsensus,
    CriticAuditor,
    InvariantAuditor,
    ProvenanceAuditor,
    lineage_counts,
    lineage_of,
    lineage_quota_violations,
)


def _approve(proposal, context):
    """A critic callable that always approves."""
    return {"verdict": "APPROVE", "reason": "ok"}


def _critic(auditor_id, lineage=None):
    """A pluggable critic seat with an optional declared lineage."""
    return CriticAuditor(_approve, auditor_id=auditor_id, lineage=lineage)


def _proposal():
    """A well-formed proposal the builtin auditors admit."""
    return {
        "source": "tests",
        "source_sha256": "deadbeef",
        "parents": [],
        "writes": {"k": 1},
    }


class TestLineageAccounting(unittest.TestCase):
    """Lineage is counted from the auditors' own identity fields."""

    def test_declared_lineage_wins(self):
        """A critic's declared lineage is its quota identity."""
        self.assertEqual(lineage_of(_critic("seat-1", lineage="family-x")), "family-x")

    def test_undeclared_falls_back_to_auditor_id(self):
        """No declared lineage: the auditor is its own lineage of one."""
        self.assertEqual(lineage_of(_critic("seat-1")), "seat-1")
        self.assertEqual(lineage_of(ProvenanceAuditor()), "provenance-auditor")

    def test_counts_group_by_lineage(self):
        """Distinct seats of one family count together."""
        panel = [
            _critic("a", lineage="family-x"),
            _critic("b", lineage="family-x"),
            _critic("c", lineage="family-y"),
        ]
        self.assertEqual(lineage_counts(panel), {"family-x": 2, "family-y": 1})


class TestQuotaCheck(unittest.TestCase):
    """The standalone 1/N share check."""

    def test_over_quota_is_reported(self):
        """Three of three seats from one lineage breaks a 1/3 cap."""
        panel = [_critic(s, lineage="family-x") for s in ("a", "b", "c")]
        violations = lineage_quota_violations(panel, 3)
        self.assertEqual(len(violations), 1)
        self.assertIn("family-x", violations[0])

    def test_at_quota_passes(self):
        """A share exactly equal to 1/N is within quota."""
        panel = [
            _critic("a", lineage="family-x"),
            _critic("b", lineage="family-x"),
            _critic("c", lineage="family-y"),
            _critic("d", lineage="family-z"),
        ]
        self.assertEqual(lineage_quota_violations(panel, 2), ())

    def test_distinct_builtins_pass_tight_cap(self):
        """The three distinct builtin kernels satisfy an N=3 cap."""
        panel = [
            InvariantAuditor({}),
            ProvenanceAuditor(),
            _critic("critic-a", lineage="family-x"),
        ]
        self.assertEqual(lineage_quota_violations(panel, 3), ())

    def test_nonpositive_cap_is_rejected(self):
        """A cap of N < 1 is a configuration error, not a silent pass."""
        with self.assertRaises(ValueError):
            lineage_quota_violations([_critic("a")], 0)


class TestConsensusEnforcement(unittest.TestCase):
    """AdversarialConsensus refuses over-quota panels at construction."""

    def test_over_quota_panel_is_rejected(self):
        """One lineage holding the whole panel breaks the cap: no engine."""
        panel = [_critic(s, lineage="family-x") for s in ("a", "b", "c")]
        with self.assertRaises(ValueError) as caught:
            AdversarialConsensus(panel, quorum=2, lineage_cap_n=3)
        self.assertIn("lineage quota", str(caught.exception))

    def test_at_quota_panel_deliberates_and_admits(self):
        """An at-quota panel constructs and admits a clean proposal."""
        panel = [
            _critic("a", lineage="family-x"),
            _critic("b", lineage="family-x"),
            InvariantAuditor({}),
            ProvenanceAuditor(),
        ]
        engine = AdversarialConsensus(panel, quorum=2, lineage_cap_n=2)
        receipt = engine.deliberate(_proposal())
        self.assertTrue(receipt.admitted)
        self.assertEqual(receipt.approvals, 4)

    def test_no_cap_keeps_legacy_behavior(self):
        """Without a cap, a single-lineage panel still constructs."""
        panel = [_critic(s, lineage="family-x") for s in ("a", "b", "c")]
        engine = AdversarialConsensus(panel, quorum=2)
        receipt = engine.deliberate(_proposal())
        self.assertTrue(receipt.admitted)


if __name__ == "__main__":
    unittest.main()

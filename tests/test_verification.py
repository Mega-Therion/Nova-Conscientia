"""Tests for the verification layer: adversarial consensus and the AST gate."""

from __future__ import annotations

import ast
import sys
import textwrap
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
for _p in (_REPO_ROOT / "core", _REPO_ROOT / "verification", _REPO_ROOT / "benchmarks"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from adversarial_auditor import (  # type: ignore
    APPROVE,
    REJECT,
    AdversarialConsensus,
    ConsistencyAuditor,
    CriticAuditor,
    InvariantAuditor,
    ProvenanceAuditor,
    proposal_digest,
)
from ast_invariant_validation import (  # type: ignore
    Violation,
    validate_module,
    validate_paths,
)


def _proposal(writes=None, source="tests", sha="deadbeef"):
    """Build a well-formed proposal for the consensus tests."""
    return {
        "source": source,
        "source_sha256": sha,
        "parents": [],
        "writes": writes or {},
    }


class TestAdversarialConsensus(unittest.TestCase):
    """The fail-closed quorum engine."""

    def _engine(self, ledger=None, quorum=2):
        """A standard three-auditor engine over a fresh ledger."""
        ledger = ledger if ledger is not None else {}
        auditors = [
            InvariantAuditor({
                "nonempty": lambda p, c: len(p.get("writes", {})) >= 1,
            }),
            ConsistencyAuditor(ledger),
            ProvenanceAuditor(),
        ]
        return AdversarialConsensus(auditors, quorum=quorum), ledger

    def test_clean_proposal_is_admitted(self):
        """A consistent, provenance-carrying proposal clears the quorum."""
        engine, ledger = self._engine()
        receipt = engine.commit(_proposal({"key": "value"}), ledger)
        self.assertTrue(receipt.admitted)
        self.assertEqual(receipt.approvals, 3)
        self.assertEqual(ledger, {"key": "value"})

    def test_invariant_failure_vetoes(self):
        """A failing hard invariant is fatal: quorum cannot override it."""
        engine, ledger = self._engine()
        receipt = engine.deliberate(_proposal({}))  # nonempty invariant fails
        self.assertFalse(receipt.admitted)
        self.assertEqual(receipt.vetoes, 1)
        self.assertEqual(ledger, {})

    def test_consistency_rejects_contradiction(self):
        """A write contradicting the ledger is rejected (non-fatal)."""
        engine, ledger = self._engine()
        ledger["key"] = "old"
        receipt = engine.commit(_proposal({"key": "new"}), ledger)
        self.assertFalse(receipt.admitted)
        self.assertEqual(ledger["key"], "old")
        self.assertGreaterEqual(receipt.rejections, 1)

    def test_provenance_is_fatal(self):
        """Missing provenance fails closed."""
        engine, _ = self._engine()
        receipt = engine.deliberate({"source": "", "source_sha256": None,
                                     "parents": [], "writes": {"k": "v"}})
        self.assertFalse(receipt.admitted)
        self.assertGreaterEqual(receipt.vetoes, 1)

    def test_critic_contract(self):
        """A compliant critic approves; garbage output fails closed."""
        good = CriticAuditor(lambda p, c: {"verdict": APPROVE, "reason": "fine"},
                              auditor_id="critic-good")
        bad_shape = CriticAuditor(lambda p, c: "looks fine to me",
                                  auditor_id="critic-bad-shape")
        raising = CriticAuditor(lambda p, c: 1 / 0, auditor_id="critic-raising")
        engine = AdversarialConsensus(
            [good, bad_shape, raising, ProvenanceAuditor()], quorum=3
        )
        receipt = engine.deliberate(_proposal({"k": "v"}))
        # good approves; the malformed and raising critics fail closed fatally.
        self.assertFalse(receipt.admitted)
        self.assertEqual(receipt.approvals, 2)  # good + provenance
        self.assertEqual(receipt.vetoes, 2)

    def test_receipts_are_deterministic(self):
        """Identical deliberations produce identical receipt digests."""
        engine, _ = self._engine()
        r1 = engine.deliberate(_proposal({"k": "v"}))
        r2 = engine.deliberate(_proposal({"k": "v"}))
        self.assertEqual(r1.receipt_hexdigest(), r2.receipt_hexdigest())
        self.assertEqual(r1.proposal_digest, proposal_digest(_proposal({"k": "v"})))

    def test_misconfiguration_fails_closed(self):
        """No auditors, impossible quorum, or duplicate ids refuse to run."""
        with self.assertRaises(ValueError):
            AdversarialConsensus([], quorum=1)
        with self.assertRaises(ValueError):
            AdversarialConsensus([ProvenanceAuditor()], quorum=2)
        dup = [ProvenanceAuditor(), ProvenanceAuditor()]
        with self.assertRaises(ValueError):
            AdversarialConsensus(dup, quorum=1)

    def test_summary(self):
        """The receipt log aggregates correctly."""
        engine, _ = self._engine()
        engine.deliberate(_proposal({"k": "v"}))
        engine.deliberate(_proposal({}))
        summary = engine.summary()
        self.assertEqual(summary["deliberations"], 2)
        self.assertEqual(summary["admitted"], 1)
        self.assertEqual(summary["vetoed"], 1)


class TestASTInvariantValidation(unittest.TestCase):
    """The compile-time zero-stub / grounded-numerology gate."""

    def _validate_source(self, source, name="probe.py"):
        """Validate a source string written to a temp file."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / name
            path.write_text(textwrap.dedent(source), encoding="utf-8")
            return validate_module(path)

    def test_clean_module_passes(self):
        """A documented, provenance-registered module passes with no violations."""
        source = '''
            PROVENANCE = {"CONST": "test constant"}
            CONST = 3.5

            def documented(x):
                """Return twice x."""
                return 2 * x
        '''
        violations = self._validate_source(source)
        self.assertEqual(violations, [])

    def test_stub_bodies_are_rejected(self):
        """pass-only, ellipsis-only, and NotImplementedError bodies fail Z1."""
        for body in ("pass", "...", "raise NotImplementedError"):
            with self.subTest(body=body):
                source = f'''
                    def unfinished(x):
                        """Doc."""
                        {body}
                '''
                violations = self._validate_source(source)
                self.assertTrue(any(v.rule.startswith("Z1") for v in violations),
                                violations)

    def test_unregistered_numeric_constant_is_rejected(self):
        """A numeric constant missing from PROVENANCE fails Z2."""
        source = '''
            MYSTERY = 0.9539
        '''
        violations = self._validate_source(source)
        self.assertTrue(any(v.rule.startswith("Z2") for v in violations),
                        violations)

    def test_registered_numeric_constant_passes(self):
        """The same constant registered in PROVENANCE passes Z2."""
        source = '''
            PROVENANCE = {"MYSTERY": "measured threshold (test)"}
            MYSTERY = 0.9539
        '''
        violations = self._validate_source(source)
        self.assertEqual(violations, [])

    def test_banned_constructs(self):
        """eval, exec, and bare except are rejected by Z3."""
        for call in ("eval(s)", "exec(s)"):
            with self.subTest(call=call):
                source = f'''
                    def f(s):
                        """Run."""
                        return {call}
                '''
                violations = self._validate_source(source)
                self.assertTrue(any(v.rule.startswith("Z3") for v in violations))
        source = '''
            def f():
                """Catch."""
                try:
                    x = 1
                except:
                    x = 2
                return x
        '''
        violations = self._validate_source(source)
        self.assertTrue(any(v.rule.startswith("Z3") for v in violations))

    def test_undocumented_public_callable(self):
        """A public function without a docstring fails Z4."""
        source = '''
            def silent(x):
                return x
        '''
        violations = self._validate_source(source)
        self.assertTrue(any(v.rule.startswith("Z4") for v in violations))

    def test_unparseable_module_fails_closed(self):
        """A syntax error yields a single Z5 violation, not a skip."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "broken.py"
            path.write_text("def broken(:\n    pass\n", encoding="utf-8")
            violations = validate_module(path)
            self.assertEqual(len(violations), 1)
            self.assertTrue(violations[0].rule.startswith("Z5"))

    def test_repository_packages_pass(self):
        """The actual repository core/ and verification/ pass the gate."""
        violations, checked = validate_paths(
            [_REPO_ROOT / "core", _REPO_ROOT / "verification",
             _REPO_ROOT / "benchmarks"]
        )
        self.assertEqual(violations, [])
        self.assertGreater(checked, 0)


if __name__ == "__main__":
    unittest.main()

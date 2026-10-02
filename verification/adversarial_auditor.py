"""Multi-agent adversarial consensus runner.

Translation target (Res-Nova / gAIng -> Nova Conscientia)
---------------------------------------------------------
The gAIng swarm of the Chyren stack runs heterogeneous model workers that
cross-audit proposed outputs before they are committed (the third engine of the
Trinity).  The Res-Nova corpus adds the standing rule that a verification gate
must *fail closed*: a check that cannot run is a failed check, never a passed
one (SELIN fail-closed verifier logic, classified P0 in the 2026-09 priority
review; gAIng v0.1.0 7-step cyclic engine with SELIN verification gates).

This module implements the consensus layer:

* ``Auditor``: a named, independent reviewer with an ``audit(proposal, context)``
  method returning a structured ``Audit`` verdict.  Builtin auditors cover
  invariant checking, ledger consistency, provenance checking, and a pluggable
  critic (any callable, e.g. a heterogeneous LLM from the swarm).
* ``AdversarialConsensus``: a fail-closed quorum engine.  A proposal is admitted
  only when (a) at least ``quorum`` auditors approve, (b) no auditor raises a
  fatal (veto) finding, and (c) every auditor actually returned a well-formed
  verdict.  Any exception, malformed output, or auditor absence fails the
  proposal.  Verdicts are hashed into deterministic receipts appended to a
  monotonic ledger.

No LLM keys or network calls are required: the deterministic builtin auditors
are complete implementations, and the pluggable critic accepts any callable
satisfying the documented contract (used to attach real model workers when the
gAIng swarm is wired in).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Protocol, Sequence, Tuple

#: Verdict constants for a single auditor's finding.
APPROVE = "APPROVE"
REJECT = "REJECT"


def _stable_json(obj: Any) -> str:
    """Deterministic JSON encoding (sorted keys) for receipts.

    Raises:
        TypeError: if the object is not JSON-serializable (fail closed).
    """
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=repr)


def proposal_digest(proposal: Dict[str, Any]) -> str:
    """SHA-256 hex digest of a proposal's canonical form (its identity)."""
    return hashlib.sha256(_stable_json(proposal).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Audit:
    """One auditor's finding on one proposal.

    Attributes:
        auditor_id: which auditor produced this finding.
        verdict: APPROVE or REJECT.
        fatal: True marks a veto finding: no quorum can override it.
        findings: structured notes supporting the verdict (JSON-serializable).
        reason: one-line human-readable justification.
    """

    auditor_id: str
    verdict: str
    fatal: bool = False
    findings: Tuple[str, ...] = ()
    reason: str = ""

    def receipt_hexdigest(self, proposal: Dict[str, Any]) -> str:
        """Deterministic SHA-256 receipt over (proposal identity, finding)."""
        payload = _stable_json(
            {"proposal": proposal_digest(proposal), "audit": {
                "auditor_id": self.auditor_id,
                "verdict": self.verdict,
                "fatal": self.fatal,
                "findings": list(self.findings),
                "reason": self.reason,
            }}
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class Auditor(Protocol):
    """The auditor contract: an independent reviewer of proposals."""

    auditor_id: str

    def audit(self, proposal: Dict[str, Any], context: Dict[str, Any]) -> Audit:
        """Return a structured finding; never raise on well-formed input."""
        ...


@dataclass
class InvariantAuditor:
    """Checks a proposal against a registry of hard invariants.

    Each invariant maps a name to a predicate over (proposal, context).  An
    invariant that raises is treated as a REJECT with its exception text as the
    finding (fail closed).

    Attributes:
        invariants: ordered mapping of invariant name -> predicate.  A predicate
            returns True when the invariant HOLDS.
    """

    invariants: Dict[str, Callable[[Dict[str, Any], Dict[str, Any]], bool]]
    auditor_id: str = "invariant-auditor"

    def audit(self, proposal: Dict[str, Any], context: Dict[str, Any]) -> Audit:
        """Evaluate every invariant; any failure is a fatal reject."""
        failures: List[str] = []
        for name, predicate in self.invariants.items():
            try:
                if not predicate(proposal, context):
                    failures.append(f"invariant '{name}' does not hold")
            except Exception as exc:  # noqa: BLE001 - fail closed on any error
                failures.append(f"invariant '{name}' raised {type(exc).__name__}: {exc}")
        if failures:
            return Audit(self.auditor_id, REJECT, fatal=True, findings=tuple(failures),
                         reason="; ".join(failures))
        return Audit(self.auditor_id, APPROVE,
                     reason=f"all {len(self.invariants)} invariants hold")


@dataclass
class ConsistencyAuditor:
    """Cross-checks a proposal against the committed ledger.

    The ledger is the monotonic state of already-admitted facts.  A proposal is
    consistent iff it does not rewrite an existing key with a different value
    (contradiction) and does not forge a parent that is absent from the ledger
    (ungrounded reference).

    Attributes:
        ledger: the shared committed state (mutable dict of key -> value).
    """

    ledger: Dict[str, Any]
    auditor_id: str = "consistency-auditor"

    def audit(self, proposal: Dict[str, Any], context: Dict[str, Any]) -> Audit:
        """Reject contradictions with the ledger and ungrounded references."""
        findings: List[str] = []
        for key, value in proposal.get("writes", {}).items():
            if key in self.ledger and self.ledger[key] != value:
                findings.append(
                    f"contradiction: ledger[{key!r}] = {self.ledger[key]!r} "
                    f"but proposal writes {value!r}"
                )
        for parent in proposal.get("parents", ()):
            if parent not in self.ledger:
                findings.append(f"ungrounded reference: {parent!r} not in ledger")
        if findings:
            return Audit(self.auditor_id, REJECT, fatal=False, findings=tuple(findings),
                         reason="; ".join(findings))
        return Audit(self.auditor_id, APPROVE, reason="consistent with ledger")


@dataclass
class ProvenanceAuditor:
    """Requires every proposal to carry machine-checkable provenance.

    The Contingent Box Protocol demands full provenance on every artifact; this
    auditor rejects proposals that lack (source, source_sha256) fields or whose
    source field is empty.

    Attributes:
        required_fields: provenance fields every proposal must carry.
    """

    required_fields: Tuple[str, ...] = ("source", "source_sha256")
    auditor_id: str = "provenance-auditor"

    def audit(self, proposal: Dict[str, Any], context: Dict[str, Any]) -> Audit:
        """Reject proposals without complete provenance fields."""
        findings: List[str] = []
        for f in self.required_fields:
            value = proposal.get(f)
            if value is None or (isinstance(value, str) and not value.strip()):
                findings.append(f"missing provenance field {f!r}")
        if findings:
            return Audit(self.auditor_id, REJECT, fatal=True, findings=tuple(findings),
                         reason="; ".join(findings))
        return Audit(self.auditor_id, APPROVE, reason="provenance complete")


@dataclass
class CriticAuditor:
    """Pluggable heterogeneous critic (e.g. an LLM from the gAIng swarm).

    The wrapped callable receives ``(proposal, context)`` and must return
    anything JSON-serializable of the form
    ``{"verdict": "APPROVE"|"REJECT", "reason": str, "fatal": bool}`` (extra keys
    ignored).  Anything else -- malformed shape, unknown verdict, raised
    exception -- is a fail-closed fatal REJECT: a critic that cannot articulate
    an approval is treated as a rejection.

    Attributes:
        critic: the callable performing the review.
        auditor_id: this auditor's stable identity.
    """

    critic: Callable[[Dict[str, Any], Dict[str, Any]], Any]
    auditor_id: str = "critic-auditor"

    def audit(self, proposal: Dict[str, Any], context: Dict[str, Any]) -> Audit:
        """Run the critic under a fail-closed output contract."""
        try:
            raw = self.critic(proposal, context)
            if not isinstance(raw, dict):
                raise TypeError(f"critic returned {type(raw).__name__}, expected dict")
            verdict = raw.get("verdict")
            if verdict not in (APPROVE, REJECT):
                raise TypeError(f"critic verdict {verdict!r} not in ({APPROVE!r}, {REJECT!r})")
            reason = raw.get("reason", "")
            if not isinstance(reason, str):
                raise TypeError("critic reason must be a string")
            fatal = bool(raw.get("fatal", verdict == REJECT))
        except Exception as exc:  # noqa: BLE001 - fail closed on any critic failure
            return Audit(self.auditor_id, REJECT, fatal=True,
                         findings=(f"critic failure: {type(exc).__name__}: {exc}",),
                         reason="critic did not produce a well-formed verdict")
        return Audit(self.auditor_id, verdict, fatal=fatal, reason=reason)


@dataclass(frozen=True)
class ConsensusReceipt:
    """The consensus outcome for one proposal.

    Attributes:
        proposal_digest: identity of the audited proposal.
        admitted: True iff quorum approved and no veto and all auditors ran.
        approvals: number of APPROVE verdicts.
        rejections: number of REJECT verdicts.
        vetoes: number of fatal REJECT verdicts (any veto blocks admission).
        verdicts: the individual audit records.
    """

    proposal_digest: str
    admitted: bool
    approvals: int
    rejections: int
    vetoes: int
    verdicts: Tuple[Audit, ...]

    def receipt_hexdigest(self) -> str:
        """Deterministic SHA-256 receipt over the full deliberation."""
        payload = _stable_json({
            "proposal": self.proposal_digest,
            "admitted": self.admitted,
            "approvals": self.approvals,
            "rejections": self.rejections,
            "vetoes": self.vetoes,
            "audits": [
                {"auditor_id": a.auditor_id, "verdict": a.verdict, "fatal": a.fatal}
                for a in self.verdicts
            ],
        })
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass
class AdversarialConsensus:
    """Fail-closed multi-auditor quorum over a stream of proposals.

    Attributes:
        auditors: the reviewing swarm (>= 1).
        quorum: minimum APPROVE count required for admission.
        receipts: monotonic append-only receipt log of every deliberation.
    """

    auditors: Sequence[Auditor]
    quorum: int = 2
    receipts: List[ConsensusReceipt] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate the configuration; fail closed on a misconfigured engine.

        Raises:
            ValueError: with no auditors, a non-positive quorum, a quorum that
                no number of auditors can satisfy, or duplicate auditor ids.
        """
        if not self.auditors:
            raise ValueError("consensus requires at least one auditor")
        if len({a.auditor_id for a in self.auditors}) != len(self.auditors):
            raise ValueError("auditor ids must be unique")
        if self.quorum < 1:
            raise ValueError(f"quorum must be >= 1, got {self.quorum}")
        if self.quorum > len(self.auditors):
            raise ValueError(
                f"quorum {self.quorum} exceeds auditor count {len(self.auditors)}"
            )

    def deliberate(self, proposal: Dict[str, Any]) -> ConsensusReceipt:
        """Run every auditor on ``proposal`` and decide admission, fail-closed.

        An auditor that raises is recorded as a fatal REJECT (fail closed: a
        check that cannot run is a failed check).

        Args:
            proposal: a JSON-serializable mapping with provenance fields.

        Returns:
            The ConsensusReceipt (also appended to ``receipts``).
        """
        context: Dict[str, Any] = {"receipt_count": len(self.receipts)}
        verdicts: List[Audit] = []
        for auditor in self.auditors:
            try:
                finding = auditor.audit(proposal, context)
                if not isinstance(finding, Audit):
                    raise TypeError(
                        f"auditor {auditor.auditor_id!r} returned "
                        f"{type(finding).__name__}, expected Audit"
                    )
                if finding.verdict not in (APPROVE, REJECT):
                    raise TypeError(
                        f"auditor {auditor.auditor_id!r} returned malformed verdict "
                        f"{finding.verdict!r}"
                    )
            except Exception as exc:  # noqa: BLE001 - fail closed
                finding = Audit(
                    auditor.auditor_id, REJECT, fatal=True,
                    findings=(f"auditor failure: {type(exc).__name__}: {exc}",),
                    reason="auditor did not produce a well-formed finding",
                )
            verdicts.append(finding)

        approvals = sum(1 for v in verdicts if v.verdict == APPROVE)
        rejections = sum(1 for v in verdicts if v.verdict == REJECT)
        vetoes = sum(1 for v in verdicts if v.verdict == REJECT and v.fatal)
        admitted = approvals >= self.quorum and vetoes == 0 and rejections == 0
        receipt = ConsensusReceipt(
            proposal_digest=proposal_digest(proposal),
            admitted=admitted,
            approvals=approvals,
            rejections=rejections,
            vetoes=vetoes,
            verdicts=tuple(verdicts),
        )
        self.receipts.append(receipt)
        return receipt

    def commit(self, proposal: Dict[str, Any], ledger: Dict[str, Any]) -> ConsensusReceipt:
        """Deliberate and, iff admitted, write the proposal into the ledger.

        The ledger is updated only through keys in ``proposal["writes"]``;
        ``proposal["parents"]`` is recorded in the context for consistency
        audits on later proposals.

        Args:
            proposal: the proposal to deliberate on.
            ledger: the shared state to write into on admission.

        Returns:
            The ConsensusReceipt of the deliberation.
        """
        receipt = self.deliberate(proposal)
        if receipt.admitted:
            for key, value in proposal.get("writes", {}).items():
                ledger[key] = value
        return receipt

    def summary(self) -> Dict[str, int]:
        """Aggregate counts over the receipt log."""
        return {
            "deliberations": len(self.receipts),
            "admitted": sum(1 for r in self.receipts if r.admitted),
            "vetoed": sum(1 for r in self.receipts if r.vetoes > 0),
        }

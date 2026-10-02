"""Sovereign Clipping Gate: information-theoretic hallucination clipping.

Translation target (Res-Nova -> Nova Conscientia)
--------------------------------------------------
The Res-Nova corpus carries a measured anti-drift threshold: watching autonomous
reasoning loops degrade, the collapse boundary was set where the cosine similarity
between the reasoning state and its task anchor stopped holding.  That measured value
is tau = 0.9539 (Res-Nova ALIGNMENT_CEILING_ONE_RELATION.md, measured 2026-09-06 on
ADCCL reasoning loops).  The corpus is explicit that this is

* a *measured engineering threshold* on *one* pipeline, "not validated against
  external agent systems or alternative LLM providers", and
* in convergence (Delta = 3.9e-5), not identity, with the two-channel band ceiling
  sqrt(theta(2-theta)) evaluated at theta = 0.7 = 0.953939... -- and equally close
  numerically to, but distinct from, the independently derived spin ceiling
  chi_s = sqrt(sqrt(2) - 1/2) = 0.956145... at theta = 1/sqrt(2).

This module encodes exactly that epistemic status.  It provides:

1. The two-channel union function and its exact inverse (Res-Nova
   TWO_CHANNEL_CEILING_ANALYSIS.md, Finding 1: the map is injective on [0, 1]).
2. The three catalogued ceiling constants with full provenance.
3. A fail-closed clipping gate: a state vector that drifts outside the acceptance
   cone around its task anchor (cosine similarity below the threshold) is either
   rejected or projected onto the boundary of the cone, and the clipped-off
   component is reported as dissipated (hallucinated) information.

All numerology in this file is grounded: every constant is registered in the
module-level PROVENANCE mapping and validated by verification/ast_invariant_validation.py.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

# ---------------------------------------------------------------------------
# Constants (all registered in PROVENANCE below; see module docstring).
# ---------------------------------------------------------------------------

#: Measured collapse boundary on ADCCL reasoning loops (engineering threshold).
MEASURED_TAU = 0.9539

#: theta = 1/sqrt(2): the equipartition floor, cos 45 deg, derived three ways.
FLOOR_THETA_EQUIPARTITION = 1.0 / math.sqrt(2.0)

PROVENANCE: Dict[str, str] = {
    "MEASURED_TAU": (
        "Measured ADCCL reasoning-loop collapse boundary, Res-Nova "
        "ALIGNMENT_CEILING_ONE_RELATION.md (measured 2026-09-06). Single-pipeline "
        "engineering threshold; NOT validated on external agent systems."
    ),
    "FLOOR_THETA_EQUIPARTITION": (
        "theta = 1/sqrt(2) = cos 45 deg, the equipartition floor. Res-Nova "
        "RapidityEquipartition.lean / ALIGNMENT_CEILING_ONE_RELATION.md: "
        "sinh(psi) = 1 implies gamma = sqrt(2), theta = tanh(psi) = 1/sqrt(2)."
    ),
}


def two_channel_union(theta: float) -> float:
    """Two-channel union probability P(at least one of two channels aligns).

    Exact algebra: 1 - (1 - theta)^2 = theta (2 - theta).  Proved as
    ``twoChannelUnion_eq`` in Res-Nova 05_lean_formalization/PillarIV_AntiDriftGate.lean.

    Args:
        theta: per-channel alignment fraction in [0, 1].

    Returns:
        The union probability theta * (2 - theta) in [0, 1].

    Raises:
        ValueError: if theta is outside [0, 1].
    """
    if not 0.0 <= theta <= 1.0:
        raise ValueError(f"theta must lie in [0, 1], got {theta}")
    return theta * (2.0 - theta)


def kappa_of_theta(theta: float) -> float:
    """Ceiling kappa = sqrt(theta (2 - theta)): the direction-cosine ceiling.

    One function evaluated at two arguments gives the two catalogued ceilings
    (Res-Nova TWO_CHANNEL_CEILING_ANALYSIS.md): theta = 0.7 -> 0.953939...
    (band ceiling, historical), theta = 1/sqrt(2) -> 0.956145... (spin ceiling,
    independently derived three ways).
    """
    if not 0.0 <= theta <= 1.0:
        raise ValueError(f"theta must lie in [0, 1], got {theta}")
    return math.sqrt(two_channel_union(theta))


def theta_of_kappa(kappa: float) -> float:
    """Exact inverse of kappa_of_theta on [0, 1]: theta = 1 - sqrt(1 - kappa^2).

    Finding 1 of Res-Nova TWO_CHANNEL_CEILING_ANALYSIS.md: the map is injective,
    so quoting a ceiling pins the floor.  kappa = 0.953939 -> theta = 0.699999;
    kappa = 0.956145 -> theta = 0.707106.
    """
    if not 0.0 <= kappa <= 1.0:
        raise ValueError(f"kappa must lie in [0, 1], got {kappa}")
    return 1.0 - math.sqrt(1.0 - kappa * kappa)


def band_ceiling_at_seven_tenths() -> float:
    """Historical band ceiling sqrt(theta(2-theta)) at theta = 7/10 = 0.953939...

    Proved as ``kappaBand_at_seven_tenths`` in PillarIV_AntiDriftGate.lean, which
    retains it explicitly as *historical record*, not as corpus doctrine: the
    provenance of theta = 7/10 failed audit on 2026-09-24 (SovereignSpinCeiling.lean
    header, rem:thetaprov in HAMILGRANGIAN_CANONICAL.tex).
    """
    return kappa_of_theta(0.7)


def derived_spin_ceiling() -> float:
    """Derived two-channel ceiling chi_s at theta = 1/sqrt(2) = 0.956145...

    Res-Nova SovereignSpinCeiling.lean: kappa = sqrt(sqrt(2) - 1/2) with the
    proved enclosure 0.914 < kappa^2 = sqrt(2) - 1/2 < 0.915, so
    kappa = 0.95614515...  This value is independently derived three ways
    (RapidityEquipartition.lean et al.) and is the *derived* ceiling, as opposed
    to the *measured* MEASURED_TAU = 0.9539.
    """
    return kappa_of_theta(FLOOR_THETA_EQUIPARTITION)


# ---------------------------------------------------------------------------
# Vector helpers (stdlib only).
# ---------------------------------------------------------------------------


def _dot(a: Sequence[float], b: Sequence[float]) -> float:
    """Dot product of two equal-length sequences.

    Raises:
        ValueError: on length mismatch or empty inputs (fail closed).
    """
    if len(a) != len(b) or len(a) == 0:
        raise ValueError("vectors must be non-empty and of equal length")
    return sum(x * y for x, y in zip(a, b))


def _norm(a: Sequence[float]) -> float:
    """Euclidean norm of a vector."""
    return math.sqrt(_dot(a, a))


def _unit(a: Sequence[float]) -> List[float]:
    """Unit vector along ``a``; raises for the zero vector (fail closed)."""
    n = _norm(a)
    if n == 0.0:
        raise ValueError("cannot normalize the zero vector")
    return [x / n for x in a]


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    """Cosine similarity between two vectors; 0.0 if either is the zero vector.

    The zero-vector convention is chosen so that a degenerate (empty) reasoning
    state never passes the gate: callers gate on ``similarity >= threshold`` and
    0.0 < threshold always, so the gate fails closed on degenerate input.
    """
    na, nb = _norm(a), _norm(b)
    if na == 0.0 or nb == 0.0:
        return 0.0
    return _dot(a, b) / (na * nb)


# ---------------------------------------------------------------------------
# Gate decisions and receipts.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GateDecision:
    """Immutable decision record for one gate evaluation.

    Attributes:
        verdict: "PASS" (state inside the cone), "CLIP" (projected onto the cone
            boundary), or "REJECT" (degenerate or anti-aligned input).
        similarity_in: cosine similarity of the input state to the anchor.
        similarity_out: cosine similarity after the decision (equals the
            threshold for CLIP; equals similarity_in for PASS).
        angle_in_deg: drift angle of the input state, in degrees.
        dissipated_norm: norm of the clipped-off (hallucinated) component.
        reason: human-readable provenance for the verdict.
    """

    verdict: str
    similarity_in: float
    similarity_out: float
    angle_in_deg: float
    dissipated_norm: float
    reason: str

    def receipt_hexdigest(self, state: Sequence[float]) -> str:
        """Deterministic SHA-256 receipt over the decision and the raw state.

        Deterministic (no timestamp): the receipt identifies the input bytes and
        the decision, so identical inputs produce identical receipts.
        """
        payload = (
            f"{self.verdict}|{self.similarity_in:.12f}|{self.similarity_out:.12f}"
            f"|{self.angle_in_deg:.12f}|{self.dissipated_norm:.12f}"
            f"|{','.join(repr(x) for x in state)}"
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class SovereignClippingGate:
    """Fail-closed acceptance cone around a task anchor.

    The gate accepts a state vector iff its cosine similarity to the anchor is at
    least ``threshold``.  A state outside the cone is *clipped*: projected, with
    its norm preserved, onto the boundary of the cone in the plane spanned by the
    state and the anchor.  The clipped-off magnitude is reported as dissipated
    (hallucinated) information.

    The default threshold is the measured engineering value MEASURED_TAU.  The
    derived value ``derived_spin_ceiling()`` is stricter (0.956145 > 0.9539) and
    is available for callers that want the audited, derived ceiling instead of the
    measured one; the difference between the two is 2.2e-3 and the choice must be
    recorded by the caller (see ARCHITECTURE.md, Epistemic status table).
    """

    def __init__(self, anchor: Sequence[float], threshold: float = MEASURED_TAU) -> None:
        """Construct a gate around ``anchor``.

        Args:
            anchor: the task anchor vector; non-zero.
            threshold: minimum cosine similarity to accept, in (0, 1].

        Raises:
            ValueError: if the anchor is degenerate or the threshold is outside
                (0, 1].
        """
        self.anchor = list(anchor)
        self.anchor_unit = _unit(self.anchor)
        self.anchor_norm = _norm(self.anchor)
        if not 0.0 < threshold <= 1.0:
            raise ValueError(f"threshold must lie in (0, 1], got {threshold}")
        self.threshold = threshold
        self.max_angle = math.acos(threshold)

    def evaluate(self, state: Sequence[float]) -> Tuple[List[float], GateDecision]:
        """Evaluate ``state`` against the gate; return (state, decision).

        Returns the *possibly clipped* state and the decision record.  This
        method never raises on well-formed non-degenerate input; degenerate
        input yields a REJECT decision and the original state unchanged.
        """
        sim = cosine_similarity(state, self.anchor)
        if sim >= self.threshold:
            angle = math.degrees(math.acos(min(1.0, max(-1.0, sim))))
            decision = GateDecision(
                verdict="PASS",
                similarity_in=sim,
                similarity_out=sim,
                angle_in_deg=angle,
                dissipated_norm=0.0,
                reason="state within acceptance cone",
            )
            return list(state), decision
        # Fail-closed degenerate branch: zero states.
        if _norm(state) == 0.0:
            decision = GateDecision(
                verdict="REJECT",
                similarity_in=sim,
                similarity_out=sim,
                angle_in_deg=180.0,
                dissipated_norm=0.0,
                reason="degenerate (zero) state vector; gate fails closed",
            )
            return list(state), decision
        # Fail-closed anti-alignment branch: states at >= 90 degrees from the
        # anchor have no meaningful projection onto the cone boundary; the whole
        # state counts as hallucinated relative to the task and is rejected.
        if sim <= 0.0:
            norm_s = _norm(state)
            decision = GateDecision(
                verdict="REJECT",
                similarity_in=sim,
                similarity_out=sim,
                angle_in_deg=math.degrees(math.acos(max(-1.0, sim))),
                dissipated_norm=norm_s,
                reason=(
                    "state at >= 90 degrees from the task anchor; "
                    f"entire state ({norm_s:.6g}) counted as hallucinated"
                ),
            )
            return list(state), decision
        clipped, dissipated = self._clip_to_cone(state)
        angle_in = math.degrees(math.acos(min(1.0, max(-1.0, sim))))
        decision = GateDecision(
            verdict="CLIP",
            similarity_in=sim,
            similarity_out=self.threshold,
            angle_in_deg=angle_in,
            dissipated_norm=dissipated,
            reason=(
                f"state clipped to acceptance cone at "
                f"{math.degrees(self.max_angle):.3f} deg "
                f"(cosine {self.threshold}); hallucinated component dissipated"
            ),
        )
        return clipped, decision

    def _clip_to_cone(self, state: Sequence[float]) -> Tuple[List[float], float]:
        """Project ``state`` onto the cone boundary, preserving its norm.

        Decompose the state into the anchor-parallel and anchor-perpendicular
        components; scale the perpendicular component so the resulting angle to
        the anchor equals the maximum allowed angle.  The clipped-off magnitude
        (norm of the removed perpendicular excess) is returned alongside.

        Raises:
            ValueError: on zero or exactly anti-parallel states (handled by the
                caller's fail-closed branch; kept strict for direct users).
        """
        norm_s = _norm(state)
        unit_s = _unit(state)
        parallel = _dot(unit_s, self.anchor_unit)  # cos(alpha)
        if parallel <= 0.0:
            # Unreachable from SovereignClippingGate.evaluate (anti-parallel
            # states are REJECTed there); kept as a strict fail-closed guard for
            # direct callers.  The entire state is reported as dissipated.
            return list(state), norm_s
        perp = [s - parallel * a for s, a in zip(unit_s, self.anchor_unit)]
        perp_norm = _norm(perp)
        if perp_norm == 0.0:
            # Already exactly on the anchor axis but below threshold: cannot
            # happen for parallel > threshold, so this is the anti-parallel case.
            return list(state), norm_s
        # Target: unit vector at angle max_angle from the anchor in the same
        # plane.  cos(max_angle) along the anchor plus sin(max_angle) along the
        # perpendicular direction.
        cos_max = self.threshold
        sin_max = math.sin(self.max_angle)
        perp_unit = [p / perp_norm for p in perp]
        clipped_unit = [
            cos_max * a + sin_max * p for a, p in zip(self.anchor_unit, perp_unit)
        ]
        clipped = [norm_s * c for c in clipped_unit]
        removed = [s - c for s, c in zip(state, clipped)]
        return clipped, _norm(removed)


class GateLedger:
    """Monotonic append-only ledger of gate decisions (audit log).

    The ledger survives context flushes in the full architecture (Chyren
    persistent-memory plane); here it is the in-process audit trail.  Entries
    are appended via ``append`` and cannot be mutated or reassigned: the
    ``entries`` property returns an immutable tuple, so the "rejects attempts
    to rewrite history" claim is enforced by construction.
    """

    def __init__(self) -> None:
        self._entries: List[GateDecision] = []
        self._cycle: int = 0

    @property
    def entries(self) -> Tuple[GateDecision, ...]:
        """Immutable snapshot of all recorded decisions (cannot be mutated)."""
        return tuple(self._entries)

    @property
    def cycle(self) -> int:
        """Current cycle count (number of decisions recorded)."""
        return self._cycle

    def append(self, decision: GateDecision, state: Sequence[float]) -> int:
        """Append a decision; returns the assigned cycle number (monotonic)."""
        self._cycle += 1
        self._entries.append(decision)
        return self._cycle

    def collapse_events(self, threshold: Optional[float] = None) -> int:
        """Count decisions whose input similarity fell below ``threshold``.

        Args:
            threshold: collapse boundary; defaults to MEASURED_TAU.
        """
        th = MEASURED_TAU if threshold is None else threshold
        return sum(1 for e in self._entries if e.similarity_in < th)

    def summary(self) -> Dict[str, float]:
        """Aggregate ledger statistics: counts by verdict and mean input similarity."""
        by_verdict: Dict[str, int] = {}
        sims: List[float] = []
        for e in self._entries:
            by_verdict[e.verdict] = by_verdict.get(e.verdict, 0) + 1
            sims.append(e.similarity_in)
        mean_sim = sum(sims) / len(sims) if sims else 0.0
        return {"cycles": float(self._cycle), "mean_similarity_in": mean_sim, **{f"count_{k}": float(v) for k, v in by_verdict.items()}}

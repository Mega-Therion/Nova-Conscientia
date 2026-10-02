"""Anti-Drift Cognitive Control Loop (ADCCL): the cybernetic oversight runtime.

Translation target (Res-Nova -> Nova Conscientia)
--------------------------------------------------
The Res-Nova corpus formalizes the ADCCL trajectory as a bounded-dissipation
dynamical system (Res-Nova 05_lean_formalization/YettParadigm.lean, sha256
f1ecdec955fa6bf0e78e269bb20355f80351de27d9e3b57603a42f7a4d8d93ba):

    theorem adccl_trajectory_bounded : the trajectory energy is uniformly
        bounded on t >= 0 under the ADCCL structure hypotheses;
    theorem adccl_non_singular : if E0 < M then the energy never reaches M.

This module is the machine-code realization of that loop for an agent state
vector:

    anchor  -- the task embedding (the "task anchor" of the measured ceiling);
    x_t     -- the scale-free drift coordinate, x = tan(alpha) where alpha is the
               angle between the state and the anchor.  x = 1 is exactly 45
               degrees of misalignment, the equipartition angle of the corpus
               (theta = cos 45 deg = 1/sqrt(2)); this makes the drift coordinate
               scale-free and ties the sovereign gate's geometry to the
               Hamilgrangian coordinate.
    E_t     -- the running Lyapunov-style energy E(t) = F_dual(x_t) of
               core.dual_channel_action (F_dual is bounded below by its minimum
               and convex, so E is a meaningful dissipation measure).

Each cycle: a proposal move is scored by the dual channel (Channel 1 generative
credit vs. Channel 2 invariant dissipation), admitted only on non-negative net
action, and the resulting state is clipped into the sovereign acceptance cone.
Rejected proposals trigger the correction force p_flux(x_t) back toward the
anchor.  The ledger records every cycle; energy beyond ``halt_energy`` fails the
loop closed (HALT), mirroring adccl_non_singular: the controller refuses to
continue once the state is outside its certified energy envelope.

All constants are registered in PROVENANCE.  The measured threshold comes from
core.sovereign_clipping_gate with its full epistemic status (measured, one
pipeline, convergence-not-identity with the derived ceiling).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

from sovereign_clipping_gate import (  # type: ignore
    COLLAPSE_TOLERANCE,
    MEASURED_TAU,
    GateDecision,
    GateLedger,
    SovereignClippingGate,
    cosine_similarity,
)
from dual_channel_action import DualChannelAction, DualChannelDecision, f_dual, p_flux  # type: ignore

PROVENANCE: Dict[str, str] = {
    "DRIFT_45_DEG_REFERENCE": (
        "x = tan(alpha) makes x = 1 the 45-degree equipartition angle "
        "(theta = cos 45 deg = 1/sqrt(2)); Res-Nova "
        "ALIGNMENT_CEILING_ONE_RELATION.md, equipartition section."
    ),
    "HALT_ENERGY_DEFAULT": (
        "E_max = 1.0 in units of F_dual(x) at x = 1 (the 45-degree drift). "
        "Nova Conscientia engineering choice for this runtime, mirroring the "
        "shape of YettParadigm.lean adccl_non_singular (bounded-energy HALT); "
        "the specific value is configurable, not a Res-Nova constant."
    ),
    "COLLAPSE_TOLERANCE": (
        "Imported from sovereign_clipping_gate. Floating-point tolerance for "
        "collapse_cycles: a post-gate similarity within 1e-9 of the threshold "
        "is NOT collapsed (the gate clips to exactly threshold, but IEEE-754 "
        "can produce threshold - epsilon)."
    ),
}


def drift_coordinate(state: Sequence[float], anchor: Sequence[float]) -> float:
    """Scale-free drift coordinate x = tan(alpha) between state and anchor.

    x = 0 means perfect alignment; x = 1 means exactly 45 degrees of drift (the
    equipartition angle); x -> infinity means approaching 90 degrees (orthogonal
    -- state fully unmoored from the task).

    Args:
        state: the agent state vector.
        anchor: the task anchor vector.

    Returns:
        The drift coordinate x >= 0.

    Raises:
        ValueError: if either vector is degenerate, or if the state is at or
            beyond 90 degrees from the anchor (x is not finite there; the
            caller must treat this as full drift, e.g. via
            ``drift_coordinate_capped``).
    """
    sim = cosine_similarity(state, anchor)
    if sim <= 0.0:
        raise ValueError(
            "state at or beyond 90 degrees from anchor: drift coordinate undefined "
            "(treat as full drift / fail closed)"
        )
    return math.tan(math.acos(min(1.0, max(-1.0, sim))))


def drift_coordinate_capped(
    state: Sequence[float], anchor: Sequence[float], cap: float = 1e6
) -> float:
    """Drift coordinate with a fail-closed cap.

    Orthogonal or anti-aligned states return ``cap`` (full drift) instead of
    raising; degenerate vectors return ``cap`` as well (fail closed).

    Args:
        state: the agent state vector.
        anchor: the task anchor vector.
        cap: the returned value for degenerate/orthogonal input; must be > 0.

    Returns:
        x = tan(alpha) when finite, else ``cap``.
    """
    if cap <= 0.0:
        raise ValueError(f"cap must be positive, got {cap}")
    try:
        return drift_coordinate(state, anchor)
    except ValueError:
        return cap


@dataclass
class CycleRecord:
    """One ADCCL cycle in the audit ledger.

    Attributes:
        cycle: monotonic cycle number (1-based).
        verdict: proposal verdict: ACCEPTED, REJECTED, or HALT.
        similarity_in / similarity_out: cosine similarity to the anchor before
            and after the cycle's gate.
        drift: drift coordinate x after the cycle (capped).
        energy: Lyapunov-style energy E = F_dual(x).
        net_action: dual-channel net action of the proposal (None on HALT).
        reason: human-readable provenance.
    """

    cycle: int
    verdict: str
    similarity_in: float
    similarity_out: float
    drift: float
    energy: float
    net_action: Optional[float]
    reason: str


@dataclass
class ADCCLController:
    """The Anti-Drift Cognitive Control Loop for one agent's state stream.

    Wiring of the three components:

    1. ``DualChannelAction`` scores each proposed move (Channel 1 exploration
       credit vs. Channel 2 invariant dissipation).
    2. The sovereign clipping gate confines the post-move state to the
       acceptance cone around the anchor (measured ceiling, fail-closed).
    3. Rejected moves trigger the correction force p_flux(x) pulling the state
       back toward the anchor.

    Attributes:
        anchor: task anchor vector.
        action: the dual-channel action evaluator.
        gate: the sovereign clipping gate.
        halt_energy: energy ceiling; exceeding it HALTs the loop (fail closed).
        ledger: read-only tuple of cycle records (the audit trail; cannot
            be mutated — use ``step`` to append).
        gate_ledger: the gate's own decision ledger.
        halted: True once the loop has HALTed; a halted controller accepts
            nothing further until explicitly reset by the owner.
    """

    anchor: Sequence[float]
    action: DualChannelAction = field(default_factory=DualChannelAction)
    gate: Optional[SovereignClippingGate] = None
    halt_energy: float = 1.0
    _ledger: List[CycleRecord] = field(default_factory=list)
    gate_ledger: GateLedger = field(default_factory=GateLedger)
    halted: bool = False
    _cycle: int = 0
    _state: Optional[List[float]] = None

    def __post_init__(self) -> None:
        """Validate configuration and initialize the gate and state.

        Raises:
            ValueError: on a degenerate anchor or a non-positive halt energy.
        """
        self.anchor = list(self.anchor)
        if self.gate is None:
            self.gate = SovereignClippingGate(self.anchor, threshold=MEASURED_TAU)
        if self.halt_energy <= 0.0:
            raise ValueError(f"halt_energy must be positive, got {self.halt_energy}")
        if self._state is None:
            # The controller starts ON the anchor: no exploration has happened yet.
            self._state = list(self.anchor)

    # -- state access -------------------------------------------------------

    @property
    def ledger(self) -> Tuple[CycleRecord, ...]:
        """Immutable snapshot of all cycle records (cannot be mutated)."""
        return tuple(self._ledger)

    @property
    def state(self) -> List[float]:
        """The current controlled state vector (a defensive copy)."""
        return list(self._state)

    @property
    def energy(self) -> float:
        """Current Lyapunov-style energy E = F_dual(x_t)."""
        x = drift_coordinate_capped(self._state, self.anchor)
        return f_dual(x)

    @property
    def similarity(self) -> float:
        """Current cosine similarity to the anchor."""
        return cosine_similarity(self._state, self.anchor)

    # -- the control loop ---------------------------------------------------

    def step(
        self,
        move: Sequence[float],
        constraint_pressure: float = 0.0,
        drift_budget: float = 1.0,
    ) -> CycleRecord:
        """One ADCCL cycle: score, admit or reject, gate, correct, record.

        Args:
            move: proposed additive move in state space.
            constraint_pressure: normalized invariant violation w >= 0 of the
                proposed move (0 for a clean proposal).
            drift_budget: tolerated drift coordinate; drift beyond it is
                charged to Channel 2 at the action's drift_penalty_rate.

        Returns:
            The CycleRecord for this cycle.  On HALT the record is still
            appended and the state is left unchanged.

        Raises:
            ValueError: on malformed input (length mismatch, negative
                pressure) or when called on a halted controller -- fail closed.
        """
        if self.halted:
            raise RuntimeError(
                "ADCCL controller is HALTed; owner must inspect the ledger and "
                "explicitly reset before further cycles"
            )
        if len(move) != len(self.anchor):
            raise ValueError(
                f"move dimension {len(move)} does not match anchor dimension "
                f"{len(self.anchor)}"
            )
        if constraint_pressure < 0.0:
            raise ValueError(f"constraint_pressure must be >= 0, got {constraint_pressure}")

        self._cycle += 1
        sim_in = self.similarity

        # Fail-closed degenerate proposal: an all-zero move is a no-op, but a
        # move of non-finite magnitude is rejected outright.
        if any(not math.isfinite(m) for m in move):
            record = self._record(sim_in, "REJECTED", None, "non-finite move rejected")
            return record

        anchor_scale = math.sqrt(sum(a * a for a in self.anchor))
        if anchor_scale == 0.0:
            # Unreachable (post_init would have raised inside the gate), kept
            # defensive: fail closed.
            record = self._record(sim_in, "REJECTED", None, "degenerate anchor")
            return record

        # Candidate post-move state.
        candidate = [s + m for s, m in zip(self._state, move)]
        move_scale = math.sqrt(sum(m * m for m in move)) / anchor_scale
        x_candidate = drift_coordinate_capped(candidate, self.anchor)
        x_current = drift_coordinate_capped(self._state, self.anchor)
        drift_excess = max(0.0, x_candidate - max(0.0, drift_budget))

        decision: DualChannelDecision = self.action.evaluate(
            momentum=move_scale,
            constraint_pressure=constraint_pressure,
            drift_excess=drift_excess,
        )

        if not decision.accepted:
            # Rejected: apply the correction force toward the anchor instead.
            # Force magnitude p_flux(x) shrinks the state back along the line to
            # the anchor: state_new = state - rate * p_flux(x) * unit(state-anchor dir).
            corrected = self._apply_correction(x_current)
            clipped, gate_decision = self.gate.evaluate(corrected)
            self._state = clipped
            sim_out = cosine_similarity(self._state, self.anchor)
            self.gate_ledger.append(gate_decision, self._state)
            record = self._record(
                sim_in,
                "REJECTED",
                decision.net_action,
                f"proposal rejected ({decision.reason}); correction force "
                f"p_flux({x_current:.6g}) = {p_flux(x_current):.6g} applied",
            )
            return record

        # Accepted: apply the move, then confine to the sovereign cone.
        clipped, gate_decision = self.gate.evaluate(candidate)
        self._state = clipped
        sim_out = cosine_similarity(self._state, self.anchor)
        self.gate_ledger.append(gate_decision, self._state)
        verdict = "ACCEPTED"
        if gate_decision.verdict == "CLIP":
            verdict = "ACCEPTED+CLIP"
        record = self._record(sim_in, verdict, decision.net_action, decision.reason)
        return record

    def _apply_correction(self, x: float) -> List[float]:
        """Pull the state toward the anchor with force p_flux(x).

        The correction moves the state a fraction mu-rate of the way along the
        chord to the anchor, where the fraction is the constitutive flux
        p_flux(x) capped below 1 (it is < 1 for all x <= 1 + sqrt(2)... in fact
        p_flux(x) < 1 iff x < the golden ratio (1+sqrt(5))/2, so an explicit cap
        keeps the update a contraction).

        Args:
            x: the current drift coordinate.

        Returns:
            The corrected state.
        """
        force = p_flux(x)
        rate = min(force, 0.5)  # contraction cap: at most half the chord per cycle
        return [s + rate * (a - s) for s, a in zip(self._state, self.anchor)]

    def _record(
        self,
        sim_in: float,
        verdict: str,
        net_action: Optional[float],
        reason: str,
    ) -> CycleRecord:
        """Append a cycle record; enforce the energy HALT (fail closed)."""
        x = drift_coordinate_capped(self._state, self.anchor)
        energy = f_dual(x)
        sim_out = self.similarity
        if verdict == "HALT":
            record = CycleRecord(
                cycle=self._cycle,
                verdict="HALT",
                similarity_in=sim_in,
                similarity_out=sim_out,
                drift=x,
                energy=energy,
                net_action=net_action,
                reason=reason,
            )
        else:
            if energy > self.halt_energy:
                self.halted = True
                verdict = "HALT"
                reason = (
                    f"energy {energy:.6g} exceeded halt_energy {self.halt_energy:.6g}; "
                    f"loop failed closed (adccl_non_singular bound); "
                    f"original verdict reason: {reason}"
                )
            record = CycleRecord(
                cycle=self._cycle,
                verdict=verdict,
                similarity_in=sim_in,
                similarity_out=sim_out,
                drift=x,
                energy=energy,
                net_action=net_action,
                reason=reason,
            )
        self._ledger.append(record)
        return record

    # -- audit --------------------------------------------------------------

    def collapse_cycles(self, threshold: Optional[float] = None) -> int:
        """Count cycles whose post-gate similarity fell below ``threshold``.

        Args:
            threshold: collapse boundary; defaults to MEASURED_TAU.
        """
        th = MEASURED_TAU if threshold is None else threshold
        return sum(1 for r in self._ledger if r.similarity_out < th - COLLAPSE_TOLERANCE)

    def summary(self) -> Dict[str, float]:
        """Aggregate statistics over the ledger (counts, means, collapses)."""
        n = len(self._ledger)
        if n == 0:
            return {"cycles": 0.0, "halted": float(self.halted)}
        accepted = sum(1 for r in self._ledger if r.verdict.startswith("ACCEPTED"))
        rejected = sum(1 for r in self._ledger if r.verdict == "REJECTED")
        return {
            "cycles": float(n),
            "accepted": float(accepted),
            "rejected": float(rejected),
            "halted": float(self.halted),
            "mean_similarity_out": sum(r.similarity_out for r in self._ledger) / n,
            "mean_energy": sum(r.energy for r in self._ledger) / n,
        }

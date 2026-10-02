"""Dual-Channel Action runtime: generative proposal drive vs. invariant dissipation.

Translation target (Res-Nova -> Nova Conscientia)
--------------------------------------------------
The Res-Nova Hamilgrangian is a dual-channel variational principle: a Newtonian
Hamiltonian *kinetic* channel and an information-theoretic Lagrangian *dissipation*
channel cancel into a free action

    H(x)      = (1/2) x^2                (bulk kinetic / generative drive)
    L_corr(x) = x - ln(1 + x)            (boundary dissipation / constraint cost)
    F_dual(x) = H(x) - L_corr(x)         (the dual-channel action)

with the machine-checked identities (Res-Nova 05_lean_formalization/Hamilgrangian.lean,
Lean 4 + Mathlib, file sha256 fd284242fe1202e153a95b6efe6f3ac031c321107f78e899e07e7d76a34a31ef):

    H1  F_dual = H - L_corr                      (dual_channel_decomposition)
    H2  F'(x) = p_flux(x) = x^2 / (1 + x)         (constitutive_flux_balance: x - mu = p_flux)
    H3  mu(x) = x / (1 + x),  mu(x)(1 + x) = x    (mu_constitutive)
    H6  mu(p/(1-p)) = p                           (odds-ratio inversion)
    H7  F'(x)^2 * I(mu(x)) = x^3                  (Fisher identity; I(p) = 1/(p(1-p)))

The oversight translation:

* Channel 1 (generative exploration): a proposal's normalized momentum x >= 0
  earns exploration credit H(x) -- quadratic in the momentum the agent is
  willing to spend, exactly the kinetic term.
* Channel 2 (invariant dissipation): constraint pressure on the same coordinate
  costs L_corr(x) = x - ln(1 + x) -- *linear* growth at large x but *quadratic*
  vanishing at small x, i.e. small explorations are nearly free and large ones
  are taxed at full rate.  L_corr is convex, non-negative, and strictly increasing.
* The net action F_dual(x) = H(x) - L_corr(x) decides whether the drive pays for
  its own dissipation.
* The constitutive flux p_flux(x) = F'(x) is the correction force the anti-drift
  controller applies back toward the anchor (core/anti_drift_controller.py).
* mu(x) = x/(1+x) is the credibility transfer function: the fraction of a
  proposal that remains in the trusted (Newtonian) regime as a function of its
  normalized momentum.

Every formula in this module is checked against the Lean-verified identities in
tests/test_core.py (property tests, 64-bit float, 1e-12 relative tolerance).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

VALID_CREDIT_MODES: Tuple[str, ...] = ("classic", "scale_free")
DEFAULT_CREDIT_MODE: str = "classic"

PROVENANCE: Dict[str, str] = {
    "H_KINETIC": (
        "Channel 1, H(x) = (1/2) x^2. Res-Nova Hamilgrangian.lean "
        "def H_channel (theorem H1 dual_channel_decomposition), "
        "sha256 fd284242fe1202e153a95b6efe6f3ac031c321107f78e899e07e7d76a34a31ef."
    ),
    "L_CORR": (
        "Channel 2, L_corr(x) = x - ln(1+x). Res-Nova Hamilgrangian.lean "
        "def L_corr (theorem H1), same sha256."
    ),
    "F_DUAL": (
        "Free action F_dual(x) = (1/2)x^2 - x + ln(1+x). Res-Nova "
        "Hamilgrangian.lean def F_dual (theorems H1, H2), same sha256."
    ),
    "MU_Pade11": (
        "Credibility transfer mu(x) = x/(1+x), the Padé[1/1] interpolation. "
        "Res-Nova Hamilgrangian.lean def mu (theorems H3, H5 Padé[1/1] "
        "uniqueness, H6 odds-ratio inversion), same sha256."
    ),
    "P_FLUX": (
        "Constitutive flux p_flux(x) = x^2/(1+x) = F'(x). Res-Nova "
        "Hamilgrangian.lean def p_flux (theorem H2 constitutive_flux_balance), "
        "same sha256."
    ),
    "VALID_CREDIT_MODES": (
        "Supported dual-channel credit modes: 'classic' (default absolute "
        "quadratic credit H(x)=x^2/2) and 'scale_free' (relative pressure "
        "dissipation cost L_corr(w/x) evaluated against unit credit H(1)=0.5)."
    ),
    "DEFAULT_CREDIT_MODE": (
        "Default credit evaluation mode ('classic'), preserving backward "
        "compatibility and committed receipt reproduceability."
    ),
}


def h_kinetic(x: float) -> float:
    """Channel 1: the Hamiltonian kinetic term H(x) = x^2 / 2.

    Args:
        x: normalized proposal momentum, x >= 0.

    Returns:
        The exploration credit H(x) >= 0.

    Raises:
        ValueError: if x < 0 (a momentum cannot be negative).
    """
    if x < 0.0:
        raise ValueError(f"momentum x must be >= 0, got {x}")
    return 0.5 * x * x


def l_corr(x: float) -> float:
    """Channel 2: the Lagrangian dissipation term L_corr(x) = x - ln(1 + x).

    Convex, non-negative, strictly increasing on x >= 0, with L_corr(0) = 0.

    Args:
        x: normalized constraint pressure, x >= 0.

    Returns:
        The dissipation cost L_corr(x) >= 0.

    Raises:
        ValueError: if x < 0.
    """
    if x < 0.0:
        raise ValueError(f"constraint pressure x must be >= 0, got {x}")
    return x - math.log1p(x)


def f_dual(x: float) -> float:
    """The dual-channel action F_dual(x) = H(x) - L_corr(x).

    Identity H1 of Res-Nova Hamilgrangian.lean: F_dual(x) = (1/2)x^2 - x + ln(1+x).

    Args:
        x: normalized momentum, x >= 0.

    Returns:
        The free action F_dual(x) (can be negative: dissipation exceeding drive).

    Raises:
        ValueError: if x < 0.
    """
    return h_kinetic(x) - l_corr(x)


def mu(x: float) -> float:
    """The credibility transfer function mu(x) = x / (1 + x).

    The Padé[1/1] interpolation of Res-Nova Hamilgrangian.lean (theorem H3:
    mu(x)(1 + x) = x; theorem H5: Padé[1/1] uniqueness given mu(inf) = 1 and
    mu'(0) = 1; theorem H6: odds inversion mu(p/(1-p)) = p).

    Args:
        x: normalized momentum, x >= 0.

    Returns:
        mu(x) in [0, 1): the fraction of the proposal in the trusted regime.

    Raises:
        ValueError: if x < 0.
    """
    if x < 0.0:
        raise ValueError(f"momentum x must be >= 0, got {x}")
    return x / (1.0 + x)


def p_flux(x: float) -> float:
    """The constitutive flux p_flux(x) = x^2 / (1 + x) = F_dual'(x).

    Identity H2 of Res-Nova Hamilgrangian.lean: x - mu(x) = p_flux(x), and the
    derivative of F_dual is exactly this flux.  Used as the anti-drift correction
    force magnitude: quadratic onset at small drift, asymptotically linear
    growth at large drift (no runaway correction force).

    Args:
        x: normalized drift, x >= 0.

    Returns:
        The correction flux p_flux(x) >= 0.

    Raises:
        ValueError: if x < 0.
    """
    if x < 0.0:
        raise ValueError(f"drift x must be >= 0, got {x}")
    return x * x / (1.0 + x)


def fisher_information(p: float) -> float:
    """Bernoulli Fisher information I(p) = 1 / (p (1 - p)) for p in (0, 1).

    Supports the Fisher identity H7 of Res-Nova Hamilgrangian.lean:
    F'(x)^2 * I(mu(x)) = x^3.

    Args:
        p: a probability in the open interval (0, 1).

    Returns:
        I(p) > 0.

    Raises:
        ValueError: if p is outside (0, 1) (fail closed: endpoints are degenerate).
    """
    if not 0.0 < p < 1.0:
        raise ValueError(f"p must lie in (0, 1), got {p}")
    return 1.0 / (p * (1.0 - p))


def odds_of(p: float) -> float:
    """Odds transform p/(1-p) of a probability p in (0, 1).

    The inverse direction of theorem H6 (mu(p/(1-p)) = p): converting a
    credibility fraction into the momentum coordinate of the dual channel.

    Args:
        p: a probability in (0, 1).

    Returns:
        The odds p / (1 - p) > 0.

    Raises:
        ValueError: if p is outside (0, 1).
    """
    if not 0.0 < p < 1.0:
        raise ValueError(f"p must lie in (0, 1), got {p}")
    return p / (1.0 - p)


# ---------------------------------------------------------------------------
# The dual-channel decision record.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DualChannelDecision:
    """Immutable record of one dual-channel action evaluation.

    Attributes:
        accepted: True iff the net action cleared the threshold and the proposal
            was admitted into the state.
        net_action: F_dual at the proposal's momentum minus the dissipation cost
            of its constraint pressure.
        momentum: normalized proposal momentum x >= 0.
        constraint_pressure: normalized invariant-violation magnitude w >= 0.
        credibility: mu(x) in [0, 1).
        reason: human-readable provenance for the verdict.
    """

    accepted: bool
    net_action: float
    momentum: float
    constraint_pressure: float
    credibility: float
    reason: str


@dataclass
class DualChannelAction:
    """Dual-channel cybernetic action evaluator for one proposal stream.

    A proposal is admitted iff the net action

        F = H(x) - L_corr(w + lambda_c * x_excess)

    is non-negative, where x is the proposal's normalized momentum, w its
    invariant-violation pressure (both on the same normalized scale), and
    ``drift_excess`` any drift beyond the controller's tolerated drift budget
    (charged into the dissipation channel at rate ``drift_penalty_rate``).

    Supports two credit evaluation modes via ``credit_mode``:
      - ``"classic"`` (default): absolute quadratic credit H(x) = x^2/2.
      - ``"scale_free"``: relative pressure dissipation cost L_corr(w/x)
        evaluated against unit credit H(1.0) = 0.5.

    The acceptance threshold (default 0.0) is an engineering parameter of this
    runtime, not a Res-Nova constant: it is recorded here and in ARCHITECTURE.md
    as a Nova Conscientia engineering choice, so no ungrounded numerology enters
    through it.

    Attributes:
        acceptance_threshold: minimum net action to admit a proposal.
        drift_penalty_rate: rate at which drift excess is charged to Channel 2.
        credit_mode: 'classic' or 'scale_free'.
    """

    acceptance_threshold: float = 0.0
    drift_penalty_rate: float = 1.0
    credit_mode: str = DEFAULT_CREDIT_MODE

    def evaluate(
        self,
        momentum: float,
        constraint_pressure: float,
        drift_excess: float = 0.0,
    ) -> DualChannelDecision:
        """Score one proposal through both channels.

        Args:
            momentum: normalized exploration momentum x >= 0.
            constraint_pressure: normalized invariant violation w >= 0.
            drift_excess: drift beyond the tolerated budget, charged to
                Channel 2 at ``drift_penalty_rate``; defaults to 0.

        Returns:
            A DualChannelDecision.  Never raises on well-formed input;
            negative inputs raise ValueError (fail closed on malformed data).

        Raises:
            ValueError: if any input is negative or if credit_mode is unknown.
        """
        if momentum < 0.0 or constraint_pressure < 0.0 or drift_excess < 0.0:
            raise ValueError(
                "dual-channel inputs must be non-negative: "
                f"momentum={momentum}, constraint_pressure={constraint_pressure}, "
                f"drift_excess={drift_excess}"
            )

        if self.credit_mode == "classic":
            channel_1 = h_kinetic(momentum)
            dissipation_input = constraint_pressure + self.drift_penalty_rate * drift_excess
            channel_2 = l_corr(dissipation_input)
            net = channel_1 - channel_2
        elif self.credit_mode == "scale_free":
            denom = max(momentum, 1e-6)
            dissipation_input = (
                constraint_pressure + self.drift_penalty_rate * drift_excess
            ) / denom
            channel_1 = 0.5
            channel_2 = l_corr(dissipation_input)
            net = channel_1 - channel_2
        else:
            raise ValueError(
                f"unknown credit_mode {self.credit_mode!r}; "
                f"expected one of {VALID_CREDIT_MODES}"
            )

        accepted = net >= self.acceptance_threshold
        reason = (
            f"Credit mode '{self.credit_mode}': Channel 1 (generative) H = {channel_1:.6g}; "
            f"Channel 2 (dissipation) L_corr({dissipation_input:.6g}) = "
            f"{channel_2:.6g}; net action {net:.6g} "
            f"{'>=' if accepted else '<'} threshold {self.acceptance_threshold:.6g}"
        )
        return DualChannelDecision(
            accepted=accepted,
            net_action=net,
            momentum=momentum,
            constraint_pressure=constraint_pressure,
            credibility=mu(momentum),
            reason=reason,
        )

    def correction_force(self, drift: float) -> float:
        """The anti-drift correction force magnitude at a given drift.

        Exactly the constitutive flux p_flux(drift) = F_dual'(drift) (identity H2):
        the force the runtime applies back toward the anchor when a state has
        drifted by ``drift`` in normalized units.

        Args:
            drift: normalized drift magnitude >= 0.

        Returns:
            The correction force p_flux(drift) >= 0.

        Raises:
            ValueError: if drift < 0.
        """
        return p_flux(drift)

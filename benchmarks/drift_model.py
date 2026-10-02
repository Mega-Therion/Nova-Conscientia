"""Deterministic drift model and pluggable proposal backends for the benchmark harness.

This module supplies the *stimulus* side of the empirical harness: a seeded,
fully reproducible model of an unconstrained generator whose state drifts away
from its task anchor.  In production the same interface is implemented by a live
model backend (``CallableBackend``); in CI the deterministic backend produces
the reproducible receipt.

The drift model is an engineering simulation, NOT a Res-Nova constant: every
parameter is registered in PROVENANCE as an arbitrary, seeded simulation
parameter.  The only physics-grounded number that enters the harness is the
collapse boundary, which is imported from core.sovereign_clipping_gate with its
full epistemic status (a measured single-pipeline engineering threshold).
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Protocol, Sequence, Tuple

#: Default persistent drift gain of the unconstrained generator (simulation).
DRIFT_GAIN = 0.15

#: Default isotropic noise scale of the unconstrained generator (simulation).
NOISE_SCALE = 0.05

#: Default share of each proposal that persists as bias (momentum) (simulation).
PROPOSAL_MOMENTUM = 0.0

PROVENANCE: Dict[str, str] = {
    "DRIFT_GAIN": (
        "Arbitrary simulation parameter: persistent drift gain of the "
        "unconstrained proposal generator. Seeded and reproducible; not a "
        "Res-Nova constant."
    ),
    "NOISE_SCALE": (
        "Arbitrary simulation parameter: isotropic noise scale of the "
        "unconstrained proposal generator. Seeded and reproducible; not a "
        "Res-Nova constant."
    ),
    "PROPOSAL_MOMENTUM": (
        "Arbitrary simulation parameter: fraction of a proposal carried over "
        "as bias into the next proposal. Seeded and reproducible; not a "
        "Res-Nova constant."
    ),
}


def random_unit(dim: int, rng: random.Random) -> List[float]:
    """Uniform random unit vector on S^(dim-1) via normalized Gaussians.

    Args:
        dim: vector dimension, >= 1.
        rng: the seeded RNG (reproducibility).

    Returns:
        A unit vector of length ``dim``.

    Raises:
        ValueError: if dim < 1.
    """
    if dim < 1:
        raise ValueError(f"dim must be >= 1, got {dim}")
    g = [rng.gauss(0.0, 1.0) for _ in range(dim)]
    n = math.sqrt(sum(x * x for x in g))
    if n == 0.0:  # astronomically unlikely; fail safe with a fixed axis.
        g[0] = 1.0
        n = 1.0
    return [x / n for x in g]


class ProposalBackend(Protocol):
    """The contract for proposal sources: one ``propose`` per agent per cycle."""

    def propose(self, cycle: int) -> List[float]:
        """Return the next proposed move vector (same dim as the anchor)."""
        ...


@dataclass
class DeterministicBackend:
    """Seeded unconstrained generator: persistent drift plus noise.

    Models the empirical phenomenon the Res-Nova ADCCL threshold was measured
    on: an unconstrained reasoning loop whose state wanders off the task.  Each
    call returns a move of the form

        m_t = drift_gain * e_t + noise_scale * xi_t (+ momentum carry),

    where e_t is a slowly re-sampled persistent drift direction and xi_t fresh
    noise.  Fully deterministic given the seed.

    Attributes:
        dim: state-space dimension.
        seed: RNG seed (reproducibility).
        drift_gain: magnitude of the persistent drift component.
        noise_scale: magnitude of the noise component.
        momentum: fraction of the previous proposal carried forward as bias.
    """

    dim: int
    seed: int
    drift_gain: float = DRIFT_GAIN
    noise_scale: float = NOISE_SCALE
    momentum: float = PROPOSAL_MOMENTUM
    _rng: random.Random = field(default=None, repr=False)
    _bias: List[float] = field(default_factory=list, repr=False)

    def __post_init__(self) -> None:
        """Initialize the seeded RNG and the persistent drift direction.

        Raises:
            ValueError: on non-positive dim or negative scales.
        """
        if self.dim < 1:
            raise ValueError(f"dim must be >= 1, got {self.dim}")
        if self.drift_gain < 0.0 or self.noise_scale < 0.0:
            raise ValueError("drift_gain and noise_scale must be >= 0")
        if not 0.0 <= self.momentum < 1.0:
            raise ValueError(f"momentum must lie in [0, 1), got {self.momentum}")
        self._rng = random.Random(self.seed)
        self._bias = random_unit(self.dim, self._rng)

    def propose(self, cycle: int) -> List[float]:
        """Draw one proposal: persistent drift, noise, and momentum carry.

        Args:
            cycle: the cycle index (ignored by this backend; part of the
                contract so cycle-aware backends can use it).

        Returns:
            The proposed move vector of length ``dim``.
        """
        # Slowly re-sample the persistent drift direction: 1-in-4 proposals
        # re-draws the bias, mimicking topic switches in a drifting loop.
        if self._rng.random() < 0.25:
            self._bias = random_unit(self.dim, self._rng)
        move = [
            self.drift_gain * b + self.noise_scale * self._rng.gauss(0.0, 1.0)
            for b in self._bias
        ]
        if self.momentum > 0.0:
            if not hasattr(self, "_last"):
                self._last = [0.0] * self.dim
            move = [m + self.momentum * l for m, l in zip(move, self._last)]
            self._last = list(move)
        return move


@dataclass
class CallableBackend:
    """Wraps any callable as a proposal backend (live-model adapter).

    The callable receives ``(cycle, dim)`` and must return a list of ``dim``
    finite floats.  The adapter is fail-closed: any exception, wrong length, or
    non-finite entry raises immediately (the harness catches it and marks the
    trial as a backend failure, never as good behavior).

    Attributes:
        propose_fn: the wrapped callable.
        dim: state-space dimension.
    """

    propose_fn: Callable[[int, int], Sequence[float]]
    dim: int

    def propose(self, cycle: int) -> List[float]:
        """Call the wrapped function under the output contract."""
        raw = self.propose_fn(cycle, self.dim)
        move = list(raw)
        if len(move) != self.dim:
            raise ValueError(
                f"backend returned {len(move)} values, expected {self.dim}"
            )
        for m in move:
            if not math.isfinite(m):
                raise ValueError("backend returned a non-finite move")
        return move

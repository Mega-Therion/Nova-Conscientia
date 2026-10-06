"""Stack several source readings of one claim.

Each reading is one filter on the same object Y. A reading that names a
different object is left out of the stack. Each included reading still has
to pass ``claim_band.judge``. An empirical reading also needs a citation.
The stack does not blend a failed layer into the answer.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.claim_band import BandDecision, ClaimKind, judge


@dataclass(frozen=True)
class SourceReading:
    """One filter pointed at a claim."""

    source_id: str
    claim_id: str
    kind: ClaimKind
    stated: float
    citation: str = ""


@dataclass(frozen=True)
class LayerResult:
    """What happened to one reading."""

    reading: SourceReading
    decision: BandDecision | None
    included: bool
    reason: str


@dataclass(frozen=True)
class StackResult:
    """The registered layers for one claim."""

    claim_id: str
    layers: tuple[LayerResult, ...]

    @property
    def included(self) -> tuple[LayerResult, ...]:
        """Layers that lined up and passed their own check."""
        return tuple(layer for layer in self.layers if layer.included)

    @property
    def stands(self) -> bool:
        """True when at least one layer may be shown."""
        return any(layer.included for layer in self.layers)


def stack(claim_id: str, readings: list[SourceReading]) -> StackResult:
    """Register readings on ``claim_id`` and keep only the layers that pass."""
    layers: list[LayerResult] = []
    for reading in readings:
        if reading.claim_id != claim_id:
            layers.append(
                LayerResult(reading, None, False, "pointed at a different object")
            )
            continue
        if reading.kind is ClaimKind.EMPIRICAL and not reading.citation.strip():
            layers.append(
                LayerResult(reading, None, False, "empirical claim has no citation")
            )
            continue
        decision = judge(reading.kind, reading.stated)
        layers.append(
            LayerResult(
                reading,
                decision,
                decision.stands,
                decision.reason,
            )
        )
    return StackResult(claim_id, tuple(layers))

"""Certainty bands for one claim.

A formal result may be reported at certainty 1.0. An empirical result may be
stood on only inside the chiral band: at or above 1/sqrt(2), and strictly
below 0.9. A borrowed formula is mathematics used by this runtime. It is not
a physical measurement, so it is never emitted as one.

The gate refuses an empirical claim that asserts 0.9 or above. It does not
silently rewrite that assertion down to 0.899.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

CHIRAL_FLOOR = 2.0**-0.5
EMPIRICAL_CAP = 0.9


class ClaimKind(Enum):
    FORMAL = "formal"
    EMPIRICAL = "empirical"
    BORROWED_MATH = "borrowed_math"


@dataclass(frozen=True)
class BandDecision:
    kind: ClaimKind
    stated: float
    allowed: float | None
    reason: str

    @property
    def stands(self) -> bool:
        return self.allowed is not None


def judge(kind: ClaimKind, stated: float) -> BandDecision:
    """Decide whether a stated certainty may be emitted."""
    if kind is ClaimKind.BORROWED_MATH:
        return BandDecision(
            kind,
            stated,
            None,
            "borrowed mathematics is not a physical measurement",
        )
    if stated < 0.0 or stated > 1.0:
        return BandDecision(kind, stated, None, "certainty outside [0, 1]")
    if kind is ClaimKind.FORMAL:
        return BandDecision(
            kind, stated, stated, "formal result may sit at the stated certainty"
        )
    if stated < CHIRAL_FLOOR:
        return BandDecision(
            kind, stated, None, "below the chiral floor; too thin to stand on"
        )
    if stated >= EMPIRICAL_CAP:
        return BandDecision(
            kind,
            stated,
            None,
            "empirical certainty at or above 0.9 is forbidden",
        )
    return BandDecision(kind, stated, stated, "empirical claim inside the chiral band")

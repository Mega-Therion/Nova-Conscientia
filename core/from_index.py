"""Turn Second Brain index rows into a multisource stack."""

from __future__ import annotations

from core.claim_band import ClaimKind
from core.multisource import SourceReading, StackResult, stack

_KINDS = {kind.value: kind for kind in ClaimKind}


def stack_rows(claim_id: str, rows: list[dict]) -> StackResult:
    """Stack index rows that were retrieved for one claim.

    A row whose claim id does not contain the query is a different object.
    Empirical rows still need a citation before the band will let them stand.
    """
    readings = []
    for row in rows:
        kind = _KINDS.get(row.get("band", ""), ClaimKind.EMPIRICAL)
        readings.append(
            SourceReading(
                source_id=row.get("path", row.get("claim_id", "note")),
                claim_id=row.get("claim_id", ""),
                kind=kind,
                stated=float(
                    row.get("stated", 0.8 if kind is ClaimKind.EMPIRICAL else 1.0)
                ),
                citation=row.get("citation", ""),
            )
        )
    return stack(claim_id, readings)

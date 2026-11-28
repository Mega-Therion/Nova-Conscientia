"""Multi-objective artifact selection function (SAMO spec section 4).

Translation target (S.A.M.O. v2.0 -> Nova Conscientia)
------------------------------------------------------
The S.A.M.O. (Sovereign ARI Mesh Omegarithm) Specification v2.0, section 4,
defines the Tier-B artifact selection function behind non-purchasable
multiplicative hard vetoes:

    F(x) = V_hard(x) * V_mech(x) * B_bridge(x) * H_local(x)

* ``V_hard`` in {0, 1}: Ring-0 checks executed *before* scoring — canonical
  schema validation, cryptographic signature validity, MVPC-X
  anti-fabrication checks, and the local sovereign clipping gate's
  energy-cone bounds.  Any failure zeroes the score: no accumulation on the
  other axes can buy a veto (the additive purchasability seam documented in
  ARCHITECTURE.md section 2.1 is closed by multiplication).
* ``V_mech`` in [0, 1]: deterministic verification yield — the ratio of
  independent deterministic checks passed, computed from MVPC-X mechanical
  witnesses (the spec section 8 wiring: MVPC-X witnesses feed ``V_mech``
  directly).  The yield is *recomputed* here from the per-witness entries
  of the MVPC-X witness feed (``mvpc.witness_feed``, schema
  ``mvpc-x/samo-v-mech-feed/1``); a ``v_mech`` figure stated by the feed is
  recorded for audit but never trusted.  A witness whose integrity flag is
  false earns no passed checks, and checks that could not run count in the
  denominator and are named in the result — unavailable checks are never
  hidden (spec section 4: "with zero hidden ``checks_unavailable``").
* ``B_bridge`` in [0, 1]: cross-cluster bridging factor over peer
  attestations across distinct neighborhoods and lineages (computed by the
  bridge router; supplied by the caller).
* ``H_local`` in [0, 1]: local operator utility and non-drift retention,
  evaluated strictly on-device (supplied by the caller, never exported raw).

Fail closed throughout: a malformed feed, an out-of-range axis, or a
missing yield source raises ``ValueError`` rather than scoring the artifact.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional, Tuple

#: Schema identifier of the MVPC-X mechanical witness feed this module
#: consumes (produced by MVPC-X ``mvpc.witness_feed``; pinned, not negotiated).
FEED_SCHEMA = "mvpc-x/samo-v-mech-feed/1"


def _stable_json(obj: Any) -> str:
    """Deterministic JSON encoding (sorted keys) for receipts.

    Raises:
        TypeError: if the object is not JSON-serializable (fail closed).
    """
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=repr)


def _check_axis(name: str, value: float) -> float:
    """Validate one soft axis lies in [0, 1]; return it as a float.

    Raises:
        ValueError: if the value is not a real number in [0, 1].
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number in [0, 1], got {value!r}")
    result = float(value)
    if not 0.0 <= result <= 1.0:
        raise ValueError(f"{name} must lie in [0, 1], got {result}")
    return result


def mechanical_verification_yield(
    feed: Mapping[str, Any],
) -> Tuple[float, Dict[str, Any]]:
    """Recompute ``V_mech`` from an MVPC-X mechanical witness feed.

    The feed's own stated ``v_mech`` is ignored for the computation (it is
    returned in the detail mapping for audit).  A witness entry earns its
    ``checks_passed`` only when its ``integrity_ok`` flag is true; its
    ``checks_total`` always counts.  Unavailable check names from every
    entry are collected into the detail mapping — never hidden.

    Args:
        feed: a mapping in the ``mvpc-x/samo-v-mech-feed/1`` schema, as
            produced by MVPC-X ``mechanical_witness_feed``.

    Returns:
        ``(v_mech, detail)`` where detail carries the recomputed counts,
        the unavailable check names, and the feed's stated yield.

    Raises:
        ValueError: on a wrong schema, a missing or malformed witness list,
            or per-entry counts that are negative or inconsistent
            (passed greater than total).
    """
    if not isinstance(feed, Mapping):
        raise ValueError(f"witness feed must be a mapping, got {type(feed).__name__}")
    if feed.get("schema") != FEED_SCHEMA:
        raise ValueError(
            f"witness feed schema {feed.get('schema')!r} != {FEED_SCHEMA!r}"
        )
    entries = feed.get("witnesses")
    if not isinstance(entries, list):
        raise ValueError("witness feed 'witnesses' must be a list")
    passed_total = 0
    checks_total = 0
    unavailable: list = []
    for entry in entries:
        if not isinstance(entry, Mapping):
            raise ValueError("witness feed entries must be mappings")
        passed = entry.get("checks_passed")
        total = entry.get("checks_total")
        if (
            isinstance(passed, bool)
            or isinstance(total, bool)
            or not isinstance(passed, int)
            or not isinstance(total, int)
            or passed < 0
            or total < 0
            or passed > total
        ):
            raise ValueError(
                f"malformed witness entry counts: passed={passed!r} total={total!r}"
            )
        if entry.get("integrity_ok") is True:
            passed_total += passed
        checks_total += total
        for name in entry.get("checks_unavailable", []) or []:
            if name not in unavailable:
                unavailable.append(name)
    v_mech = (passed_total / checks_total) if checks_total > 0 else 0.0
    detail = {
        "checks_passed": passed_total,
        "checks_total": checks_total,
        "checks_unavailable": unavailable,
        "feed_stated_v_mech": feed.get("v_mech"),
        "witness_count": len(entries),
    }
    return v_mech, detail


def hard_veto(
    *,
    schema_valid: bool,
    signature_valid: bool,
    antifabrication_ok: bool,
    gate_verdict: Optional[str] = None,
) -> int:
    """Compute ``V_hard`` in {0, 1} from the Ring-0 pre-scoring checks.

    Args:
        schema_valid: canonical schema validation passed.
        signature_valid: cryptographic signature validity passed.
        antifabrication_ok: MVPC-X anti-fabrication checks passed.
        gate_verdict: the local sovereign clipping gate's verdict for the
            artifact's state (``GateDecision.verdict``); ``"REJECT"`` is a
            veto, ``"PASS"``/``"CLIP"`` are not, ``None`` means the caller
            did not gate (recorded as no gate input, not as a pass claim).
            Any other value is not a gate result at all — a typo or an
            unsupported verdict fails closed (veto), because an artifact
            must not be scored on a gate outcome nobody can interpret.

    Returns:
        1 iff every supplied check holds, else 0.
    """
    if gate_verdict is not None:
        if gate_verdict == "REJECT":
            return 0
        if gate_verdict not in ("PASS", "CLIP"):
            return 0
    return 1 if (schema_valid and signature_valid and antifabrication_ok) else 0


@dataclass(frozen=True)
class SelectionScore:
    """One artifact's selection score and the axes it was computed from.

    Attributes:
        v_hard: the hard veto bit (0 or 1).
        v_mech: the deterministic verification yield in [0, 1].
        b_bridge: the cross-cluster bridging factor in [0, 1].
        h_local: the local operator utility in [0, 1].
        score: the product ``V_hard * V_mech * B_bridge * H_local``.
        checks_passed: mechanical checks passed (from the witness feed).
        checks_total: mechanical checks that should have run.
        checks_unavailable: names of checks that could not run (never
            hidden; empty when scored from an explicit ``v_mech`` value).
    """

    v_hard: int
    v_mech: float
    b_bridge: float
    h_local: float
    score: float
    checks_passed: int = 0
    checks_total: int = 0
    checks_unavailable: Tuple[str, ...] = ()

    def receipt_hexdigest(self) -> str:
        """Deterministic SHA-256 receipt over the score and its axes."""
        payload = _stable_json(
            {
                "v_hard": self.v_hard,
                "v_mech": self.v_mech,
                "b_bridge": self.b_bridge,
                "h_local": self.h_local,
                "score": self.score,
                "checks_passed": self.checks_passed,
                "checks_total": self.checks_total,
                "checks_unavailable": list(self.checks_unavailable),
            }
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def artifact_selection_score(
    *,
    v_hard: int,
    b_bridge: float,
    h_local: float,
    witness_feed: Optional[Mapping[str, Any]] = None,
    v_mech: Optional[float] = None,
) -> SelectionScore:
    """Score one artifact under the SAMO section 4 selection function.

    Exactly one yield source must be supplied: ``witness_feed`` (the MVPC-X
    mechanical witness feed, from which ``V_mech`` is recomputed) or an
    explicit ``v_mech`` value (for callers with no witness feed; the score
    then records zero check counts rather than inventing coverage).

    Args:
        v_hard: the hard veto bit, 0 or 1 (see :func:`hard_veto`).
        b_bridge: cross-cluster bridging factor in [0, 1].
        h_local: local operator utility in [0, 1].
        witness_feed: MVPC-X witness feed mapping, or None.
        v_mech: explicit verification yield in [0, 1], or None.

    Returns:
        The :class:`SelectionScore` with the multiplicative product.

    Raises:
        ValueError: if both or neither yield source is given, if ``v_hard``
            is not 0 or 1, if any axis is out of range, or if the witness
            feed is malformed.
    """
    if (witness_feed is None) == (v_mech is None):
        raise ValueError("supply exactly one of witness_feed / v_mech")
    if v_hard not in (0, 1) or isinstance(v_hard, bool):
        raise ValueError(f"v_hard must be 0 or 1, got {v_hard!r}")
    b = _check_axis("b_bridge", b_bridge)
    h = _check_axis("h_local", h_local)
    checks_passed = 0
    checks_total = 0
    unavailable: Tuple[str, ...] = ()
    if witness_feed is not None:
        mech, detail = mechanical_verification_yield(witness_feed)
        checks_passed = detail["checks_passed"]
        checks_total = detail["checks_total"]
        unavailable = tuple(detail["checks_unavailable"])
    else:
        mech = _check_axis("v_mech", v_mech)
    score = float(v_hard) * mech * b * h
    return SelectionScore(
        v_hard=int(v_hard),
        v_mech=mech,
        b_bridge=b,
        h_local=h,
        score=score,
        checks_passed=checks_passed,
        checks_total=checks_total,
        checks_unavailable=unavailable,
    )

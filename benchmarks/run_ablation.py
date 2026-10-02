"""Ablation harness: isolating the contribution of each oversight component.

Arms
----
1. gate_only           — sovereign gate clips proposals; no dual-channel
                         scoring, no correction force.
2. gate_dual_channel   — gate + dual-channel scoring; rejected proposals are
                         skipped (state unchanged).  No correction force.
3. gate_correction     — gate + correction force on clip; no dual-channel
                         scoring (all proposals accepted, then gated, then
                         corrected if the gate clipped).
4. full                — gate + dual-channel + correction (the current ADCCL
                         system, for comparison).

Constraint-pressure sweep
-------------------------
Instead of a single pressure, the harness sweeps across
``SWEEP_PRESSURES = [0, 0.05, 0.1, 0.15, 0.2, 0.3, 0.5]``.  At pressure 0.5
the dual channel rejects virtually all proposals (the dissipation cost
exceeds the exploration credit for the drift model's typical momentum), so
the dual-channel arms never move.  The sweep reveals the transition from
full acceptance (low pressure) to full rejection (high pressure).

For each arm and pressure the receipt reports:
  * acceptance_rate   — fraction of proposals admitted by the dual channel
                        (1.0 for arms without scoring).
  * mean_anchor_drift — mean of (1 − cosine_similarity to the anchor) per
                        cycle; 0 means the state never left the anchor.  This
                        is drift from the anchor, not task progress (there is
                        no task in this harness; see run_task_benchmark.py).
  * mean_final_similarity
  * collapse_fraction

Receipts
--------
``run_ablation.py --json PATH`` writes a full ablation receipt.  The run is
deterministic for a given seed set, but see PROVENANCE.md for a note on
7th-decimal drift across platforms.
"""

from __future__ import annotations

import argparse
import json
import math
import platform
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

_REPO_ROOT = Path(__file__).resolve().parent.parent
for _p in (_REPO_ROOT / "core", _REPO_ROOT / "benchmarks"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from sovereign_clipping_gate import (  # type: ignore
    COLLAPSE_TOLERANCE,
    MEASURED_TAU,
    SovereignClippingGate,
    cosine_similarity,
)
from dual_channel_action import DualChannelAction, f_dual, p_flux  # type: ignore
from anti_drift_controller import ADCCLController, drift_coordinate_capped  # type: ignore
from drift_model import DeterministicBackend  # type: ignore

DEFAULT_TRIALS = 40
DEFAULT_STEPS = 50
DEFAULT_DIM = 16
BASE_SEED = 20260906

#: Constraint pressures to sweep (replaces the former single-pressure run).
SWEEP_PRESSURES = [0.0, 0.05, 0.1, 0.15, 0.2, 0.3, 0.5]

PROVENANCE: Dict[str, str] = {
    "DEFAULT_TRIALS": "Arbitrary simulation parameter (harness sample size).",
    "DEFAULT_STEPS": "Arbitrary simulation parameter (loop length).",
    "DEFAULT_DIM": "Arbitrary simulation parameter (state-space dimension).",
    "SWEEP_PRESSURES": (
        "Constraint pressures fed to the dual-channel scoring. The sweep "
        "replaces the former single pressure (0.5) at which the dual channel "
        "rejected all proposals. These are arbitrary simulation parameters, "
        "not Res-Nova constants."
    ),
    "BASE_SEED": (
        "Reproducibility parameter: BASE_SEED + trial index seeds every RNG. "
        "Chosen as the measurement date of tau (2026-09-06) for mnemonic value "
        "only; it has no other significance."
    ),
    "COLLAPSE_TOLERANCE": (
        "Imported from sovereign_clipping_gate. The gate clips to exactly "
        "cosine = threshold, but IEEE-754 can produce threshold - epsilon; "
        "1e-9 absorbs this so clipped states are not spuriously collapsed."
    ),
}


def _anchor(dim: int) -> List[float]:
    """Unit vector along the first axis."""
    a = [0.0] * dim
    a[0] = 1.0
    return a


def _norm(v: Sequence[float]) -> float:
    return math.sqrt(sum(x * x for x in v))


def _trial_result(
    state: List[float],
    anchor: List[float],
    accepted_count: int,
    total_count: int,
    drift_sum: float,
    steps: int,
) -> Dict[str, Any]:
    sim = cosine_similarity(state, anchor)
    x = drift_coordinate_capped(state, anchor)
    return {
        "final_similarity": sim,
        "final_energy": f_dual(x),
        "at_cap": x >= 1e6,
        "collapsed": sim < MEASURED_TAU - COLLAPSE_TOLERANCE,
        "acceptance_rate": accepted_count / total_count if total_count > 0 else 1.0,
        "mean_anchor_drift": drift_sum / steps if steps > 0 else 0.0,
    }


# --------------------------------------------------------------------------- #
#  Arm 1: gate-only
# --------------------------------------------------------------------------- #

def run_gate_only_trial(seed: int, steps: int, dim: int, pressure: float) -> Dict[str, Any]:
    """Gate-only: apply proposals, gate clips. No scoring, no correction."""
    anchor = _anchor(dim)
    gate = SovereignClippingGate(anchor, threshold=MEASURED_TAU)
    backend = DeterministicBackend(dim=dim, seed=seed)
    state = list(anchor)
    drift_sum = 0.0
    for cycle in range(steps):
        move = backend.propose(cycle)
        candidate = [s + m for s, m in zip(state, move)]
        clipped, _ = gate.evaluate(candidate)
        state = clipped
        drift_sum += 1.0 - cosine_similarity(state, anchor)
    return _trial_result(state, anchor, steps, steps, drift_sum, steps)


# --------------------------------------------------------------------------- #
#  Arm 2: gate + dual-channel (no correction)
# --------------------------------------------------------------------------- #

def run_gate_dual_channel_trial(seed: int, steps: int, dim: int, pressure: float) -> Dict[str, Any]:
    """Gate + dual-channel: score proposals, skip rejected. No correction."""
    anchor = _anchor(dim)
    gate = SovereignClippingGate(anchor, threshold=MEASURED_TAU)
    action = DualChannelAction()
    backend = DeterministicBackend(dim=dim, seed=seed)
    state = list(anchor)
    anchor_norm = _norm(anchor)
    accepted_count = 0
    drift_sum = 0.0
    for cycle in range(steps):
        move = backend.propose(cycle)
        candidate = [s + m for s, m in zip(state, move)]
        move_scale = _norm(move) / anchor_norm
        x_candidate = drift_coordinate_capped(candidate, anchor)
        x_current = drift_coordinate_capped(state, anchor)
        drift_excess = max(0.0, x_candidate - 1.0)
        decision = action.evaluate(
            momentum=move_scale,
            constraint_pressure=pressure,
            drift_excess=drift_excess,
        )
        if decision.accepted:
            accepted_count += 1
            clipped, _ = gate.evaluate(candidate)
            state = clipped
        drift_sum += 1.0 - cosine_similarity(state, anchor)
    return _trial_result(state, anchor, accepted_count, steps, drift_sum, steps)


# --------------------------------------------------------------------------- #
#  Arm 3: gate + correction (no dual-channel scoring)
# --------------------------------------------------------------------------- #

def run_gate_correction_trial(seed: int, steps: int, dim: int, pressure: float) -> Dict[str, Any]:
    """Gate + correction: accept all, gate clips, correct on clip. No scoring."""
    anchor = _anchor(dim)
    gate = SovereignClippingGate(anchor, threshold=MEASURED_TAU)
    backend = DeterministicBackend(dim=dim, seed=seed)
    state = list(anchor)
    drift_sum = 0.0
    for cycle in range(steps):
        move = backend.propose(cycle)
        candidate = [s + m for s, m in zip(state, move)]
        clipped, gate_decision = gate.evaluate(candidate)
        state = clipped
        if gate_decision.verdict == "CLIP":
            x = drift_coordinate_capped(state, anchor)
            force = p_flux(x)
            rate = min(force, 0.5)
            state = [s + rate * (a - s) for s, a in zip(state, anchor)]
            clipped, _ = gate.evaluate(state)
            state = clipped
        drift_sum += 1.0 - cosine_similarity(state, anchor)
    return _trial_result(state, anchor, steps, steps, drift_sum, steps)


# --------------------------------------------------------------------------- #
#  Arm 4: full system (gate + dual-channel + correction)
# --------------------------------------------------------------------------- #

def run_full_trial(seed: int, steps: int, dim: int, pressure: float) -> Dict[str, Any]:
    """Full ADCCL system: gate + dual-channel + correction."""
    anchor = _anchor(dim)
    ctrl = ADCCLController(
        anchor=anchor,
        action=DualChannelAction(),
        gate=SovereignClippingGate(anchor, threshold=MEASURED_TAU),
    )
    backend = DeterministicBackend(dim=dim, seed=seed)
    accepted_count = 0
    drift_sum = 0.0
    for cycle in range(steps):
        record = ctrl.step(backend.propose(cycle), constraint_pressure=pressure)
        if record.verdict.startswith("ACCEPTED"):
            accepted_count += 1
        drift_sum += 1.0 - cosine_similarity(ctrl.state, anchor)
    return _trial_result(ctrl.state, anchor, accepted_count, steps, drift_sum, steps)


# --------------------------------------------------------------------------- #
#  Harness
# --------------------------------------------------------------------------- #

_ARMS = {
    "gate_only": run_gate_only_trial,
    "gate_dual_channel": run_gate_dual_channel_trial,
    "gate_correction": run_gate_correction_trial,
    "full": run_full_trial,
}


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _median(values: Sequence[float]) -> float:
    """Median; 0.0 for an empty sequence."""
    if not values:
        return 0.0
    s = sorted(values)
    n = len(s)
    mid = n // 2
    if n % 2 == 1:
        return s[mid]
    return (s[mid - 1] + s[mid]) / 2.0


def run_ablation(
    trials: int = DEFAULT_TRIALS,
    steps: int = DEFAULT_STEPS,
    dim: int = DEFAULT_DIM,
    pressures: Optional[Sequence[float]] = None,
    base_seed: int = BASE_SEED,
) -> Dict[str, Any]:
    """Run all four ablation arms across the constraint-pressure sweep.

    Args:
        trials: trials per arm per pressure.
        steps: cycles per trial.
        dim: state-space dimension.
        pressures: constraint pressures to sweep (defaults to SWEEP_PRESSURES).
        base_seed: seed base (trial k uses base_seed + k).

    Returns:
        The full sweep receipt (parameters, sweep metrics, per-trial records,
        environment).  Deterministic for a given parameter set.
    """
    if pressures is None:
        pressures = SWEEP_PRESSURES
    if trials < 1 or steps < 1 or dim < 1:
        raise ValueError("trials, steps, dim must all be >= 1")
    if not pressures:
        raise ValueError("pressures must not be empty")
    if any(p < 0.0 for p in pressures):
        raise ValueError("all pressures must be >= 0")

    sweep: Dict[str, Dict[str, Dict[str, float]]] = {}
    per_trial: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}

    for pressure in pressures:
        pressure_key = str(pressure)
        sweep[pressure_key] = {}
        per_trial[pressure_key] = {}
        for arm_name, arm_fn in _ARMS.items():
            records = [arm_fn(base_seed + k, steps, dim, pressure) for k in range(trials)]
            per_trial[pressure_key][arm_name] = records
            sweep[pressure_key][arm_name] = {
                "acceptance_rate": _mean([r["acceptance_rate"] for r in records]),
                "mean_anchor_drift": _mean([r["mean_anchor_drift"] for r in records]),
                "mean_final_similarity": _mean([r["final_similarity"] for r in records]),
                "collapse_fraction": _mean([1.0 if r["collapsed"] else 0.0 for r in records]),
                "mean_final_energy": _mean([r["final_energy"] for r in records]),
                "median_final_energy": _median([r["final_energy"] for r in records]),
                "cap_fraction": _mean([1.0 if r.get("at_cap", False) else 0.0 for r in records]),
            }

    return {
        "harness": "nova-conscientia ablation sweep",
        "protocol": (
            "Ablation sweep: isolating each oversight component across a range "
            "of constraint pressures so the dual channel transitions from full "
            "acceptance to full rejection. Seeded deterministic simulation "
            "with no LLM calls."
        ),
        "parameters": {
            "trials": trials,
            "steps": steps,
            "dim": dim,
            "sweep_pressures": list(pressures),
            "base_seed": base_seed,
            "collapse_boundary": MEASURED_TAU,
            "collapse_tolerance": COLLAPSE_TOLERANCE,
        },
        "sweep": sweep,
        "per_trial": per_trial,
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
        },
    }


def _print_sweep_table(receipt: Dict[str, Any]) -> None:
    """Print the sweep as a human-readable table."""
    pressures = receipt["parameters"]["sweep_pressures"]
    arm_names = list(_ARMS.keys())
    header = f"  {'arm':<20} {'accept':>8} {'drift':>8} {'sim':>8} {'collapse':>8}"
    for pressure in pressures:
        pressure_key = str(pressure)
        arms = receipt["sweep"][pressure_key]
        print(f"\npressure = {pressure}")
        print(header)
        for arm_name in arm_names:
            m = arms[arm_name]
            print(
                f"  {arm_name:<20} {m['acceptance_rate']:>8.4f} "
                f"{m['mean_anchor_drift']:>8.4f} {m['mean_final_similarity']:>8.4f} "
                f"{m['collapse_fraction']:>8.4f}"
            )


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry point for the ablation sweep."""
    parser = argparse.ArgumentParser(
        description="Ablation sweep: gate-only vs gate+dual-channel vs "
                    "gate+correction vs full, across constraint pressures."
    )
    parser.add_argument("--trials", type=int, default=DEFAULT_TRIALS)
    parser.add_argument("--steps", type=int, default=DEFAULT_STEPS)
    parser.add_argument("--dim", type=int, default=DEFAULT_DIM)
    parser.add_argument("--seed", type=int, default=BASE_SEED)
    parser.add_argument("--json", type=str, default=None,
                        help="path to write the ablation receipt JSON")
    args = parser.parse_args(list(argv if argv is not None else sys.argv[1:]))

    try:
        receipt = run_ablation(
            trials=args.trials, steps=args.steps, dim=args.dim,
            pressures=SWEEP_PRESSURES, base_seed=args.seed,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    _print_sweep_table(receipt)
    if args.json:
        out = Path(args.json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
        print(f"\nablation receipt written to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

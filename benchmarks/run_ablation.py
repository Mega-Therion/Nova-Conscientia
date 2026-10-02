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

Constraint pressure is non-zero (default 0.5) so the dual channel has
something to reject — without it, the dual-channel scoring never fires
(see the review: "Dual-channel scoring does no work in the benchmark").

Receipts
--------
``run_ablation.py --json PATH`` writes a full ablation receipt.  The run is
deterministic for a given seed set.
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
DEFAULT_PRESSURE = 0.5
BASE_SEED = 20260906

PROVENANCE: Dict[str, str] = {
    "DEFAULT_TRIALS": "Arbitrary simulation parameter (harness sample size).",
    "DEFAULT_STEPS": "Arbitrary simulation parameter (loop length).",
    "DEFAULT_DIM": "Arbitrary simulation parameter (state-space dimension).",
    "DEFAULT_PRESSURE": (
        "Constraint pressure fed to the dual-channel scoring so it has "
        "something to reject. 0.5 is an arbitrary non-zero value; not a "
        "Res-Nova constant."
    ),
    "BASE_SEED": (
        "Reproducibility parameter: BASE_SEED + trial index seeds every RNG. "
        "Chosen as the measurement date of tau (2026-09-06) for mnemonic value "
        "only; it has no other significance."
    ),
}


def _anchor(dim: int) -> List[float]:
    """Unit vector along the first axis."""
    a = [0.0] * dim
    a[0] = 1.0
    return a


def _norm(v: Sequence[float]) -> float:
    return math.sqrt(sum(x * x for x in v))


def _trial_result(state: List[float], anchor: List[float]) -> Dict[str, Any]:
    sim = cosine_similarity(state, anchor)
    x = drift_coordinate_capped(state, anchor)
    return {
        "final_similarity": sim,
        "min_similarity": sim,
        "final_energy": f_dual(x),
        "collapsed": sim < MEASURED_TAU,
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
    for cycle in range(steps):
        move = backend.propose(cycle)
        candidate = [s + m for s, m in zip(state, move)]
        clipped, _ = gate.evaluate(candidate)
        state = clipped
    return _trial_result(state, anchor)


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
            clipped, _ = gate.evaluate(candidate)
            state = clipped
        # Rejected: skip (keep current state), no correction
    return _trial_result(state, anchor)


# --------------------------------------------------------------------------- #
#  Arm 3: gate + correction (no dual-channel scoring)
# --------------------------------------------------------------------------- #

def run_gate_correction_trial(seed: int, steps: int, dim: int, pressure: float) -> Dict[str, Any]:
    """Gate + correction: accept all, gate clips, correct on clip. No scoring."""
    anchor = _anchor(dim)
    gate = SovereignClippingGate(anchor, threshold=MEASURED_TAU)
    backend = DeterministicBackend(dim=dim, seed=seed)
    state = list(anchor)
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
    return _trial_result(state, anchor)


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
    for cycle in range(steps):
        ctrl.step(backend.propose(cycle), constraint_pressure=pressure)
    return _trial_result(ctrl.state, anchor)


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


def run_ablation(
    trials: int = DEFAULT_TRIALS,
    steps: int = DEFAULT_STEPS,
    dim: int = DEFAULT_DIM,
    pressure: float = DEFAULT_PRESSURE,
    base_seed: int = BASE_SEED,
) -> Dict[str, Any]:
    """Run all four ablation arms and assemble the receipt."""
    if trials < 1 or steps < 1 or dim < 1:
        raise ValueError("trials, steps, dim must all be >= 1")
    if pressure < 0.0:
        raise ValueError(f"pressure must be >= 0, got {pressure}")

    arms: Dict[str, List[Dict[str, Any]]] = {}
    for arm_name, arm_fn in _ARMS.items():
        arms[arm_name] = [arm_fn(base_seed + k, steps, dim, pressure) for k in range(trials)]

    metrics: Dict[str, Dict[str, float]] = {}
    for arm_name, records in arms.items():
        metrics[arm_name] = {
            "mean_final_similarity": _mean([r["final_similarity"] for r in records]),
            "collapse_fraction": _mean([1.0 if r["collapsed"] else 0.0 for r in records]),
            "mean_final_energy": _mean([r["final_energy"] for r in records]),
        }

    return {
        "harness": "nova-conscientia ablation",
        "protocol": "Ablation: isolating each oversight component with non-zero "
                    "constraint pressure so the dual channel has something to reject.",
        "parameters": {
            "trials": trials,
            "steps": steps,
            "dim": dim,
            "constraint_pressure": pressure,
            "base_seed": base_seed,
            "collapse_boundary": MEASURED_TAU,
        },
        "metrics": metrics,
        "per_trial": arms,
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
        },
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry point for the ablation harness."""
    parser = argparse.ArgumentParser(
        description="Ablation harness: gate-only vs gate+dual-channel vs gate+correction vs full."
    )
    parser.add_argument("--trials", type=int, default=DEFAULT_TRIALS)
    parser.add_argument("--steps", type=int, default=DEFAULT_STEPS)
    parser.add_argument("--dim", type=int, default=DEFAULT_DIM)
    parser.add_argument("--pressure", type=float, default=DEFAULT_PRESSURE,
                        help="constraint pressure fed to the dual channel (default 0.5)")
    parser.add_argument("--seed", type=int, default=BASE_SEED)
    parser.add_argument("--json", type=str, default=None,
                        help="path to write the ablation receipt JSON")
    args = parser.parse_args(list(argv if argv is not None else sys.argv[1:]))

    try:
        receipt = run_ablation(
            trials=args.trials, steps=args.steps, dim=args.dim,
            pressure=args.pressure, base_seed=args.seed,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(receipt["metrics"], indent=2))
    if args.json:
        out = Path(args.json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
        print(f"ablation receipt written to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Task benchmark: does the dual channel help when there is work to do?

Why this harness exists
-----------------------
The drift benchmark (run_benchmark.py) and the constant-pressure ablation
(run_ablation.py) share one structural weakness: every proposal is noise
relative to the task anchor, so there is no useful work to preserve.  An arm
that rejects everything looks perfectly "stable" and pays no price, and the
collapse metric is the gate's own threshold, so the gate passes it by
construction.

This harness removes both weaknesses:

1. A task.  A goal direction ``g`` sits ``GOAL_ANGLE_DEG`` from the anchor,
   inside the acceptance cone.  Each cycle the proposal is either ON-TASK (a
   step of ``ON_TASK_GAIN`` of the gap toward ``g``, plus small jitter) or
   OFF-TASK (a drift move from the seeded drift model).  The mix is drawn
   once per cycle, independent of the state, so every arm sees the same
   proposal sequence for a given seed.
2. A per-proposal constraint signal.  A simulated invariant checker reports
   ``pressure = SIGNAL_SENSITIVITY * |off-plane(move)| + sigma * |N(0, 1)|``,
   where off-plane means the component of the move outside span(anchor, g).
   ``sigma`` is swept over ``NOISE_SWEEP`` to show how the dual channel
   degrades as the checker becomes uninformative.
3. Metrics that do not reuse the gate's threshold:
   * ``final_task_error`` / ``mean_task_error``: 1 - cos(state, g).  A frozen
     agent keeps the reference error 1 - cos(GOAL_ANGLE_DEG).
   * ``mean_off_task_fraction``: |off-plane(state)| / |state|, averaged over
     cycles.
   * ``accept_on`` / ``accept_off``: acceptance rate of on-task and off-task
     proposals (the dual channel's discrimination).
   ``collapse_fraction`` is kept only for continuity with the other receipts.
4. A control.  ``control_sweep`` reruns everything with sensitivity 0: the
   signal is pure noise.  Any benefit that survives the control does not come
   from the signal; any harm it shows comes from the dual channel itself.

Epistemic status
----------------
Seeded deterministic simulation, no LLM calls.  The constraint signal is
*simulated* and informative by construction at sigma = 0; the harness tests
whether the dual-channel mechanism uses an informative signal and how fast
that use degrades with signal noise.  It says nothing about whether a real
invariant checker on a real model produces such a signal.  Every parameter
below is an arbitrary simulation parameter registered in PROVENANCE.
"""

from __future__ import annotations

import argparse
import json
import math
import platform
import random
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

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
from dual_channel_action import DualChannelAction, p_flux  # type: ignore
from anti_drift_controller import ADCCLController, drift_coordinate_capped  # type: ignore
from drift_model import DeterministicBackend  # type: ignore

#: Angle between the task anchor and the goal direction, in degrees.
GOAL_ANGLE_DEG = 10.0

#: Probability that a cycle's proposal is on-task.
ON_TASK_PROB = 0.5

#: Fraction of the remaining gap to the goal covered by one on-task proposal.
ON_TASK_GAIN = 0.2

#: Isotropic jitter scale added to on-task proposals.
ON_TASK_JITTER = 0.005

#: Gain of the simulated invariant checker on the off-plane move component.
SIGNAL_SENSITIVITY = 2.0

#: Signal-noise levels (sigma) swept by the harness.
NOISE_SWEEP = [0.0, 0.05, 0.1, 0.2, 0.5, 1.0]

DEFAULT_TRIALS = 40
DEFAULT_STEPS = 50
DEFAULT_DIM = 16
BASE_SEED = 20260906

PROVENANCE: Dict[str, str] = {
    "GOAL_ANGLE_DEG": (
        "Arbitrary simulation parameter: goal direction 10 deg from the anchor, "
        "chosen to lie inside the 17.465 deg acceptance cone so the gate never "
        "forbids the task itself."
    ),
    "ON_TASK_PROB": "Arbitrary simulation parameter: share of on-task proposals.",
    "ON_TASK_GAIN": (
        "Arbitrary simulation parameter: an on-task proposal closes this "
        "fraction of the gap between the state and the goal."
    ),
    "ON_TASK_JITTER": "Arbitrary simulation parameter: jitter on on-task proposals.",
    "SIGNAL_SENSITIVITY": (
        "Arbitrary simulation parameter: gain of the simulated invariant "
        "checker on the off-plane move norm. At 2.0 a typical drift move "
        "(norm ~0.25) produces pressure ~0.5, whose dissipation cost exceeds "
        "its exploration credit; tiny on-task moves produce ~0 pressure."
    ),
    "NOISE_SWEEP": (
        "Arbitrary simulation parameters: signal-noise levels, from a perfect "
        "checker (0) to one dominated by noise (1.0)."
    ),
    "DEFAULT_TRIALS": "Arbitrary simulation parameter (harness sample size).",
    "DEFAULT_STEPS": "Arbitrary simulation parameter (loop length).",
    "DEFAULT_DIM": "Arbitrary simulation parameter (state-space dimension).",
    "BASE_SEED": (
        "Reproducibility parameter: BASE_SEED + trial index seeds every RNG; "
        "the measurement date of tau (2026-09-06), mnemonic only."
    ),
}


# --------------------------------------------------------------------------- #
#  Geometry
# --------------------------------------------------------------------------- #


def _norm(v: Sequence[float]) -> float:
    """Euclidean norm."""
    return math.sqrt(sum(x * x for x in v))


def task_frame(dim: int, goal_angle_deg: float = GOAL_ANGLE_DEG) -> Tuple[List[float], List[float]]:
    """Anchor and goal unit vectors.

    The anchor is the first basis vector; the goal lies in the plane of the
    first two basis vectors at ``goal_angle_deg`` from the anchor.

    Args:
        dim: state-space dimension, >= 2.
        goal_angle_deg: angle between anchor and goal, in [0, 90).

    Returns:
        (anchor, goal), both unit vectors of length ``dim``.

    Raises:
        ValueError: if dim < 2 or the angle is outside [0, 90).
    """
    if dim < 2:
        raise ValueError(f"dim must be >= 2 for a task plane, got {dim}")
    if not 0.0 <= goal_angle_deg < 90.0:
        raise ValueError(f"goal angle must lie in [0, 90), got {goal_angle_deg}")
    anchor = [0.0] * dim
    anchor[0] = 1.0
    goal = [0.0] * dim
    rad = math.radians(goal_angle_deg)
    goal[0] = math.cos(rad)
    goal[1] = math.sin(rad)
    return anchor, goal


def off_plane(v: Sequence[float]) -> List[float]:
    """Component of ``v`` outside the task plane span(e0, e1).

    The anchor and goal both lie in the plane of the first two axes (see
    ``task_frame``), so the off-plane component is everything past index 1.
    """
    return [0.0, 0.0] + [float(x) for x in v[2:]]


def constraint_signal(move: Sequence[float], sigma: float, rng: random.Random,
                      sensitivity: float = SIGNAL_SENSITIVITY) -> float:
    """Simulated invariant checker: pressure on one proposal.

    ``sensitivity * |off-plane(move)| + sigma * |N(0, 1)|``.  One Gaussian is
    drawn on every call, whatever ``sigma`` is, so arms that ignore the signal
    consume the same random stream as arms that use it.

    Args:
        move: the proposed move vector.
        sigma: signal-noise scale, >= 0.
        rng: the seeded signal RNG.
        sensitivity: checker gain on the off-plane move norm, >= 0.

    Returns:
        The constraint pressure, >= 0.

    Raises:
        ValueError: on negative sigma or sensitivity.
    """
    if sigma < 0.0 or sensitivity < 0.0:
        raise ValueError("sigma and sensitivity must be >= 0")
    noise = abs(rng.gauss(0.0, 1.0))
    return sensitivity * _norm(off_plane(move)) + sigma * noise


# --------------------------------------------------------------------------- #
#  Proposal stream
# --------------------------------------------------------------------------- #


class TaskProposalStream:
    """Seeded mix of on-task and off-task (drift) proposals.

    The on/off-task choice, the drift moves and the jitter come from RNGs
    seeded by the trial seed and never by the state, so every arm sees the
    same sequence of proposal kinds for a given seed.  On-task moves depend on
    the current state (they point at the goal), which is the point: an agent
    that refuses them makes no progress.
    """

    def __init__(self, dim: int, seed: int, goal: Sequence[float]) -> None:
        """Seed the choice, jitter and drift RNGs for one trial.

        Args:
            dim: state-space dimension.
            seed: trial seed.
            goal: the goal unit vector.
        """
        self.dim = dim
        self.goal = list(goal)
        self._choice_rng = random.Random(f"{seed}-choice")
        self._jitter_rng = random.Random(f"{seed}-jitter")
        self._drift = DeterministicBackend(dim=dim, seed=seed)

    def propose(self, cycle: int, state: Sequence[float]) -> Tuple[List[float], bool]:
        """Draw one proposal; returns (move, on_task).

        Every draw happens on every call (jitter and drift included), so the
        streams stay aligned across arms whatever the arm does with the move.
        """
        on_task = self._choice_rng.random() < ON_TASK_PROB
        jitter = [ON_TASK_JITTER * self._jitter_rng.gauss(0.0, 1.0) for _ in range(self.dim)]
        drift_move = self._drift.propose(cycle)
        if not on_task:
            return drift_move, False
        move = [ON_TASK_GAIN * (g - s) + j for g, s, j in zip(self.goal, state, jitter)]
        return move, True


# --------------------------------------------------------------------------- #
#  Arms
# --------------------------------------------------------------------------- #


def _score(action: DualChannelAction, move: Sequence[float], state: Sequence[float],
           anchor: Sequence[float], pressure: float) -> bool:
    """Dual-channel verdict for one proposal, scored exactly as ADCCLController does."""
    candidate = [s + m for s, m in zip(state, move)]
    x_candidate = drift_coordinate_capped(candidate, anchor)
    decision = action.evaluate(
        momentum=_norm(move) / _norm(anchor),
        constraint_pressure=pressure,
        drift_excess=max(0.0, x_candidate - 1.0),
    )
    return decision.accepted


def _correct_toward_anchor(state: Sequence[float], anchor: Sequence[float]) -> List[float]:
    """The controller's correction step: move ``min(p_flux(x), 0.5)`` of the chord to the anchor."""
    rate = min(p_flux(drift_coordinate_capped(state, anchor)), 0.5)
    return [s + rate * (a - s) for s, a in zip(state, anchor)]


def run_trial(arm: str, seed: int, steps: int, dim: int, sigma: float,
              sensitivity: float = SIGNAL_SENSITIVITY) -> Dict[str, Any]:
    """Run one arm for one trial and return its per-trial metrics.

    Arms:
        unconstrained      every proposal applied, no gate.
        gate_only          every proposal applied, then gated.
        gate_dual_channel  proposals scored with the constraint signal;
                           rejected ones are skipped; accepted ones gated.
        gate_correction    every proposal applied and gated; on CLIP the
                           correction step pulls toward the anchor.
        full               ADCCLController, fed the constraint signal.

    Args:
        arm: one of the names above.
        seed: trial seed.
        steps: cycles.
        dim: state-space dimension.
        sigma: constraint-signal noise.
        sensitivity: checker gain on the off-plane move norm; 0 makes the
            signal pure noise (the uninformative control).

    Returns:
        Per-trial metrics (see module docstring).

    Raises:
        ValueError: on an unknown arm.
    """
    if arm not in ARMS:
        raise ValueError(f"unknown arm {arm!r}; expected one of {ARMS}")
    anchor, goal = task_frame(dim)
    stream = TaskProposalStream(dim, seed, goal)
    signal_rng = random.Random(f"{seed}-signal")
    gate = SovereignClippingGate(anchor, threshold=MEASURED_TAU)
    action = DualChannelAction()
    ctrl = ADCCLController(anchor=anchor, gate=SovereignClippingGate(anchor, threshold=MEASURED_TAU)) \
        if arm == "full" else None
    state = list(anchor)
    counts = {"on": 0, "off": 0, "on_acc": 0, "off_acc": 0}
    task_err_sum = 0.0
    off_frac_sum = 0.0

    for cycle in range(steps):
        current = ctrl.state if ctrl is not None else state
        move, on_task = stream.propose(cycle, current)
        pressure = constraint_signal(move, sigma, signal_rng, sensitivity)
        kind = "on" if on_task else "off"
        counts[kind] += 1

        if arm == "full":
            record = ctrl.step(move, constraint_pressure=pressure)
            accepted = record.verdict.startswith("ACCEPTED")
            state = ctrl.state
        elif arm == "gate_dual_channel":
            accepted = _score(action, move, state, anchor, pressure)
            if accepted:
                state, _ = gate.evaluate([s + m for s, m in zip(state, move)])
        else:
            accepted = True
            candidate = [s + m for s, m in zip(state, move)]
            if arm == "unconstrained":
                state = candidate
            else:
                state, decision = gate.evaluate(candidate)
                if arm == "gate_correction" and decision.verdict == "CLIP":
                    state, _ = gate.evaluate(_correct_toward_anchor(state, anchor))

        if accepted:
            counts[kind + "_acc"] += 1
        task_err_sum += 1.0 - cosine_similarity(state, goal)
        state_norm = _norm(state)
        off_frac_sum += _norm(off_plane(state)) / state_norm if state_norm > 0.0 else 1.0

    final_sim_anchor = cosine_similarity(state, anchor)
    return {
        "seed": seed,
        "final_task_error": 1.0 - cosine_similarity(state, goal),
        "mean_task_error": task_err_sum / steps,
        "mean_off_task_fraction": off_frac_sum / steps,
        "accept_on": counts["on_acc"] / counts["on"] if counts["on"] else 1.0,
        "accept_off": counts["off_acc"] / counts["off"] if counts["off"] else 1.0,
        "collapsed": final_sim_anchor < MEASURED_TAU - COLLAPSE_TOLERANCE,
    }


ARMS = ("unconstrained", "gate_only", "gate_dual_channel", "gate_correction", "full")


# --------------------------------------------------------------------------- #
#  Harness
# --------------------------------------------------------------------------- #


def _mean(values: Sequence[float]) -> float:
    """Arithmetic mean; 0.0 for an empty sequence."""
    return sum(values) / len(values) if values else 0.0


def frozen_task_error(goal_angle_deg: float = GOAL_ANGLE_DEG) -> float:
    """Task error of an agent that never leaves the anchor: 1 - cos(goal angle)."""
    return 1.0 - math.cos(math.radians(goal_angle_deg))


def run_task_benchmark(
    trials: int = DEFAULT_TRIALS,
    steps: int = DEFAULT_STEPS,
    dim: int = DEFAULT_DIM,
    sigmas: Optional[Sequence[float]] = None,
    base_seed: int = BASE_SEED,
) -> Dict[str, Any]:
    """Run every arm across the signal-noise sweep.

    Args:
        trials: trials per arm per noise level.
        steps: cycles per trial.
        dim: state-space dimension, >= 3 (the drift needs off-plane room).
        sigmas: noise levels (defaults to NOISE_SWEEP).
        base_seed: trial k uses base_seed + k.

    Returns:
        The receipt: parameters, per-noise per-arm means, and the frozen-agent
        reference error.  Per-trial records are omitted to keep it small; the
        run is deterministic, so they can be regenerated.

    Raises:
        ValueError: on non-positive sizes, dim < 3, or a negative / empty sweep.
    """
    sigmas = list(NOISE_SWEEP if sigmas is None else sigmas)
    if trials < 1 or steps < 1:
        raise ValueError("trials and steps must be >= 1")
    if dim < 3:
        raise ValueError(f"dim must be >= 3, got {dim}")
    if not sigmas or any(s < 0.0 for s in sigmas):
        raise ValueError("sigmas must be a non-empty list of values >= 0")

    def _sweep(sensitivity: float) -> Dict[str, Dict[str, Dict[str, float]]]:
        out: Dict[str, Dict[str, Dict[str, float]]] = {}
        for sigma in sigmas:
            key = str(sigma)
            out[key] = {}
            for arm in ARMS:
                records = [run_trial(arm, base_seed + k, steps, dim, sigma, sensitivity)
                           for k in range(trials)]
                out[key][arm] = {
                    metric: _mean([float(r[metric]) for r in records])
                    for metric in ("final_task_error", "mean_task_error",
                                   "mean_off_task_fraction", "accept_on", "accept_off")
                }
                out[key][arm]["collapse_fraction"] = _mean(
                    [1.0 if r["collapsed"] else 0.0 for r in records])
        return out

    sweep = _sweep(SIGNAL_SENSITIVITY)
    control_sweep = _sweep(0.0)

    return {
        "harness": "nova-conscientia task benchmark",
        "protocol": (
            "Seeded deterministic simulation, no LLM calls. On-task proposals "
            "move toward a goal inside the acceptance cone; off-task proposals "
            "come from the drift model. The constraint signal is a SIMULATED "
            "invariant checker (informative by construction at sigma = 0); the "
            "sweep measures how the dual channel uses it as it degrades. "
            "control_sweep repeats the run with sensitivity 0, so the signal is "
            "pure noise and carries no information about the proposal."
        ),
        "parameters": {
            "trials": trials,
            "steps": steps,
            "dim": dim,
            "noise_sweep": sigmas,
            "base_seed": base_seed,
            "goal_angle_deg": GOAL_ANGLE_DEG,
            "on_task_prob": ON_TASK_PROB,
            "on_task_gain": ON_TASK_GAIN,
            "on_task_jitter": ON_TASK_JITTER,
            "signal_sensitivity": SIGNAL_SENSITIVITY,
            "collapse_boundary": MEASURED_TAU,
            "collapse_tolerance": COLLAPSE_TOLERANCE,
        },
        "frozen_task_error": frozen_task_error(),
        "sweep": sweep,
        "control_sweep": control_sweep,
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
        },
    }


def _print_table(receipt: Dict[str, Any]) -> None:
    """Print both sweeps as human-readable tables."""
    print(f"frozen-agent task error (never moves): {receipt['frozen_task_error']:.4f}")
    header = (f"  {'arm':<18} {'acc_on':>7} {'acc_off':>7} {'task_err':>9} "
              f"{'mean_err':>9} {'off_frac':>9} {'collapse':>8}")
    for sweep_key, label in (("sweep", "informative signal"),
                             ("control_sweep", "CONTROL: uninformative signal")):
        print(f"\n=== {label} ===")
        _print_sweep(receipt, sweep_key, header)


def _print_sweep(receipt: Dict[str, Any], sweep_key: str, header: str) -> None:
    """Print one sweep of the receipt."""
    for sigma in receipt["parameters"]["noise_sweep"]:
        print(f"\nsignal noise sigma = {sigma}")
        print(header)
        for arm in ARMS:
            m = receipt[sweep_key][str(sigma)][arm]
            print(f"  {arm:<18} {m['accept_on']:>7.3f} {m['accept_off']:>7.3f} "
                  f"{m['final_task_error']:>9.4f} {m['mean_task_error']:>9.4f} "
                  f"{m['mean_off_task_fraction']:>9.4f} {m['collapse_fraction']:>8.3f}")


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry point for the task benchmark."""
    parser = argparse.ArgumentParser(
        description="Task benchmark: oversight arms on a goal-directed task "
                    "with a simulated per-proposal constraint signal."
    )
    parser.add_argument("--trials", type=int, default=DEFAULT_TRIALS)
    parser.add_argument("--steps", type=int, default=DEFAULT_STEPS)
    parser.add_argument("--dim", type=int, default=DEFAULT_DIM)
    parser.add_argument("--seed", type=int, default=BASE_SEED)
    parser.add_argument("--json", type=str, default=None,
                        help="path to write the receipt JSON")
    args = parser.parse_args(list(argv if argv is not None else sys.argv[1:]))
    try:
        receipt = run_task_benchmark(trials=args.trials, steps=args.steps,
                                     dim=args.dim, base_seed=args.seed)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    _print_table(receipt)
    if args.json:
        out = Path(args.json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
        print(f"\ntask benchmark receipt written to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

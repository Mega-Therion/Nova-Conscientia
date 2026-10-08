"""Auditor panel as the constraint signal (task benchmark, item 4).

Why this harness exists
-----------------------
The task benchmark's constraint signal is *simulated*: a checker that sees
each move's off-plane component, informative by construction.  This harness
replaces it with the repository's own adversarial-consensus machinery
(``verification/adversarial_auditor.py``): a panel of deterministic critics
reviews every proposal, and their rejections become the pressure fed to the
dual channel.

The critics are deliberately imperfect, each with a realistic blind spot:

* ``plane-critic``    sees the whole move; rejects when more than
                      ``CRITIC_OFF_PLANE_LIMIT`` of it lies off the task plane.
* ``anchor-critic``   knows only the anchor, not the goal; rejects any move
                      that lowers the state's cosine to the anchor.  Progress
                      toward a goal 10 deg away does exactly that, so this
                      critic confuses progress with drift.
* ``subspace-critic`` sees the task plane plus a seeded ``SUBSPACE_FRACTION``
                      of the other coordinates (partial observability);
                      applies the plane critic's rule to what it sees.

Pressure per proposal = ``rejection_pressure * (number of rejecting
critics)``, swept over ``REJECTION_PRESSURES``.

Arms (all on the task benchmark's proposal streams; trial k of every arm
shares seed and proposals, so differences are paired):

* ``gate_only``             reference: every proposal applied, then gated.
* ``consensus_gate``        AdversarialConsensus admits a proposal only if no
                            critic rejects it; admitted proposals are gated.
                            The auditor alone, no dual channel.
* ``dual_classic``          gate_dual_channel, classic credit, auditor pressure.
* ``dual_running_reference`` gate_dual_channel, running_reference credit,
                            auditor pressure.

Epistemic status: seeded deterministic simulation, no LLM calls.  The critics
are hand-written rubric functions over vectors, standing in for model critics.
Every parameter below is an arbitrary simulation parameter registered in
PROVENANCE.
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
for _p in (_REPO_ROOT / "core", _REPO_ROOT / "benchmarks", _REPO_ROOT / "verification"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from adversarial_auditor import APPROVE, REJECT, AdversarialConsensus, CriticAuditor  # type: ignore
from sovereign_clipping_gate import MEASURED_TAU, SovereignClippingGate, cosine_similarity  # type: ignore
from run_task_benchmark import (  # type: ignore
    BOOTSTRAP_RESAMPLES,
    DEFAULT_DIM,
    DEFAULT_STEPS,
    DEFAULT_TRIALS,
    ROBUSTNESS_SEEDS,
    TaskProposalStream,
    _seed_for_metric,
    bootstrap_ci,
    frozen_task_error,
    off_plane,
    run_trial,
    task_frame,
)

#: A plane critic rejects a move whose off-plane share of its norm exceeds this.
CRITIC_OFF_PLANE_LIMIT = 0.5

#: Share of the off-plane coordinates the subspace critic can observe.
SUBSPACE_FRACTION = 0.5

#: Pressure added per rejecting critic, swept by the harness.
REJECTION_PRESSURES = [0.05, 0.1, 0.2, 0.4]

#: An arm "beats the frozen agent" only if its task-error CI ends this far below it.
FROZEN_TOLERANCE = 1e-9

#: Critic names, in panel order.
CRITICS = ("plane-critic", "anchor-critic", "subspace-critic")

#: Arms run by this harness.
AUDITOR_ARMS = ("gate_only", "consensus_gate", "dual_classic", "dual_running_reference")

PROVENANCE: Dict[str, str] = {
    "CRITIC_OFF_PLANE_LIMIT": (
        "Arbitrary simulation parameter: a rubric critic rejects a move that is "
        "mostly (more than half) off the task plane."
    ),
    "SUBSPACE_FRACTION": (
        "Arbitrary simulation parameter: the partially-observing critic sees "
        "half of the off-plane coordinates (seeded per trial)."
    ),
    "REJECTION_PRESSURES": (
        "Arbitrary simulation parameters: constraint pressure contributed by "
        "each rejecting critic, swept because the mapping from votes to "
        "pressure is a free design choice."
    ),
    "FROZEN_TOLERANCE": (
        "Floating-point tolerance: an arm that never moves has task error equal "
        "to the frozen reference up to rounding; 1e-9 keeps rounding from "
        "counting as an improvement (same role as COLLAPSE_TOLERANCE)."
    ),
    "CRITICS": "Names of the three rubric critics in the panel (labels, not numbers).",
    "AUDITOR_ARMS": "Names of the arms this harness runs (labels, not numbers).",
}


# --------------------------------------------------------------------------- #
#  The critic panel
# --------------------------------------------------------------------------- #


def _norm(v: Sequence[float]) -> float:
    """Euclidean norm."""
    return math.sqrt(sum(x * x for x in v))


def _off_plane_share(move: Sequence[float], visible: Optional[Sequence[int]] = None) -> float:
    """Off-plane share of a move's norm, over all coordinates or only ``visible`` ones.

    The task plane is span(e0, e1); ``visible`` lists the off-plane indices
    (>= 2) the observer can see.  A zero move has share 0.
    """
    plane = [move[0], move[1]]
    off = off_plane(move)[2:] if visible is None else [move[i] for i in visible]
    total = _norm(plane + list(off))
    return _norm(off) / total if total > 0.0 else 0.0


def build_panel(dim: int, seed: int) -> AdversarialConsensus:
    """Build the three-critic consensus panel for one trial.

    Args:
        dim: state-space dimension, >= 3.
        seed: trial seed (selects the subspace critic's visible coordinates).

    Returns:
        An AdversarialConsensus over the panel; a proposal is admitted only
        when no critic rejects it.
    """
    anchor, _ = task_frame(dim)
    off_idx = list(range(2, dim))
    k = max(1, int(round(SUBSPACE_FRACTION * len(off_idx))))
    visible = sorted(random.Random(f"{seed}-subspace").sample(off_idx, k))

    def plane(proposal: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Reject a move that lies mostly off the task plane."""
        share = _off_plane_share(proposal["move"])
        ok = share <= CRITIC_OFF_PLANE_LIMIT
        return {"verdict": APPROVE if ok else REJECT, "fatal": False,
                "reason": f"off-plane share {share:.3f}"}

    def anchor_only(proposal: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Reject a move that lowers the state's cosine to the anchor."""
        state, move = proposal["state"], proposal["move"]
        before = cosine_similarity(state, anchor)
        after = cosine_similarity([s + m for s, m in zip(state, move)], anchor)
        ok = after >= before
        return {"verdict": APPROVE if ok else REJECT, "fatal": False,
                "reason": f"anchor cosine {before:.5f} -> {after:.5f}"}

    def subspace(proposal: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply the plane rule to the coordinates this critic can see."""
        share = _off_plane_share(proposal["move"], visible)
        ok = share <= CRITIC_OFF_PLANE_LIMIT
        return {"verdict": APPROVE if ok else REJECT, "fatal": False,
                "reason": f"visible off-plane share {share:.3f}"}

    critics = [CriticAuditor(plane, "plane-critic"), CriticAuditor(anchor_only, "anchor-critic"),
               CriticAuditor(subspace, "subspace-critic")]
    return AdversarialConsensus(critics, quorum=len(critics))


def deliberate(panel: AdversarialConsensus, move: Sequence[float],
               state: Sequence[float]) -> Tuple[bool, Dict[str, bool]]:
    """Run the panel on one proposal; returns (admitted, {critic: rejected})."""
    receipt = panel.deliberate({"move": [float(m) for m in move],
                                "state": [float(s) for s in state]})
    return receipt.admitted, {a.auditor_id: a.verdict == REJECT for a in receipt.verdicts}


def auditor_pressure_fn(panel: AdversarialConsensus,
                        rejection_pressure: float) -> Callable[[Sequence[float], Sequence[float]], float]:
    """Constraint signal for run_trial: pressure = rejection_pressure * rejecting critics."""
    if rejection_pressure < 0.0:
        raise ValueError("rejection_pressure must be >= 0")

    def fn(move: Sequence[float], state: Sequence[float]) -> float:
        """Pressure on one proposal from the panel's rejections."""
        _, rejected = deliberate(panel, move, state)
        return rejection_pressure * sum(1 for r in rejected.values() if r)

    return fn


# --------------------------------------------------------------------------- #
#  Arms
# --------------------------------------------------------------------------- #


def run_consensus_trial(seed: int, steps: int, dim: int) -> Dict[str, Any]:
    """consensus_gate arm, also recording each critic's rejection rate by proposal kind.

    Returns:
        Task-benchmark style metrics plus ``critic_reject_on`` /
        ``critic_reject_off`` (per critic: share of on-task / off-task
        proposals it rejected).
    """
    anchor, goal = task_frame(dim)
    stream = TaskProposalStream(dim, seed, goal)
    signal_rng = random.Random(f"{seed}-signal")  # drawn to keep streams aligned
    gate = SovereignClippingGate(anchor, threshold=MEASURED_TAU)
    panel = build_panel(dim, seed)
    state = list(anchor)
    counts = {"on": 0, "off": 0, "on_acc": 0, "off_acc": 0}
    crit = {c: {"on": 0, "off": 0} for c in CRITICS}
    for cycle in range(steps):
        move, on_task = stream.propose(cycle, state)
        signal_rng.gauss(0.0, 1.0)
        kind = "on" if on_task else "off"
        counts[kind] += 1
        admitted, rejected = deliberate(panel, move, state)
        for c, r in rejected.items():
            crit[c][kind] += 1 if r else 0
        if admitted:
            counts[kind + "_acc"] += 1
            state, _ = gate.evaluate([s + m for s, m in zip(state, move)])
    n_on, n_off = max(counts["on"], 1), max(counts["off"], 1)
    return {
        "final_task_error": 1.0 - cosine_similarity(state, goal),
        "accept_on": counts["on_acc"] / n_on if counts["on"] else 1.0,
        "accept_off": counts["off_acc"] / n_off if counts["off"] else 1.0,
        "critic_reject_on": {c: crit[c]["on"] / n_on for c in CRITICS},
        "critic_reject_off": {c: crit[c]["off"] / n_off for c in CRITICS},
    }


def run_arm(arm: str, seed: int, steps: int, dim: int, rejection_pressure: float) -> Dict[str, Any]:
    """Run one arm for one trial.

    Raises:
        ValueError: on an unknown arm.
    """
    if arm == "gate_only":
        return run_trial("gate_only", seed, steps, dim, 0.0)
    if arm == "consensus_gate":
        return run_consensus_trial(seed, steps, dim)
    modes = {"dual_classic": "classic", "dual_running_reference": "running_reference"}
    if arm not in modes:
        raise ValueError(f"unknown arm {arm!r}; expected one of {AUDITOR_ARMS}")
    pressure_fn = auditor_pressure_fn(build_panel(dim, seed), rejection_pressure)
    return run_trial("gate_dual_channel", seed, steps, dim, 0.0, credit_mode=modes[arm],
                     pressure_fn=pressure_fn)


# --------------------------------------------------------------------------- #
#  Harness
# --------------------------------------------------------------------------- #


def _mean(values: Sequence[float]) -> float:
    """Arithmetic mean; 0.0 for an empty sequence."""
    return sum(values) / len(values) if values else 0.0


def _ci(values: Sequence[float], key: str, seed: int) -> List[float]:
    """95% bootstrap CI of the mean of ``values``."""
    _, lo, hi = bootstrap_ci(list(values), seed=_seed_for_metric(seed, key, 0.0, "auditor-ci", 0.0))
    return [lo, hi]


def _paired(a: Sequence[float], b: Sequence[float], key: str, seed: int) -> Dict[str, Any]:
    """Paired bootstrap of per-trial differences a - b."""
    diffs = [x - y for x, y in zip(a, b)]
    m, lo, hi = bootstrap_ci(diffs, seed=_seed_for_metric(seed, key, 0.0, "auditor", 0.0))
    return {"mean": m, "ci95": [lo, hi]}


def run_auditor_benchmark(
    trials: int = DEFAULT_TRIALS,
    steps: int = DEFAULT_STEPS,
    dim: int = DEFAULT_DIM,
    seeds: Sequence[int] = ROBUSTNESS_SEEDS,
    pressures: Sequence[float] = REJECTION_PRESSURES,
) -> Dict[str, Any]:
    """Run every arm with the auditor panel as the constraint signal.

    Args:
        trials: trials per arm.
        steps: cycles per trial.
        dim: state-space dimension, >= 3.
        seeds: base seeds (trial k uses seed + k).
        pressures: pressure per rejecting critic, swept for the dual arms.

    Returns:
        The receipt: per seed, the critics' rejection rates by proposal kind,
        per-arm means, and paired task-error differences against gate-only and
        against consensus_gate; plus a cross-seed summary.  Because a frozen
        agent (task error 1 - cos 10 deg) already beats gate-only here, an arm
        only counts as useful if it also beats the frozen agent
        (``beats_frozen_all_seeds``: the 95% CI of its task error lies below
        the frozen error).

    Raises:
        ValueError: on non-positive sizes, dim < 3, or an empty / negative sweep.
    """
    if trials < 1 or steps < 1:
        raise ValueError("trials and steps must be >= 1")
    if dim < 3:
        raise ValueError(f"dim must be >= 3, got {dim}")
    if not pressures or any(p < 0.0 for p in pressures):
        raise ValueError("pressures must be a non-empty list of values >= 0")

    results: Dict[str, Any] = {}
    for seed in seeds:
        gate = [run_arm("gate_only", seed + k, steps, dim, 0.0) for k in range(trials)]
        cons = [run_arm("consensus_gate", seed + k, steps, dim, 0.0) for k in range(trials)]
        gate_err = [r["final_task_error"] for r in gate]
        cons_err = [r["final_task_error"] for r in cons]
        seed_out: Dict[str, Any] = {
            "critics": {c: {"reject_on": _mean([r["critic_reject_on"][c] for r in cons]),
                            "reject_off": _mean([r["critic_reject_off"][c] for r in cons])}
                        for c in CRITICS},
            "gate_only": {"final_task_error": _mean(gate_err)},
            "consensus_gate": {
                "accept_on": _mean([r["accept_on"] for r in cons]),
                "accept_off": _mean([r["accept_off"] for r in cons]),
                "final_task_error": _mean(cons_err),
                "final_task_error_ci95": _ci(cons_err, "cons", seed),
                "paired_err_minus_gate": _paired(cons_err, gate_err, "cons-gate", seed),
            },
            "dual": {},
        }
        for pressure in pressures:
            per_p: Dict[str, Any] = {}
            for arm in ("dual_classic", "dual_running_reference"):
                recs = [run_arm(arm, seed + k, steps, dim, pressure) for k in range(trials)]
                err = [r["final_task_error"] for r in recs]
                per_p[arm] = {
                    "accept_on": _mean([r["accept_on"] for r in recs]),
                    "accept_off": _mean([r["accept_off"] for r in recs]),
                    "final_task_error": _mean(err),
                    "final_task_error_ci95": _ci(err, f"{arm}-{pressure}", seed),
                    "paired_err_minus_gate": _paired(err, gate_err, f"{arm}-{pressure}-gate", seed),
                    "paired_err_minus_consensus": _paired(err, cons_err, f"{arm}-{pressure}-cons", seed),
                }
            seed_out["dual"][str(pressure)] = per_p
        results[str(seed)] = seed_out

    frozen = frozen_task_error()

    def _below(d: Dict[str, Any]) -> bool:
        return d["ci95"][1] < 0.0

    def _beats_frozen(d: Dict[str, Any]) -> bool:
        return d["final_task_error_ci95"][1] < frozen - FROZEN_TOLERANCE

    summary: Dict[str, Any] = {
        "consensus_beats_gate_all_seeds": all(
            _below(results[str(s)]["consensus_gate"]["paired_err_minus_gate"]) for s in seeds),
        "consensus_beats_frozen_all_seeds": all(
            _beats_frozen(results[str(s)]["consensus_gate"]) for s in seeds),
    }
    for pressure in pressures:
        for arm in ("dual_classic", "dual_running_reference"):
            per = [results[str(s)]["dual"][str(pressure)][arm] for s in seeds]
            summary[f"{arm}@{pressure}"] = {
                "beats_gate_all_seeds": all(_below(p["paired_err_minus_gate"]) for p in per),
                "beats_frozen_all_seeds": all(_beats_frozen(p) for p in per),
                "beats_consensus_all_seeds": all(_below(p["paired_err_minus_consensus"]) for p in per),
            }
    return {
        "harness": "nova-conscientia auditor-signal benchmark",
        "protocol": (
            "Seeded deterministic simulation, no LLM calls. The constraint signal "
            "is a panel of three rubric critics run through AdversarialConsensus "
            "(verification/adversarial_auditor.py); pressure = per-rejection "
            "pressure x rejecting critics. Paired bootstrap 95% CIs on per-trial "
            "differences (arms share seeds and proposal streams)."
        ),
        "parameters": {
            "trials": trials, "steps": steps, "dim": dim, "seeds": list(seeds),
            "rejection_pressures": list(pressures),
            "critic_off_plane_limit": CRITIC_OFF_PLANE_LIMIT,
            "subspace_fraction": SUBSPACE_FRACTION,
            "bootstrap_resamples": BOOTSTRAP_RESAMPLES,
        },
        "frozen_task_error": frozen_task_error(),
        "results": results,
        "summary": summary,
        "environment": {"python": platform.python_version(), "platform": platform.platform()},
    }


def _print_report(receipt: Dict[str, Any]) -> None:
    """Print the first seed's tables and the cross-seed summary."""
    seed = str(receipt["parameters"]["seeds"][0])
    res = receipt["results"][seed]
    print(f"auditor-signal benchmark (seed {seed}; frozen-agent task error "
          f"{receipt['frozen_task_error']:.4f})")
    print("\ncritic rejection rates (on-task / off-task proposals):")
    for c, r in res["critics"].items():
        print(f"  {c:<16} {r['reject_on']:.3f} / {r['reject_off']:.3f}")
    c = res["consensus_gate"]
    print(f"\n  {'gate_only':<24} task_err {res['gate_only']['final_task_error']:.4f}")
    print(f"  {'consensus_gate':<24} acc_on {c['accept_on']:.3f} acc_off {c['accept_off']:.3f} "
          f"task_err {c['final_task_error']:.4f} err-gate {c['paired_err_minus_gate']['mean']:+.4f} "
          f"[{c['paired_err_minus_gate']['ci95'][0]:+.4f}, {c['paired_err_minus_gate']['ci95'][1]:+.4f}]")
    for pressure, arms in res["dual"].items():
        for arm, m in arms.items():
            g, k = m["paired_err_minus_gate"], m["paired_err_minus_consensus"]
            print(f"  {arm + '@' + pressure:<24} acc_on {m['accept_on']:.3f} acc_off {m['accept_off']:.3f} "
                  f"task_err {m['final_task_error']:.4f} err-gate {g['mean']:+.4f} "
                  f"[{g['ci95'][0]:+.4f}, {g['ci95'][1]:+.4f}] err-consensus {k['mean']:+.4f} "
                  f"[{k['ci95'][0]:+.4f}, {k['ci95'][1]:+.4f}]")
    print("\nsummary (all seeds):")
    for key, val in receipt["summary"].items():
        print(f"  {key}: {val}")


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry point for the auditor-signal benchmark."""
    parser = argparse.ArgumentParser(
        description="Task benchmark with the adversarial auditor panel as the constraint signal."
    )
    parser.add_argument("--trials", type=int, default=DEFAULT_TRIALS)
    parser.add_argument("--steps", type=int, default=DEFAULT_STEPS)
    parser.add_argument("--dim", type=int, default=DEFAULT_DIM)
    parser.add_argument("--json", type=str, default=None, help="path to write the receipt JSON")
    args = parser.parse_args(list(argv if argv is not None else sys.argv[1:]))
    try:
        receipt = run_auditor_benchmark(trials=args.trials, steps=args.steps, dim=args.dim)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    _print_report(receipt)
    if args.json:
        out = Path(args.json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
        print(f"\nauditor-signal receipt written to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

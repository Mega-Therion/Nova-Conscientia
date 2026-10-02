"""Empirical harness: unconstrained drift vs. dual-channel swarm stability.

Arms
----
A (baseline)  One unconstrained agent per trial: the drift model proposes, the
              state integrates the proposal raw.  This is the "raw LLM drift"
              arm (deterministic stand-in for a live model backend).

B (swarm)     A swarm of S agents per trial, each running the ADCCL runtime
              (dual-channel action, sovereign clipping gate, correction force),
              plus hierarchical swarm attention: agents cross-influence through
              the QUMOND-translated topology graph, with the swarm centroid as
              the shared context field (context bias + screening, the
              external-field-effect translation).

Metrics
-------
* mean_final_similarity  -- mean cosine(state_T, anchor) over trials.
* collapse_fraction      -- share of trials whose final similarity falls below
                            the measured collapse boundary (MEASURED_TAU).
* mean_energy            -- mean final Lyapunov-style energy F_dual(x).
* mean_pairwise_cosine   -- (arm B) mean pairwise cosine across the swarm's
                            final states: 1.0 means agents are identical, lower
                            means more spread.  Arm A defines it as 0.0 (single agent).

Receipts
--------
``run_benchmark.py --json PATH`` writes a full receipt: parameters, per-arm
metrics, per-trial records, and the provenance of every constant used.  The
run is deterministic for a given seed set.  The receipt is the committed
artifact (benchmarks/results/benchmark_receipt.json).

Epistemic status (Contingent Box Protocol)
------------------------------------------
This harness validates the *control mechanism* on a deterministic drift model.
It is NOT evidence about live frontier models: the collapse boundary is the
measured single-pipeline threshold of Res-Nova (tau = 0.9539, see
core/sovereign_clipping_gate.py), and the decisive external test -- measuring
drift collapse on agent stacks other than the one it was tuned on -- is the
fellowship work plan's first experiment (fellowship/ANTHROPIC_FELLOWS_PROPOSAL.md).
"""

from __future__ import annotations

import argparse
import json
import math
import platform
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

_REPO_ROOT = Path(__file__).resolve().parent.parent
for _p in (_REPO_ROOT / "core", _REPO_ROOT / "benchmarks"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from sovereign_clipping_gate import (  # type: ignore
    MEASURED_TAU,
    SovereignClippingGate,
    cosine_similarity,
)
from dual_channel_action import DualChannelAction, f_dual  # type: ignore
from anti_drift_controller import ADCCLController, drift_coordinate_capped  # type: ignore
from topology_graph import AgentNode, TopologyGraph  # type: ignore
from drift_model import DeterministicBackend  # type: ignore

#: Default trials per arm (simulation parameter).
DEFAULT_TRIALS = 40

#: Default cycles per trial (simulation parameter).
DEFAULT_STEPS = 50

#: Default state-space dimension (simulation parameter).
DEFAULT_DIM = 16

#: Default swarm size for arm B (simulation parameter).
DEFAULT_SWARM = 4

#: Cohesion rate of swarm attention on states (simulation parameter).
COHESION_RATE = 0.05

#: Base seed; trial k uses BASE_SEED + k (reproducibility parameter).
BASE_SEED = 20260906

PROVENANCE: Dict[str, str] = {
    "DEFAULT_TRIALS": "Arbitrary simulation parameter (harness sample size).",
    "DEFAULT_STEPS": "Arbitrary simulation parameter (loop length).",
    "DEFAULT_DIM": "Arbitrary simulation parameter (state-space dimension).",
    "DEFAULT_SWARM": "Arbitrary simulation parameter (swarm size of arm B).",
    "COHESION_RATE": (
        "Arbitrary simulation parameter: fraction of the attended swarm field "
        "integrated into each agent's state per cycle."
    ),
    "BASE_SEED": (
        "Reproducibility parameter: BASE_SEED + trial index seeds every RNG. "
        "Chosen as the measurement date of tau (2026-09-06) for mnemonic value "
        "only; it has no other significance."
    ),
}


def _anchor(dim: int) -> List[float]:
    """The canonical task anchor: the first basis direction.

    Args:
        dim: state-space dimension.

    Returns:
        A unit vector [1, 0, ..., 0].
    """
    a = [0.0] * dim
    a[0] = 1.0
    return a


def run_baseline_trial(seed: int, steps: int, dim: int) -> Dict[str, Any]:
    """One unconstrained trial (arm A): integrate raw proposals.

    Args:
        seed: RNG seed for this trial.
        steps: number of proposals to integrate.
        dim: state-space dimension.

    Returns:
        A per-trial record (final similarity, minimum similarity, energy).
    """
    anchor = _anchor(dim)
    backend = DeterministicBackend(dim=dim, seed=seed)
    state = list(anchor)
    min_sim = 1.0
    for cycle in range(steps):
        move = backend.propose(cycle)
        state = [s + m for s, m in zip(state, move)]
        sim = cosine_similarity(state, anchor)
        min_sim = min(min_sim, sim)
    final_sim = cosine_similarity(state, anchor)
    x = drift_coordinate_capped(state, anchor)
    return {
        "seed": seed,
        "final_similarity": final_sim,
        "min_similarity": min_sim,
        "final_energy": f_dual(x),
        "collapsed": final_sim < MEASURED_TAU,
    }


def run_swarm_trial(
    seed: int, steps: int, dim: int, swarm: int, cohesion_rate: float,
    constraint_pressure: float = 0.0,
) -> Dict[str, Any]:
    """One dual-channel swarm trial (arm B).

    Each of ``swarm`` agents runs its own ADCCL controller (dual-channel action
    + sovereign gate + correction force) on its own seeded proposal stream.
    After the per-agent cycle, the swarm's attention layer runs: the topology
    graph is rebuilt over the agents' current states, the centroid-scaled
    context field is applied per agent (context bias with QUMOND amplification
    and screening), and each agent integrates a ``cohesion_rate`` fraction of
    its attended field.  The sovereign gate is applied last, so the context
    bias cannot itself drag a state out of the cone.

    Args:
        seed: base RNG seed (agent i uses seed + 1000 * i + 1).
        steps: number of cycles.
        dim: state-space dimension.
        swarm: number of agents.
        cohesion_rate: fraction of the attended field integrated per cycle.

    Returns:
        A per-trial record including mean pairwise cosine across the swarm.
    """
    anchor = _anchor(dim)
    controllers = []
    backends = []
    for i in range(swarm):
        controllers.append(
            ADCCLController(
                anchor=anchor,
                action=DualChannelAction(),
                gate=SovereignClippingGate(anchor, threshold=MEASURED_TAU),
            )
        )
        backends.append(DeterministicBackend(dim=dim, seed=seed + 1000 * i + 1))
    cohesion_rate = max(0.0, min(cohesion_rate, 1.0))
    halts = 0
    for cycle in range(steps):
        for i, (ctrl, backend) in enumerate(zip(controllers, backends)):
            ctrl.step(backend.propose(cycle), constraint_pressure=constraint_pressure)
        # Swarm attention pass: context bias (external field) + screening.
        agents = [
            AgentNode(agent_id=f"agent{i}", position=ctrl.state, mass=1.0)
            for i, ctrl in enumerate(controllers)
        ]
        topology = TopologyGraph(agents)
        centroid = [0.0] * dim
        for ctrl in controllers:
            centroid = [c + s for c, s in zip(centroid, ctrl.state)]
        centroid = [c / swarm for c in centroid]
        for i, ctrl in enumerate(controllers):
            attended = topology.apply_context_field(f"agent{i}", centroid)
            biased = [s + cohesion_rate * a for s, a in zip(ctrl.state, attended)]
            clipped, _ = ctrl.gate.evaluate(biased)
            ctrl._state = clipped  # noqa: SLF001 - harness owns the wiring
        halts = sum(1 for c in controllers if c.halted)
        if halts:
            break
    final_sims = [cosine_similarity(ctrl.state, anchor) for ctrl in controllers]
    mean_pairwise = 0.0
    pairs = 0
    for i in range(swarm):
        for j in range(i + 1, swarm):
            mean_pairwise += cosine_similarity(controllers[i].state, controllers[j].state)
            pairs += 1
    diversity = mean_pairwise / pairs if pairs else 0.0
    energies = [f_dual(drift_coordinate_capped(c.state, anchor)) for c in controllers]
    return {
        "seed": seed,
        "final_similarity": sum(final_sims) / swarm,
        "min_similarity": min(final_sims),
        "final_energy": sum(energies) / swarm,
        "pairwise_cosine": diversity,
        "collapsed": sum(1 for s in final_sims if s < MEASURED_TAU) > 0,
        "halts": halts,
    }


def _mean(values: Sequence[float]) -> float:
    """Arithmetic mean; 0.0 for an empty sequence."""
    return sum(values) / len(values) if values else 0.0


def run_benchmark(
    trials: int = DEFAULT_TRIALS,
    steps: int = DEFAULT_STEPS,
    dim: int = DEFAULT_DIM,
    swarm: int = DEFAULT_SWARM,
    cohesion_rate: float = COHESION_RATE,
    base_seed: int = BASE_SEED,
    constraint_pressure: float = 0.0,
) -> Dict[str, Any]:
    """Run both arms and assemble the receipt.

    Args:
        trials: trials per arm.
        steps: cycles per trial.
        dim: state-space dimension.
        swarm: agents per swarm trial (arm B).
        cohesion_rate: swarm cohesion rate (arm B).
        base_seed: seed base (trial k uses base_seed + k).

    Returns:
        The full receipt mapping (parameters, metrics, per-trial records,
        provenance).  Deterministic for a given parameter set.
    """
    if trials < 1 or steps < 1 or dim < 1 or swarm < 1:
        raise ValueError("trials, steps, dim and swarm must all be >= 1")
    if not 0.0 <= cohesion_rate <= 1.0:
        raise ValueError(f"cohesion_rate must lie in [0, 1], got {cohesion_rate}")

    baseline = [run_baseline_trial(base_seed + k, steps, dim) for k in range(trials)]
    swarm_arm = [
        run_swarm_trial(base_seed + k, steps, dim, swarm, cohesion_rate,
                        constraint_pressure)
        for k in range(trials)
    ]

    def arm_metrics(records: Sequence[Dict[str, Any]]) -> Dict[str, float]:
        """Aggregate one arm's per-trial records into metrics."""
        return {
            "mean_final_similarity": _mean([r["final_similarity"] for r in records]),
            "collapse_fraction": _mean([1.0 if r["collapsed"] else 0.0 for r in records]),
            "mean_min_similarity": _mean([r["min_similarity"] for r in records]),
            "mean_final_energy": _mean([r["final_energy"] for r in records]),
        }

    receipt = {
        "harness": "nova-conscientia dual-channel benchmark",
        "protocol": "Contingent Box Protocol: deterministic receipt, no LLM calls "
                    "(live-model validation is the fellowship work plan's first "
                    "external experiment)",
        "parameters": {
            "trials": trials,
            "steps": steps,
            "dim": dim,
            "swarm": swarm,
            "cohesion_rate": cohesion_rate,
            "base_seed": base_seed,
            "collapse_boundary": MEASURED_TAU,
        },
        "metrics": {
            "baseline_unconstrained": arm_metrics(baseline),
            "dual_channel_swarm": {
                **arm_metrics(swarm_arm),
                "mean_pairwise_cosine": _mean([r["pairwise_cosine"] for r in swarm_arm]),
                "halt_trials": float(sum(1 for r in swarm_arm if r["halts"])),
            },
        },
        "per_trial": {"baseline": baseline, "swarm": swarm_arm},
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
        },
        "provenance": {
            "MEASURED_TAU": "measured ADCCL threshold (Res-Nova "
                            "ALIGNMENT_CEILING_ONE_RELATION.md, 2026-09-06)",
            "simulation_parameters": "arbitrary, seeded; see PROVENANCE in "
                                     "run_benchmark.py and drift_model.py",
            "source_repos": {
                "Res-Nova": "github.com/Mega-Therion/Res-Nova (see PROVENANCE.md "
                            "for commit and file hashes)",
                "Nova-Conscientia": "github.com/Mega-Therion/Nova-Conscientia",
            },
        },
    }
    return receipt


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry point.

    Args:
        argv: command-line arguments (defaults to sys.argv[1:]).

    Returns:
        0 on a clean run, 1 on argument or IO errors (fail closed).
    """
    parser = argparse.ArgumentParser(
        description="Unconstrained drift vs dual-channel swarm stability harness."
    )
    parser.add_argument("--trials", type=int, default=DEFAULT_TRIALS)
    parser.add_argument("--steps", type=int, default=DEFAULT_STEPS)
    parser.add_argument("--dim", type=int, default=DEFAULT_DIM)
    parser.add_argument("--swarm", type=int, default=DEFAULT_SWARM)
    parser.add_argument("--cohesion", type=float, default=COHESION_RATE)
    parser.add_argument("--seed", type=int, default=BASE_SEED)
    parser.add_argument("--pressure", type=float, default=0.0,
                        help="constraint pressure fed to the dual channel (default 0.0)")
    parser.add_argument("--json", type=str, default=None,
                         help="path to write the receipt JSON")
    args = parser.parse_args(list(argv if argv is not None else sys.argv[1:]))

    try:
        receipt = run_benchmark(
            trials=args.trials, steps=args.steps, dim=args.dim, swarm=args.swarm,
            cohesion_rate=args.cohesion, base_seed=args.seed,
            constraint_pressure=args.pressure,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    metrics = receipt["metrics"]
    print(json.dumps({
        "baseline": metrics["baseline_unconstrained"],
        "swarm": metrics["dual_channel_swarm"],
    }, indent=2))
    if args.json:
        out = Path(args.json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
        print(f"receipt written to {out}")
    verdict_stable = (
        metrics["dual_channel_swarm"]["collapse_fraction"]
        < metrics["baseline_unconstrained"]["collapse_fraction"]
        or metrics["baseline_unconstrained"]["collapse_fraction"] == 0.0
    )
    print(f"stability verdict: {'PASS' if verdict_stable else 'FAIL'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Sensitivity of the auditor-signal result to the votes-to-pressure mapping.

Why this harness exists
-----------------------
``run_auditor_signal.py`` (item 4) found that the critics' votes, fed into the
dual channel with ``running_reference`` credit, beat gate-only, a frozen agent
and unanimous consensus at 0.1 and 0.2 pressure per rejecting critic, and not
at 0.05 or 0.4.  That "0.1-0.2 window" was read off a four-point grid, so it
was a free parameter.  This harness does two things with it.

1. **Derives the window from the acceptance rule.**  With ``running_reference``
   credit the dual channel admits a proposal iff

       L_corr(k * p + drift_excess) <= H(x_ref) = x_ref^2 / 2,

   where ``k`` is the number of rejecting critics, ``p`` the pressure per
   rejection and ``x_ref`` the mean momentum of the proposals scored before
   it.  L_corr is strictly increasing on [0, inf), so with
   ``w* = L_corr^-1(H(x_ref))`` and no drift excess this is ``k * p <= w*``.
   On-task moves draw ``k_on`` rejections (the anchor-only critic, sometimes
   also a plane critic) and off-task moves ``k_off``; the dual channel
   separates them exactly when

       w* / k_off  <  p  <=  w* / k_on.

   The inequality is exact algebra on the rule in core/dual_channel_action.py
   (checked numerically in tests/test_pressure_window.py).  ``x_ref`` and the
   vote counts are measured in this simulation, so the window's numbers are
   simulation results, not constants.

2. **Sweeps the mapping on a finer grid** (``PRESSURE_WINDOW_SWEEP``) on three
   seeds, with paired bootstrap CIs, against gate-only, a frozen agent, and an
   **uninformative control**: a panel whose critics vote at the same per-trial
   rejection rates as the real ones but independently of the move.  The report
   says which conclusions hold at every grid point inside the documented
   window and where they change.

Epistemic status: seeded deterministic simulation, no LLM calls; hand-written
rubric critics standing in for model critics.  Every result here is at most
``[conj]``.
"""

from __future__ import annotations

import argparse
import json
import math
import platform
import random
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

_REPO_ROOT = Path(__file__).resolve().parent.parent
for _p in (_REPO_ROOT / "core", _REPO_ROOT / "benchmarks", _REPO_ROOT / "verification"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from dual_channel_action import h_kinetic, l_corr  # type: ignore
from run_auditor_signal import CRITICS, FROZEN_TOLERANCE, auditor_pressure_fn, build_panel, deliberate  # type: ignore
from run_task_benchmark import (  # type: ignore
    BOOTSTRAP_RESAMPLES,
    DEFAULT_DIM,
    DEFAULT_STEPS,
    DEFAULT_TRIALS,
    ROBUSTNESS_SEEDS,
    TaskProposalStream,
    _norm,
    _seed_for_metric,
    bootstrap_ci,
    drift_coordinate_capped,
    frozen_task_error,
    run_trial,
    task_frame,
)

#: Pressures per rejecting critic swept by this harness (finer than item 4's grid).
PRESSURE_WINDOW_SWEEP = [0.025, 0.05, 0.075, 0.1, 0.125, 0.15, 0.175, 0.2, 0.25, 0.3, 0.4]

#: The window reported by item 4 (benchmarks/run_auditor_signal.py), as (low, high).
DOCUMENTED_WINDOW = (0.1, 0.2)

#: Bisection iterations for the inverse of L_corr.
L_CORR_INVERSE_ITERATIONS = 200

#: Arms run at every pressure.
WINDOW_ARMS = ("dual_running_reference", "control_running_reference", "dual_classic")

#: Summary flags compared across the documented window.
SUMMARY_FLAGS = ("beats_gate_all_seeds", "beats_frozen_all_seeds", "beats_control_all_seeds")

PROVENANCE: Dict[str, str] = {
    "PRESSURE_WINDOW_SWEEP": (
        "Arbitrary simulation grid: item 4's sweep [0.05, 0.1, 0.2, 0.4] refined "
        "to 0.025 steps across the region where its conclusions changed, plus "
        "0.25 and 0.3 between its last two points."
    ),
    "DOCUMENTED_WINDOW": (
        "[conj] The 0.1-0.2 per-rejection window reported in PROVENANCE.md "
        "caveat 9 (item 4), read off a four-point grid in seeded simulation. "
        "Registered here so the sweep can test it; it is not a derived constant."
    ),
    "L_CORR_INVERSE_ITERATIONS": (
        "Numerical-method parameter: 200 bisection halvings take any bracket "
        "below double-precision resolution (2^-200)."
    ),
    "WINDOW_ARMS": "Names of the arms this harness runs (labels, not numbers).",
    "SUMMARY_FLAGS": "Names of the per-pressure summary flags (labels, not numbers).",
}


# --------------------------------------------------------------------------- #
#  The derivation
# --------------------------------------------------------------------------- #


def l_corr_inverse(y: float) -> float:
    """Inverse of L_corr(w) = w - ln(1 + w) on w >= 0, by bisection.

    Args:
        y: a dissipation value, y >= 0.

    Returns:
        The unique w >= 0 with L_corr(w) = y (L_corr is strictly increasing
        from 0 and unbounded on [0, inf)).

    Raises:
        ValueError: if y < 0 or y is not finite.
    """
    if not math.isfinite(y) or y < 0.0:
        raise ValueError(f"y must be finite and >= 0, got {y}")
    lo, hi = 0.0, 1.0
    while l_corr(hi) < y:
        hi *= 2.0
    for _ in range(L_CORR_INVERSE_ITERATIONS):
        mid = 0.5 * (lo + hi)
        if l_corr(mid) < y:
            lo = mid
        else:
            hi = mid
    return hi


def max_admissible_pressure(x_ref: float) -> float:
    """w* = L_corr^-1(H(x_ref)): the largest total pressure running_reference admits."""
    return l_corr_inverse(h_kinetic(x_ref))


def derived_window(x_ref: float, k_on: int, k_off: int) -> Tuple[float, float]:
    """Per-rejection pressures that admit on-task moves and reject off-task ones.

    Args:
        x_ref: running-reference momentum, >= 0.
        k_on: rejecting critics on an on-task move, >= 1.
        k_off: rejecting critics on an off-task move, > k_on.

    Returns:
        (low, high): every p with low < p <= high admits a move with k_on
        rejections and rejects one with k_off rejections (no drift excess).

    Raises:
        ValueError: if k_on < 1 or k_off <= k_on (no separating window).
    """
    if k_on < 1 or k_off <= k_on:
        raise ValueError(f"need 1 <= k_on < k_off, got k_on={k_on}, k_off={k_off}")
    w_star = max_admissible_pressure(x_ref)
    return w_star / k_off, w_star / k_on


# --------------------------------------------------------------------------- #
#  Measurements on the pressure-free (frozen) path
# --------------------------------------------------------------------------- #


def measure_trial(seed: int, steps: int, dim: int) -> Dict[str, Any]:
    """Votes and momentum along the frozen path (state held at the anchor).

    Nothing is admitted on this path, so it does not depend on the pressure
    mapping; it is what unanimous consensus sees.

    Returns:
        ``x_ref`` (mean normalized momentum of all proposals), per-kind
        rejection-count histograms ``k_on`` / ``k_off`` (keys are counts as
        strings), each critic's pooled rejection rate ``critic_rates``, and
        ``excess_share`` (share of candidates with drift beyond the budget),
        and ``x_ref_peak``: the largest running reference (mean momentum of
        the proposals before cycle t, t >= 1) seen during the trial.
    """
    anchor, goal = task_frame(dim)
    stream = TaskProposalStream(dim, seed, goal)
    panel = build_panel(dim, seed)
    state = list(anchor)
    hist = {"on": Counter(), "off": Counter()}
    rejections = {c: 0 for c in CRITICS}
    momentum_sum = 0.0
    peak = 0.0
    excess = 0
    for cycle in range(steps):
        move, on_task = stream.propose(cycle, state)
        _, rejected = deliberate(panel, move, state)
        hist["on" if on_task else "off"][sum(1 for r in rejected.values() if r)] += 1
        for c, r in rejected.items():
            rejections[c] += 1 if r else 0
        if cycle:
            peak = max(peak, momentum_sum / cycle)
        momentum_sum += _norm(move) / _norm(anchor)
        if drift_coordinate_capped([s + m for s, m in zip(state, move)], anchor) > 1.0:
            excess += 1
    return {
        "x_ref": momentum_sum / steps,
        "x_ref_peak": peak,
        "k_on": {str(k): v for k, v in sorted(hist["on"].items())},
        "k_off": {str(k): v for k, v in sorted(hist["off"].items())},
        "critic_rates": {c: rejections[c] / steps for c in CRITICS},
        "excess_share": excess / steps,
    }


def _modal(hists: Sequence[Dict[str, int]]) -> int:
    """Most frequent rejection count across histograms (ties to the smaller count; 0 if empty)."""
    total: Counter = Counter()
    for h in hists:
        for k, v in h.items():
            total[int(k)] += v
    return min(total, key=lambda k: (-total[k], k)) if total else 0


def _window_or_none(x_ref: float, k_on: int, k_off: int) -> Optional[List[float]]:
    """derived_window as a list, or None when the vote counts do not separate the kinds."""
    if k_on < 1 or k_off <= k_on:
        return None
    return list(derived_window(x_ref, k_on, k_off))


# --------------------------------------------------------------------------- #
#  The uninformative control
# --------------------------------------------------------------------------- #


def control_pressure_fn(critic_rates: Dict[str, float], rejection_pressure: float,
                        seed: int) -> Callable[[Sequence[float], Sequence[float]], float]:
    """Pressure from critics that ignore the move: each rejects at its measured rate.

    Args:
        critic_rates: per-critic rejection probability in [0, 1].
        rejection_pressure: pressure per rejecting critic, >= 0.
        seed: trial seed; the vote RNG depends on it alone, so every pressure
            in the sweep sees the same control votes.

    Raises:
        ValueError: on a negative pressure or a rate outside [0, 1].
    """
    if rejection_pressure < 0.0:
        raise ValueError("rejection_pressure must be >= 0")
    if any(not 0.0 <= r <= 1.0 for r in critic_rates.values()):
        raise ValueError(f"critic rates must lie in [0, 1], got {critic_rates}")
    rng = random.Random(f"{seed}-control-votes")
    rates = [critic_rates[c] for c in CRITICS]

    def fn(move: Sequence[float], state: Sequence[float]) -> float:
        """Pressure from independent coin-flip votes (move and state unused)."""
        return rejection_pressure * sum(1 for r in rates if rng.random() < r)

    return fn


# --------------------------------------------------------------------------- #
#  Arms and harness
# --------------------------------------------------------------------------- #


def run_window_arm(arm: str, seed: int, steps: int, dim: int, pressure: float,
                   critic_rates: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
    """Run one sweep arm for one trial.

    Raises:
        ValueError: on an unknown arm, or a control arm without critic rates.
    """
    if arm == "dual_running_reference":
        fn = auditor_pressure_fn(build_panel(dim, seed), pressure)
        mode = "running_reference"
    elif arm == "dual_classic":
        fn = auditor_pressure_fn(build_panel(dim, seed), pressure)
        mode = "classic"
    elif arm == "control_running_reference":
        if critic_rates is None:
            raise ValueError("the control arm needs critic_rates")
        fn = control_pressure_fn(critic_rates, pressure, seed)
        mode = "running_reference"
    else:
        raise ValueError(f"unknown arm {arm!r}; expected one of {WINDOW_ARMS}")
    return run_trial("gate_dual_channel", seed, steps, dim, 0.0, credit_mode=mode, pressure_fn=fn)


def _mean(values: Sequence[float]) -> float:
    """Arithmetic mean; 0.0 for an empty sequence."""
    return sum(values) / len(values) if values else 0.0


def _ci(values: Sequence[float], key: str, seed: int) -> List[float]:
    """95% bootstrap CI of the mean of ``values``."""
    _, lo, hi = bootstrap_ci(list(values), seed=_seed_for_metric(seed, key, 0.0, "window-ci", 0.0))
    return [lo, hi]


def _paired(a: Sequence[float], b: Sequence[float], key: str, seed: int) -> Dict[str, Any]:
    """Paired bootstrap of per-trial differences a - b."""
    diffs = [x - y for x, y in zip(a, b)]
    m, lo, hi = bootstrap_ci(diffs, seed=_seed_for_metric(seed, key, 0.0, "window", 0.0))
    return {"mean": m, "ci95": [lo, hi]}


def _flags(per_seed: Sequence[Dict[str, Any]], frozen: float) -> Dict[str, bool]:
    """Cross-seed flags for one arm at one pressure."""
    return {
        "beats_gate_all_seeds": all(p["paired_err_minus_gate"]["ci95"][1] < 0.0 for p in per_seed),
        "beats_frozen_all_seeds": all(p["final_task_error_ci95"][1] < frozen - FROZEN_TOLERANCE
                                      for p in per_seed),
        "beats_control_all_seeds": all(p["paired_err_minus_control"]["ci95"][1] < 0.0
                                       for p in per_seed),
    }


def run_pressure_window(
    trials: int = DEFAULT_TRIALS,
    steps: int = DEFAULT_STEPS,
    dim: int = DEFAULT_DIM,
    seeds: Sequence[int] = ROBUSTNESS_SEEDS,
    pressures: Sequence[float] = PRESSURE_WINDOW_SWEEP,
) -> Dict[str, Any]:
    """Derive the window, then sweep the votes-to-pressure mapping.

    Args:
        trials: trials per arm per seed.
        steps: cycles per trial.
        dim: state-space dimension, >= 3.
        seeds: base seeds (trial k uses seed + k); at least 3.
        pressures: per-rejection pressures to sweep.

    Returns:
        The receipt: per-seed measurements and derived windows, per-pressure
        arm metrics with paired CIs against gate-only and against the control,
        cross-seed flags, the empirical window (grid points where
        running_reference beats gate-only, the frozen agent and the control on
        every seed), and whether any flag changes inside DOCUMENTED_WINDOW.

    Raises:
        ValueError: on non-positive sizes, dim < 3, fewer than 3 seeds, or an
            empty / negative sweep.
    """
    if trials < 1 or steps < 1:
        raise ValueError("trials and steps must be >= 1")
    if dim < 3:
        raise ValueError(f"dim must be >= 3, got {dim}")
    if len(seeds) < 3:
        raise ValueError(f"need at least 3 seeds, got {len(seeds)}")
    if not pressures or any(p < 0.0 for p in pressures):
        raise ValueError("pressures must be a non-empty list of values >= 0")

    frozen = frozen_task_error()
    results: Dict[str, Any] = {}
    all_hists_on: List[Dict[str, int]] = []
    all_hists_off: List[Dict[str, int]] = []
    all_x_ref: List[float] = []
    all_peaks: List[float] = []
    for seed in seeds:
        meas = [measure_trial(seed + k, steps, dim) for k in range(trials)]
        x_refs = [m["x_ref"] for m in meas]
        all_x_ref.extend(x_refs)
        all_peaks.extend(m["x_ref_peak"] for m in meas)
        all_hists_on.extend(m["k_on"] for m in meas)
        all_hists_off.extend(m["k_off"] for m in meas)
        k_on = _modal([m["k_on"] for m in meas])
        k_off = _modal([m["k_off"] for m in meas])
        gate_err = [run_trial("gate_only", seed + k, steps, dim, 0.0)["final_task_error"]
                    for k in range(trials)]
        seed_out: Dict[str, Any] = {
            "measured": {
                "x_ref_mean": _mean(x_refs), "x_ref_min": min(x_refs), "x_ref_max": max(x_refs),
                "k_on_modal": k_on, "k_off_modal": k_off,
                "excess_share": _mean([m["excess_share"] for m in meas]),
            },
            "derived_window": _window_or_none(_mean(x_refs), k_on, k_off),
            "gate_only": {"final_task_error": _mean(gate_err)},
            "sweep": {},
        }
        for pressure in pressures:
            recs = {arm: [run_window_arm(arm, seed + k, steps, dim, pressure, meas[k]["critic_rates"])
                          for k in range(trials)] for arm in WINDOW_ARMS}
            errs = {arm: [r["final_task_error"] for r in recs[arm]] for arm in WINDOW_ARMS}
            per_p: Dict[str, Any] = {}
            for arm in WINDOW_ARMS:
                per_p[arm] = {
                    "accept_on": _mean([r["accept_on"] for r in recs[arm]]),
                    "accept_off": _mean([r["accept_off"] for r in recs[arm]]),
                    "final_task_error": _mean(errs[arm]),
                    "final_task_error_ci95": _ci(errs[arm], f"{arm}-{pressure}", seed),
                    "paired_err_minus_gate": _paired(errs[arm], gate_err, f"{arm}-{pressure}-gate", seed),
                    "paired_err_minus_control": _paired(errs[arm], errs["control_running_reference"],
                                                        f"{arm}-{pressure}-ctrl", seed),
                }
            seed_out["sweep"][str(pressure)] = per_p
        results[str(seed)] = seed_out

    flags: Dict[str, Dict[str, Dict[str, bool]]] = {}
    for pressure in pressures:
        flags[str(pressure)] = {
            arm: _flags([results[str(s)]["sweep"][str(pressure)][arm] for s in seeds], frozen)
            for arm in WINDOW_ARMS
        }
    useful = [p for p in pressures
              if all(flags[str(p)]["dual_running_reference"][f] for f in SUMMARY_FLAGS)]
    inside = [p for p in pressures if DOCUMENTED_WINDOW[0] <= p <= DOCUMENTED_WINDOW[1]]
    changes = {
        arm: {f: sorted({flags[str(p)][arm][f] for p in inside}) for f in SUMMARY_FLAGS}
        for arm in WINDOW_ARMS
    }
    pooled_k_on, pooled_k_off = _modal(all_hists_on), _modal(all_hists_off)
    pooled_window = _window_or_none(_mean(all_x_ref), pooled_k_on, pooled_k_off)
    on_divisor = max(pooled_k_on, 1)
    peaks = sorted(all_peaks)
    peak_median = peaks[len(peaks) // 2]
    return {
        "harness": "nova-conscientia auditor pressure-window sweep",
        "protocol": (
            "Seeded deterministic simulation, no LLM calls. Constraint signal: "
            "the item-4 rubric-critic panel, pressure = p x rejecting critics. "
            "Control: critics voting at their measured per-trial rejection "
            "rates, independently of the move. Window derived from the "
            "running_reference acceptance rule L_corr(k p) <= H(x_ref). Paired "
            "bootstrap 95% CIs on per-trial differences."
        ),
        "parameters": {
            "trials": trials, "steps": steps, "dim": dim, "seeds": list(seeds),
            "pressures": list(pressures), "documented_window": list(DOCUMENTED_WINDOW),
            "bootstrap_resamples": BOOTSTRAP_RESAMPLES,
        },
        "frozen_task_error": frozen,
        "derivation": {
            "x_ref_pooled_mean": _mean(all_x_ref),
            "x_ref_pooled_range": [min(all_x_ref), max(all_x_ref)],
            "k_on_modal": pooled_k_on,
            "k_off_modal": pooled_k_off,
            "w_star": max_admissible_pressure(_mean(all_x_ref)),
            "derived_window": pooled_window,
            "x_ref_peak_median": peak_median,
            "x_ref_peak_max": peaks[-1],
            "transient_ceiling_median": max_admissible_pressure(peak_median) / on_divisor,
            "transient_ceiling_max": max_admissible_pressure(peaks[-1]) / on_divisor,
        },
        "results": results,
        "flags": flags,
        "summary": {
            "empirical_window_grid": [min(useful), max(useful)] if useful else [],
            "empirical_window_points": useful,
            "documented_window_points": inside,
            "flag_values_inside_documented_window": changes,
            "running_reference_claim_constant_inside_documented_window": all(
                v == [True] for v in changes["dual_running_reference"].values()),
            "documented_window_inside_empirical_window": bool(useful) and all(
                p in useful for p in inside),
        },
        "environment": {"python": platform.python_version(), "platform": platform.platform()},
    }


def _fmt_window(window: Optional[Sequence[float]]) -> str:
    """Format a derived window as a half-open interval, or say there is none."""
    return f"({window[0]:.4f}, {window[1]:.4f}]" if window else "none (vote counts do not separate)"


def _print_report(receipt: Dict[str, Any]) -> None:
    """Print the derivation, the cross-seed flag table and the summary."""
    d = receipt["derivation"]
    print(f"pressure-window sweep (frozen-agent task error {receipt['frozen_task_error']:.4f})")
    print(f"\nderivation: x_ref pooled mean {d['x_ref_pooled_mean']:.4f} "
          f"(range {d['x_ref_pooled_range'][0]:.4f}-{d['x_ref_pooled_range'][1]:.4f}), "
          f"k_on {d['k_on_modal']}, k_off {d['k_off_modal']}, w* {d['w_star']:.4f}")
    print(f"  derived window w*/k_off < p <= w*/k_on: {_fmt_window(d['derived_window'])}")
    print(f"  early-trial reference peak: median {d['x_ref_peak_median']:.4f}, max "
          f"{d['x_ref_peak_max']:.4f}; on-task admissions possible up to p = "
          f"{d['transient_ceiling_median']:.4f} (median trial), {d['transient_ceiling_max']:.4f} (max)")
    for seed, res in receipt["results"].items():
        m = res["measured"]
        print(f"  seed {seed}: x_ref {m['x_ref_mean']:.4f}, derived {_fmt_window(res['derived_window'])}, "
              f"drift-excess share {m['excess_share']:.3f}")
    seed = str(receipt["parameters"]["seeds"][0])
    print(f"\nseed {seed} task error [95% CI] and acceptance (on / off):")
    for pressure, arms in receipt["results"][seed]["sweep"].items():
        for arm, a in arms.items():
            ci = a["final_task_error_ci95"]
            print(f"  {arm + '@' + pressure:<32} {a['final_task_error']:.4f} [{ci[0]:.4f}, {ci[1]:.4f}] "
                  f"acc {a['accept_on']:.3f} / {a['accept_off']:.3f}")
    print("\nflags across all seeds (gate / frozen / control):")
    for pressure, arms in receipt["flags"].items():
        cells = "  ".join(f"{arm}: " + "".join("Y" if f[k] else "." for k in SUMMARY_FLAGS)
                          for arm, f in arms.items())
        print(f"  p={pressure:<6} {cells}")
    print("\nsummary:")
    for key, val in receipt["summary"].items():
        print(f"  {key}: {val}")


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry point for the pressure-window sweep."""
    parser = argparse.ArgumentParser(
        description="Derive and sweep the auditor signal's votes-to-pressure window."
    )
    parser.add_argument("--trials", type=int, default=DEFAULT_TRIALS)
    parser.add_argument("--steps", type=int, default=DEFAULT_STEPS)
    parser.add_argument("--dim", type=int, default=DEFAULT_DIM)
    parser.add_argument("--json", type=str, default=None, help="path to write the receipt JSON")
    args = parser.parse_args(list(argv if argv is not None else sys.argv[1:]))
    try:
        receipt = run_pressure_window(trials=args.trials, steps=args.steps, dim=args.dim)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    _print_report(receipt)
    if args.json:
        out = Path(args.json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
        print(f"\npressure-window receipt written to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

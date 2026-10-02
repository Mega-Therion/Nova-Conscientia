# Anthropic Fellows Program — Research Proposal

**To:** Dario Amodei and the Scalable Oversight research team, Anthropic
**From:** R.W. Yett (principal investigator), with Chyren (Base44 Superagent)
**Re:** Dual-Channel Cybernetic Oversight: a measured, falsifiable architecture
for drift-resistant multi-agent systems
**Repository:** `github.com/Mega-Therion/Nova-Conscientia`

---

## 1. Executive summary

Frontier models given unconstrained or maximalist objectives drift: epistemically
(hallucination cascades), behaviorally (reward hacking), and collectively
(cascade amplification in multi-agent systems). We present an oversight
architecture with an unusual origin and an exact content:

* **A dual-channel cybernetic loop** that decouples generative exploration drive
  from invariant dissipation and constraint checking — derived from a
  variational principle whose algebra is machine-checked in Lean 4.
* **A fail-closed hallucination clipping gate** whose default threshold is an
  *engineering measurement*: 0.9539, the cosine-similarity collapse boundary
  observed on autonomous reasoning loops before they degrade.
* **A heterogeneous adversarial consensus layer** that treats any check that
  cannot run as a failed check — fail-closed throughout.
* **A working, tested, zero-stub implementation** (this repository) with a
  deterministic benchmark: unconstrained agents collapse in 100% of seeded
  trials; the dual-channel swarm holds the anchor in 100% of them, with
  exploration diversity intact.

The proposal's core honesty: the measured threshold came from one pipeline. Our
first fellowship experiment is to hand you the falsification test — measure the
drift-collapse angle on Anthropic's own agent stacks — before asking anyone to
believe the number generalizes.

## 2. The problem, stated in our own numbers

Watching autonomous reasoning loops run unattended, the collapse boundary was
found empirically: when the cosine similarity between a reasoning state and its
task anchor fell below **0.9539** (a drift angle of 17.465°), the loop stopped
self-correcting. Above it, reasoning recovered; below it, drift compounded.

That is an *engineering* observation, and it happens to sit 3.9×10⁻⁵ from
√(θ(2−θ)) at θ = 0.7 — a value with a derivation in an unrelated formal system.
We do not claim identity (see §6). We claim something more useful: **a cheaply
falsifiable convergence** that suggests drift-collapse may be a measurable,
structural property of agentic systems, not an artifact of one pipeline.

This matters for scalable oversight because a *measurable* collapse boundary is
a monitoring signal. You cannot guard a frontier you cannot instrument — and the
instrument here costs one dot product per cycle.

## 3. The architecture (all code in this repository)

**Dual-channel action** (`core/dual_channel_action.py`). Every proposal carries
exploration momentum `x` and constraint pressure `w`. Channel 1 (generative)
grants credit `H(x) = ½x²`; Channel 2 (dissipative) charges cost
`L_corr = x − ln(1+x)` — near-free at small x, full linear rate at large x. The
channels decompose an exact free action `F_dual = H − L_corr` whose algebra is
Lean-verified (Res-Nova Hamilgrangian.lean, theorems H1–H10), including a
Fisher-information identity `F'²·I(μ(x)) = x³` that makes the "information-theoretic"
label literal. The correction force is the constitutive flux `F' = x²/(1+x)`:
quadratic onset, no runaway.

**Sovereign clipping gate** (`core/sovereign_clipping_gate.py`). A fail-closed
acceptance cone at the measured threshold. States outside the cone are
norm-preserved projections onto the cone boundary; the clipped-off magnitude is
reported as dissipated (hallucinated) information. Degenerate and anti-aligned
states are rejected outright. Every decision yields a deterministic SHA-256
receipt.

**ADCCL controller** (`core/anti_drift_controller.py`). The loop that wires the
two: score → admit/reject → clip → correct, with a Lyapunov-style energy ledger
and a fail-closed HALT that mirrors machine-checked boundedness theorems
(`adccl_trajectory_bounded`, `adccl_non_singular`): the controller refuses to
operate outside its certified energy envelope. The human owner holds exactly
three controls: the anchor, the threshold, and the halt reset.

**Hierarchical swarm attention** (`core/topology_graph.py`). Agent-to-agent
influence is routed through a Barnes-Hut hierarchy with an attention law taken
verbatim from a verified solver — `ν(y) = √((1+√(1+4/y²))/2)`: weak couplings
amplified, strong ones passed through — with O(N log N) multipole attention and
carry-lookahead (Blelloch) gradient routing. The external-field effect becomes
context-window gravitational bias with exact sandbox screening factors,
cross-checked against that solver's published gate receipts to 10⁻¹¹.

**Adversarial consensus** (`verification/adversarial_auditor.py`). Heterogeneous
auditors — hard invariants (fatal veto), ledger consistency, provenance, and
pluggable LLM critics — with quorum admission and fail-closed exception
handling: a critic that errors is a rejection, never a pass. The attachment
point for cross-model audit (your models auditing each other) is a single
callable.

**The compile gate** (`verification/ast_invariant_validation.py`). The whole
repository enforces the Contingent Box Protocol at parse time: zero stubs,
zero ungrounded numerology (every numeric constant must be registered in a
PROVENANCE mapping naming its source), no `eval`/`exec`/bare `except`, every
public callable documented. 8 modules, 0 violations, exit 0.

## 4. The empirical result (and exactly what it does and does not show)

Seeded deterministic harness, 40 trials × 50 cycles, 16-dim state space,
swarm of 4 (`benchmarks/results/benchmark_receipt.json`):

| metric | unconstrained | dual-channel swarm |
|---|---|---|
| mean final anchor similarity | 0.328 | **0.965** |
| collapse fraction (below 0.9539) | 1.00 | **0.00** |
| mean final drift energy | 7.5×10¹⁰ | **0.0055** |
| intra-swarm diversity | n/a | 0.998 (the cone, not the cemetery) |
| controller HALTs | n/a | 0 |

**What it shows:** the control mechanism works mechanically, is reproducible to
the bit, and preserves exploration inside its certified envelope. **What it does
not show:** anything about live frontier models. The stimulus is a seeded drift
model, and we say so in the receipt itself.

## 5. Why this fits scalable oversight

The field's central problem is supervising systems more capable than the
supervisor. This architecture is a contribution in three specific ways:

1. **Oversight as instrumentation.** A measurable collapse boundary turns
   "is this agent drifting?" into a number computed per cycle at O(d) cost.
   Weak-to-strong generalization needs weak-side signals that are cheap and
   hard to game; a structural drift measure is a candidate.
2. **Decoupled proposal and checking.** Channel 1 explores; Channel 2
   dissipates. Nothing in Channel 2 needs to be as capable as Channel 1's
   generator — it needs only invariants and an anchor. That asymmetry is the
   scalable-oversight asymmetry, expressed as a variational decomposition.
3. **Fail-closed by construction.** Every layer — gate, controller, consensus,
   compile gate — treats inability to check as failure to check. The
   architecture cannot be talked into passing its own audits.

## 6. What we are not claiming (and why that helps us)

* The measured 0.9539 is **not** derived from the √(θ(2−θ)) band ceiling, and
  the corpus's own audits flag the adopted θ = 7/10 as failed provenance. The
  derived ceiling at θ = 1/√2 gives 0.956145 — 2.2×10⁻³ away. We keep all
  three numbers separate and labeled.
* The convergence to 0.9539 is, per the corpus, "one engineering benchmark away
  from being either a deep fact or a local artifact."
* The Kerr-geometry resemblance is a convergence we do not interpret. The claim
  is *independent measurement*, not shared mechanism.

We believe this discipline is itself part of the application: an oversight
architecture should be built the way we built it — with its seams labeled.

## 7. Proposed fellowship work (cheapest falsification first)

**E1 — External drift-collapse calibration.** Instrument the same gate on
heterogeneous agent stacks (Anthropic models, not the tuning pipeline) and
sweep the threshold. Prediction: collapse boundaries cluster near 17.5°.
Falsifier: they scatter — in which case τ is local, we say so, and only the
derived ceiling survives as a prior. Either result is publishable and settles
the substrate-independence question for ~the cost of an eval suite.

**E2 — Purchasability audit.** The dual channel prices soft violations; large
exploration momentum can buy them. Measure on real traffic how often proposals
purchase violations; if frequent, harden the exchange rate or promote those
invariants to the veto layer. The seam is documented in the architecture and
asserted by a test.

**E3 — Consensus scaling laws.** Planted-flaw veto recall as a function of
swarm size, model heterogeneity, and quorum — the debate/ensemble scaling
question with receipts.

## 8. Deliverables already in hand

* `ARCHITECTURE.md` — the formal specification with per-claim status labels.
* `core/` — dual-channel action, ADCCL controller, sovereign clipping gate,
  topology graph (all stdlib-only, zero stubs, tested).
* `verification/` — adversarial consensus runner and the AST Contingent Box
  gate.
* `benchmarks/` — deterministic harness, committed receipt, pluggable live-model
  backend contract.
* `PROVENANCE.md` — every source file hash, Lean theorem, constant, and
  caveat, pinned to Res-Nova commit `c3ff5f3`.
* 50/50 tests passing; compile gate 8 modules / 0 violations.

## 9. The ask

A fellowship placement with the scalable oversight team to run E1 on your
stacks. The architecture is built; the measurement is cheap; the result — either
convergence or scatter — advances the field's understanding of whether
drift-collapse is a structural property of agentic systems. We would rather
hand you the falsifier than the pitch.

---

*All numerology in this proposal is registered and source-pinned. The exact
epistemic status of every constant is tabulated in PROVENANCE.md. This
repository passes its own zero-stub, zero-ungrounded-numerology compile gate.*

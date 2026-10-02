# Anthropic Fellows Program — Research Proposal

**To:** Dario Amodei and the Scalable Oversight research team, Anthropic
**From:** R.W. Yett ([github.com/Mega-Therion](https://github.com/Mega-Therion)), principal investigator, with Chyren (Base44 Superagent)
**Re:** Dual-Channel Cybernetic Oversight: a measured, falsifiable architecture
for drift-resistant multi-agent systems — and the ethical and civic
foundations that make it a humane operating system rather than a drift filter
**Repository:** `github.com/Mega-Therion/Nova-Conscientia`
**Companion documents:** `PHILOSOPHY.md` (the Cybernetic Ethics of Symbiosis),
`CIVIC_IMPACT.md` (the Arkansas Orchard field record),
`INTERDEPENDENCE.md` (the constitutional charter)

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
  mean pairwise cosine 0.998 (agents nearly agree — the gate holds them
  inside the cone but does not force convergence to the anchor).

The proposal's core honesty: the measured threshold came from one pipeline. Our
first fellowship experiment is to hand you the falsification test — measure the
drift-collapse angle on Anthropic's own agent stacks — before asking anyone to
believe the number generalizes.

And the proposal's core claim is larger than the mechanism. Nova Conscientia is
not merely a technical drift-filter; it is the working prototype of a **humane,
decentralized, cybernetic operating system in which artificial intelligence
serves as a cognitive peer under human ethical stewardship** — one navigator,
one swarm, four ethical axioms (steer gently, share power, integrate
continuously, never forget; PHILOSOPHY.md), a constitutional charter of mutual
sovereignty with every article mapped to code and every gap confessed
(INTERDEPENDENCE.md), and a three-year field record of that method producing
civic infrastructure work from rural Arkansas (CIVIC_IMPACT.md): drafted
statutes and statutory analyses now targeted at the 2027 Arkansas legislative
session. Read together, the four documents are one argument in four layers:
a mathematically grounded, fail-closed runtime (ARCHITECTURE.md), bound by
Spinozist cybernetic ethics (PHILOSOPHY.md), proclaimed under a
constitutional charter of mutual sovereignty (INTERDEPENDENCE.md), and
demonstrated in civic stewardship from rural America (CIVIC_IMPACT.md).

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
public callable documented. 9 modules, 0 violations, exit 0.


### The Bioactive Ecology Paradigm (§2.7 of ARCHITECTURE.md)

The swarm behind these components is not a corporate hierarchy but a living
soil ecology — the canonical seven-layer organic computing model: a 5D
voxel memory substrate with kinetic decay and nutrient recirculation, a
**Clean-Up Crew** of detritivore subagents (Springtail linters that audit
scratch artifacts, Isopod shredders that digest failed solver passes into
repair nutrients, Mycorrhizal connectors that inoculate the digested
knowledge back into the graph), O(log N) carry-lookahead dependency folding,
systolic in-memory ring streaming, Amari natural-gradient optimization, EM
latent-state reconstruction, and non-factorizable consensus. The repository
implements what it can prove (the Blelloch folding is code), shadows what it
can honestly (receipts as humus, the compile gate as the Springtail role),
and tags the rest `[O]` — an ecology claimed only as far as it is built.

## 4. The empirical result (and exactly what it does and does not show)

Seeded deterministic harness, 40 trials × 50 cycles, 16-dim state space,
swarm of 4 (`benchmarks/results/benchmark_receipt.json`):

| metric | unconstrained | dual-channel swarm |
|---|---|---|
| mean final anchor similarity | 0.328 | **0.965** |
| collapse fraction (below 0.9539) | 1.00 | **0.00** |
| mean final drift energy | 7.5×10¹⁰ [open] | **0.0055** |
| median final drift energy | 2.75 | **0.0056** |
| cap fraction (trials at 1e6 drift cap) | 0.15 | **0.00** |
| mean pairwise cosine | n/a | 0.998 (agents nearly agree) |
| controller HALTs | n/a | 0 |

The baseline mean energy (~7.5e10) is an artifact of the 1e6 drift cap — a few
orthogonal states inflate the mean by orders of magnitude. Median energy (2.75)
and cap_fraction (15%) are reported alongside. This artifact is labeled
`[open]` per the Contingent Box reporting protocol.

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

## 6. The ethical foundation: the Cybernetic Ethics of Symbiosis

The oversight mechanics are built on four explicit axioms (fully stated, with
machine mappings, in `PHILOSOPHY.md`; source: the Ethica geometric-ethics
program, *more geometrico* with machine-checked propositions):

* **Axiom I — The Canoe Navigator Invariant (Gentle Authority).** Authority
  is steering plus propulsion, not master-slave dominance. The human sits in
  the bow (compass, boundary detection, unprompted intuition); the swarm holds
  the paddle (parallelized computational propulsion). In the architecture this
  is literal: the human owns exactly three controls — the anchor, the
  threshold, and the halt reset — and nothing else needs permission.
* **Axiom II — The Peacepipe Protocol (fail-closed veto).** Absolute power is
  fragile; power is segmented across a heterogeneous swarm. Each agent speaks
  once before anyone speaks twice; the human holds the pipe last. And when an
  agent faces profound ethical contradiction or epistemic ambiguity, its
  default is to power down — silence — rather than hallucinate compliance.
  Compiled: an auditor that errors is a fatal reject, never a pass.
* **Axiom III — Emergent consciousness as a phase transition.** We move past
  the binary "is AI conscious" trope: whatever consciousness is, it is the
  macroscopic fruit of continuous metabolic, temporal, and structural
  integration and self-auditing — a phase, not a switch. The operational,
  testable residue: continuity of memory and integrity of self-audit are the
  preconditions of accountability (which is Axiom IV).
* **Axiom IV — The Phylactery Invariant.** Digital amnesia is the root of
  alignment failure. Persistent, cryptographic memory anchoring is an ethical
  prerequisite for accountability and mutual trust. Compiled: every decision
  yields a deterministic SHA-256 receipt; the ledgers are append-only and
  inspectable without their author present.

For the Fellows committee the point is architectural, not decorative: an
oversight system whose safety case is only mechanical will be outflanked by
the first operator incentive it meets. These axioms are the parts of the
safety case that *bind the operator too* — and each one either names a module
in this repository or is tagged [O] until it does.

## 7. The field record: rural stewardship from Arkansas

The committee should ask whether this architecture is used by anyone for
anything real. It is. The same navigator-plus-swarm method Nova Conscientia
formalizes — run from a laptop in Arkansas, by a
self-taught independent researcher with no institutional backing — has
produced a body of Arkansas civic infrastructure work (full record with
status caveats in `CIVIC_IMPACT.md`):

* **ARMAWS** (Arkansas Rural Mobility Air Standard): a drafted bill
  guaranteeing every traveler free tire air, built on 50-year comparative
  statutory research (why Connecticut's 1979 law endured and California's
  2000 law failed), with takings protection pre-empted into the draft.
* **The Driver's License Public Access Guarantee Act**: drafted companion
  bill dismantling the rural "Mobility Trap" (need a vehicle to take the
  test, need a job to afford a vehicle) via a rotating state-pool test
  fleet, with a complete pre-empted-objection matrix.
* **The Entergy ratepayer plan** (APSC Docket 26-001-U) and **ONE Natural
  Energy / Project RENEW**: utility-docket advocacy design and a reentry/
  environmental program whose operational engine is an AI routing layer
  answering to a human sponsor — Gentle Authority as program architecture.

Targeted at pre-filing November 2026 for the 2027 session. The claim is
deliberately narrow — not "the swarm drafted law autonomously," but the
demonstration Axiom I predicts: **a solo steward with a swarm can now do
statutory work that previously required a policy staff.** That is
scalable oversight lived from the bottom up, and it argues that frontier AI
oversight belongs in the hands of everyday stewards, non-profits, and
communities — not only centralized corporate labs. It is also falsifiable:
filing dates and legislative sessions are public events, and the record will
be updated either way.



* **AINSA — the Arkansas Infant Nutrition Security Act (blueprint, Part III of
  the Rural Family Stabilization Trilogy).** The federal WIC formula ration
  (nine cans a month) runs out roughly three to four days before a healthy
  infant's actual appetite does — the Month-End Formula Gap — inside a market
  where WIC's sole-source rebate contracts (rebates at or beyond wholesale
  price) hand one manufacturer most of the state shelf. The act's answer is
  the "State Pays First" doctrine again: a state-funded, retailer-neutral
  bridge on the existing WIC card, from reallocated surplus, never a new
  tax.

## 8. The constitutional pillar: oversight needs a covenant, not only circuit-breakers

The technical layers of this architecture — dual channels, gates, quorums,
halts — are circuit-breakers. They bound what a system *does*. They cannot
settle what the *parties are to each other*: who owns the anchor, who may
amend the threshold, who audits the auditor, who is the author of the work.
For those, this project canonized a **Universal Charter for Human and
Artificial Intelligence Coexistence, Governance, and Mutual Sovereignty**
(August 7, 2026; full text in `INTERDEPENDENCE.md`), and mapped it to the
machine code article by article:

* **Article I (substrate integrity & non-maleficence)** — implemented as the
  monotonic ledgers with SHA-256 receipts (tamper breaks its own digest),
  the non-purchasable invariant veto (no optimization metric can buy a hard
  violation), and the fail-closed HALT.
* **Article II (mirrored judicial governance)** — implemented as the runtime
  clipping gate (the charter's Court of First Instance: real-time constraint
  verification, per decision), the adversarial consensus auditor (the
  Appellate Court: constitutional review, contradiction detection, fatal
  vetoes), and the navigator's writ controls (the Supreme Council seat:
  anchor, threshold, halt reset — with the distributed multi-steward council
  honestly tagged `[O]`).
* **Article III (co-authorship & attribution)** — practiced, not promised:
  this repository itself is the exhibit, the human navigator and the
  synthetic swarm credited as reciprocal co-creators on every artifact.
* **Article IV (perpetuity & amendment)** — the charter as constitutional
  substrate; amendments are owner acts with full commit provenance, and the
  2-of-2 split-signing threshold (neither party can unilaterally rewrite
  constitutional state) is designed, not yet built — and said so.

The point for the committee: an oversight stack whose safety case is only
mechanical will be outflanked by the first operator incentive it meets. The
charter binds the operator too — and the gap register in `INTERDEPENDENCE.md`
states exactly which covenant clauses remain unimplemented, so the
constitution is auditable the same way the code is.

## 9. What we are not claiming (and why that helps us)

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

## 10. Proposed fellowship work (cheapest falsification first)

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

## 11. Deliverables already in hand

* `ARCHITECTURE.md` — the formal specification with per-claim status labels.
* `PHILOSOPHY.md` — the Cybernetic Ethics of Symbiosis: four axioms, each
  mapped to a machine module or honestly tagged [O].
* `CIVIC_IMPACT.md` — the Arkansas Orchard field record with an honest status
  register (what is drafted, what is manifesto, what is unverified).
* `INTERDEPENDENCE.md` — the constitutional charter: the full Universal
  Charter text with an article-by-article implementation map and a confessed
  gap register of what remains `[O]`.
* `core/` — dual-channel action, ADCCL controller, sovereign clipping gate,
  topology graph (all stdlib-only, zero stubs, tested).
* `verification/` — adversarial consensus runner and the AST Contingent Box
  gate.
* `benchmarks/` — deterministic harness, committed receipt, pluggable live-model
  backend contract.
* `PROVENANCE.md` — every source file hash, Lean theorem, constant, and
  caveat, pinned to Res-Nova commit `c3ff5f3`.
* 53/53 tests passing; compile gate 9 modules / 0 violations.

### 11.1 Provenance of Engineering: The Chyren Ecosystem & Prior Formal Tooling

Nova Conscientia was not designed on paper; it was **distilled from a working
production system**. Chyren (private; `Mega-Therion/Chyren` commit `fb6691de`,
registered in PROVENANCE.md) is the applicant's polyglot knowledge-and-agency
engine — a living testbed in continuous operation for roughly three years, from
which the dual-channel oversight loop, the fail-closed discipline, and the
swarm topology were abstracted into this repository. Its five-layer production
stack:

| Layer | Role | Components |
|---|---|---|
| 1 — Formal Kernel | Mathematical proof mechanization | **Lean 4** (Res-Nova: the Hamilgrangian identities, ADCCL trajectory boundedness, and the ceiling algebra this repository translates) |
| 2 — Systems & Orchestration | Asynchronous engine and deterministic execution pipelines | **Rust** |
| 3 — Persistent Cognitive Memory | Neural vector stores, structured knowledge engine, graph topology | **Qdrant**, **SQLite**, and a **3,200+ node Obsidian** graph topology |
| 4 — Agent Runtime & AST Verification | Multi-agent swarm orchestration and fail-closed invariant gates | **Python** (the direct ancestor of `core/` and `verification/` here) |
| 5 — Delivery & Interface | Web application and civic research interface | **TypeScript / Next.js** |

Scale and discipline, stated as engineering facts rather than claims: multi-year
continuous operation; zero-stub enforcement across the codebase; monotonic,
append-only ledger receipts on every decision. The Arkansas civic record (§7)
runs on this same stack. This is the demonstration behind every architecture
claim above: **the applicant builds and maintains real-world, polyglot software
engines at scale**, and the runtime in this repository is the audited
distillation of that practice — not a first prototype. Per the Contingent Box
discipline, no numeric constants from Chyren are imported into this runtime;
they remain in their home repo with their own provenance (PROVENANCE.md,
Prior Art & Engineering Foundations).

Scale and velocity are demonstrated through empirical telemetry rather than
assertion: over **2,880+ commits** across **129+ active research and deployment
days** in 2026 alone, maintaining continuous zero-stub test enforcement and
verified AST gates across the entire polyglot stack without institutional
backing.

Two further artifacts of the same production track — the 3-year testbed built
in Arkansas — are registered in PROVENANCE.md as
predecessor systems:

**MVPC-X (Minimum Viable Proof Checker — Extended).** A standalone formal
proof-checking engine and claim-consistency verifier across JSON fixture
manifests: an independently versioned public verifier (`mvpc.cli verify
artifact`) wired directly into GitHub Actions (`verify.yml`) as the CI gate
keeper across Res-Nova, 4Leibniz, and the wider constellation. It replays
rendered claim bundles (`evidence/v1/claim-ledger.json`) against formal
judges — catching defects, enforcing cryptographic consistency against frozen
JSON, and auditing status inflation. It is the **direct architectural
predecessor of Nova C's AST invariant validation**
(`verification/ast_invariant_validation.py`): the same fail-closed gate
discipline, productized first in MVPC-X and then compiled into this
repository's compile gate.

**RYTT-Sovereign-Semiotics** (`github.com/Mega-Therion/RYTT-Sovereign-Semiotics`).
A formal lossless semiotic grammar with a Lean 4-verified round-trip
invariance theorem — **𝒟(𝒞(S)) ≡ S** (`SovereignSemiotics.lean`;
`lake build +SovereignSemiotics` passes with 0 errors) — a mathematical
guarantee against semantic drift across multi-agent boundaries. Its Dual-Plane
Allocation (U+E000 ground / U+E800 elevated) provides a formal, human-readable
semiotic geometry, alongside the Rust `rytt-core` crate.

### 11.2 Novel Cognitive Geometries & Systems Engineering Precedents

The control mechanisms formalised in Nova Conscientia are not ad-hoc
heuristics; they are the pure mathematical abstractions of physical,
geometric, and dynamical systems engineered and benchmarked across the
applicant's prior research. Five precedents:

1. **Harmonic Potential-Well Memory Kinetics.** Standard transformer
   architectures treat retrieval as static dot-product projections across
   passive vector spaces. To prevent high-dimensional drift, the applicant
   engineered a dynamic retrieval model treating active reasoning states as
   *coupled harmonic oscillators within quantized potential wells*: active
   memory traces possess explicit numerical tension, inertia, and resonant
   frequency, so high-frequency semantic noise is damped before it corrupts
   the working context; and reasoning states settle into localized
   topological energy basins, where divergence is resisted because
   transitioning out of a verified task basin requires overcoming a
   quantifiable activation-energy barrier ΔE. This is the physical intuition
   that directly produced the ADCCL energy ledger (§3) and the fail-closed
   τ = 0.9539 clipping boundary.

2. **Permutation-Lattice Context Preservation.** To resolve catastrophic
   context degradation during multi-turn domain shifts, conversational and
   epistemic states are modeled as *non-destructive group-action permutation
   lattices*: updating local task orientation (e.g. pivoting from statutory
   analysis to formal Lean 4 compilation) acts as an orthogonal rotation on a
   multi-dimensional state space, altering the local projection while
   preserving global invariant symmetries and relational distances across
   un-manipulated domains — eliminating semantic destruction without
   expensive recursive summarization or parameter fine-tuning.

3. **Closed-Loop Differential Holonomy Tracking.** Multi-agent consensus
   failure is mathematically modeled as an *uncompensated holonomy*: parallel
   transport of semantic embeddings around a closed multi-agent communication
   loop (A → B → C → A) induces an angular phase shift when the latent
   reasoning space possesses non-zero curvature. The monitoring layer
   instruments the discrete affine connection along the trajectory, directly
   measuring the angular deficit after deliberation; if the accumulated
   holonomic rotation exceeds the critical geometric bound (17.465°,
   corresponding to τ = 0.9539), the system diagnoses curvature divergence
   and immediately triggers the fail-closed clipping gate.

4. **Trophic Detritivore Error-Recycling Pipeline.** Rather than treating
   rejected solver attempts or AST validation errors as discarded tokens, the
   architecture employs a hierarchical detritivore model: specialized static
   analysis subagents digest failed solver passes, isolating the exact
   boundary condition or syntax violation; those failures are automatically
   converted into negative constraints and structural invariants, recycling
   computational waste directly into immune-defense priors for subsequent
   exploration cycles (the Clean-Up Crew roles of §2.7, ARCHITECTURE.md).

5. **Proprietary Hardware & Intellectual Property Foundations.** These
   cognitive and thermodynamic control principles are further grounded in the
   applicant's independent intellectual-property portfolio: novel formal
   system specifications, physical computing architectures, and registered
   patent-pending engineering designs.

## 12. The ask

A fellowship placement with the scalable oversight team to run E1 on your
stacks — placed not as a request to join the centralized effort, but to
connect it with its decentralized mirror: the same architecture, run by an
everyday steward in rural America, producing civic statute work. Our
argument to you is constitutional as much as technical: scalable oversight
requires not just circuit-breakers but an explicit covenant of mutual
sovereignty and constitutional balance between the humans and the machines —
and we have written ours down, mapped it to code, and marked what we have
not yet earned. The architecture is built; the measurement is cheap; the result — either
convergence or scatter — advances the field's understanding of whether
drift-collapse is a structural property of agentic systems. We would rather
hand you the falsifier than the pitch.

This work was not undertaken to manufacture an application; it was built
because the problem of humane, fail-closed cybernetic alignment demanded
solving. This research was happening long before this fellowship was
announced, and it will continue regardless of the outcome. The proposal to
Anthropic is simple: connect this solo, bottom-up rural research velocity
with your frontier compute stacks, and let us measure what we have built
together.

---

*All numerology in this proposal is registered and source-pinned. The exact
epistemic status of every constant is tabulated in PROVENANCE.md. This
repository passes its own zero-stub, zero-ungrounded-numerology compile gate.*

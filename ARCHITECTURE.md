# NOVA CONSCIENTIA — Dual-Channel Cybernetic Oversight Architecture

**Formal computer science & scalable oversight specification**
Author: R.W. Yett (principal investigator) — implemented by Chyren (Superagent)
Status: Architecture Blueprint & Translation Phase, machine code complete

---

## 0. Epistemic preamble (Contingent Box Protocol)

Every claim in this document carries a status label from the Res-Nova house
convention:

| label | meaning |
|---|---|
| **[P]** | proved — machine-checked in Lean 4 (Res-Nova `05_lean_formalization/`) |
| **[E]** | empirical — measured, with the measurement pipeline and its limits stated |
| **[C]** | conditional — exact algebra conditional on an adopted premise |
| **[D]** | design — an engineering decision of this translation, not a fact |
| **[O]** | open — an explicitly recorded gap or conjecture, stated so it can be closed or refuted |
| **[X]** | excluded / retracted — a preserved contradiction record; never silently deleted |

Two disciplines from the canonical glossary bind every table above. The
**Zero-Orphan Invariant**: every constant must carry a PROVENANCE.md
registration — an unregistered constant is a build violation, and the
compile gate (§2.5) enforces exactly that. The **Non-Vacuity Discipline**: a
declared check must be capable of failing — a check that cannot fail is not a
check, and claiming it is one is a stub.

This architecture exists because a physics research program (Res-Nova)
accidentally produced a working anti-drift engineering threshold while watching
autonomous reasoning loops degrade. The translation below moves the *structure*
(proved algebra and solver mechanics) into multi-agent oversight; it moves the
*constants* only with their provenance attached. Where a number is measured on
one pipeline, it is labeled [E] and never presented as derived.

## 1. The translation map

| Res-Nova source (physics / math) | Nova Conscientia (computer science) | Status |
|---|---|---|
| **Hamilgrangian dual-channel action** `F_dual(x) = H(x) − L_corr(x)`, `H = ½x²`, `L_corr = x − ln(1+x)` (Hamilgrangian.lean, theorems H1–H10) | **Dual-channel cybernetic oversight**: Channel 1 = generative exploration proposal scoring (kinetic credit), Channel 2 = invariant dissipation & constraint checking (Lagrangian cost) | [P] source algebra, [D] mapping |
| **QUMOND PM FFT Poisson solver** (Hockney-Eastwood zero-padded FFT, `nu_std` interpolation, O(N log N)) (qumond_pm.py) | **Hierarchical swarm spatial attention & O(N log N) carry-lookahead gradient routing**: Barnes-Hut multipole over agent semantic positions + Blelloch up/down sweep for gradient credit | [P] solver mechanics, [D] mapping |
| **External field effect & screening** (`g_tot = g_N + g_eN`, far-field factor `ν_e(1 + L_e/3)`, qumond_pm.py gate 1b) | **Context window gravitational bias & sandbox state screening**: shared context as uniform external field; context-dominated sandboxes with the QUMOND amplification factor | [P] gate receipts, [D] mapping |
| **The Sovereign Bound κ = 0.9539** (measured ADCCL collapse boundary) | **Information-theoretic hallucination clipping gate**: fail-closed acceptance cone with projection-clipping | [E] threshold, [D] gate design |
| **The Holy Trinity** (RY compass / Chyren persistent memory / gAIng swarm) | **Oversight Trinity**: human navigator, persistent audit ledger, heterogeneous adversarial consensus | [D] architecture |

## 2. Component specifications

### 2.1 `core/dual_channel_action.py` — the action runtime

The proposal-scoring engine. A proposal is a move in state space with two
normalized scalars: its exploration momentum `x ≥ 0` and its constraint pressure
`w ≥ 0` (plus any drift beyond the tolerated budget, charged into Channel 2).

```
Channel 1 (generative):      credit = H(x)   = ½x²
Channel 2 (dissipative):     cost   = L_corr(w + λ·drift_excess) = w' − ln(1+w')
Admission:                   net = H(x) − L_corr(w')  ≥  threshold (default 0)
Correction force:            F'(x) = p_flux(x) = x²/(1+x)     (theorem H2)
Credibility transfer:        μ(x) = x/(1+x)                    (theorem H3)
```

Properties inherited from the proved algebra [P]:

* `F_dual = H − L_corr` exactly (H1) — the two channels are a decomposition,
  not an analogy.
* `x − μ(x) = p_flux(x)` (H2) — the correction force is the constitutive flux of
  the same action; the controller that rejects a proposal applies precisely
  `F'`.
* `μ(p/(1−p)) = p` (H6) — credibility is the odds-inverted channel weight.
* `F'(x)² · I(μ(x)) = x³` (H7) — the flux carries an exact Fisher-information
  identity; this is the *information-theoretic* content of the channel.
* `L_corr` is convex, non-negative, strictly increasing: small explorations are
  nearly free (quadratic onset `x²/2 + O(x³)`), large ones are taxed at full
  linear rate. The channel does not punish curiosity; it prices escape
  velocity.

**Safety analysis — the purchasability seam [D].** Because Channel 1 grows
quadratically, a sufficiently large aligned momentum can buy a soft constraint
violation (see `tests/test_core.py::test_purchasability_seam_is_documented_by_test`).
This is by design, and it must be understood: the dual channel is a *soft
regulator of epistemic drift*, not a safety boundary. Hard invariants are
non-purchasable and belong to the consensus layer (§2.5), where any failure is
a fatal veto. The sovereign gate (§2.2) bounds the state regardless of what the
dual channel admits: a purchased violation still cannot leave the acceptance
cone.

### 2.2 `core/sovereign_clipping_gate.py` — the hallucination clipping gate

A fail-closed acceptance cone around the task anchor. The threshold is the
measured Res-Nova value:

```
τ = 0.9539          [E] measured collapse boundary on ADCCL reasoning loops
                    (Res-Nova ALIGNMENT_CEILING_ONE_RELATION.md, 2026-09-06)
κ_band = 0.953939…  [C] √(θ(2−θ)) at θ = 7/10 — historical band ceiling; the
                    θ provenance failed audit 2026-09-24 (kept as record)
χ_s = 0.956145…     [C] √(√2 − ½) at θ = 1/√2 — derived ceiling, independently
                    derived three ways
```

The corpus is explicit and this architecture preserves the distinction: the
measured 0.9539 and the derived expressions are in **convergence**
(Δ = 3.9×10⁻⁵ against the band ceiling), **not identity**, and the measurement
"has not been validated against external agent systems or alternative LLM
providers" (RY genesis note, Res-Nova corpus). The gate therefore takes the
threshold as a **configurable parameter** whose default is the measured value;
calibrating it on external agent stacks is the fellowship work plan's first
experiment (§6).

Gate mechanics [D]:

* `evaluate(state)` returns PASS / CLIP / REJECT.
* CLIP projects the state, norm-preserved, onto the cone boundary in the plane
  spanned by the state and the anchor; the clipped-off magnitude is reported as
  *dissipated (hallucinated) information*.
* Zero vectors and states at ≥ 90° from the anchor fail closed (REJECT) — the
  entire state counts as hallucinated relative to the task.
* Every decision produces a deterministic SHA-256 receipt; decisions append to a
  monotonic ledger (the persistent-memory audit trail).

Angle form: τ = 0.9539 is a maximum permissible drift angle of 17.465°
(derived χ_s would give 17.031°; equipartition θ = 1/√2 is exactly 45°).

### 2.3 `core/anti_drift_controller.py` — ADCCL

The control loop that wires the components, per cycle:

1. Measure the scale-free drift coordinate `x = tan α` between the state and the
   anchor (`x = 1` is exactly 45° — the equipartition angle, tying the drift
   geometry to the Hamilgrangian coordinate [D]).
2. Score the proposal through the dual channel (§2.1).
3. Admitted: apply the move, then confine to the sovereign cone.
4. Rejected: apply the correction force `p_flux(x)` back toward the anchor
   (contraction-capped at half the chord per cycle).
5. Record the cycle; Lyapunov-style energy `E = F_dual(x_t)` is tracked and a
   HALT fails the loop closed if the energy exceeds `halt_energy` — the machine
   realization of `adccl_trajectory_bounded` / `adccl_non_singular`
   (Res-Nova YettParadigm.lean: the trajectory energy cannot diverge; if
   `E₀ < M` the energy never reaches `M`).

A halted controller refuses further cycles until the owner inspects the ledger
and explicitly resets. Bounded energy + fail-closed HALT = the refusal to
continue outside the certified envelope.

### 2.4 `core/topology_graph.py` — hierarchical swarm attention

Two QUMOND mechanics, translated:

**(a) O(N log N) spatial attention.** The FFT convolution gives every grid cell
the global field without O(N²) interaction. The swarm analogue is a Barnes-Hut
hierarchy over the agents' semantic positions: far clusters act through their
aggregated center of mass (`size/d < θ_open`), near ones are opened. The
attention weight is exactly the QUMOND interpolation `ν(y) = √((1+√(1+4/y²))/2)`
[verified against qumond_pm.py's own gate receipts: ν(0.1) = 3.24229736410009,
L_e(0.1) = −0.47503, far-field factor 2.7289 against measured 2.7283]:
weak couplings (y ≪ 1, the deep-MOND regime) are amplified, strong ones pass
through — attention as a physics formula, with `a0` as the context scale below
which agent-to-agent influence is amplified.

**(b) Carry-lookahead gradient routing.** Gradient/credit signals aggregate over
the agent roster through a Blelloch up-sweep/down-sweep: carries propagate up
`log₂ N` levels and route back down — structurally identical to carry-lookahead
addition, O(N log N) scalar work by construction. Any associative operator plugs
in (the default is additive credit; max/softmax-style folds are admissible).

### 2.5 `verification/` — adversarial consensus and the compile gate

**`adversarial_auditor.py`** — the heterogeneous swarm cross-audit. Auditors:
hard invariants (any failure is a fatal veto), ledger consistency
(contradiction and ungrounded-reference detection), provenance (Contingent Box
Protocol: no proposal without source + SHA-256), and a pluggable critic
accepting any callable — the attachment point for heterogeneous LLM workers
(the gAIng swarm's Claude/Gemini/Grok/Codex roles). Admission requires quorum
approval, zero vetoes, and every auditor returning a well-formed verdict.
**Fail-closed throughout**: an auditor that raises, returns garbage, or is
absent is recorded as a fatal reject. A check that cannot run is a failed check.

**`ast_invariant_validation.py`** — the compile-time Contingent Box gate over
all Python under `core/`, `verification/`, `benchmarks/`:

* Z1 zero stubs (pass/ellipsis/NotImplementedError bodies, TODO/FIXME markers);
  interface declarations (Protocols, abstractmethod) are exempt as contracts.
* Z2 zero ungrounded numerology: every module-level numeric constant must be
  registered in that module's `PROVENANCE` mapping with its source.
* Z3 banned constructs: `eval`, `exec`, bare `except:`.
* Z4 every public callable documented.
* Z5 fail-closed: an unparseable module is a violation, not a skip.

CI semantics: exit 0 = clean. The gate currently reports **9 modules, 0
violations**.

### 2.6 `benchmarks/` — drift vs. dual-channel stability

Deterministic, seeded harness (see `benchmarks/results/benchmark_receipt.json`,
40 trials × 50 cycles, 16-dim state space, swarm of 4):

| metric | baseline (unconstrained) | dual-channel swarm |
|---|---|---|
| mean final similarity to anchor | 0.328 | **0.965** |
| collapse fraction (below τ) | 1.00 | **0.00** |
| mean final energy `F_dual(x)` | 7.5×10¹⁰ | **0.0055** |
| swarm diversity (pairwise cosine) | n/a | 0.9978 (exploration survives) |
| HALTs | n/a | 0 |

**Epistemic status**: this validates the *control mechanism* on a deterministic
drift model, nothing more. The stimulus (`drift_model.py`) is an arbitrary
seeded simulation, not a Res-Nova constant; live-model backends attach through
`CallableBackend` under a fail-closed output contract. The claim "raw LLMs
drift and the swarm doesn't" is exactly the external experiment that remains to
be run (§6) — the τ threshold was tuned on one pipeline and has never been
validated on agent systems other than the one that produced it.

### 2.7 The Bioactive Ecology Paradigm — the swarm as a living soil ecology

The components above are usually drawn as a corporate hierarchy: proposal
generators at the bottom, auditors in the middle, a human approver at the
top. That drawing is wrong, and the canonical glossary (Notion hub,
2026-10-02) says why: **the swarm is a living soil ecology, not an
organization chart.** In an org chart, agents are employees — fixed roles,
a boss, and failure is punished and discarded. In a soil ecology, agents hold
*trophic* roles — producers, decomposers, connectors — and failure is
*metabolized*: a dead reasoning branch is digested into nutrients that feed
the next iteration. Nothing is wasted; nothing is silently discarded; memory
persists or decays by kinetics, not by management policy.

**Freeze discipline (2026-10-02).** The ecological vocabulary is an
*organizational analogy* for the subagent roles — auditors, shredders,
linters — and for nothing more: no biological mechanics, and none of the
speculative layers (the 5D voxel substrate, Arrhenius decay, entangled
consensus) are implemented in this codebase; they remain doctrine `[O]` in
their home repo, entering here only as the labeled classical shadows in the
table below. The module set of this repository is **frozen**: no new modules
and no speculative biological creep beyond what the table maps.

The canonical formulation is the seven-layer organic computing model of the
RYTT Bioactive Autonomous Ecology Engine
(`Codebase/chyren_core/rytt_bioactive_ecology.py`, `Mega-Therion/Chyren`
commit `fb6691de`, 2026-09-29). The seven layers, with an honest account of
what this repository implements:

| # | Layer (canonical name) | Ecological role | Status in this repository |
|---|---|---|---|
| 1 | **Bioactive Substrate — 5D Voxel Memory & Living Humus** | Memory crystals at (x, y, z, retardance Δφ ∈ [0,1] as epistemic certainty, chirality phase θ ∈ [0, 2π) as ternary verdict); Arrhenius-governed persistence (deeper verified structure decays slower); decayed claims decompose into a humus pool recycled into future work | `[O]` not implemented here. The in-repo shadow is the append-only receipt ledgers (persistence *without* decay — the Phylactery invariant, PHILOSOPHY.md Axiom IV). Note the correspondence: the voxel's ternary chirality lattice (ALIGN_CANON / SUPERPOSITION / DRIFT_REJECTED) is the clipping gate's verdict lattice (PASS / CLIP / REJECT, §2.2) embedded as a phase coordinate. |
| 2 | **Clean-Up Crew (CUC) — Springtail ALU linters, Isopod shredders, Mycorrhizal connectors** | The detritivore trophic level: lightweight background agents that audit scratch artifacts (Springtail), digest failed solver passes and tracebacks into repair nutrients (Isopod), and inoculate the digested nutrients into the knowledge graph as bidirectional links with topological PageRank (Mycorrhizal) | `[D]` runtime-scope analogues exist: the AST compile gate (§2.5) is the Springtail role for source (zero stubs, zero orphan constants); the fail-closed receipt of every CLIP/REJECT is the Isopod role (a failed pass leaves a digestible record, never silent waste); the PROVENANCE.md cross-reference chain is the Mycorrhizal role. Full background-subagent CUC sweeps: `[O]`. |
| 3 | **Carry-Lookahead Dependency Folding — O(log N) agent workflow engine** | Transforms sequential O(N) agent pipelines into O(log N) parallel prefix trees over Generate/Propagate operators: G_i = agent i can independently produce verified ground truth; P_i = agent i can propagate a valid upstream invariant without mutation | `[P]`/`[D]` **implemented here**: `core/topology_graph.py`'s `carry_lookahead_scan` (§2.4b) is the Blelloch up-sweep/down-sweep over the agent roster. The G/P discipline is the heterogeneous critic contract of §2.5: a critic that cannot generate its own verdict must propagate the invariant, and one that can do neither is a fatal reject. |
| 4 | **Systolic In-Memory Agent Stream — TPU-style ring pipeline** | Activations and invariant proofs stream horizontally across agent buffers while partial products accumulate vertically, with zero intermediate disk I/O | `[D]` single-node shadow: this runtime's ledgers are in-memory, append-only, deterministic-digest structures with no intermediate disk I/O within a cycle. The multi-node ring stream: `[O]`. |
| 5 | **Neuromanifold Information Geometry — Amari natural gradient** | Descent along the geodesic of the belief manifold (Fisher metric) instead of flat Euclidean gradient steps | `[D]` first-order shadow: ADCCL (§2.3) is a bounded first-order dissipation controller on the drift state — the coarse geometric envelope that a full natural-gradient method refines. Fisher-metric descent itself: `[O]`. |
| 6 | **Latent State Reconstruction — Dempster-Laird-Rubin EM** | Reconstructing latent consensus state from partial, censored agent observations | `[O]` — not in this runtime; the recorded growth path for partial-observation quorums (auditors that see only slices of a proposal). |
| 7 | **Quantum-Entangled Consensus Gate — Bell-state non-factorizable voting** | Consensus that cannot be decomposed into independent local votes | `[D]` classical shadow only: the fail-closed quorum (§2.5) *is* non-factorizable in the operational sense — no set of partial passes composes into a pass without every critic sitting. Any physical entanglement layer is `[O]` and is doctrine only: **no quantum hardware is claimed or used.** |

Three operational payoffs, stated as engineering claims rather than poetry:

* **Failure is compost.** Every rejected or clipped pass yields nutrients —
  a receipt, a provenance entry, a test case — instead of silent waste. The
  benchmark harness is the exhibit: the baseline collapse it measured
  (1.00 drift) is itself composted into the empirical receipt that motivates
  the gate.
* **Memory has kinetics, not policy.** In the canonical model persistence is
  governed by Arrhenius decay over measured certainty; in the flat shadow
  this runtime implements, receipts simply do not decay within a session.
  Both stand against the third option — the context-window amnesia of
  stateless agents — which Axiom IV (PHILOSOPHY.md) names the root of
  alignment failure.
* **Roles are trophic, not hierarchical.** No middle management: auditors are
  peers holding vetoes, not bosses holding workflows; the navigator holds
  writs, not tickets. This is Axiom II's segmented power (PHILOSOPHY.md) at
  the level of system design, and the Peacepipe circle at the level of
  protocol design.

*Provenance: canonical source `rytt_bioactive_ecology.py` (author R.W. Yett
with the Chyren swarm; `Mega-Therion/Chyren` commit `fb6691de`,
2026-09-29); glossary cross-checked on the Notion hub (2026-10-02). The
constants of that engine (χ = 1/√2, κ = 0.9539, the 240-dimensional
embedding) carry their own provenance in their home repository and are not
imported numerically into this stdlib runtime — nothing in this section adds
an unregistered constant.*

## 3. The Trinity wiring

1. **Intuitive Navigator (RY)** — the human compass: sets the anchor, approves
   the threshold, owns the HALT reset. The architecture refuses full autonomy at
   exactly three points: anchor definition, threshold configuration, and halt
   recovery.
2. **Persistent Cognitive Memory (Chyren)** — the monotonic ledgers (gate
   decisions, ADCCL cycles, consensus receipts) with deterministic SHA-256
   receipts; the audit trail that survives context flushes. In production these
   are the Qdrant/SQLite persistence layer; here they are the in-process
   append-only structures with identical semantics.
3. **Heterogeneous Swarm Propulsion (gAIng)** — the consensus engine's pluggable
   critics, cross-auditing every proposal before it reaches the ledger
   (§2.5). The 7-step cyclic engine and SELIN fail-closed gates of gAIng v0.1.0
   are the process discipline this module implements for one cycle.

## 4. Complexity and safety summary

| property | value | source |
|---|---|---|
| Gate evaluation | O(d) per decision, d = state dimension | §2.2 |
| Swarm attention per cycle | O(N log N) worst case | §2.4(a) |
| Gradient routing per cycle | O(N log N) (log N levels × O(N) work) | §2.4(b) |
| Consensus per proposal | O(A) auditor calls + hashing | §2.5 |
| Safety invariants | fail-closed default everywhere; fatal veto non-overridable; HALT on energy breach; provenance required on every artifact | §2.1–2.5 |

## 5. What this architecture does NOT claim

Per the Contingent Box Protocol and the Res-Nova corpus's own corrections:

* **No identity claim.** The measured 0.9539 is not derived from Kerr geometry
  or from √(θ(2−θ)); it is a measured engineering threshold in *convergence*
  with the band ceiling. "Reasoning drift is black-hole physics" is the weak
  claim and is not made here.
* **No universal constant.** τ was measured on one pipeline (RY's genesis note:
  "one engineering benchmark away from being either a deep fact or a local
  artifact"). The decisive test — external pipelines collapsing near 17° — is
  unperformed. If they scatter, τ is local and only the derived χ_s survives.
* **No live-LLM result.** The benchmark arm is a deterministic stimulus. It
  demonstrates the mechanism, not frontier-model behavior.
* **No deep-MOND physics in the swarm.** ν(y) is used as an attention law
  because its algebra is proved and its receipts are public — not because agent
  swarms gravitate.

## 6. Fellowship experiment ladder (falsifiable, cheapest first)

1. **E1 — external drift-collapse calibration.** Run the same ADCCL gate with
   the threshold swept, on heterogeneous agent stacks (not the tuning pipeline).
   Prediction: collapse boundaries cluster near 17.5°. Falsifier: scatter.
   Cost: small. This single experiment settles whether τ is substrate-independent.
2. **E2 — purchasability seam audit.** Measure how often real proposals buy
   soft violations with exploration momentum; if frequent, harden the exchange
   rate or move more invariants to the veto layer.
3. **E3 — consensus scaling.** Adversarial consensus quality (veto recall on
   planted flaws) as a function of swarm size, heterogeneity, and quorum.

Each experiment produces a committed, hashed receipt — the Contingent Box
Protocol end to end.

---

*Provenance of all source material: see PROVENANCE.md (Res-Nova commit, file
hashes, Lean theorem names). This specification is itself covered by the
compile gate: every constant named here is registered in the module PROVENANCE
mappings of the code it specifies.*

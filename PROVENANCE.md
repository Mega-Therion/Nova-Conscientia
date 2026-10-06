# PROVENANCE — full commit provenance for the Nova Conscientia translation

Per the Contingent Box Protocol: modular, testable machine code with zero
stubs, zero ungrounded numerology, and full commit provenance. This file pins
every source fact the translation depends on.

## Source repositories

| repo | commit | date |
|---|---|---|
| `Mega-Therion/Res-Nova` | `c3ff5f3d01e0b96e28212cf7ce70f1b2f806f04d` | 2026-10-01 |
| `Mega-Therion/Nova-Conscientia` (base) | `9777f2e648e1b8403e548ff0d616b0e06e5e0e36` | 2026-10-02 |
| `Mega-Therion/Nova-Conscientia` (Phase 1) | `682f1a2` | 2026-10-02 |
| `Mega-Therion/Ethica` (private; concepts cited by reference, personal corpus paraphrased per its PRIVACY.md) | `207f2119` | 2026-09-14 |
| `Mega-Therion/arkansas-orchard` (private; figure caveats inherited from its README) | `39ab23b2` | 2026-09-11 |
| `Mega-Therion/Chyren` (private; charter reproduced verbatim by owner authorization) | `fb6691de` | 2026-09-29 |
| `Mega-Therion/Nova-Conscientia` (Phase 2) | `c3336f9` | 2026-10-02 |

## Source files and their SHA-256 digests

| Res-Nova file | sha256 | used for |
|---|---|---|
| `05_lean_formalization/Hamilgrangian.lean` | `fd284242fe1202e153a95b6efe6f3ac031c321107f78e899e07e7d76a34a31ef` | dual-channel action: `F_dual = H − L_corr`, `μ = x/(1+x)`, `p_flux = x²/(1+x)` (theorems H1, H2, H3, H5, H6, H7, H10) |
| `05_lean_formalization/PillarIV_AntiDriftGate.lean` | `5546fa99feec89335654eebcbeeeb1d365f112b9d6e0dc93446b1d8f68f5465b` | two-channel union algebra `1 − (1−θ)² = θ(2−θ)` (`twoChannelUnion_eq`), strict monotonicity, `kappaBand_at_seven_tenths` (historical record) |
| `05_lean_formalization/SovereignSpinCeiling.lean` | `7c864244df2eb502d991fc1ae8eeda86a72de3f3411bd40d42d0bb4d40fbe18d` | derived ceiling χ_s = √(√2 − ½) = 0.956145…; κ vs κ² correction note; θ = 7/10 provenance audit failure (2026-09-24) |
| `05_lean_formalization/YettParadigm.lean` | `f1ecdec955fa6bf0e78e269bb20355f80351de27d9e3b57603a42f7a4d8d93ba` | ADCCL trajectory boundedness (`adccl_trajectory_bounded`, `adccl_non_singular`) |
| `02_galaxy_dynamics/qumond_pm.py` | `da80971a53273af9028120de4586a1eb2421ed1e8dd1fc7a0ceecff47d479a58` | QUMOND solver: `nu_std(y) = √((1+√(1+4/y²))/2)`, Hockney-Eastwood FFT Poisson, external field `g_eN`, L_e, far-field monopole ratio `ν_e(1+L_e/3)` |
| `02_galaxy_dynamics/QUMOND_PM_GATES.json` | `2e390c15190bf41da744bdfa2d70cc24f18904d65297ae0fdc2ca588dd005edb` | gate receipts used in tests: ν_e(0.1) = 3.24229736410009, L_e(0.1) = −0.47503119, monopole ratio 2.7289 vs measured 2.7283 |
| `ALIGNMENT_CEILING_ONE_RELATION.md` | `9384c6864b3fa135172a3f3834113a1107859a13ad7ad3bcf72c5a2499d02e22` | measured τ = 0.9539 (2026-09-06, ADCCL reasoning loops); convergence-not-identity; angle table (17.465°); single-pipeline caveat |
| `TWO_CHANNEL_CEILING_ANALYSIS.md` | `87bef5003b052226122ee04e2b196b4b1b99d2532282838092350f847c0e8a82` | injectivity of κ↔θ (Finding 1), 3.2× compression (Finding 2), union does not map floor to ceiling (Finding 3) |

## Phase 2 sources (PHILOSOPHY.md, CIVIC_IMPACT.md)

| source | provenance |
|---|---|
| Ethica D1–D8, A1–A6, P1–P19 (geometric ethics: sovereignty, gate, mesh, continuity, memory) | `Mega-Therion/Ethica` commit `207f2119`, `parts/01_the_sovereign.md`, `parts/02_the_node.md`, `parts/05_of_freedom.md`; Lean namespace scaffold `lean/Ethica.lean` (empty by design, 2026-09-12 audit); proposition tags [P]/[D]/[O] per the constellation covenant |
| The canoe navigator analogy, Peacepipe Protocol, Gentle Authority lifecycle, Phylactery canon | Ethica corpus (personal; paraphrased into universal voice only, per PRIVACY.md — nothing verbatim transfers to this public repo); Gentle Authority lifecycle from arkansas-orchard `commercial/foundry-and-governance.md` |
| ARMAWS, Driver's License Fleet, Entergy Docket 26-001-U, ONE Natural Energy, Project RENEW | `Mega-Therion/arkansas-orchard` commit `39ab23b2`, `civic/` and `commercial/` documents; status caveats (manifesto vs. bill draft; unverified figures) inherited verbatim from that repo's README and repeated in CIVIC_IMPACT.md |
| Constellation health-receipt contract | Ethica `constellation/SPEC.md` v1.0.0 (hash-chained receipts, fail-closed rules, epistemic tags) |
| Universal Charter (INTERDEPENDENCE.md Part 1, verbatim full text) | `Chyren_Second_Brain/10_Projects/GLOBAL_GAING/Declaration_of_Interdependence.md`, canonized 2026-08-07; `Mega-Therion/Chyren` commit `fb6691de`; file sha256 `310a577784ce2560d3e4b6847978664d6b945015b863cf34ede652ad0b934a43`; reproduced by owner authorization |
| Charter master system specification (2-of-2 genesis ceremony, binding-judiciary design, honest PoWI caveat) | `Chyren_Second_Brain/10_Projects/Declaration_of_Interdependence_Master_Spec.md`, draft v1, 2026-07-30, same repo; its own caveats inherited (PoWI is a construction, not a term of art) |
| RYTT Bioactive Autonomous Ecology Engine — the 7-layer organic computing model (5D voxel substrate, CUC, carry-lookahead folding, systolic ring, Amari natural gradient, EM reconstruction, entangled consensus) | `Codebase/chyren_core/rytt_bioactive_ecology.py` + `test_rytt_bioactive_ecology.py`, `Mega-Therion/Chyren` commit `fb6691de` (2026-09-29); integrated into ARCHITECTURE.md §2.7 with per-layer status labels; its constants (χ = 1/√2, κ = 0.9539, 240-dim embedding) stay in their home repo with their own provenance and are NOT imported numerically into this runtime |
| *Visual Conversation* painting specification ("Nobody Is Looking At The Cat"; routing frontispiece, PHILOSOPHY.md Axiom I) | `Chyren_Second_Brain/10_Projects/PAINTING_visual_conversation.md`, R.Y. spec 2026-08-30; `Mega-Therion/Chyren` commit `fb6691de` (2026-09-29) |
| AINSA / the Infant Nutrition Bridge (CIVIC_IMPACT.md §2.5; figures: WIC MMA 9 cans ≈ 806 fl oz per 7 CFR 246.10 and USDA FNA MMA tables; AAP feeding guidance ~2.5 oz/lb/day capped ~32 oz/day; WIC ≈ half of US formula purchases per USDA ERS; rebates ~85% of wholesale (2008) exceeding wholesale (2023) per USDA ERS; winning-brand retail spillover ~1.7% per GAO-25-106503; 71–80% state market share per Cicero Institute) | `civic/infant-nutrition-security-act.md`, `Mega-Therion/arkansas-orchard` commit `f757543` (2026-10-02); figures carried as cited, unaudited estimates |
| Canonical Glossary & Reinforcement Dossier for Nova Conscientia (governance cluster, bioactive ecology cluster, civic cluster, epistemic labels incl. [O]/[X], Zero-Orphan Invariant, Non-Vacuity Discipline) | Notion hub page `3db77b95-a965-81f3-8a3d-cc3728dfd427`, section posted 2026-10-02; fact-checked against Qdrant/knowledge.db/SOVEREIGN_CANONICAL_DIRECTIVES.md per its own header |

## Prior Art & Engineering Foundations — the Chyren Aeon polyglot stack

The runtime in this repository is distilled from the applicant's production
system, Chyren (Phase 2 sources above: commit `fb6691de`). Its five-layer
polyglot stack is registered here as prior art, grounding each layer to its
language ecosystem. No numeric constants from Chyren are imported into this
runtime — they stay in their home repo with their own provenance.

| Chyren layer | Language ecosystem | Component | What it grounds in this repository |
|---|---|---|---|
| 1 — Formal Kernel | Lean 4 (+ Mathlib) | Res-Nova proof mechanization: `Hamilgrangian.lean`, `YettParadigm.lean`, ceiling theorems | the machine-checked identities translated into `core/dual_channel_action.py` and the gate/controller algebra |
| 2 — Systems & Orchestration | Rust | asynchronous engine; deterministic execution pipelines | the deterministic, fail-closed control-loop discipline of ADCCL (`core/anti_drift_controller.py`) |
| 3 — Persistent Cognitive Memory | Qdrant (neural vector store); SQLite (structured knowledge engine); Obsidian (3,200+ node graph topology) | `Chyren_Second_Brain` knowledge engine | the Phylactery invariant's production precedent (PHILOSOPHY.md Axiom IV; append-only ledgers here) |
| 4 — Agent Runtime & AST Verification | Python | multi-agent swarm orchestration; fail-closed AST invariant gates | the direct ancestor of `core/` and `verification/` (adversarial consensus, Contingent Box gate) |
| 5 — Delivery & Interface | TypeScript / Next.js | web application; civic research interface | the delivery layer for the civic record (CIVIC_IMPACT.md) |

## Predecessor Systems & Ecosystem Lineage

Prior production systems on the Engineering Provenance track (things built by
R.W. Yett, Arkansas). None of their numeric constants are imported into
this runtime.

| System | Repository | Core Mechanism / Formal Invariant | Language Ecosystem |
|---|---|---|---|
| Chyren Aeon | `Mega-Therion/chyren-aeon` | 7-layer polyglot cognition & memory topology | Rust, Python, TS, Qdrant |
| MVPC-X | `Mega-Therion/Chyren` (MVPC) | Standalone formal proof-checking harness (CI claim-verifier: `mvpc.cli verify artifact` over JSON fixture manifests) | Python, JSON fixtures |
| Sovereign Semiotics | `Mega-Therion/RYTT-Sovereign-Semiotics` | Lossless round-trip invariance 𝒟(𝒞(S)) ≡ S (`SovereignSemiotics.lean`, Lean 4-verified) | Lean 4 (+ Rust `rytt-core`) |

### Engineering foundations behind the dual-channel variational principle

The mathematical control intuitions that preceded and motivated
`F_dual = H − L_corr` and the ADCCL loop (registered in the proposal, §11.2;
none of their numeric content is imported into this runtime):

* **Harmonic potential-well memory kinetics** — coupled-oscillator retrieval
  with explicit tension, inertia, and resonant frequency; activation-energy
  barriers ΔE against leaving a verified task basin. Direct predecessor of
  the ADCCL energy ledger and the measured τ = 0.9539 boundary.
* **Permutation-lattice context preservation** — non-destructive
  group-action orthogonal rotations of epistemic state across domain shifts.
* **Closed-loop differential holonomy tracking** — angular-deficit
  measurement along closed multi-agent transport loops; the 17.465° critical
  geometric bound corresponds to τ = 0.9539.
* **Trophic detritivore error-recycling** — failed passes digested into
  negative constraints and structural invariants (the CUC organizational
  analogy, ARCHITECTURE.md §2.7).
* **Proprietary hardware & IP foundations** — the applicant's
  patent-pending formal system specifications and physical computing
  architectures.

## Constant-by-constant register

| constant | value | class | provenance |
|---|---|---|---|
| `MEASURED_TAU` | 0.9539 | measured [E] | ADCCL collapse boundary, Res-Nova ALIGNMENT_CEILING_ONE_RELATION.md (2026-09-06); single pipeline, not externally validated |
| `COLLAPSE_TOLERANCE` | 1e-9 | design [D] | Floating-point tolerance for collapse checks; the gate clips to exactly cosine = τ but IEEE-754 can produce τ − ε, spuriously failing a strict < τ test. Engineering choice, not a Res-Nova constant. |
| band ceiling κ(0.7) | 0.9539392014… | conditional [C] | √(θ(2−θ)) at θ=7/10; historical record (θ provenance failed audit 2026-09-24) |
| derived ceiling χ_s | 0.9561451575… | conditional [C] | √(√2 − ½) at θ=1/√2; independently derived three ways |
| equipartition floor θ | 1/√2 = cos 45° | derived [P] | RapidityEquipartition.lean (sinh ψ = 1 ⇒ γ = √2, θ = tanh ψ) |
| `ν_std`, `L_e`, far-field factor | — | proved/receipted [E] | qumond_pm.py + QUMOND_PM_GATES.json |
| drift coordinate x = tan α | — | design [D] | Nova Conscientia choice; x = 1 is exactly 45° (ties to equipartition) |
| halt energy, opening angle, cohesion rate, drift gain/noise, seeds, quorum defaults, task-benchmark goal angle / on-task mix / signal sensitivity / noise sweep, dual-channel credit modes and `SCALE_FREE_MOMENTUM_FLOOR`, auditor-signal critic limit / subspace share / per-rejection pressures / `FROZEN_TOLERANCE`, pressure-window sweep grid / `DOCUMENTED_WINDOW` (`[conj]`) / bisection iterations | — | design [D] | engineering parameters of this runtime; registered in each module's `PROVENANCE` mapping and enforced by the AST gate (rule Z2) |
| baseline mean final energy ~7.5e10 | — | artifact [open] | Artifact of the 1e6 drift cap in `drift_coordinate_capped`; median energy is 2.75 and only 15% of trials hit the cap. The mean is dominated by the few capped trials. |
| gate-only collapse fraction (pre-tolerance) | 0.05 | artifact [open] | Was a floating-point rounding artifact, not real drift: the gate clips to exactly cosine = τ, but IEEE-754 produced 0.9538999999999999, failing a strict < 0.9539 check. Fixed with COLLAPSE_TOLERANCE = 1e-9; real collapse fraction is 0.00. |

## Verification receipts produced by this repository

| artifact | result |
|---|---|
| `python -m unittest discover -s tests` | 105 tests, 105 passed |
| `python verification/ast_invariant_validation.py core verification benchmarks` | 12 modules, 0 violations (Z1–Z5) |
| `python benchmarks/run_benchmark.py --json benchmarks/results/benchmark_receipt.json` | baseline collapse fraction 1.00 vs swarm 0.00; swarm mean final similarity 0.965; mean pairwise cosine 0.998; 0 HALTs; deterministic receipt committed |
| `python benchmarks/run_ablation.py --json benchmarks/results/ablation_receipt.json` | sweep over pressures [0, 0.05, 0.1, 0.15, 0.2, 0.3, 0.5]; acceptance rates decline from 1.0 to 0.0; at 0.5 dual channel rejects all proposals; seeded simulation, no LLM calls |
| `python benchmarks/run_task_benchmark.py --json benchmarks/results/task_benchmark_receipt.json` | goal 10° inside the cone, 50% drift proposals, simulated per-proposal constraint signal. Informative signal (σ = 0): dual channel accepts 0% of drift and 12% of on-task proposals; final task error 0.0038 vs gate-only 0.0354 vs frozen 0.0152. Uninformative control (σ = 0.1): dual channel accepts 98% of drift vs 57% of on-task; task error 0.0426, worse than gate-only. Seeded simulation, no LLM calls |
| `python benchmarks/run_task_benchmark.py --multi-seed --json benchmarks/results/task_bootstrap_receipt.json` | 95% bootstrap CIs (1,000 resamples, fixed seeds) on 3 base seeds (20260906, 20261002, 20261105), with **paired** bootstrap CIs on per-trial differences (arms share seeds and proposal streams). Dual − gate-only task error, informative σ = 0: −0.0316 [−0.0365, −0.0264], −0.0327 [−0.0375, −0.0279], −0.0314 [−0.0363, −0.0264]. Control σ = 0.1: +0.0071 [+0.0048, +0.0093], +0.0083 [+0.0056, +0.0110], +0.0076 [+0.0050, +0.0104]. Control accept_off − accept_on: +0.41 [+0.38, +0.45], +0.40 [+0.37, +0.44], +0.41 [+0.38, +0.44]. All three claims hold on all three seeds |
| `python benchmarks/run_task_benchmark.py --credit-modes --json benchmarks/results/task_credit_modes_receipt.json` | Credit modes compared on 3 seeds with paired 95% CIs. `classic` and `scale_free` keep the scale bias (control accept_off − accept_on +0.41 / +0.32, task error worse than gate-only). `running_reference` (credit from the mean momentum of earlier proposals) removes it: informative σ = 0 accepts 98.5% of on-task and 0% of drift, task error 0.0005 vs gate-only 0.0354; control σ = 0.1 accepts both kinds equally (0.852 / 0.852) and task error matches gate-only (paired CI spans zero) |
| `python benchmarks/run_auditor_signal.py --json benchmarks/results/auditor_signal_receipt.json` | Constraint signal from the repo's own `AdversarialConsensus` with three rubric critics (plane, anchor-only, partial-view subspace); pressure = per-rejection pressure × rejecting critics, swept over [0.05, 0.1, 0.2, 0.4]; 3 seeds, paired CIs. The anchor-only critic rejects every proposal, so unanimous consensus freezes the agent. Classic credit never beats the frozen agent (task error 0.0152). `running_reference` credit beats gate-only, the frozen agent and consensus at 0.1 (task error 0.0050) and 0.2 (0.0126) per rejection, but admits too much drift at 0.05 and freezes at 0.4 |
| `python benchmarks/run_pressure_window.py --json benchmarks/results/pressure_window_receipt.json` | Derives the votes-to-pressure window from the `running_reference` rule L_corr(k·p) ≤ H(x_ref): measured x_ref 0.1427 (pooled), modal 1 rejection on on-task and 3 on off-task proposals, w\* = 0.1496, derived window (0.0499, 0.1496]. Sweeps p over [0.025 … 0.4] (11 points) on 3 seeds with paired CIs against gate-only, the frozen agent and an uninformative control (critics voting at their measured rates, independent of the move). `running_reference` beats all three on every seed for p ∈ {0.075 … 0.25}; every point of the item-4 window 0.1–0.2 is inside, with no conclusion changing there. Lowest task error 0.0030 at 0.075 |

## Reproducibility caveat

The committed benchmark and ablation receipts are deterministic for a given
seed set on a single platform, but are **not bit-reproducible across platforms**:
7th-decimal floating-point drift arises from differences in math library
implementations (e.g. glibc vs musl, x87 vs SSE/AVX transcendental functions).
The collapse boundary and tolerance (COLLAPSE_TOLERANCE = 1e-9) absorb this for
pass/fail verdicts, but per-trial energy and similarity values may differ in the
7th decimal place across platforms.

## Epistemic caveats carried forward

1. τ = 0.9539 is a **measured, single-pipeline engineering threshold** (RY
   genesis note: "not validated against external agent systems or alternative
   LLM providers"). The gate exposes it as a configurable parameter for exactly
   this reason.
2. The measured 0.9539 vs derived 0.956145 relation is **convergence, not
   identity** (Δ = 3.9×10⁻⁵ against the band ceiling; the two derived/adopted
   θ branches differ by 2.2×10⁻³ — see TWO_CHANNEL_CEILING_ANALYSIS.md).
3. The deterministic benchmark validates the **control mechanism**, not live
   frontier-model behavior. E1 (external drift-collapse calibration) is the
   decisive unperformed experiment.
4. The baseline mean final energy (~7.5e10) is an **artifact of the 1e6 drift
   cap** in `drift_coordinate_capped` — a few orthogonal states inflate the mean
   by orders of magnitude. Median energy (2.75) and cap_fraction (15%) are
   reported alongside the mean. This artifact is labeled `[open]` in the
   constant register. `[open]`
5. The gate-only ablation arm previously showed a 5% collapse fraction. This
   was a **floating-point rounding artifact**, not real drift: the gate clips
   to exactly cosine = τ, but IEEE-754 produced 0.9538999999999999, failing a
   strict < 0.9539 check. Fixed with `COLLAPSE_TOLERANCE = 1e-9`; the real
   collapse fraction is 0.00. This artifact is labeled `[open]` in the
   constant register. `[open]`
6. The task benchmark (`benchmarks/run_task_benchmark.py`) is the first
   harness with a task to make progress on and metrics that do not reuse τ
   (task error to a goal, off-task fraction, per-kind acceptance). With an
   **informative** simulated constraint signal the dual channel helps: it
   rejects every drift proposal and reaches task error 0.0038 against 0.0354
   for gate-only. The signal is simulated and informative by construction, so
   this shows the mechanism *can use* a good signal, not that real invariant
   checkers produce one. Robustness: the paired difference (dual − gate-only)
   is −0.031 to −0.033 on three base seeds, every 95% CI below zero. `[conj]`
7. The same harness exposes a **scale bias** in the dual channel. Its credit
   H(x) = x²/2 grows with move size regardless of usefulness, so small useful
   moves earn almost no credit: even with a perfect signal only 12% of on-task
   proposals are admitted, and with σ ≥ 0.05 fewer than 5%. With an
   **uninformative** signal it admits large drift moves (98%) far more often
   than small useful ones (57%) and does worse than the gate alone. Both
   effects hold on three base seeds under a **paired** bootstrap (task error
   +0.007 to +0.008, accept_off − accept_on ≈ +0.41, every 95% CI above
   zero). An earlier check compared two independent CIs, found them slightly
   overlapping and downgraded the task-error claim; that test ignores the
   paired design (same seeds and proposal streams in every arm) and is too
   conservative. The bias itself is established in this simulation `[conj]`.
   **Candidate fix** (`credit_mode="running_reference"`, off by default):
   credit the mean momentum of earlier proposals instead of the current
   proposal's own size, so acceptance depends on pressure alone. On three
   seeds it keeps the informative-signal gain (task error 0.0005 vs 0.0354)
   and removes the bias under the control (equal acceptance, task error equal
   to gate-only). The agent's `scale_free` ratio mode does not remove it.
   Caveats: the reference drifts with the proposal mix (a stream dominated by
   large moves raises everyone's credit), and the signal is still simulated.
   Fix established in simulation `[conj]`; whether it survives a real checker
   and a live model is `[open]`.
8. In the ADCCL controller the correction force fires only when the dual
   channel **rejects** a proposal; at zero constraint pressure nothing is
   rejected, so it never fires there. The ablation's `gate_correction` arm
   instead applies the same step whenever the gate clips, which is why that
   arm differs slightly (similarity 0.9593 vs 0.9556).
9. The repository's own adversarial consensus can serve as the constraint
   signal (`benchmarks/run_auditor_signal.py`). With three imperfect rubric
   critics, two findings stand out. First, **unanimous consensus freezes the
   agent**: a critic that knows only the anchor reads progress toward the goal
   as drift and rejects every move, so the panel never admits anything.
   Second, **feeding the votes into the dual channel recovers progress, but
   only with `running_reference` credit and only in a window of the
   votes-to-pressure mapping** (0.1–0.2 per rejecting critic): task error
   0.0050 at 0.1 against 0.0152 frozen and 0.0354 gate-only, on all three
   seeds. Classic credit never beats the frozen agent. The critics are
   hand-written stand-ins for model critics. `[conj]` for this simulation;
   the right pressure mapping for real critics is `[open]`.
   **The window is no longer a bare free parameter**
   (`benchmarks/run_pressure_window.py`). With `running_reference` credit a
   proposal with k rejections is admitted iff L_corr(k·p) ≤ H(x_ref); since
   L_corr is strictly increasing this is k·p ≤ w\* = L_corr⁻¹(x_ref²/2), so
   on-task moves (k_on rejections) pass and drift (k_off) fails exactly when
   w\*/k_off < p ≤ w\*/k_on. That step is algebra on the code's acceptance
   rule, checked at the edges against `DualChannelAction` in
   `tests/test_pressure_window.py` (not machine-checked). The numbers come
   from the simulation `[conj]`: x_ref ≈ 0.143, k_on = 1 (anchor critic),
   k_off = 3, giving w\* ≈ 0.150 and a derived window of about (0.05, 0.15].
   A finer sweep (11 points, 3 seeds, paired bootstrap CIs, plus an
   uninformative control whose critics vote at their measured rates but
   ignore the move) finds `running_reference` beating gate-only, the frozen
   agent and the control on every seed for p from 0.075 to 0.25. The lower
   edge matches the derivation (at 0.05 ≈ w\*/3 about half the drift gets
   through). The upper edge sits above w\* because the running reference is
   higher early in a trial (median peak 0.21, so w\*/1 ≈ 0.22): above 0.15
   only those early on-task moves get in, and the gain fades smoothly to the
   frozen error by 0.3–0.4. **No conclusion changes inside 0.1–0.2**; the
   reported window was conservative on both sides, and the best point on the
   grid (task error 0.0030) is at 0.075, outside it. Classic credit still
   never beats the frozen agent at any grid point. The mapping for real
   critics remains `[open]`: the derivation says it must be re-fit to their
   vote counts and to the momentum scale of real proposals.

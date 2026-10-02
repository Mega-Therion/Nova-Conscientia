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
R.W. Yett, Story, Arkansas). None of their numeric constants are imported into
this runtime.

| System | Repository | Core Mechanism / Formal Invariant | Language Ecosystem |
|---|---|---|---|
| Chyren Aeon | `Mega-Therion/chyren-aeon` | 7-layer polyglot cognition & memory topology | Rust, Python, TS, Qdrant |
| MVPC-X | `Mega-Therion/Chyren` (MVPC) | Standalone formal proof-checking harness (CI claim-verifier: `mvpc.cli verify artifact` over JSON fixture manifests) | Python, JSON fixtures |
| Sovereign Semiotics | `Mega-Therion/RYTT-Sovereign-Semiotics` | Lossless round-trip invariance 𝒟(𝒞(S)) ≡ S (`SovereignSemiotics.lean`, Lean 4-verified) | Lean 4 (+ Rust `rytt-core`) |

## Constant-by-constant register

| constant | value | class | provenance |
|---|---|---|---|
| `MEASURED_TAU` | 0.9539 | measured [E] | ADCCL collapse boundary, Res-Nova ALIGNMENT_CEILING_ONE_RELATION.md (2026-09-06); single pipeline, not externally validated |
| band ceiling κ(0.7) | 0.9539392014… | conditional [C] | √(θ(2−θ)) at θ=7/10; historical record (θ provenance failed audit 2026-09-24) |
| derived ceiling χ_s | 0.9561451575… | conditional [C] | √(√2 − ½) at θ=1/√2; independently derived three ways |
| equipartition floor θ | 1/√2 = cos 45° | derived [P] | RapidityEquipartition.lean (sinh ψ = 1 ⇒ γ = √2, θ = tanh ψ) |
| `ν_std`, `L_e`, far-field factor | — | proved/receipted [E] | qumond_pm.py + QUMOND_PM_GATES.json |
| drift coordinate x = tan α | — | design [D] | Nova Conscientia choice; x = 1 is exactly 45° (ties to equipartition) |
| halt energy, opening angle, cohesion rate, drift gain/noise, seeds, quorum defaults | — | design [D] | engineering parameters of this runtime; registered in each module's `PROVENANCE` mapping and enforced by the AST gate (rule Z2) |

## Verification receipts produced by this repository

| artifact | result |
|---|---|
| `python -m unittest discover -s tests` | 50 tests, 50 passed |
| `python verification/ast_invariant_validation.py core verification benchmarks` | 8 modules, 0 violations (Z1–Z5) |
| `python benchmarks/run_benchmark.py --json benchmarks/results/benchmark_receipt.json` | baseline collapse fraction 1.00 vs swarm 0.00; swarm mean final similarity 0.965; 0 HALTs; deterministic receipt committed |

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

# PROVENANCE — full commit provenance for the Nova Conscientia translation

Per the Contingent Box Protocol: modular, testable machine code with zero
stubs, zero ungrounded numerology, and full commit provenance. This file pins
every source fact the translation depends on.

## Source repositories

| repo | commit | date |
|---|---|---|
| `Mega-Therion/Res-Nova` | `c3ff5f3d01e0b96e28212cf7ce70f1b2f806f04d` | 2026-10-01 |
| `Mega-Therion/Nova-Conscientia` (base) | `9777f2e648e1b8403e548ff0d616b0e06e5e0e36` | 2026-10-02 |

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

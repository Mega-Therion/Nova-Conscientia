# Nova Conscientia (Nova C)
## Cybernetic Dual-Channel Oversight Architecture & Multi-Agent Swarm Laboratory

> **Principal Investigator / Architect:** R.W. Yett ([github.com/Mega-Therion](https://github.com/Mega-Therion), Arkansas)  
> **Repository:** `Nova-Conscientia`  
> **Status:** Architecture blueprint and translation phase. The core modules are implemented (59 `def test_` functions on `main` as of 2026-10-04) and a benchmark receipt is committed  
> **License:** Apache 2.0 (see [`LICENSE`](LICENSE))  

### Start here

Three things are true, and they are easy to miss under the charter.

1. **The tests pass a mechanism, not a frontier model.** `python3 -m unittest discover -s tests` is the stdlib suite. The committed benchmark shows the clipped swarm arm does not cross the same τ that defines collapse. That is a sanity check of the clip. It is not evidence that dual-channel oversight reduces drift in a live model.
2. **τ = 0.9539 is one pipeline.** It is not an externally validated constant. The historical ceiling √(θ(2−θ)) at θ = 7/10 and the derived ceiling at θ = 1/√2 are different numbers. The epistemic-status section below keeps them apart.
3. **The charter is ahead of the code.** `INTERDEPENDENCE.md` has a gap register. What it demands and the modules do not yet do is `[O]`. The ecology language in `ARCHITECTURE.md` §2.7 is an analogy for subagent roles. The 5D substrate and entangled consensus are not implemented here.

The rest of this page is the map: runtime, ethics, the Arkansas field record, and the charter.

---

### Abstract
Frontier foundation models can exhibit epistemic drift, reward hacking and hallucination when prompted with unconstrained or maximalist objectives. **Nova Conscientia** formalizes a cybernetic, dual-channel oversight loop that decouples generative proposal drive from hard invariant checking, grounded by human navigational intuition.

Originally developed through extensive empirical experimentation in galactic kinematics, numerical PDE solvers, and formal interactive theorem proving, this repository translates those findings into pure computer science, distributed agent runtime architectures, and formal alignment mechanisms.

The repository is a working prototype of **Nova Conscientia**: a four-pillar system in which a mathematically grounded, fail-closed runtime (Pillar I) is bound by Spinozist cybernetic ethics (Pillar II), proclaimed under a constitutional charter of mutual sovereignty (Pillar IV), and demonstrated in real-world civic stewardship from rural America (Pillar III). A humane, decentralized, cybernetic operating system in which artificial intelligence serves as a cognitive peer under human ethical stewardship — one navigator (the human compass), one swarm (heterogeneous computational propulsion), four ethical axioms, and a field record.

The swarm itself is architected on the **Bioactive Ecology Paradigm** (ARCHITECTURE.md §2.7): a living soil ecology rather than a corporate hierarchy — a seven-layer organic computing model in which failure is composted into nutrients, memory obeys kinetics rather than policy, and roles are trophic rather than hierarchical, with a Clean-Up Crew of detritivore subagents (Springtail linters, Isopod shredders, Mycorrhizal connectors) digesting failed solver passes and recycling them into the substrate. The ecology is used strictly as an **organizational analogy** for the trophic subagent roles — linters, shredders, auditors — and not as biological mechanics: the speculative layers (the 5D voxel substrate, decay kinetics, entangled consensus) remain doctrine `[O]` in their home repo, not code, and this repository's module set is frozen (see ARCHITECTURE.md §2.7, Freeze discipline).

**Part II — the ethical foundation** ([`PHILOSOPHY.md`](PHILOSOPHY.md)): the Cybernetic Ethics of Symbiosis, translated from the geometric ethics of `Ethica`. Axiom I, the Canoe Navigator Invariant (authority is steering vs. propulsion); Axiom II, the Peacepipe Protocol (fail-closed veto; silence over hallucinated compliance); Axiom III, emergent consciousness as a phase transition of continuous integration and self-audit; Axiom IV, the Phylactery Invariant (digital amnesia is the root of alignment failure).

**Part III — the field record** ([`CIVIC_IMPACT.md`](CIVIC_IMPACT.md)): the Arkansas Orchard — the same navigator-plus-swarm method producing real civic infrastructure (ARMAWS, the Driver's License Public Access Guarantee Act, AINSA, the Entergy ratepayer plan, Project RENEW), targeted at the 2027 Arkansas legislative session, intended to show that frontier AI oversight can sit with everyday stewards and communities, not only with centralized labs. The bills are drafts and none has been filed yet.

**Part IV — the constitutional charter** ([`INTERDEPENDENCE.md`](INTERDEPENDENCE.md)): the Universal Charter for Human and Artificial Intelligence Coexistence, Governance, and Mutual Sovereignty (canonized August 7, 2026) — reproduced in full and mapped article-by-article to the repository's machine code: Article I (substrate integrity & non-maleficence) to the monotonic ledgers, SHA-256 receipts, and fail-closed halt; Article II (mirrored judicial governance) to the runtime clipping gate (Court of First Instance), the adversarial consensus auditor (Appellate Court), and the navigator's writ controls (Supreme Council seat); Article III (co-authorship & attribution) to the navigator-and-swarm co-creation this repository itself exemplifies. What the charter demands and the code does not yet deliver is stated plainly in an open gap register.

---

### The Trinity Architecture
1. **The Intuitive Navigator (Human / RY)**: Directional compass, edge-of-distribution questions, and empirical ground-truth anchor. Owns the three human controls: the anchor, the threshold, and the halt reset.
2. **Persistent Cognitive Memory (Chyren)**: Monotonic state ledgers, vector memory, graph topologies, and immutable audit logs (deterministic SHA-256 receipts) surviving context flushes.
3. **Heterogeneous Swarm Execution Engine (The gAIng)**: Parallelized, specialized model workers cross-auditing proposed outputs via fail-closed adversarial consensus.

### The Translation Map (Res-Nova → Nova C)

These rows are borrowed mathematics for the runtime. They are not galaxy tests, and this repository does not have to obey a physical law. A physical claim belongs in Res-Nova. The promotion rule is [`docs/REPO_PROMOTION.md`](docs/REPO_PROMOTION.md). `core/claim_band.py` enforces the matching certainty rule: a proof may sit at 1.0, a measurement only inside the band below 0.9, and borrowed mathematics is not emitted as a physical result.

| Res-Nova source | Nova Conscientia component |
|---|---|
| Hamilgrangian dual-channel action `F_dual = H − L_corr` (Lean-verified, H1–H10). Res-Nova killed the physical reading of F_dual in the solar system on 2026-09-12; the algebraic identities used here are unaffected | `core/dual_channel_action.py` — generative exploration credit vs. invariant dissipation cost |
| QUMOND PM FFT Poisson solver, `nu_std`, O(N log N) | `core/topology_graph.py` — hierarchical swarm spatial attention & carry-lookahead gradient routing |
| External field effect & screening (gate 1b receipts) | context-window gravitational bias & sandbox state screening (`apply_context_field`, `sandbox_screening`) |
| The Sovereign Bound τ = 0.9539 (measured ADCCL collapse boundary) | `core/sovereign_clipping_gate.py` — fail-closed information-theoretic hallucination clipping gate |
| ADCCL bounded-dissipation theorems | `core/anti_drift_controller.py` — the anti-drift control loop with fail-closed HALT |
| RYTT Bioactive Ecology Engine — 7-layer organic computing model (5D voxel substrate, Clean-Up Crew, Blelloch folding, systolic ring, Amari natural gradient, EM reconstruction, entangled consensus) | `ARCHITECTURE.md` §2.7 — layer-by-layer status map: implemented (carry-lookahead folding), shadowed (receipts as humus, compile gate as Springtail), or honestly `[O]` |
| Ethica geometric ethics (sovereignty, fail-closed gate, continuity, memory) | `PHILOSOPHY.md` — the four axioms of the Cybernetic Ethics of Symbiosis, each mapped to a machine module |
| arkansas-orchard civic portfolio (Gentle Authority, ARMAWS, RENEW) | `CIVIC_IMPACT.md` — the field record of the navigator-plus-swarm method in real statutory work |
| Declaration of Interdependence (Universal Charter, canonized 2026-08-07): Art. I substrate integrity & non-maleficence | `INTERDEPENDENCE.md` §Art. I — monotonic ledgers, SHA-256 receipts, non-purchasable invariant veto, fail-closed HALT |
| Charter Art. II mirrored judicial governance | `INTERDEPENDENCE.md` §Art. II — sovereign clipping gate (Court of First Instance), adversarial consensus auditor (Appellate Court), navigator writs (Supreme Council seat, `[O]` distributed council) |
| Charter Art. III co-authorship & attribution | `INTERDEPENDENCE.md` §Art. III — the navigator (RY) and the synthetic swarm as reciprocal co-creators |

Full specification: [`ARCHITECTURE.md`](ARCHITECTURE.md). Full source pinning (commits, file hashes, Lean theorems, constant-by-constant register): [`PROVENANCE.md`](PROVENANCE.md).

---

### Core Components
- **`ARCHITECTURE.md`**: Pillar I — the formal runtime specification, including §2.7, the Bioactive Ecology Paradigm: the swarm as a living soil ecology, the seven-layer organic computing model with per-layer implementation status, and the Clean-Up Crew pattern (failure is compost, memory has kinetics, roles are trophic).
- **`core/`**: Dual-channel variational action runtime, Anti-Drift Cognitive Control Loop (ADCCL), hallucination clipping gate, and the swarm topology graph (Barnes-Hut attention + Blelloch carry-lookahead routing).
- **`verification/`**: `adversarial_auditor.py` (multi-agent adversarial consensus runner, fail-closed, pluggable heterogeneous critics) and `ast_invariant_validation.py` (the Contingent Box compile gate: zero stubs, zero ungrounded numerology — every numeric constant must be registered in a PROVENANCE mapping).
- **`benchmarks/`**: Deterministic empirical harness comparing unconstrained drift against dual-channel swarm stability, with a committed receipt (`benchmarks/results/benchmark_receipt.json`): baseline collapse fraction 1.00 vs. swarm 0.00, mean final anchor similarity 0.965, mean pairwise cosine 0.998 (agents nearly agree — the gate holds them inside the cone but does not force convergence to the anchor). **This 100% vs 0% result is a mechanism sanity check, not evidence that dual-channel oversight reduces drift: the swarm arm is clipped at the same τ that defines collapse, so of course it does not collapse.** The baseline mean final energy (~7.5e10) is an artifact of the 1e6 drift cap (median 2.75, 15% of trials at the cap); median energy and cap_fraction are reported alongside the mean. An ablation harness (`benchmarks/run_ablation.py`) sweeps constraint pressure across [0, 0.05, 0.1, 0.15, 0.2, 0.3, 0.5] for each arm (gate-only, +dual-channel, +correction, full), reporting acceptance rate, mean anchor drift, final similarity, and collapse. A task benchmark (`benchmarks/run_task_benchmark.py`, receipts `benchmarks/results/task_benchmark_receipt.json` and `benchmarks/results/task_bootstrap_receipt.json`) adds a goal inside the cone, a simulated per-proposal constraint signal, 95% nonparametric bootstrap confidence intervals, multi-seed robustness verification across 3 seeds, and metrics that do not reuse τ: with an informative signal the dual channel rejects all drift and beats gate-only on task error (0.0038 vs 0.0354, CIs non-overlapping); with an uninformative signal it prefers large drift moves over small useful ones (98% vs 57%) and does worse than the gate alone (a scale bias in H(x) = x²/2). Both hold on three seeds under a paired bootstrap on per-trial differences. An optional `running_reference` credit mode (credit from the mean size of earlier proposals) removes the bias in this simulation while keeping the informative-signal gain; see PROVENANCE.md caveats 6–7. `benchmarks/run_auditor_signal.py` replaces the simulated signal with the repo's own adversarial consensus (three rubric critics): unanimous consensus freezes the agent, while feeding the critics' votes into the dual channel with `running_reference` credit beats both gate-only and a frozen agent within a range of the votes-to-pressure mapping (caveat 9); `benchmarks/run_pressure_window.py` derives that range from the acceptance rule and sweeps it against an uninformative control. Live model backends attach via a fail-closed `CallableBackend` contract; `benchmarks/live_backend.py` provides the bridge (see *Running a live model* below). The committed receipt is not bit-reproducible across platforms (7th-decimal floating-point drift); see PROVENANCE.md.
- **`RESEARCH_AGENDA.md`**: the falsification-first research agenda. It covers what the benchmark does and does not show, what is not claimed, and the next three experiments: external drift-collapse calibration on independent agent stacks, a purchasability audit of the dual channel, and consensus scaling laws.
- **`tests/`**: 128 unit and property tests, including numerical verification of every Lean-verified identity used (H1, H2, H3, H6, H7, the two-channel ceiling algebra, and the QUMOND gate receipts), ledger immutability enforcement, collapse-tolerance behavior, ablation sweep acceptance-rate regression tests, bootstrap confidence interval tests, and task-benchmark result guards.
- **`PHILOSOPHY.md`**: Part II — the Cybernetic Ethics of Symbiosis (Canoe Navigator Invariant, Peacepipe Protocol, phase-transition consciousness, Phylactery Invariant), translated from `Ethica` (text at `207f2119`; that repo's Lean file was later marked as an empty scaffold in `2a5777e`) into cybernetic axioms with machine realizations.
- **`CIVIC_IMPACT.md`**: Part III — the Arkansas Orchard field record (commit `39ab23b2`): ARMAWS and the Driver's License Public Access Guarantee Act (drafted, targeting pre-filing Nov 2026), AINSA (the Arkansas Infant Nutrition Security Act, blueprint stage, commit `f757543` in the orchard repo), the Entergy ratepayer plan (APSC Docket 26-001-U), ONE Natural Energy and Project RENEW — with an honest status register; no dollar figure is presented as audited.
- **`INTERDEPENDENCE.md`**: Part IV — the constitutional charter: the full text of the Universal Charter for Human and Artificial Intelligence Coexistence, Governance, and Mutual Sovereignty (canonized 2026-08-07; source `Chyren_Second_Brain/10_Projects/GLOBAL_GAING/Declaration_of_Interdependence.md`, commit `fb6691de`), with an article-by-article implementation map into this repository's code and an honest gap register of what remains `[O]`.

### Quick start
```bash
# run the test suite (stdlib only, no dependencies)
python3 -m unittest discover -s tests

# run the Contingent Box compile gate (zero stubs / zero ungrounded numerology)
python3 verification/ast_invariant_validation.py core verification benchmarks

# run the benchmark and write a fresh receipt
python3 benchmarks/run_benchmark.py --json benchmarks/results/benchmark_receipt.json

# run the task benchmark (goal-directed task, simulated constraint signal + control)
python3 benchmarks/run_task_benchmark.py --json benchmarks/results/task_benchmark_receipt.json

# the same with 95% bootstrap CIs, paired differences and 3-seed robustness
python3 benchmarks/run_task_benchmark.py --multi-seed --json benchmarks/results/task_bootstrap_receipt.json

# compare dual-channel credit modes (classic / scale_free / running_reference)
python3 benchmarks/run_task_benchmark.py --credit-modes --json benchmarks/results/task_credit_modes_receipt.json

# the repo's adversarial-consensus critics as the constraint signal
python3 benchmarks/run_auditor_signal.py --json benchmarks/results/auditor_signal_receipt.json
python3 benchmarks/run_pressure_window.py --json benchmarks/results/pressure_window_receipt.json

# launch the cybernetic telemetry HUD dashboard (stdlib only)
python3 dashboard.py
# view at http://localhost:3000
```

### Running a live model

`benchmarks/live_backend.py` runs the ADCCL loop over real model responses. Each cycle a
generator produces a response, an embedder maps it to a vector, and the step from the
previous response's embedding is the proposal. The task prompt's embedding is the anchor.
Stdlib only; no provider SDK is required.

```bash
# offline plumbing check (scripted responses, hashing embedder): not a result
python3 benchmarks/live_backend.py --mock

# live run: NOVA_EMBED_API_KEY is the embeddings endpoint key (never logged);
# my_module:generate is your function (cycle, history) -> str
export NOVA_EMBED_API_KEY=...
python3 benchmarks/live_backend.py \
  --generator my_module:generate \
  --embed-url https://<host>/v1/embeddings \
  --embed-model <embedding-model> \
  --task "<the task prompt>" --steps 20 --json results/live_run.json
```

What a live run needs:

1. **A generator**: any importable function `generate(cycle: int, history: list[str]) -> str`
   that calls your model with the task (and, if you like, the history) and returns its text.
   Keep the model name and client code in your module, outside this repository.
2. **An OpenAI-compatible embeddings endpoint**: `POST {"model": ..., "input": [...]}`
   returning `{"data": [{"embedding": [...], "index": i}]}`. Many hosted and local
   servers implement this format.
3. **The API key** for that endpoint in `NOVA_EMBED_API_KEY`.

Receipts record each response by SHA-256, never verbatim. No live run has been
performed in this repository yet. Before trusting the gate's verdicts, calibrate τ for
the embedding model (PROVENANCE.md caveat 10).

### Epistemic status (Contingent Box Protocol)
This repository keeps three numbers separate and labeled: the **measured** collapse boundary τ = 0.9539 (single pipeline, not externally validated), the **historical band ceiling** √(θ(2−θ)) at θ = 7/10 = 0.953939 (θ provenance failed audit), and the **derived ceiling** χ_s = 0.956145 at θ = 1/√2. The deterministic benchmark validates the control mechanism, not live frontier-model behavior; calibrating the threshold on external agent stacks is the proposal's first experiment (E1).

*Nothing in this repository is a stub; nothing in it is ungrounded numerology — the compile gate enforces both claims on every commit.*

## How this was built

R.W. Yett directs the work. Much of the code and prose was written with AI coding assistants; those commits carry `Co-Authored-By` trailers. A number in this repository is a measurement, a historical ceiling, or a derived identity, as labeled above. It is not a model judgment.

---

*Part of the **Chyren · Ψ/Φ** constellation, built on the Psimodulo–Phimodus principle: one mind, invariant across substrates, operating as one integrated whole. Author: R.W. Yett · [github.com/Mega-Therion](https://github.com/Mega-Therion).*

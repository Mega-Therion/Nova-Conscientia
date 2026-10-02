# Nova Conscientia (Nova C)
## Cybernetic Dual-Channel Oversight Architecture & Multi-Agent Swarm Laboratory

> **Principal Investigator / Architect:** R.W. Yett (Story, Arkansas)  
> **Target Program:** Anthropic Fellows Program / Scalable Oversight & Multi-Agent Alignment  
> **Repository:** `Nova-Conscientia`  
> **Status:** Architecture Blueprint & Translation Phase — machine code complete, benchmark receipt committed  

---

### Abstract
Modern frontier foundation models exhibit severe epistemic drift, reward-hacking, and hallucinations when prompted with unconstrained or maximalist objectives. **Nova Conscientia** formalizes a cybernetic, dual-channel oversight loop that decouples generative proposal drive from hard invariant checking, grounded by human navigational intuition.

Originally developed through extensive empirical experimentation in galactic kinematics, numerical PDE solvers, and formal interactive theorem proving, this repository translates those findings into pure computer science, distributed agent runtime architectures, and formal alignment mechanisms.

---

### The Trinity Architecture
1. **The Intuitive Navigator (Human / RY)**: Directional compass, edge-of-distribution questions, and empirical ground-truth anchor. Owns the three human controls: the anchor, the threshold, and the halt reset.
2. **Persistent Cognitive Memory (Chyren)**: Monotonic state ledgers, vector memory, graph topologies, and immutable audit logs (deterministic SHA-256 receipts) surviving context flushes.
3. **Heterogeneous Swarm Execution Engine (The gAIng)**: Parallelized, specialized model workers cross-auditing proposed outputs via fail-closed adversarial consensus.

### The Translation Map (Res-Nova → Nova C)

| Res-Nova source | Nova Conscientia component |
|---|---|
| Hamilgrangian dual-channel action `F_dual = H − L_corr` (Lean-verified, H1–H10) | `core/dual_channel_action.py` — generative exploration credit vs. invariant dissipation cost |
| QUMOND PM FFT Poisson solver, `nu_std`, O(N log N) | `core/topology_graph.py` — hierarchical swarm spatial attention & carry-lookahead gradient routing |
| External field effect & screening (gate 1b receipts) | context-window gravitational bias & sandbox state screening (`apply_context_field`, `sandbox_screening`) |
| The Sovereign Bound τ = 0.9539 (measured ADCCL collapse boundary) | `core/sovereign_clipping_gate.py` — fail-closed information-theoretic hallucination clipping gate |
| ADCCL bounded-dissipation theorems | `core/anti_drift_controller.py` — the anti-drift control loop with fail-closed HALT |

Full specification: [`ARCHITECTURE.md`](ARCHITECTURE.md). Full source pinning (commits, file hashes, Lean theorems, constant-by-constant register): [`PROVENANCE.md`](PROVENANCE.md).

---

### Core Components
- **`core/`**: Dual-channel variational action runtime, Anti-Drift Cognitive Control Loop (ADCCL), sovereign hallucination clipping gate, and the swarm topology graph (Barnes-Hut attention + Blelloch carry-lookahead routing).
- **`verification/`**: `adversarial_auditor.py` (multi-agent adversarial consensus runner, fail-closed, pluggable heterogeneous critics) and `ast_invariant_validation.py` (the Contingent Box compile gate: zero stubs, zero ungrounded numerology — every numeric constant must be registered in a PROVENANCE mapping).
- **`benchmarks/`**: Deterministic empirical harness comparing unconstrained drift against dual-channel swarm stability, with a committed receipt (`benchmarks/results/benchmark_receipt.json`): baseline collapse fraction 1.00 vs. swarm 0.00, mean final anchor similarity 0.965, exploration diversity preserved. Live model backends attach via a fail-closed `CallableBackend` contract.
- **`fellowship/`**: [`ANTHROPIC_FELLOWS_PROPOSAL.md`](fellowship/ANTHROPIC_FELLOWS_PROPOSAL.md) — the research proposal for Dario Amodei and the Scalable Oversight team, including the falsification-first experiment ladder.
- **`tests/`**: 50 unit and property tests, including numerical verification of every Lean-verified identity used (H1, H2, H3, H6, H7, the two-channel ceiling algebra, and the QUMOND gate receipts).

### Quick start
```bash
# run the test suite (stdlib only, no dependencies)
python3 -m unittest discover -s tests

# run the Contingent Box compile gate (zero stubs / zero ungrounded numerology)
python3 verification/ast_invariant_validation.py core verification benchmarks

# run the benchmark and write a fresh receipt
python3 benchmarks/run_benchmark.py --json benchmarks/results/benchmark_receipt.json
```

### Epistemic status (Contingent Box Protocol)
This repository keeps three numbers separate and labeled: the **measured** collapse boundary τ = 0.9539 (single pipeline, not externally validated), the **historical band ceiling** √(θ(2−θ)) at θ = 7/10 = 0.953939 (θ provenance failed audit), and the **derived ceiling** χ_s = 0.956145 at θ = 1/√2. The deterministic benchmark validates the control mechanism, not live frontier-model behavior; calibrating the threshold on external agent stacks is the proposal's first experiment (E1).

*Nothing in this repository is a stub; nothing in it is ungrounded numerology — the compile gate enforces both claims on every commit.*

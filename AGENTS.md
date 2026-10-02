# Base44 Dev Environment — Nova Conscientia

## Project Overview
Nova Conscientia is a pure-Python research project (AI alignment architecture).
No third-party dependencies — Python stdlib only. No web frontend originally;
a lightweight dashboard (`dashboard.py`) was added for the preview.

## Running the App
```bash
docker compose -f docker-compose.base44.yml up -d
```
Serves a web dashboard on port 3000 using Python's built-in `http.server`.

## Architecture
- `dashboard.py` — stdlib-only web server serving the project dashboard on :3000
- `dashboard_page.py` — HTML/CSS/JS rendering for the dashboard (imported by dashboard.py)
- `core/` — dual-channel action, anti-drift controller, sovereign clipping gate, topology graph
- `verification/` — adversarial auditor, AST invariant validation (Contingent Box gate)
- `benchmarks/` — drift model, benchmark, ablation, task benchmark, auditor-signal benchmark and the live-model bridge, with JSON receipts
- `tests/` — 103 unittest tests (all pass, stdlib only)

## Verification
- **Tests:** `python3 -m unittest discover -s tests -v` (103 tests, ~5s)
- **Contingent Box gate:** `python3 verification/ast_invariant_validation.py` (checks 12 modules, 0 violations)
- **Benchmark:** `python3 benchmarks/run_benchmark.py --json benchmarks/results/benchmark_receipt.json`
- **Task benchmark:** `python3 benchmarks/run_task_benchmark.py --json benchmarks/results/task_benchmark_receipt.json` (add `--multi-seed` for paired CIs over 3 seeds, `--credit-modes` to compare credit modes)
- **Auditor signal:** `python3 benchmarks/run_auditor_signal.py --json benchmarks/results/auditor_signal_receipt.json`
- **Live backend (offline check):** `python3 benchmarks/live_backend.py --mock` (live runs need a generator, an embeddings endpoint and `NOVA_EMBED_API_KEY`; see README)
- **Ablation:** `python3 benchmarks/run_ablation.py --json benchmarks/results/ablation_receipt.json` (sweep over constraint pressures [0, 0.05, 0.1, 0.15, 0.2, 0.3, 0.5])
- **Dashboard API:** `/api/receipt` (read-only; subprocess-spawning endpoints removed)

## Key Facts
- Python 3.12 (slim Docker image); CI (`.github/workflows/ci.yml`) runs the tests, the gate and the benchmark-receipt check on every PR
- No secrets needed for anything except an optional live-model run (`NOVA_EMBED_API_KEY`, see README)
- No database, no cache, no external services
- The dashboard is a static page; only `/api/receipt` is served (read-only)
- Committed receipts in `benchmarks/results/`: `benchmark_receipt.json`, `ablation_receipt.json`, `task_benchmark_receipt.json`, `task_bootstrap_receipt.json`, `task_credit_modes_receipt.json`, `auditor_signal_receipt.json`
- Swarm agreement metric: `mean_pairwise_cosine` in receipts (`pairwise_cosine` per trial); it was `mean_swarm_diversity`, which misdescribed it
- `GateLedger.entries` and `ADCCLController.ledger` are read-only tuples (append-only enforced)
- Epistemic tags: PROVENANCE.md's constant register uses `[E]/[C]/[D]/[P]`; claims elsewhere use `[thm]/[emp]/[conj]/[open]`. Never upgrade a tag; simulated results are at most `[conj]`

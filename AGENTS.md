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
- `benchmarks/` — drift model + benchmark harness + ablation harness + task benchmark with JSON receipts
- `tests/` — 72 unittest tests (all pass, stdlib only)

## Verification
- **Tests:** `python3 -m unittest discover -s tests -v` (72 tests, ~2s)
- **Contingent Box gate:** `python3 verification/ast_invariant_validation.py` (checks 10 modules, 0 violations)
- **Benchmark:** `python3 benchmarks/run_benchmark.py --json benchmarks/results/benchmark_receipt.json`
- **Task benchmark:** `python3 benchmarks/run_task_benchmark.py --json benchmarks/results/task_benchmark_receipt.json`
- **Ablation:** `python3 benchmarks/run_ablation.py --json benchmarks/results/ablation_receipt.json` (sweep over constraint pressures [0, 0.05, 0.1, 0.15, 0.2, 0.3, 0.5])
- **Dashboard API:** `/api/receipt` (read-only; subprocess-spawning endpoints removed)

## Key Facts
- Python 3.12 (slim Docker image)
- No external secrets or credentials needed
- No database, no cache, no external services
- The dashboard is a static page; only `/api/receipt` is served (read-only)
- Benchmark receipt is committed at `benchmarks/results/benchmark_receipt.json`
- Ablation receipt is at `benchmarks/results/ablation_receipt.json`
- The diversity metric is renamed `mean_pairwise_cosine` (was `mean_swarm_diversity`)
- GateLedger.entries is now an immutable tuple property (append-only enforced)

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
- `core/` — dual-channel action, anti-drift controller, sovereign clipping gate, topology graph
- `verification/` — adversarial auditor, AST invariant validation (Contingent Box gate)
- `benchmarks/` — drift model + benchmark harness with JSON receipts
- `tests/` — 50 unittest tests (all pass, stdlib only)

## Verification
- **Tests:** `python3 -m unittest discover -s tests -v` (50 tests, ~1.5s)
- **Contingent Box gate:** `python3 verification/ast_invariant_validation.py` (checks 8 modules, 0 violations)
- **Benchmark:** `python3 benchmarks/run_benchmark.py --json benchmarks/results/benchmark_receipt.json`
- **Dashboard API:** `/api/tests`, `/api/gate`, `/api/benchmark`, `/api/receipt`

## Key Facts
- Python 3.12 (slim Docker image)
- No external secrets or credentials needed
- No database, no cache, no external services
- The dashboard runs tests/benchmarks as subprocesses on demand
- Benchmark receipt is committed at `benchmarks/results/benchmark_receipt.json`

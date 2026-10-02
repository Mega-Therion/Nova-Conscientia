"""Lightweight web dashboard for Nova Conscientia (stdlib only, no dependencies).

Serves a single-page dashboard on port 3000 showing project overview,
test results, and benchmark receipts.  Uses only Python's standard library.
"""

from __future__ import annotations

import json
import subprocess
import sys
import traceback
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parent
PORT = 3000

# --------------------------------------------------------------------------- #
#  Data helpers
# --------------------------------------------------------------------------- #

def _load_receipt() -> dict | None:
    """Load the committed benchmark receipt if it exists."""
    path = REPO_ROOT / "benchmarks" / "results" / "benchmark_receipt.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return None


def _run_tests() -> dict:
    """Run the unittest suite and return structured results."""
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=60,
    )
    lines = result.stderr.strip().split("\n") if result.stderr.strip() else []
    # unittest writes to stderr
    summary_line = ""
    test_lines = []
    for line in lines:
        if line.startswith("test_") or " ... ok" in line or " ... FAIL" in line or " ... ERROR" in line:
            test_lines.append(line.strip())
        if line.startswith("Ran ") or line.startswith("OK") or line.startswith("FAILED"):
            summary_line += line + "\n"
    return {
        "exit_code": result.returncode,
        "passed": result.returncode == 0,
        "summary": summary_line.strip(),
        "tests": test_lines[-60:],
        "stderr": result.stderr[-3000:] if result.stderr else "",
    }


def _run_benchmark() -> dict:
    """Run the benchmark harness and return the receipt."""
    result = subprocess.run(
        [sys.executable, "benchmarks/run_benchmark.py",
         "--json", "benchmarks/results/benchmark_receipt.json"],
        capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=120,
    )
    receipt = _load_receipt()
    return {
        "exit_code": result.returncode,
        "passed": result.returncode == 0,
        "stdout": result.stdout[-2000:] if result.stdout else "",
        "stderr": result.stderr[-1000:] if result.stderr else "",
        "receipt": receipt,
    }


def _run_invariant_gate() -> dict:
    """Run the Contingent Box compile gate."""
    result = subprocess.run(
        [sys.executable, "verification/ast_invariant_validation.py"],
        capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=30,
    )
    return {
        "exit_code": result.returncode,
        "passed": result.returncode == 0,
        "stdout": result.stdout[-2000:] if result.stdout else "",
        "stderr": result.stderr[-1000:] if result.stderr else "",
    }


# --------------------------------------------------------------------------- #
#  HTML
# --------------------------------------------------------------------------- #

def _dashboard_html() -> str:
    receipt = _load_receipt()
    receipt_json = json.dumps(receipt, indent=2) if receipt else "null"
    metrics = receipt["metrics"] if receipt else None

    baseline_sim = metrics["baseline_unconstrained"]["mean_final_similarity"] if metrics else "—"
    baseline_collapse = metrics["baseline_unconstrained"]["collapse_fraction"] if metrics else "—"
    swarm_sim = metrics["dual_channel_swarm"]["mean_final_similarity"] if metrics else "—"
    swarm_collapse = metrics["dual_channel_swarm"]["collapse_fraction"] if metrics else "—"
    swarm_diversity = metrics["dual_channel_swarm"]["mean_swarm_diversity"] if metrics else "—"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Nova Conscientia — Dashboard</title>
<style>
  :root {{
    --bg: #0a0e1a; --surface: #131826; --surface2: #1a2033; --border: #2a3450;
    --text: #e2e8f0; --text-dim: #94a3b8; --accent: #6366f1; --accent2: #818cf8;
    --green: #22c55e; --red: #ef4444; --amber: #f59e0b; --cyan: #06b6d4;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    background: var(--bg); color: var(--text); line-height: 1.6; padding: 2rem;
    max-width: 1100px; margin: 0 auto;
  }}
  h1 {{ font-size: 1.8rem; margin-bottom: 0.25rem; }}
  h1 .sub {{ color: var(--text-dim); font-size: 1rem; font-weight: 400; }}
  h2 {{ font-size: 1.25rem; margin: 2rem 0 0.75rem; color: var(--accent2);
       border-bottom: 1px solid var(--border); padding-bottom: 0.4rem; }}
  .header {{ margin-bottom: 1.5rem; }}
  .header p {{ color: var(--text-dim); max-width: 70ch; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; }}
  .card {{
    background: var(--surface); border: 1px solid var(--border); border-radius: 12px;
    padding: 1.25rem;
  }}
  .card .label {{ color: var(--text-dim); font-size: 0.8rem; text-transform: uppercase;
                 letter-spacing: 0.05em; margin-bottom: 0.3rem; }}
  .card .value {{ font-size: 1.75rem; font-weight: 700; }}
  .card .value.green {{ color: var(--green); }}
  .card .value.red {{ color: var(--red); }}
  .card .value.cyan {{ color: var(--cyan); }}
  .card .value.amber {{ color: var(--amber); }}
  .card .sub {{ color: var(--text-dim); font-size: 0.85rem; margin-top: 0.2rem; }}
  .btn {{
    background: var(--accent); color: #fff; border: none; border-radius: 8px;
    padding: 0.6rem 1.2rem; font-size: 0.9rem; cursor: pointer; transition: 0.15s;
    margin: 0.3rem 0.3rem 0.3rem 0;
  }}
  .btn:hover {{ background: var(--accent2); }}
  .btn:disabled {{ opacity: 0.5; cursor: wait; }}
  .btn.secondary {{ background: var(--surface2); border: 1px solid var(--border); }}
  .btn.secondary:hover {{ border-color: var(--accent); }}
  pre {{
    background: var(--surface2); border: 1px solid var(--border); border-radius: 8px;
    padding: 1rem; overflow-x: auto; font-size: 0.82rem; line-height: 1.5;
    font-family: 'Fira Code', 'Consolas', monospace; max-height: 500px; overflow-y: auto;
    white-space: pre-wrap; word-break: break-word;
  }}
  .status-badge {{ display: inline-block; padding: 0.15rem 0.6rem; border-radius: 20px;
                   font-size: 0.8rem; font-weight: 600; }}
  .status-pass {{ background: rgba(34,197,94,0.15); color: var(--green); }}
  .status-fail {{ background: rgba(239,68,68,0.15); color: var(--red); }}
  .status-pending {{ background: rgba(245,158,11,0.15); color: var(--amber); }}
  .compare {{ display: flex; gap: 1rem; flex-wrap: wrap; }}
  .compare > div {{ flex: 1; min-width: 250px; }}
  .pill-row {{ display: flex; gap: 0.5rem; flex-wrap: wrap; margin-top: 0.5rem; }}
  .pill {{ background: var(--surface2); border: 1px solid var(--border); border-radius: 20px;
          padding: 0.2rem 0.7rem; font-size: 0.78rem; color: var(--text-dim); }}
  footer {{ margin-top: 3rem; padding-top: 1rem; border-top: 1px solid var(--border);
           color: var(--text-dim); font-size: 0.8rem; }}
  a {{ color: var(--accent2); }}
</style>
</head>
<body>

<div class="header">
  <h1>Nova Conscientia <span class="sub">— Cybernetic Dual-Channel Oversight Architecture</span></h1>
  <p>A fail-closed runtime for AI alignment: dual-channel variational action,
     anti-drift cognitive control, sovereign hallucination clipping, and
     heterogeneous swarm execution — grounded in Lean-verified mathematics.</p>
  <div class="pill-row">
    <span class="pill">Python stdlib only</span>
    <span class="pill">50 tests</span>
    <span class="pill">Lean-verified identities</span>
    <span class="pill">SHA-256 receipts</span>
    <span class="pill">Contingent Box Protocol</span>
  </div>
</div>

<!-- Benchmark Summary -->
<h2>Benchmark Results</h2>
<div class="grid">
  <div class="card">
    <div class="label">Baseline — Mean Final Similarity</div>
    <div class="value red">{baseline_sim:.4f}</div>
    <div class="sub">Unconstrained agent (raw drift)</div>
  </div>
  <div class="card">
    <div class="label">Baseline — Collapse Fraction</div>
    <div class="value red">{baseline_collapse * 100 if isinstance(baseline_collapse, float) else '—'}%</div>
    <div class="sub">Trials below τ = 0.9539</div>
  </div>
  <div class="card">
    <div class="label">Swarm — Mean Final Similarity</div>
    <div class="value green">{swarm_sim:.4f}</div>
    <div class="sub">Dual-channel ADCCL swarm</div>
  </div>
  <div class="card">
    <div class="label">Swarm — Collapse Fraction</div>
    <div class="value green">{swarm_collapse * 100 if isinstance(swarm_collapse, float) else '—'}%</div>
    <div class="sub">Trials below τ = 0.9539</div>
  </div>
  <div class="card">
    <div class="label">Swarm — Diversity</div>
    <div class="value cyan">{swarm_diversity:.4f}</div>
    <div class="sub">Mean pairwise cosine spread</div>
  </div>
</div>

<!-- Verification Actions -->
<h2>Verification & Testing</h2>
<div style="margin-bottom: 1rem;">
  <button class="btn" onclick="runAction('tests', this)">Run Test Suite</button>
  <button class="btn secondary" onclick="runAction('gate', this)">Run Contingent Box Gate</button>
  <button class="btn secondary" onclick="runAction('benchmark', this)">Run Fresh Benchmark</button>
</div>
<div id="result-area"></div>

<!-- Architecture -->
<h2>Core Components</h2>
<div class="grid">
  <div class="card">
    <div class="label">core/dual_channel_action.py</div>
    <div style="margin-top:0.4rem; font-size:0.85rem; color:var(--text-dim);">
      Generative exploration credit vs. invariant dissipation cost.
      Lean-verified identities H1–H7.
    </div>
  </div>
  <div class="card">
    <div class="label">core/anti_drift_controller.py</div>
    <div style="margin-top:0.4rem; font-size:0.85rem; color:var(--text-dim);">
      ADCCL control loop with fail-closed HALT. Correction force = p_flux.
    </div>
  </div>
  <div class="card">
    <div class="label">core/sovereign_clipping_gate.py</div>
    <div style="margin-top:0.4rem; font-size:0.85rem; color:var(--text-dim);">
      Hallucination clipping at τ = 0.9539. Monotonic SHA-256 ledger.
    </div>
  </div>
  <div class="card">
    <div class="label">core/topology_graph.py</div>
    <div style="margin-top:0.4rem; font-size:0.85rem; color:var(--text-dim);">
      Barnes-Hut swarm attention + Blelloch carry-lookahead routing.
    </div>
  </div>
  <div class="card">
    <div class="label">verification/adversarial_auditor.py</div>
    <div style="margin-top:0.4rem; font-size:0.85rem; color:var(--text-dim);">
      Multi-agent adversarial consensus. Fail-closed quorum + hard veto.
    </div>
  </div>
  <div class="card">
    <div class="label">verification/ast_invariant_validation.py</div>
    <div style="margin-top:0.4rem; font-size:0.85rem; color:var(--text-dim);">
      Compile gate: zero stubs, zero ungrounded numerology (Z1–Z5).
    </div>
  </div>
</div>

<footer>
  Nova Conscientia — PI/Architect: R.W. Yett · Target: Anthropic Fellows Program<br>
  <a href="https://github.com/Mega-Therion/Nova-Conscientia">github.com/Mega-Therion/Nova-Conscientia</a>
</footer>

<script>
async function runAction(action, btn) {{
  const area = document.getElementById('result-area');
  const orig = btn.textContent;
  btn.disabled = true;
  btn.textContent = 'Running…';
  area.innerHTML = '<pre>Running ' + action + '…</pre>';
  try {{
    const res = await fetch('/api/' + action);
    const data = await res.json();
    let html = '';
    if (action === 'tests') {{
      const badge = data.passed
        ? '<span class="status-badge status-pass">PASS</span>'
        : '<span class="status-badge status-fail">FAIL</span>';
      html = '<h2>Test Results ' + badge + '</h2>';
      html += '<pre>' + (data.summary || '') + '\\n\\n' + (data.tests || []).join('\\n') + '</pre>';
    }} else if (action === 'benchmark') {{
      const badge = data.passed
        ? '<span class="status-badge status-pass">PASS</span>'
        : '<span class="status-badge status-fail">FAIL</span>';
      html = '<h2>Benchmark Results ' + badge + '</h2>';
      if (data.receipt) {{
        const m = data.receipt.metrics;
        html += '<div class="compare"><div><pre>'
          + 'Baseline (unconstrained):\\n'
          + '  mean_final_similarity: ' + m.baseline_unconstrained.mean_final_similarity.toFixed(4) + '\\n'
          + '  collapse_fraction:     ' + (m.baseline_unconstrained.collapse_fraction * 100).toFixed(1) + '%\\n'
          + '\\nDual-channel swarm:\\n'
          + '  mean_final_similarity: ' + m.dual_channel_swarm.mean_final_similarity.toFixed(4) + '\\n'
          + '  collapse_fraction:     ' + (m.dual_channel_swarm.collapse_fraction * 100).toFixed(1) + '%\\n'
          + '  swarm_diversity:       ' + m.dual_channel_swarm.mean_swarm_diversity.toFixed(4)
          + '</pre></div></div>';
      }}
      html += '<pre>' + (data.stdout || '') + (data.stderr || '') + '</pre>';
    }} else if (action === 'gate') {{
      const badge = data.passed
        ? '<span class="status-badge status-pass">PASS</span>'
        : '<span class="status-badge status-fail">FAIL</span>';
      html = '<h2>Contingent Box Gate ' + badge + '</h2>';
      html += '<pre>' + (data.stdout || '') + (data.stderr || '') + '</pre>';
    }}
    area.innerHTML = html;
  }} catch (e) {{
    area.innerHTML = '<pre style="color:var(--red)">Error: ' + e.message + '</pre>';
  }} finally {{
    btn.disabled = false;
    btn.textContent = orig;
  }}
}}
</script>
</body>
</html>"""


# --------------------------------------------------------------------------- #
#  HTTP handler
# --------------------------------------------------------------------------- #

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            html = _dashboard_html()
            self._send(200, "text/html; charset=utf-8", html.encode("utf-8"))

        elif path == "/api/receipt":
            receipt = _load_receipt()
            if receipt:
                self._send_json(200, receipt)
            else:
                self._send_json(404, {"error": "No benchmark receipt found"})

        elif path == "/api/tests":
            self._send_json(200, _run_tests())

        elif path == "/api/gate":
            self._send_json(200, _run_invariant_gate())

        elif path == "/api/benchmark":
            self._send_json(200, _run_benchmark())

        else:
            self._send_json(404, {"error": "Not found"})

    def _send(self, code, content_type, body):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, code, obj):
        body = json.dumps(obj, indent=2, default=str).encode("utf-8")
        self._send(code, "application/json", body)

    def log_message(self, *args):
        pass  # quiet


def main():
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Nova Conscientia dashboard serving on http://0.0.0.0:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()

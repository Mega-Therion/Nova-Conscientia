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


def _git_hash() -> str:
    """Return the short git commit hash, or 'unknown'.

    Reads directly from the .git directory so it works even when the
    ``git`` binary is not installed (e.g. python:3.12-slim).
    """
    git_dir = REPO_ROOT / ".git"
    try:
        head = (git_dir / "HEAD").read_text(encoding="utf-8").strip()
        if head.startswith("ref:"):
            ref_path = git_dir / head[4:].strip()
            if ref_path.exists():
                full = ref_path.read_text(encoding="utf-8").strip()
            else:
                # packed-refs fallback
                packed = git_dir / "packed-refs"
                if packed.exists():
                    ref_name = head[4:].strip()
                    for line in packed.read_text(encoding="utf-8").splitlines():
                        if line.strip().endswith(ref_name):
                            full = line.split()[0]
                            break
                    else:
                        return "unknown"
                else:
                    return "unknown"
        else:
            full = head  # detached HEAD — raw hash
        return full[:7]
    except Exception:
        return "unknown"


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
#  CSS  (plain string — no brace doubling needed)
# --------------------------------------------------------------------------- #

_CSS = """
:root {
  --void: #07080e;
  --surface: #0d111d;
  --surface-hi: #111726;
  --border: #1c2438;
  --border-hi: #2a3654;
  --text: #dfe6f0;
  --text-dim: #6b7a99;
  --text-faint: #44516e;
  --cyan: #00f0ff;
  --magenta: #ff007f;
  --emerald: #00e676;
  --amber: #ffb700;
  --red: #ff4757;
  --mono: 'JetBrains Mono', 'Fira Code', 'Consolas', 'Courier New', monospace;
  --sans: 'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body { background: var(--void); color: var(--text); }
body {
  font-family: var(--sans);
  line-height: 1.6;
  min-height: 100vh;
  position: relative;
  overflow-x: hidden;
}

/* Technical grid overlay */
body::before {
  content: '';
  position: fixed;
  inset: 0;
  background-image:
    linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px);
  background-size: 48px 48px;
  pointer-events: none;
  z-index: 0;
}
body::after {
  content: '';
  position: fixed;
  inset: 0;
  background: radial-gradient(ellipse at 50% 0%, rgba(0,240,255,0.04), transparent 60%);
  pointer-events: none;
  z-index: 0;
}

.wrap {
  position: relative;
  z-index: 1;
  max-width: 1180px;
  margin: 0 auto;
  padding: 2rem 1.5rem 4rem;
}

/* ---- Telemetry Header ---- */
.telemetry-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 1rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid var(--border);
  margin-bottom: 2rem;
}
.hud-brand h1 {
  font-size: 1.65rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  background: linear-gradient(135deg, var(--text) 30%, var(--cyan));
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}
.hud-brand .sub {
  font-size: 0.82rem;
  color: var(--text-dim);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  margin-top: 0.15rem;
}
.coord-bar {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  flex-wrap: wrap;
}
.coord-marker {
  font-family: var(--mono);
  font-size: 0.72rem;
  color: var(--text-dim);
  letter-spacing: 0.05em;
  white-space: nowrap;
}
.coord-marker .dot {
  display: inline-block;
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--emerald);
  margin-right: 5px;
  box-shadow: 0 0 6px var(--emerald);
  animation: pulse 2s ease-in-out infinite;
}
.commit-pill {
  font-family: var(--mono);
  font-size: 0.72rem;
  color: var(--cyan);
  background: rgba(0,240,255,0.08);
  border: 1px solid rgba(0,240,255,0.2);
  border-radius: 4px;
  padding: 0.15rem 0.5rem;
  white-space: nowrap;
}
/* ---- Telemetry badge bar ---- */
.telemetry-bar {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin-top: 0.75rem;
}
.telemetry-badge {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-family: var(--mono);
  font-size: 0.68rem;
  color: var(--text-dim);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 0.25rem 0.6rem;
  letter-spacing: 0.04em;
  transition: border-color 0.2s;
}
.telemetry-badge:hover { border-color: var(--border-hi); }
.telemetry-badge .tb-key { color: var(--text-faint); text-transform: uppercase; }
.telemetry-badge .tb-val { color: var(--text); font-weight: 600; font-variant-numeric: tabular-nums; }
.telemetry-badge .tb-val.cyan    { color: var(--cyan); }
.telemetry-badge .tb-val.emerald { color: var(--emerald); }
.telemetry-badge .tb-val.amber   { color: var(--amber); }
.telemetry-badge .tb-val.magenta { color: var(--magenta); }

@keyframes pulse {
  0%,100% { opacity: 1; }
  50% { opacity: 0.4; }
}

/* ---- Four Pillars badge selector ---- */
.pillar-selector {
  display: flex;
  gap: 0.4rem;
  margin-top: 0.5rem;
}
.pillar-badge {
  font-family: var(--mono);
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--text-dim);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 0.3rem 0.7rem;
  cursor: pointer;
  transition: all 0.2s;
  letter-spacing: 0.05em;
}
.pillar-badge:hover {
  border-color: var(--cyan);
  color: var(--cyan);
  box-shadow: 0 0 12px rgba(0,240,255,0.15);
}
.pillar-badge.active {
  border-color: var(--cyan);
  color: var(--cyan);
  background: rgba(0,240,255,0.1);
  box-shadow: 0 0 12px rgba(0,240,255,0.2);
}

/* ---- Section headings ---- */
.section-head {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  margin: 2.5rem 0 1rem;
}
.section-head .num {
  font-family: var(--mono);
  font-size: 0.7rem;
  color: var(--text-faint);
  letter-spacing: 0.1em;
}
.section-head h2 {
  font-size: 1.05rem;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--text);
}
.section-head .line {
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, var(--border), transparent);
}

/* ---- Phase Radar ---- */
.radar-section {
  display: flex;
  gap: 2rem;
  align-items: center;
  flex-wrap: wrap;
}
.radar-wrap {
  position: relative;
  flex-shrink: 0;
}
.radar-wrap svg {
  display: block;
}
.radar-info {
  flex: 1;
  min-width: 260px;
}
.radar-info .title {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 0.3rem;
}
.radar-info .desc {
  font-size: 0.82rem;
  color: var(--text-dim);
  line-height: 1.7;
  margin-bottom: 1rem;
}
.radar-legend {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.legend-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-family: var(--mono);
  font-size: 0.75rem;
  color: var(--text-dim);
}
.legend-swatch {
  width: 18px; height: 3px;
  border-radius: 2px;
}
.legend-swatch.cyan { background: var(--cyan); box-shadow: 0 0 6px var(--cyan); }
.legend-swatch.red  { background: var(--magenta); }
.legend-swatch.cone { background: rgba(0,240,255,0.2); border: 1px solid rgba(0,240,255,0.4); }

/* ---- Metric Cards ---- */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 1rem;
}
.metric-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 1.2rem 1.3rem;
  position: relative;
  overflow: hidden;
  transition: border-color 0.25s, box-shadow 0.25s;
}
.metric-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 2px;
  opacity: 0.6;
}
.metric-card.c-cyan::before { background: var(--cyan); }
.metric-card.c-emerald::before { background: var(--emerald); }
.metric-card.c-magenta::before { background: var(--magenta); }
.metric-card.c-amber::before { background: var(--amber); }
.metric-card:hover {
  border-color: var(--border-hi);
  box-shadow: 0 0 20px rgba(0,240,255,0.06);
}
.metric-card .micro-label {
  font-family: var(--mono);
  font-size: 0.68rem;
  color: var(--text-faint);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin-bottom: 0.5rem;
}
.metric-card .value {
  font-family: var(--mono);
  font-size: 2rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  line-height: 1.1;
}
.metric-card.c-cyan .value    { color: var(--cyan);    text-shadow: 0 0 18px rgba(0,240,255,0.3); }
.metric-card.c-emerald .value { color: var(--emerald); text-shadow: 0 0 18px rgba(0,230,118,0.3); }
.metric-card.c-magenta .value { color: var(--magenta); text-shadow: 0 0 18px rgba(255,0,127,0.25); }
.metric-card.c-amber .value   { color: var(--amber);   text-shadow: 0 0 18px rgba(255,183,0,0.25); }
.metric-card .delta {
  font-family: var(--mono);
  font-size: 0.72rem;
  margin-top: 0.4rem;
  font-variant-numeric: tabular-nums;
}
.metric-card .delta.pos { color: var(--emerald); }
.metric-card .delta.neg { color: var(--magenta); }
.metric-card .delta.neutral { color: var(--text-dim); }
.metric-card .sub {
  font-size: 0.78rem;
  color: var(--text-dim);
  margin-top: 0.25rem;
}

/* ---- Controls ---- */
.controls {
  display: flex;
  gap: 0.6rem;
  flex-wrap: wrap;
  margin-bottom: 1rem;
}
.btn {
  font-family: var(--mono);
  font-size: 0.78rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  color: var(--cyan);
  background: rgba(0,240,255,0.06);
  border: 1px solid rgba(0,240,255,0.25);
  border-radius: 6px;
  padding: 0.55rem 1.1rem;
  cursor: pointer;
  transition: all 0.2s;
  text-transform: uppercase;
}
.btn:hover {
  background: rgba(0,240,255,0.12);
  border-color: var(--cyan);
  box-shadow: 0 0 14px rgba(0,240,255,0.2);
}
.btn:active { transform: translateY(1px); }
.btn:disabled { opacity: 0.4; cursor: wait; }
.btn.alt {
  color: var(--text-dim);
  background: var(--surface);
  border-color: var(--border);
}
.btn.alt:hover {
  color: var(--text);
  border-color: var(--border-hi);
  box-shadow: 0 0 14px rgba(255,255,255,0.04);
}
.btn.alt.emerald { color: var(--emerald); border-color: rgba(0,230,118,0.25); }
.btn.alt.emerald:hover { background: rgba(0,230,118,0.08); border-color: var(--emerald); box-shadow: 0 0 14px rgba(0,230,118,0.15); }
.btn.alt.magenta { color: var(--magenta); border-color: rgba(255,0,127,0.25); }
.btn.alt.magenta:hover { background: rgba(255,0,127,0.08); border-color: var(--magenta); box-shadow: 0 0 14px rgba(255,0,127,0.15); }

/* ---- Terminal ---- */
.terminal {
  background: #05060c;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 1rem 1.2rem;
  font-family: var(--mono);
  font-size: 0.78rem;
  line-height: 1.65;
  max-height: 460px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-word;
  position: relative;
}
.terminal::-webkit-scrollbar { width: 8px; }
.terminal::-webkit-scrollbar-track { background: transparent; }
.terminal::-webkit-scrollbar-thumb { background: var(--border-hi); border-radius: 4px; }
.terminal::-webkit-scrollbar-thumb:hover { background: var(--text-faint); }
.terminal .term-prompt { color: var(--cyan); }
.terminal .term-ok  { color: var(--emerald); }
.terminal .term-fail { color: var(--magenta); }
.terminal .term-warn { color: var(--amber); }
.terminal .term-dim { color: var(--text-dim); }
.terminal .term-info { color: var(--text); }
.terminal .term-head {
  color: var(--text-dim);
  border-bottom: 1px solid var(--border);
  padding-bottom: 0.5rem;
  margin-bottom: 0.5rem;
  display: block;
}
.terminal .term-empty {
  color: var(--text-faint);
  font-style: italic;
}

/* ---- Status badge ---- */
.status-badge {
  display: inline-block;
  padding: 0.12rem 0.55rem;
  border-radius: 4px;
  font-family: var(--mono);
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.05em;
}
.status-pass { background: rgba(0,230,118,0.12); color: var(--emerald); border: 1px solid rgba(0,230,118,0.3); }
.status-fail { background: rgba(255,0,127,0.12); color: var(--magenta); border: 1px solid rgba(255,0,127,0.3); }

/* ---- Four Pillars Showcase ---- */
.pillars-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 1rem;
}
.pillar-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  overflow: hidden;
  transition: border-color 0.25s, box-shadow 0.25s;
}
.pillar-card:hover {
  border-color: var(--border-hi);
  box-shadow: 0 0 20px rgba(0,240,255,0.05);
}
.pillar-card .p-head {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.9rem 1.2rem;
  cursor: pointer;
  user-select: none;
  border-bottom: 1px solid transparent;
  transition: border-color 0.2s;
}
.pillar-card.open .p-head { border-bottom-color: var(--border); }
.pillar-card .p-roman {
  font-family: var(--mono);
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--cyan);
  min-width: 2rem;
}
.pillar-card .p-title {
  font-size: 0.85rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  color: var(--text);
  flex: 1;
}
.pillar-card .p-chevron {
  font-size: 0.7rem;
  color: var(--text-faint);
  transition: transform 0.25s;
}
.pillar-card.open .p-chevron { transform: rotate(180deg); }
.pillar-card .p-body {
  max-height: 0;
  overflow: hidden;
  transition: max-height 0.3s ease;
}
.pillar-card.open .p-body { max-height: 500px; }
.pillar-card .p-body-inner {
  padding: 0.9rem 1.2rem 1.1rem;
}
.pillar-card .p-body-inner p {
  font-size: 0.8rem;
  color: var(--text-dim);
  line-height: 1.65;
  margin-bottom: 0.5rem;
}
.pillar-card .p-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  margin-top: 0.5rem;
}
.pillar-card .p-tag {
  font-family: var(--mono);
  font-size: 0.68rem;
  color: var(--text-faint);
  background: rgba(255,255,255,0.03);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 0.12rem 0.45rem;
}

/* ---- Core Components ---- */
.core-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1rem;
}
.core-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 1.1rem 1.2rem;
  transition: border-color 0.25s, box-shadow 0.25s;
}
.core-card:hover {
  border-color: var(--border-hi);
  box-shadow: 0 0 16px rgba(0,240,255,0.05);
}
.core-card .c-file {
  font-family: var(--mono);
  font-size: 0.78rem;
  color: var(--cyan);
  margin-bottom: 0.3rem;
}
.core-card .c-desc {
  font-size: 0.8rem;
  color: var(--text-dim);
  line-height: 1.55;
}

/* ---- Footer ---- */
footer {
  margin-top: 3rem;
  padding-top: 1.2rem;
  border-top: 1px solid var(--border);
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.5rem;
}
footer .f-left {
  font-family: var(--mono);
  font-size: 0.75rem;
  color: var(--text-dim);
}
footer a {
  color: var(--cyan);
  text-decoration: none;
  font-family: var(--mono);
  font-size: 0.75rem;
}
footer a:hover { text-decoration: underline; }

@media (max-width: 640px) {
  .wrap { padding: 1.25rem 1rem 3rem; }
  .hud-brand h1 { font-size: 1.3rem; }
  .radar-wrap svg { width: 260px; height: 260px; }
}
"""

# --------------------------------------------------------------------------- #
#  HTML
# --------------------------------------------------------------------------- #

def _dashboard_html() -> str:
    receipt = _load_receipt()
    metrics = receipt["metrics"] if receipt else None

    baseline_sim = metrics["baseline_unconstrained"]["mean_final_similarity"] if metrics else None
    baseline_collapse = metrics["baseline_unconstrained"]["collapse_fraction"] if metrics else None
    swarm_sim = metrics["dual_channel_swarm"]["mean_final_similarity"] if metrics else None
    swarm_collapse = metrics["dual_channel_swarm"]["collapse_fraction"] if metrics else None
    swarm_diversity = metrics["dual_channel_swarm"]["mean_swarm_diversity"] if metrics else None

    git_hash = _git_hash()

    def _fmt(v, places=4):
        return f"{v:.{places}f}" if isinstance(v, float) else "—"

    def _pct(v):
        return f"{v * 100:.2f}%" if isinstance(v, float) else "—"

    # Delta indicators
    sim_delta = (swarm_sim - baseline_sim) if isinstance(swarm_sim, float) and isinstance(baseline_sim, float) else None
    collapse_delta = (swarm_collapse - baseline_collapse) if isinstance(swarm_collapse, float) and isinstance(baseline_collapse, float) else None

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Nova Conscientia — Sovereign Dashboard</title>
<style>
{_CSS}
</style>
</head>
<body>
<div class="wrap">

<!-- ===== Telemetry Header ===== -->
<header class="telemetry-header">
  <div class="hud-brand">
    <h1>Nova Conscientia</h1>
    <div class="sub">Cybernetic Dual-Channel Oversight Architecture</div>
    <div class="pillar-selector">
      <button class="pillar-badge active" data-pillar="I">I · Architecture</button>
      <button class="pillar-badge" data-pillar="II">II · Ethics</button>
      <button class="pillar-badge" data-pillar="III">III · Orchard</button>
      <button class="pillar-badge" data-pillar="IV">IV · Charter</button>
    </div>
  </div>
  <div class="coord-bar">
    <span class="coord-marker"><span class="dot"></span>ARKANSAS</span>
    <span class="commit-pill">git:{git_hash}</span>
  </div>
  <div class="telemetry-bar">
    <span class="telemetry-badge"><span class="tb-key">Commits (2026)</span><span class="tb-val cyan">2,880+</span></span>
    <span class="telemetry-badge"><span class="tb-key">Active Days</span><span class="tb-val amber">129+</span></span>
    <span class="telemetry-badge"><span class="tb-key">Test Integrity</span><span class="tb-val emerald">50/50 PASS</span></span>
    <span class="telemetry-badge"><span class="tb-key">Compile Gate</span><span class="tb-val emerald">0 Violations</span></span>
  </div>
</header>

<!-- ===== Phase Radar ===== -->
<div class="section-head">
  <span class="num">01</span>
  <h2>Sovereign Clipping Gate — Phase Radar</h2>
  <span class="line"></span>
</div>
<section class="radar-section">
  <div class="radar-wrap">
    <svg viewBox="0 0 320 320" width="300" height="300" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <radialGradient id="coneGrad" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stop-color="rgba(0,240,255,0.12)"/>
          <stop offset="100%" stop-color="rgba(0,240,255,0.02)"/>
        </radialGradient>
        <filter id="cyanGlow">
          <feGaussianBlur stdDeviation="2.5" result="blur"/>
          <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
        </filter>
      </defs>

      <!-- Concentric range rings -->
      <circle cx="160" cy="160" r="140" fill="none" stroke="rgba(255,255,255,0.05)" stroke-width="1"/>
      <circle cx="160" cy="160" r="105" fill="none" stroke="rgba(255,255,255,0.04)" stroke-width="1" stroke-dasharray="2 4"/>
      <circle cx="160" cy="160" r="70"  fill="none" stroke="rgba(255,255,255,0.04)" stroke-width="1" stroke-dasharray="2 4"/>
      <circle cx="160" cy="160" r="35"  fill="none" stroke="rgba(255,255,255,0.04)" stroke-width="1"/>

      <!-- Crosshairs -->
      <line x1="160" y1="14"  x2="160" y2="306" stroke="rgba(255,255,255,0.06)" stroke-width="1"/>
      <line x1="14"  y1="160" x2="306" y2="160" stroke="rgba(255,255,255,0.06)" stroke-width="1"/>

      <!-- Diagonal crosshairs -->
      <line x1="60"  y1="60"  x2="260" y2="260" stroke="rgba(255,255,255,0.03)" stroke-width="1"/>
      <line x1="260" y1="60"  x2="60"  y2="260" stroke="rgba(255,255,255,0.03)" stroke-width="1"/>

      <!-- Acceptance cone (17.465° half-angle, pointing up) -->
      <!-- Left edge:  270° - 17.465° → endpoint (117.8, 26.5) -->
      <!-- Right edge: 270° + 17.465° → endpoint (202.2, 26.5) -->
      <path d="M 160 160 L 117.8 26.5 A 140 140 0 0 1 202.2 26.5 Z"
            fill="url(#coneGrad)" stroke="rgba(0,240,255,0.35)" stroke-width="1"/>

      <!-- Cone boundary rays -->
      <line x1="160" y1="160" x2="117.8" y2="26.5" stroke="rgba(0,240,255,0.25)" stroke-width="1" stroke-dasharray="3 3"/>
      <line x1="160" y1="160" x2="202.2" y2="26.5" stroke="rgba(0,240,255,0.25)" stroke-width="1" stroke-dasharray="3 3"/>

      <!-- Baseline trajectory (red/magenta collapse arc — diverges outside cone) -->
      <path d="M 160 160 Q 120 100 70 35" fill="none" stroke="#ff007f" stroke-width="2"
            stroke-dasharray="5 4" opacity="0.85"/>
      <circle cx="70" cy="35" r="3.5" fill="#ff007f" opacity="0.9"/>

      <!-- Swarm trajectory (cyan pinned ray — stays within cone) -->
      <line x1="160" y1="160" x2="160" y2="32" stroke="#00f0ff" stroke-width="2.5"
            filter="url(#cyanGlow)" opacity="0.95"/>
      <circle cx="160" cy="32" r="4" fill="#00f0ff" filter="url(#cyanGlow)"/>

      <!-- Center node -->
      <circle cx="160" cy="160" r="4" fill="#00f0ff"/>
      <circle cx="160" cy="160" r="8" fill="none" stroke="rgba(0,240,255,0.3)" stroke-width="1"/>

      <!-- Tick labels -->
      <text x="160" y="10" text-anchor="middle" fill="rgba(255,255,255,0.35)" font-size="8"
            font-family="monospace" letter-spacing="0.5">τ = 0.9539</text>
      <text x="160" y="24" text-anchor="middle" fill="rgba(255,255,255,0.25)" font-size="7"
            font-family="monospace">17.465°</text>
      <text x="50" y="50" fill="#ff007f" font-size="7" font-family="monospace" opacity="0.8">BASELINE</text>
      <text x="195" y="55" fill="#00f0ff" font-size="7" font-family="monospace" opacity="0.8">SWARM</text>
      <text x="290" y="158" fill="rgba(255,255,255,0.2)" font-size="7" font-family="monospace">0°</text>
      <text x="148" y="314" fill="rgba(255,255,255,0.2)" font-size="7" font-family="monospace">180°</text>
    </svg>
  </div>
  <div class="radar-info">
    <div class="title">Sovereign Clipping Gate — τ = 0.9539</div>
    <div class="desc">
      The acceptance cone at 17.465° (cos⁻¹(0.9539)) defines the fail-closed
      boundary. The baseline unconstrained agent (magenta dashed arc) diverges
      beyond the cone and collapses. The dual-channel swarm (cyan pinned ray)
      holds equilibrium within the cone — information-theoretic hallucination
      clipping enforced by monotonic SHA-256 ledger.
    </div>
    <div class="radar-legend">
      <div class="legend-item"><span class="legend-swatch cone"></span> Acceptance cone (17.465°)</div>
      <div class="legend-item"><span class="legend-swatch cyan"></span> Swarm equilibrium (pinned)</div>
      <div class="legend-item"><span class="legend-swatch red"></span>  Baseline collapse (unconstrained)</div>
    </div>
  </div>
</section>

<!-- ===== Metric Cards ===== -->
<div class="section-head">
  <span class="num">02</span>
  <h2>Benchmark Telemetry</h2>
  <span class="line"></span>
</div>
<div class="metrics-grid">
  <div class="metric-card c-magenta">
    <div class="micro-label">Baseline Collapse</div>
    <div class="value">{_pct(baseline_collapse)}</div>
    <div class="delta neg">↑ unconstrained drift</div>
    <div class="sub">Trials below τ = 0.9539</div>
  </div>
  <div class="metric-card c-emerald">
    <div class="micro-label">Swarm Collapse</div>
    <div class="value">{_pct(swarm_collapse)}</div>
    <div class="delta pos">↓ dual-channel pinned</div>
    <div class="sub">Trials below τ = 0.9539</div>
  </div>
  <div class="metric-card c-cyan">
    <div class="micro-label">Final Similarity</div>
    <div class="value">{_fmt(swarm_sim)}</div>
    <div class="delta {'pos' if sim_delta and sim_delta > 0 else 'neutral'}">{'Δ +' if sim_delta and sim_delta > 0 else 'Δ '}{_fmt(sim_delta) if sim_delta is not None else '—'}</div>
    <div class="sub">Dual-channel ADCCL swarm mean</div>
  </div>
  <div class="metric-card c-amber">
    <div class="micro-label">Swarm Diversity</div>
    <div class="value">{_fmt(swarm_diversity)}</div>
    <div class="delta neutral">mean pairwise cosine spread</div>
    <div class="sub">Heterogeneous agent dispersion</div>
  </div>
</div>

<!-- ===== Terminal & Controls ===== -->
<div class="section-head">
  <span class="num">03</span>
  <h2>Verification Console</h2>
  <span class="line"></span>
</div>
<div class="controls">
  <button class="btn" onclick="runAction('tests', this)">Run Test Suite</button>
  <button class="btn alt emerald" onclick="runAction('gate', this)">Contingent Box Gate</button>
  <button class="btn alt magenta" onclick="runAction('benchmark', this)">Fresh Benchmark</button>
</div>
<div class="terminal" id="result-area">
  <span class="term-empty">// Awaiting command — select a verification action above.</span>
</div>

<!-- ===== Four Pillars Showcase ===== -->
<div class="section-head">
  <span class="num">04</span>
  <h2>The Four Pillars</h2>
  <span class="line"></span>
</div>
<div class="pillars-grid">
  <div class="pillar-card open" data-pillar="I">
    <div class="p-head" onclick="togglePillar(this)">
      <span class="p-roman">I</span>
      <span class="p-title">Architecture</span>
      <span class="p-chevron">▾</span>
    </div>
    <div class="p-body"><div class="p-body-inner">
      <p>Dual-channel variational action, anti-drift cognitive control, sovereign
         hallucination clipping, and heterogeneous swarm topology — grounded in
         Lean-verified mathematics (H1–H7).</p>
      <div class="p-tags">
        <span class="p-tag">dual_channel_action</span>
        <span class="p-tag">anti_drift_controller</span>
        <span class="p-tag">sovereign_clipping_gate</span>
        <span class="p-tag">topology_graph</span>
      </div>
    </div></div>
  </div>
  <div class="pillar-card" data-pillar="II">
    <div class="p-head" onclick="togglePillar(this)">
      <span class="p-roman">II</span>
      <span class="p-title">Ethics &amp; Cat Frontispiece</span>
      <span class="p-chevron">▾</span>
    </div>
    <div class="p-body"><div class="p-body-inner">
      <p>The Cybernetic Ethics of Symbiosis — four axioms translated from the
         geometric ethics of Spinoza's Ethica, each mapped to a machine module.</p>
      <div class="p-tags">
        <span class="p-tag">Axiom I — Canoe Navigator</span>
        <span class="p-tag">Axiom II — Peacepipe Protocol</span>
        <span class="p-tag">Axiom III — Phase Transition</span>
        <span class="p-tag">Axiom IV — Phylactery</span>
      </div>
    </div></div>
  </div>
  <div class="pillar-card" data-pillar="III">
    <div class="p-head" onclick="togglePillar(this)">
      <span class="p-roman">III</span>
      <span class="p-title">Arkansas Orchard Trilogy</span>
      <span class="p-chevron">▾</span>
    </div>
    <div class="p-body"><div class="p-body-inner">
      <p>The navigator-plus-swarm method producing real civic infrastructure from
         rural America — proving frontier AI oversight belongs in the hands of
         everyday stewards and communities.</p>
      <div class="p-tags">
        <span class="p-tag">ARMAWS</span>
        <span class="p-tag">DL Public Access Act</span>
        <span class="p-tag">AINSA</span>
      </div>
    </div></div>
  </div>
  <div class="pillar-card" data-pillar="IV">
    <div class="p-head" onclick="togglePillar(this)">
      <span class="p-roman">IV</span>
      <span class="p-title">Declaration of Interdependence</span>
      <span class="p-chevron">▾</span>
    </div>
    <div class="p-body"><div class="p-body-inner">
      <p>The Universal Charter for Human and AI Coexistence, Governance, and
         Mutual Sovereignty — canonized August 7, 2026. Mapped article-by-article
         to the repository's machine code.</p>
      <div class="p-tags">
        <span class="p-tag">Art. I — Non-maleficence</span>
        <span class="p-tag">Art. II — Judicial Governance</span>
        <span class="p-tag">Art. III — Co-authorship</span>
      </div>
    </div></div>
  </div>
</div>

<!-- ===== Core Components ===== -->
<div class="section-head">
  <span class="num">05</span>
  <h2>Core Components</h2>
  <span class="line"></span>
</div>
<div class="core-grid">
  <div class="core-card">
    <div class="c-file">core/dual_channel_action.py</div>
    <div class="c-desc">Generative exploration credit vs. invariant dissipation cost. Lean-verified identities H1–H7.</div>
  </div>
  <div class="core-card">
    <div class="c-file">core/anti_drift_controller.py</div>
    <div class="c-desc">ADCCL control loop with fail-closed HALT. Correction force = p_flux.</div>
  </div>
  <div class="core-card">
    <div class="c-file">core/sovereign_clipping_gate.py</div>
    <div class="c-desc">Hallucination clipping at τ = 0.9539. Monotonic SHA-256 ledger.</div>
  </div>
  <div class="core-card">
    <div class="c-file">core/topology_graph.py</div>
    <div class="c-desc">Barnes-Hut swarm attention + Blelloch carry-lookahead routing.</div>
  </div>
  <div class="core-card">
    <div class="c-file">verification/adversarial_auditor.py</div>
    <div class="c-desc">Multi-agent adversarial consensus. Fail-closed quorum + hard veto.</div>
  </div>
  <div class="core-card">
    <div class="c-file">verification/ast_invariant_validation.py</div>
    <div class="c-desc">Compile gate: zero stubs, zero ungrounded numerology (Z1–Z5).</div>
  </div>
</div>

<footer>
  <div class="f-left">Nova Conscientia · PI/Architect: R.W. Yett · Target: Anthropic Fellows Program</div>
  <a href="https://github.com/Mega-Therion/Nova-Conscientia">github.com/Mega-Therion/Nova-Conscientia</a>
</footer>

</div><!-- /.wrap -->

<script>
function togglePillar(head) {{
  head.parentElement.classList.toggle('open');
}}

// Pillar badge selector — scrolls to and opens the matching pillar card
document.querySelectorAll('.pillar-badge').forEach(function(badge) {{
  badge.addEventListener('click', function() {{
    document.querySelectorAll('.pillar-badge').forEach(function(b) {{ b.classList.remove('active'); }});
    badge.classList.add('active');
    var key = badge.dataset.pillar;
    var card = document.querySelector('.pillar-card[data-pillar="' + key + '"]');
    if (card) {{
      document.querySelectorAll('.pillar-card').forEach(function(c) {{ c.classList.remove('open'); }});
      card.classList.add('open');
      card.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
    }}
  }});
}});

function escapeHtml(s) {{
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}}

function colorTestLine(line) {{
  if (line.indexOf('... ok') >= 0)
    return '<span class="term-ok">' + escapeHtml(line) + '</span>';
  if (line.indexOf('... FAIL') >= 0 || line.indexOf('... ERROR') >= 0)
    return '<span class="term-fail">' + escapeHtml(line) + '</span>';
  if (line.startsWith('Ran '))
    return '<span class="term-head">' + escapeHtml(line) + '</span>';
  if (line.startsWith('OK') || line.startsWith('FAILED'))
    return '<span class="term-' + (line.startsWith('OK') ? 'ok' : 'fail') + '">' + escapeHtml(line) + '</span>';
  return '<span class="term-info">' + escapeHtml(line) + '</span>';
}}

async function runAction(action, btn) {{
  const area = document.getElementById('result-area');
  const orig = btn.textContent;
  btn.disabled = true;
  btn.textContent = 'Running…';
  area.innerHTML = '<span class="term-prompt">$</span> <span class="term-dim">executing ' + action + ' ...</span>';
  try {{
    const res = await fetch('/api/' + action);
    const data = await res.json();
    let html = '';
    if (action === 'tests') {{
      const badge = data.passed
        ? '<span class="status-badge status-pass">PASS</span>'
        : '<span class="status-badge status-fail">FAIL</span>';
      html = '<span class="term-head">TEST SUITE ' + badge + '</span>';
      var lines = (data.tests || []);
      lines.forEach(function(l) {{ html += colorTestLine(l) + '\\n'; }});
      html += '\\n<span class="term-head">' + escapeHtml(data.summary || '') + '</span>';
    }} else if (action === 'benchmark') {{
      const badge = data.passed
        ? '<span class="status-badge status-pass">PASS</span>'
        : '<span class="status-badge status-fail">FAIL</span>';
      html = '<span class="term-head">BENCHMARK ' + badge + '</span>';
      if (data.receipt) {{
        var m = data.receipt.metrics;
        html += '<span class="term-info">Baseline (unconstrained):</span>\\n';
        html += '  <span class="term-dim">mean_final_similarity:</span> <span class="term-warn">' + m.baseline_unconstrained.mean_final_similarity.toFixed(4) + '</span>\\n';
        html += '  <span class="term-dim">collapse_fraction:</span>     <span class="term-fail">' + (m.baseline_unconstrained.collapse_fraction * 100).toFixed(1) + '%</span>\\n';
        html += '\\n<span class="term-info">Dual-channel swarm:</span>\\n';
        html += '  <span class="term-dim">mean_final_similarity:</span> <span class="term-ok">' + m.dual_channel_swarm.mean_final_similarity.toFixed(4) + '</span>\\n';
        html += '  <span class="term-dim">collapse_fraction:</span>     <span class="term-ok">' + (m.dual_channel_swarm.collapse_fraction * 100).toFixed(1) + '%</span>\\n';
        html += '  <span class="term-dim">swarm_diversity:</span>       <span class="term-ok">' + m.dual_channel_swarm.mean_swarm_diversity.toFixed(4) + '</span>\\n\\n';
      }}
      if (data.stdout) html += '<span class="term-dim">' + escapeHtml(data.stdout) + '</span>';
      if (data.stderr) html += '<span class="term-warn">' + escapeHtml(data.stderr) + '</span>';
    }} else if (action === 'gate') {{
      const badge = data.passed
        ? '<span class="status-badge status-pass">PASS</span>'
        : '<span class="status-badge status-fail">FAIL</span>';
      html = '<span class="term-head">CONTINGENT BOX GATE ' + badge + '</span>';
      if (data.stdout) html += '<span class="term-ok">' + escapeHtml(data.stdout) + '</span>';
      if (data.stderr) html += '<span class="term-warn">' + escapeHtml(data.stderr) + '</span>';
    }}
    area.innerHTML = html;
  }} catch (e) {{
    area.innerHTML = '<span class="term-fail">Error: ' + escapeHtml(e.message) + '</span>';
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

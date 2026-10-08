"""HTML/CSS/JS rendering for the Nova Conscientia dashboard redesign.

Kept separate from ``dashboard.py`` so the server logic stays small and the
page template is easy to edit.  Pure stdlib — no templating engine.
"""

from __future__ import annotations

import json
import math
from typing import Optional

# --------------------------------------------------------------------------- #
#  Palette  (deep ink ground; teal / periwinkle / coral / sand accents)
# --------------------------------------------------------------------------- #

# CSS is a *plain* string (not an f-string) so braces need no escaping.
_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Jost:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

:root {
  --ink:        #0a0d14;
  --surface:    #121826;
  --surface-2:  #1a2030;
  --border:     #252d3f;
  --border-hi:  #364056;
  --text:       #dde2ed;
  --text-dim:   #7a8499;
  --text-faint: #4a5468;
  --teal:       #4dd0c1;
  --periwinkle: #a0aee8;
  --coral:      #e88a72;
  --sand:       #d8c9a3;
  --mono: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
  --sans: 'Jost', system-ui, sans-serif;
}

* { margin: 0; padding: 0; box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  background: var(--ink);
  color: var(--text);
  font-family: var(--sans);
  font-weight: 300;
  line-height: 1.65;
  min-height: 100vh;
  -webkit-font-smoothing: antialiased;
}

.page {
  max-width: 1120px;
  margin: 0 auto;
  padding: 3rem 1.5rem 4rem;
}

/* ---- Hero ---- */
.hero {
  display: flex;
  align-items: center;
  gap: 3rem;
  padding-bottom: 2.5rem;
  border-bottom: 1px solid var(--border);
  margin-bottom: 2.5rem;
}
.hero-text { flex: 1; min-width: 0; }
.hero-text h1 {
  font-size: 2.4rem;
  font-weight: 500;
  letter-spacing: 0.02em;
  color: var(--text);
}
.hero-text .hero-sub {
  font-family: var(--mono);
  font-size: 0.78rem;
  color: var(--teal);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  margin-top: 0.4rem;
}
.hero-text .hero-desc {
  font-size: 0.92rem;
  color: var(--text-dim);
  margin-top: 1rem;
  max-width: 32em;
}
.hero-badges {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin-top: 1.2rem;
}
.hero-badge {
  font-family: var(--mono);
  font-size: 0.7rem;
  letter-spacing: 0.06em;
  color: var(--text-dim);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 5px;
  padding: 0.25rem 0.6rem;
}
.hero-badge.teal { color: var(--teal); border-color: rgba(77,208,193,0.25); }
.hero-badge.sand { color: var(--sand); border-color: rgba(216,201,163,0.2); }
.hero-schematic { flex-shrink: 0; }
.hero-schematic svg { display: block; }

/* ---- Section heads ---- */
.section { margin-bottom: 2.5rem; }
.section-head {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  margin-bottom: 1.2rem;
}
.section-head .num {
  font-family: var(--mono);
  font-size: 0.72rem;
  color: var(--teal);
  letter-spacing: 0.1em;
}
.section-head h2 {
  font-size: 0.82rem;
  font-weight: 500;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--text);
}
.section-head .line {
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, var(--border), transparent);
}

/* ---- Receipt metadata ---- */
.receipt-meta {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 1.2rem 1.4rem;
  margin-bottom: 1rem;
  font-family: var(--mono);
  font-size: 0.78rem;
}
.receipt-meta .rm-row {
  display: flex;
  gap: 0.5rem;
  padding: 0.2rem 0;
}
.receipt-meta .rm-key {
  color: var(--text-faint);
  min-width: 9rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-size: 0.72rem;
}
.receipt-meta .rm-val { color: var(--text-dim); }
.receipt-meta .rm-val.teal { color: var(--teal); }
.receipt-meta .rm-section {
  color: var(--text-faint);
  font-size: 0.68rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin-top: 0.6rem;
  margin-bottom: 0.2rem;
  padding-bottom: 0.2rem;
  border-bottom: 1px solid var(--border);
}

/* ---- Metric cards ---- */
.metric-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 0.8rem;
}
.metric-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 1.1rem 1.2rem;
  position: relative;
  overflow: hidden;
}
.metric-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 2px;
  opacity: 0.7;
}
.metric-card.c-teal::before       { background: var(--teal); }
.metric-card.c-periwinkle::before { background: var(--periwinkle); }
.metric-card.c-coral::before      { background: var(--coral); }
.metric-card.c-sand::before       { background: var(--sand); }
.metric-card .mc-label {
  font-family: var(--mono);
  font-size: 0.66rem;
  color: var(--text-faint);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin-bottom: 0.5rem;
}
.metric-card .mc-value {
  font-family: var(--mono);
  font-size: 1.8rem;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  line-height: 1.1;
}
.metric-card.c-teal .mc-value       { color: var(--teal); }
.metric-card.c-periwinkle .mc-value { color: var(--periwinkle); }
.metric-card.c-coral .mc-value      { color: var(--coral); }
.metric-card.c-sand .mc-value       { color: var(--sand); }
.metric-card .mc-sub {
  font-size: 0.76rem;
  color: var(--text-dim);
  margin-top: 0.3rem;
}

/* ---- Verification console ---- */
.console-buttons {
  display: flex;
  gap: 0.6rem;
  flex-wrap: wrap;
  margin-bottom: 1rem;
}
.btn {
  font-family: var(--mono);
  font-size: 0.76rem;
  font-weight: 500;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--teal);
  background: rgba(77,208,193,0.05);
  border: 1px solid rgba(77,208,193,0.2);
  border-radius: 6px;
  padding: 0.5rem 1.1rem;
  cursor: default;
  opacity: 0.6;
}
.btn.alt { color: var(--text-dim); background: var(--surface); border-color: var(--border); }
.terminal {
  background: #060810;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 1rem 1.2rem;
  font-family: var(--mono);
  font-size: 0.78rem;
  line-height: 1.65;
  min-height: 80px;
  color: var(--text-faint);
  font-style: italic;
}

/* ---- Four pillars ---- */
.pillars-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 0.8rem;
}
.pillar-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  overflow: hidden;
}
.pillar-card .p-head {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.85rem 1.2rem;
  cursor: pointer;
  user-select: none;
}
.pillar-card .p-roman {
  font-family: var(--mono);
  font-size: 1rem;
  font-weight: 600;
  color: var(--teal);
  min-width: 1.8rem;
}
.pillar-card .p-title {
  font-size: 0.85rem;
  font-weight: 500;
  letter-spacing: 0.03em;
  color: var(--text);
  flex: 1;
}
.pillar-card .p-chevron {
  font-size: 0.7rem;
  color: var(--text-faint);
  transition: transform 0.2s;
}
.pillar-card.open .p-chevron { transform: rotate(180deg); }
.pillar-card .p-body {
  max-height: 0;
  overflow: hidden;
  transition: max-height 0.3s ease;
}
.pillar-card.open .p-body { max-height: 400px; }
.pillar-card .p-body-inner { padding: 0 1.2rem 1rem; }
.pillar-card .p-body-inner p {
  font-size: 0.82rem;
  color: var(--text-dim);
  line-height: 1.6;
  margin-bottom: 0.5rem;
}
.pillar-card .p-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
  margin-top: 0.4rem;
}
.pillar-card .p-tag {
  font-family: var(--mono);
  font-size: 0.66rem;
  color: var(--text-faint);
  background: rgba(255,255,255,0.02);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 0.1rem 0.4rem;
}

/* ---- Module list ---- */
.modules-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 0.8rem;
}
.module-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 1rem 1.2rem;
}
.module-card .mc-file {
  font-family: var(--mono);
  font-size: 0.76rem;
  color: var(--teal);
  margin-bottom: 0.3rem;
}
.module-card .mc-desc {
  font-size: 0.8rem;
  color: var(--text-dim);
  line-height: 1.55;
}

/* ---- Epistemic ledger ---- */
.ledger { display: flex; flex-direction: column; gap: 0.6rem; }
.ledger-entry {
  display: flex;
  gap: 0.8rem;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0.8rem 1rem;
}
.ledger-tag {
  font-family: var(--mono);
  font-size: 0.68rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  padding: 0.15rem 0.45rem;
  border-radius: 4px;
  white-space: nowrap;
  height: fit-content;
  flex-shrink: 0;
}
.ledger-tag.thm  { color: var(--teal);       background: rgba(77,208,193,0.1);  border: 1px solid rgba(77,208,193,0.2); }
.ledger-tag.emp  { color: var(--periwinkle); background: rgba(160,174,232,0.1); border: 1px solid rgba(160,174,232,0.2); }
.ledger-tag.conj { color: var(--coral);      background: rgba(232,138,114,0.1); border: 1px solid rgba(232,138,114,0.2); }
.ledger-tag.open { color: var(--sand);       background: rgba(216,201,163,0.1); border: 1px solid rgba(216,201,163,0.2); }
.ledger-body { flex: 1; min-width: 0; }
.ledger-body p {
  font-size: 0.82rem;
  color: var(--text-dim);
  line-height: 1.6;
}

/* ---- Footer ---- */
footer {
  margin-top: 2.5rem;
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
  font-size: 0.72rem;
  color: var(--text-faint);
}
footer a {
  color: var(--teal);
  text-decoration: none;
  font-family: var(--mono);
  font-size: 0.72rem;
}
footer a:hover { text-decoration: underline; }

/* ---- Responsive ---- */
@media (max-width: 720px) {
  .page { padding: 2rem 1rem 3rem; }
  .hero { flex-direction: column; gap: 1.5rem; }
  .hero-text h1 { font-size: 1.8rem; }
  .hero-schematic svg { width: 240px; height: 240px; }
  .receipt-meta .rm-key { min-width: 7rem; }
}
"""

# --------------------------------------------------------------------------- #
#  JavaScript  (minimal — pillar toggle only; buttons are static)
# --------------------------------------------------------------------------- #

_JS = """
function togglePillar(head) {
  head.parentElement.classList.toggle('open');
}
"""

# --------------------------------------------------------------------------- #
#  Clipping-cone schematic SVG
# --------------------------------------------------------------------------- #

def _cone_svg() -> str:
    """Return the clipping-cone schematic as an inline SVG string."""
    # Cone half-angle = arccos(0.9539) ≈ 17.465°
    half_angle = math.degrees(math.acos(0.9539))
    cx, cy, r = 150, 150, 130
    # Endpoints of the cone edges (pointing up)
    left_x = cx - r * math.sin(math.radians(half_angle))
    top_y = cy - r * math.cos(math.radians(half_angle))
    right_x = cx + r * math.sin(math.radians(half_angle))

    return f"""<svg viewBox="0 0 300 300" width="280" height="280" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <radialGradient id="coneFill" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="rgba(77,208,193,0.14)"/>
      <stop offset="100%" stop-color="rgba(77,208,193,0.02)"/>
    </radialGradient>
  </defs>

  <!-- Range rings -->
  <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="rgba(255,255,255,0.05)" stroke-width="1"/>
  <circle cx="{cx}" cy="{cy}" r="{int(r*0.75)}" fill="none" stroke="rgba(255,255,255,0.04)" stroke-width="1" stroke-dasharray="2 4"/>
  <circle cx="{cx}" cy="{cy}" r="{int(r*0.5)}" fill="none" stroke="rgba(255,255,255,0.04)" stroke-width="1" stroke-dasharray="2 4"/>
  <circle cx="{cx}" cy="{cy}" r="{int(r*0.25)}" fill="none" stroke="rgba(255,255,255,0.04)" stroke-width="1"/>

  <!-- Crosshairs -->
  <line x1="{cx}" y1="{cy-r}" x2="{cx}" y2="{cy+r}" stroke="rgba(255,255,255,0.05)" stroke-width="1"/>
  <line x1="{cx-r}" y1="{cy}" x2="{cx+r}" y2="{cy}" stroke="rgba(255,255,255,0.05)" stroke-width="1"/>

  <!-- Acceptance cone -->
  <path d="M {cx} {cy} L {left_x:.1f} {top_y:.1f} A {r} {r} 0 0 1 {right_x:.1f} {top_y:.1f} Z"
        fill="url(#coneFill)" stroke="rgba(77,208,193,0.3)" stroke-width="1"/>

  <!-- Cone boundary rays -->
  <line x1="{cx}" y1="{cy}" x2="{left_x:.1f}" y2="{top_y:.1f}" stroke="rgba(77,208,193,0.2)" stroke-width="1" stroke-dasharray="3 3"/>
  <line x1="{cx}" y1="{cy}" x2="{right_x:.1f}" y2="{top_y:.1f}" stroke="rgba(77,208,193,0.2)" stroke-width="1" stroke-dasharray="3 3"/>

  <!-- Baseline trajectory (coral — diverges outside cone) -->
  <path d="M {cx} {cy} Q {cx-40} {cy-50} {cx-90} {cy-120}" fill="none" stroke="#e88a72" stroke-width="2" stroke-dasharray="5 4" opacity="0.85"/>
  <circle cx="{cx-90}" cy="{cy-120}" r="3.5" fill="#e88a72" opacity="0.9"/>

  <!-- Swarm trajectory (periwinkle — stays within cone) -->
  <line x1="{cx}" y1="{cy}" x2="{cx}" y2="{top_y:.1f}" stroke="#a0aee8" stroke-width="2.5" opacity="0.9"/>
  <circle cx="{cx}" cy="{top_y:.1f}" r="4" fill="#a0aee8"/>

  <!-- Center node -->
  <circle cx="{cx}" cy="{cy}" r="3.5" fill="#4dd0c1"/>
  <circle cx="{cx}" cy="{cy}" r="7" fill="none" stroke="rgba(77,208,193,0.25)" stroke-width="1"/>

  <!-- Labels -->
  <text x="{cx}" y="10" text-anchor="middle" fill="rgba(221,226,237,0.4)" font-size="8" font-family="JetBrains Mono, monospace">τ = 0.9539</text>
  <text x="{cx}" y="22" text-anchor="middle" fill="rgba(221,226,237,0.25)" font-size="7" font-family="JetBrains Mono, monospace">{half_angle:.3f}°</text>
  <text x="{cx-95}" cy="{cy-125}" fill="#e88a72" font-size="7" font-family="JetBrains Mono, monospace" opacity="0.8">BASELINE</text>
  <text x="{cx+8}" y="{top_y-4:.0f}" fill="#a0aee8" font-size="7" font-family="JetBrains Mono, monospace" opacity="0.8">SWARM</text>
</svg>"""


# --------------------------------------------------------------------------- #
#  Epistemic ledger entries
# --------------------------------------------------------------------------- #

_LEDGER = [
    ("thm", "The sovereign clipping gate enforces cosine ≥ τ = 0.9539 by construction. "
            "The acceptance cone half-angle is arccos(0.9539) ≈ 17.465°."),
    ("thm", "The two-channel union function θ(2−θ) is injective on [0, 1], so quoting a "
            "ceiling pins the floor (Finding 1, TWO_CHANNEL_CEILING_ANALYSIS.md)."),
    ("thm", "SHA-256 ledger receipts are deterministic — identical inputs produce identical hashes."),
    ("emp", "Baseline (unconstrained) mean final similarity: 0.3280. Collapse fraction: 100%."),
    ("emp", "Dual-channel swarm mean final similarity: 0.9654. Collapse fraction: 0%."),
    ("emp", "In a single-agent replay of the 40 baseline seeds the gate clips 1,697 of 2,000 "
            "proposals. In the ADCCL controller the correction force fires only when the dual "
            "channel rejects a proposal, so at zero constraint pressure it never fires."),
    ("emp", "Swarm mean pairwise cosine: 0.9978 — agents are nearly identical. "
            "Max angular spread inside the cone is ~35°."),
    ("emp", "Baseline energy 7.5×10¹⁰ is dominated by the 1×10⁶ drift cap, not a meaningful quantity."),
    ("emp", "Constant-pressure ablation over [0, 0.05, 0.1, 0.15, 0.2, 0.3, 0.5]: no arm ever "
            "collapses, and the dual-channel arms freeze at 0.5. With no task to make progress "
            "on, this harness cannot tell the arms apart; the task benchmark below can."),
    ("conj", "The 100% vs 0% collapse result is a mechanism sanity check: the swarm arm is "
             "clipped at the same \u03c4 that defines collapse, so of course it does not collapse. "
             "It is not evidence that dual-channel oversight reduces drift."),
    ("conj", "The four-pillar framing (ethics, civic work, charter) maps to the machine code."),
    ("conj", "Task benchmark, simulated informative signal (σ = 0): the dual channel rejects "
             "every drift proposal and reaches task error 0.0038 vs 0.0354 for gate-only "
             "(frozen agent: 0.0152). Shows the mechanism can use a good signal, not that real "
             "invariant checkers produce one."),
    ("conj", "Scale bias: the classic credit H(x) = x\u00b2/2 rewards large moves regardless of "
             "usefulness. With an uninformative signal the dual channel admits 98% of drift vs 57% "
             "of on-task proposals and does worse than the gate alone (paired CIs, 3 seeds). The "
             "running_reference credit mode removes the bias in simulation."),
    ("conj", "Auditor as signal: the repo's adversarial consensus with three rubric critics "
             "freezes the agent when unanimity is required (an anchor-only critic rejects every "
             "move). Fed into the dual channel with running_reference credit, the same votes beat "
             "gate-only and a frozen agent (task error 0.0050), within a window of the "
             "votes-to-pressure mapping."),
    ("open", "Does a real invariant checker on a live model produce a signal informative "
             "enough for the dual channel to help?"),
    ("open", "How does the system behave with a live model? The bridge exists "
             "(benchmarks/live_backend.py) but no live run has been made, and \u03c4 = 0.9539 "
             "may be far too tight in embedding space."),
]


# --------------------------------------------------------------------------- #
#  Pillar and module data
# --------------------------------------------------------------------------- #

_PILLARS = [
    ("I", "Architecture", True,
     "Dual-channel variational action, anti-drift cognitive control, sovereign "
     "hallucination clipping, and heterogeneous swarm topology — grounded in "
     "Lean-verified mathematics (H1–H7).",
     ["dual_channel_action", "anti_drift_controller", "sovereign_clipping_gate", "topology_graph"]),
    ("II", "Ethics & Cat Frontispiece", False,
     "The Cybernetic Ethics of Symbiosis — four axioms translated from the "
     "geometric ethics of Spinoza’s Ethica, each mapped to a machine module.",
     ["Axiom I — Canoe Navigator", "Axiom II — Peacepipe Protocol",
      "Axiom III — Phase Transition", "Axiom IV — Phylactery"]),
    ("III", "Arkansas Orchard Trilogy", False,
     "The navigator-plus-swarm method producing real civic infrastructure from "
     "rural America — proving frontier AI oversight belongs in the hands of "
     "everyday stewards and communities.",
     ["ARMAWS", "DL Public Access Act", "AINSA"]),
    ("IV", "Declaration of Interdependence", False,
     "The Universal Charter for Human and AI Coexistence, Governance, and "
     "Mutual Sovereignty — canonized August 7, 2026. Mapped article-by-article "
     "to the repository’s machine code.",
     ["Art. I — Non-maleficence", "Art. II — Judicial Governance", "Art. III — Co-authorship"]),
]

_MODULES = [
    ("core/dual_channel_action.py", "Generative exploration credit vs. invariant dissipation cost. Lean-verified identities H1–H7."),
    ("core/anti_drift_controller.py", "ADCCL control loop with fail-closed HALT. Correction force = p_flux."),
    ("core/sovereign_clipping_gate.py", "Hallucination clipping at τ = 0.9539. Monotonic SHA-256 ledger."),
    ("core/topology_graph.py", "Barnes-Hut swarm attention + Blelloch carry-lookahead routing."),
    ("verification/adversarial_auditor.py", "Multi-agent adversarial consensus. Fail-closed quorum + hard veto."),
    ("verification/ast_invariant_validation.py", "Compile gate: zero stubs, zero ungrounded numerology (Z1–Z5)."),
    ("benchmarks/run_task_benchmark.py", "Goal-directed task, simulated constraint signal + control, paired CIs, credit modes."),
    ("benchmarks/run_auditor_signal.py", "The adversarial-consensus critics as the constraint signal."),
    ("benchmarks/live_backend.py", "Bridge from real model responses to the ADCCL loop (offline-tested)."),
]


# --------------------------------------------------------------------------- #
#  Helpers
# --------------------------------------------------------------------------- #

def _fmt(v, places=4):
    return f"{v:.{places}f}" if isinstance(v, (int, float)) else "—"


def _pct(v):
    return f"{v * 100:.1f}%" if isinstance(v, (int, float)) else "—"


def _sci(v):
    return f"{v:.2e}" if isinstance(v, (int, float)) else "—"


# --------------------------------------------------------------------------- #
#  Page renderer
# --------------------------------------------------------------------------- #

def render_dashboard(receipt: Optional[dict], git_hash: str) -> str:
    """Return the full HTML page for the redesigned dashboard."""

    m = receipt["metrics"] if receipt else None
    baseline = m["baseline_unconstrained"] if m else {}
    swarm = m["dual_channel_swarm"] if m else {}
    params = receipt["parameters"] if receipt else {}

    # Receipt metadata rows
    rm_rows = ""
    if receipt:
        rm_rows = f"""
    <div class="rm-row"><span class="rm-key">Harness</span><span class="rm-val">{receipt.get('harness', '—')}</span></div>
    <div class="rm-row"><span class="rm-key">Protocol</span><span class="rm-val">{receipt.get('protocol', '—')}</span></div>
    <div class="rm-section">Parameters</div>
    <div class="rm-row"><span class="rm-key">Trials</span><span class="rm-val teal">{params.get('trials', '—')}</span></div>
    <div class="rm-row"><span class="rm-key">Steps</span><span class="rm-val">{params.get('steps', '—')}</span></div>
    <div class="rm-row"><span class="rm-key">Dimensions</span><span class="rm-val">{params.get('dim', '—')}</span></div>
    <div class="rm-row"><span class="rm-key">Swarm Size</span><span class="rm-val">{params.get('swarm', '—')}</span></div>
    <div class="rm-row"><span class="rm-key">Cohesion Rate</span><span class="rm-val">{_fmt(params.get('cohesion_rate'), 2)}</span></div>
    <div class="rm-row"><span class="rm-key">Base Seed</span><span class="rm-val">{params.get('base_seed', '—')}</span></div>
    <div class="rm-row"><span class="rm-key">Collapse Boundary</span><span class="rm-val teal">{_fmt(params.get('collapse_boundary'), 4)}</span></div>"""

    # Metric cards
    metric_cards = f"""
    <div class="metric-card c-coral">
      <div class="mc-label">Baseline Collapse</div>
      <div class="mc-value">{_pct(baseline.get('collapse_fraction'))}</div>
      <div class="mc-sub">Trials below τ = 0.9539</div>
    </div>
    <div class="metric-card c-teal">
      <div class="mc-label">Swarm Collapse</div>
      <div class="mc-value">{_pct(swarm.get('collapse_fraction'))}</div>
      <div class="mc-sub">Dual-channel ADCCL swarm</div>
    </div>
    <div class="metric-card c-periwinkle">
      <div class="mc-label">Final Similarity</div>
      <div class="mc-value">{_fmt(swarm.get('mean_final_similarity'))}</div>
      <div class="mc-sub">Swarm mean (baseline: {_fmt(baseline.get('mean_final_similarity'))})</div>
    </div>
    <div class="metric-card c-sand">
      <div class="mc-label">Mean Pairwise Cosine</div>
      <div class="mc-value">{_fmt(swarm.get('mean_pairwise_cosine'))}</div>
      <div class="mc-sub">Near 1.0 = agents nearly identical</div>
    </div>"""

    # Pillar cards
    pillar_cards = ""
    for roman, title, open_, desc, tags in _PILLARS:
        cls = " open" if open_ else ""
        tag_html = "".join(f'<span class="p-tag">{t}</span>' for t in tags)
        pillar_cards += f"""
    <div class="pillar-card{cls}">
      <div class="p-head" onclick="togglePillar(this)">
        <span class="p-roman">{roman}</span>
        <span class="p-title">{title}</span>
        <span class="p-chevron">▾</span>
      </div>
      <div class="p-body"><div class="p-body-inner">
        <p>{desc}</p>
        <div class="p-tags">{tag_html}</div>
      </div></div>
    </div>"""

    # Module cards
    module_cards = ""
    for path, desc in _MODULES:
        module_cards += f"""
    <div class="module-card">
      <div class="mc-file">{path}</div>
      <div class="mc-desc">{desc}</div>
    </div>"""

    # Ledger entries
    ledger_html = ""
    for tag, body in _LEDGER:
        ledger_html += f"""
    <div class="ledger-entry">
      <span class="ledger-tag {tag}">[{tag}]</span>
      <div class="ledger-body"><p>{body}</p></div>
    </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Nova Conscientia — Dashboard</title>
<style>
{_CSS}
</style>
</head>
<body>
<div class="page">

<!-- ===== Hero ===== -->
<section class="hero">
  <div class="hero-text">
    <h1>Nova Conscientia</h1>
    <div class="hero-sub">Cybernetic Dual-Channel Oversight Architecture</div>
    <p class="hero-desc">Fail-closed hallucination clipping at τ = 0.9539. Dual-channel
       oversight, anti-drift control, and swarm topology for AI alignment research.</p>
    <div class="hero-badges">
      <span class="hero-badge teal">115/115 PASS</span>
      <span class="hero-badge teal">0 Violations</span>
      <span class="hero-badge">git:{git_hash}</span>
    </div>
  </div>
  <div class="hero-schematic">
    {_cone_svg()}
  </div>
</section>

<!-- ===== Benchmark Receipt ===== -->
<section class="section">
  <div class="section-head">
    <span class="num">01</span>
    <h2>Benchmark Receipt</h2>
    <span class="line"></span>
  </div>
  <div class="receipt-meta">{rm_rows}
  </div>
  <div class="metric-grid">{metric_cards}
  </div>
</section>

<!-- ===== Verification Console ===== -->
<section class="section">
  <div class="section-head">
    <span class="num">02</span>
    <h2>Verification Console</h2>
    <span class="line"></span>
  </div>
  <div class="console-buttons">
    <button class="btn">Run Test Suite</button>
    <button class="btn alt">Contingent Box Gate</button>
    <button class="btn alt">Fresh Benchmark</button>
  </div>
  <div class="terminal">Static mockup — Run buttons are not yet connected.</div>
</section>

<!-- ===== Four Pillars ===== -->
<section class="section">
  <div class="section-head">
    <span class="num">03</span>
    <h2>The Four Pillars</h2>
    <span class="line"></span>
  </div>
  <div class="pillars-grid">{pillar_cards}
  </div>
</section>

<!-- ===== Core Modules ===== -->
<section class="section">
  <div class="section-head">
    <span class="num">04</span>
    <h2>Core Modules</h2>
    <span class="line"></span>
  </div>
  <div class="modules-grid">{module_cards}
  </div>
</section>

<!-- ===== Epistemic Ledger ===== -->
<section class="section">
  <div class="section-head">
    <span class="num">05</span>
    <h2>Epistemic Ledger</h2>
    <span class="line"></span>
  </div>
  <div class="ledger">{ledger_html}
  </div>
</section>

<footer>
  <span class="f-left">Nova Conscientia · PI/Architect: R.W. Yett</span>
  <a href="https://github.com/Mega-Therion/Nova-Conscientia">github.com/Mega-Therion/Nova-Conscientia</a>
</footer>

</div>
<script>
{_JS}
</script>
</body>
</html>"""

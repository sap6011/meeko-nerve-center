#!/usr/bin/env python3
"""
EVOLUTION_VIEWER.py -- Chimera Evolution Dashboard
===================================================
Generates docs/evolution.html showing real evolution data from:
  - chimera_evolution_report.json (current cycle)
  - mutation_vault.json (generation history)
  - mutation_leaderboard.json (top mutations + velocity)
  - live_wire_report.json (topology stats)
  - nanobot_heal_report.json (health data)

Replaces the old failure-count-only dashboard with a full
evolution tracking view.

Zero secrets needed.
"""
import json
import os
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
DOCS = Path("docs")


def load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8", errors="replace"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def generate_evolution_report():
    chimera = load_json(DATA / "chimera_evolution_report.json")
    vault = load_json(DATA / "mutation_vault.json")
    board = load_json(DATA / "mutation_leaderboard.json")
    wire = load_json(DATA / "live_wire_report.json")
    nanobot = load_json(DATA / "nanobot_heal_report.json")
    failures = {}
    if os.path.exists(DATA / "self_builder_queue.json"):
        try:
            for line in open(DATA / "self_builder_queue.json", "r", encoding="utf-8", errors="replace"):
                task = json.loads(line)
                target = task.get("target", "Unknown")
                failures[target] = failures.get(target, 0) + 1
        except Exception:
            pass

    # Extract data
    gen = chimera.get("generation", 0)
    score = chimera.get("composite_score", 0)
    best = vault.get("best_score", 0)
    total_cycles = vault.get("total_cycles", 0)
    velocity = board.get("velocity", {})
    vel_val = velocity.get("velocity", 0)
    vel_trend = velocity.get("trend", "unknown")

    wire_stats = wire.get("stats", {})
    engines = wire_stats.get("total_engines", 0)
    wires = wire_stats.get("total_wires_discovered", 0)
    zs_chains = wire_stats.get("zero_secret_chains", 0)
    hungry = wire_stats.get("hungry_inputs", 0)
    orphans = wire_stats.get("orphan_outputs", 0)

    healed = nanobot.get("healed", 0)
    scanned = nanobot.get("scanned", 0)
    syntax_ok = nanobot.get("syntax_ok", 0)

    scores = chimera.get("scores", {})

    # Gen history for chart
    gens = vault.get("generations", [])
    gen_labels = [str(g.get("cycle", i)) for i, g in enumerate(gens[-20:])]
    gen_scores = [g.get("composite_score", 0) for g in gens[-20:]]

    # Top skills
    top_skills = board.get("top_skills", [])[:10]

    html = f"""<!DOCTYPE html>
<html>
<head><title>SolarPunk Evolution Dashboard</title>
<meta charset="utf-8">
<style>
    body {{ font-family: 'Courier New', monospace; background: #0a0e14; color: #00ffcc; padding: 30px; }}
    .grid {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; margin: 20px 0; }}
    .card {{ background: #111820; border: 1px solid #1a3a2a; border-radius: 8px; padding: 20px; }}
    .card h3 {{ margin-top: 0; color: #4cff8c; font-size: 14px; text-transform: uppercase; letter-spacing: 2px; }}
    .big {{ font-size: 42px; font-weight: bold; margin: 10px 0; }}
    .score-bar {{ background: #1a1a2a; height: 20px; border-radius: 10px; overflow: hidden; }}
    .score-fill {{ height: 100%; border-radius: 10px; transition: width 0.5s; }}
    .green {{ background: linear-gradient(90deg, #00cc66, #4cff8c); }}
    .amber {{ background: linear-gradient(90deg, #cc8800, #ffcc00); }}
    .red {{ background: linear-gradient(90deg, #cc0000, #ff4444); }}
    h1 {{ text-align: center; letter-spacing: 5px; font-size: 20px; }}
    .sub {{ color: #668877; font-size: 12px; }}
    table {{ width: 100%; border-collapse: collapse; }}
    td {{ padding: 6px 10px; border-bottom: 1px solid #1a2a1a; }}
    .right {{ text-align: right; }}
    .velocity {{ font-size: 18px; }}
    .up {{ color: #4cff8c; }}
    .down {{ color: #ff4444; }}
    .flat {{ color: #888; }}
</style>
</head>
<body>
<h1>SOLARPUNK EVOLUTION DASHBOARD</h1>
<p style="text-align:center" class="sub">Generation {gen} | {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}</p>

<div class="grid">
  <div class="card">
    <h3>Composite Score</h3>
    <div class="big">{score}<span style="font-size:18px">/100</span></div>
    <div class="score-bar"><div class="score-fill {'green' if score >= 70 else 'amber' if score >= 40 else 'red'}" style="width:{score}%"></div></div>
    <p class="sub">Best ever: {best}/100</p>
  </div>
  <div class="card">
    <h3>Topology</h3>
    <table>
      <tr><td>Engines</td><td class="right">{engines}</td></tr>
      <tr><td>Live Wires</td><td class="right">{wires}</td></tr>
      <tr><td>Zero-Secret Chains</td><td class="right">{zs_chains}</td></tr>
      <tr><td>Hungry Inputs</td><td class="right">{hungry}</td></tr>
      <tr><td>Orphan Outputs</td><td class="right">{orphans}</td></tr>
    </table>
  </div>
  <div class="card">
    <h3>Health</h3>
    <table>
      <tr><td>Engines Scanned</td><td class="right">{scanned}</td></tr>
      <tr><td>Syntax Clean</td><td class="right">{syntax_ok}</td></tr>
      <tr><td>Auto-Healed</td><td class="right">{healed}</td></tr>
      <tr><td>Total Generations</td><td class="right">{total_cycles}</td></tr>
    </table>
    <p class="velocity {'up' if vel_val > 0 else 'down' if vel_val < 0 else 'flat'}">
      Velocity: {vel_val:+.1f} ({vel_trend})
    </p>
  </div>
</div>

<div class="grid" style="grid-template-columns: 1fr 1fr;">
  <div class="card">
    <h3>Score Breakdown</h3>
    <table>
      <tr><td>Wiring</td><td class="right">{scores.get('wiring', '-')}/100</td></tr>
      <tr><td>Hunger Reduction</td><td class="right">{scores.get('hunger_reduction', '-')}/100</td></tr>
      <tr><td>Bridge Rate</td><td class="right">{scores.get('bridge_rate', '-')}/100</td></tr>
      <tr><td>Health</td><td class="right">{scores.get('health', '-')}/100</td></tr>
      <tr><td>Mutation</td><td class="right">{scores.get('mutation', '-')}/100</td></tr>
    </table>
  </div>
  <div class="card">
    <h3>Top Mutated Skills</h3>
    <table>
      {"".join(f'<tr><td>{s[0]}</td><td class="right">{s[1]}x</td></tr>' for s in top_skills) if top_skills else '<tr><td colspan="2">No mutations yet</td></tr>'}
    </table>
  </div>
</div>

<div class="card" style="margin-top:20px">
  <h3>Legacy: Synthesis Failures</h3>
  <p>Active Synthesis failures: {failures.get('projects/Active_Synthesis/main.py', 0)}</p>
</div>

<p style="text-align:center" class="sub">Built by CHIMERA_EVOLUTION_ENGINE | Ethics: 99% mutual aid / 1% node fuel</p>
</body>
</html>"""

    DOCS.mkdir(exist_ok=True)
    with open(DOCS / "evolution.html", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Evolution Dashboard updated: docs/evolution.html (gen {gen}, score {score}/100)")


if __name__ == "__main__":
    generate_evolution_report()

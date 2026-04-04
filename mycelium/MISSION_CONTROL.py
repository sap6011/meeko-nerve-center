#!/usr/bin/env python3
"""
MISSION_CONTROL.py -- Nerve Center Dashboard
=============================================
Generates docs/index.html with live data from ALL subsystems:
  - Knowledge graph (engine topology)
  - Chimera evolution (generation, score, velocity)
  - Live wire (wiring stats, zero-secret chains)
  - Nanobot healer (health status)
  - Polymarket scanner (market edges)
  - Hemisphere sync (left/right brain status)
  - Relay baton (Claude handoff state)
  - Product factory (digital products ready to sell)

Zero secrets needed.
"""
import json
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
DOCS = Path("docs")


def load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8", errors="replace"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def rebuild_mission_control():
    graph = load_json(DATA / "knowledge_graph.json")
    chimera = load_json(DATA / "chimera_evolution_report.json")
    wire = load_json(DATA / "live_wire_report.json")
    nanobot = load_json(DATA / "nanobot_heal_report.json")
    poly = load_json(DATA / "polymarket_scan.json")
    hemisphere = load_json(DATA / "hemisphere_state.json")
    relay = load_json(DATA / "relay_baton.json")
    products = load_json(DATA / "product_registry.json")
    vault = load_json(DATA / "mutation_vault.json")

    if not graph:
        graph = {"nodes": {}, "edges": [], "top_hubs": []}
    nodes = graph.get("nodes", graph.get("total_nodes", 0))
    node_count = len(nodes) if isinstance(nodes, dict) else nodes
    edges = graph.get("edges", [])
    edge_count = len(edges) if isinstance(edges, list) else edges

    wire_stats = wire.get("stats", {})
    gen = chimera.get("generation", 0)
    score = chimera.get("composite_score", 0)
    best = vault.get("best_score", 0)

    poly_edges = poly.get("edges_found", 0)
    poly_markets = poly.get("total_markets_scanned", 0)

    hemi_left = hemisphere.get("left", {}).get("status", "offline")
    hemi_right = hemisphere.get("right", {}).get("status", "offline")
    hemi_sync = hemisphere.get("last_sync", "never")

    relay_holder = relay.get("holder", "idle")
    relay_tasks = len(relay.get("tasks", []))

    prod_count = len(products.get("products", {})) if isinstance(products.get("products"), dict) else 0
    prod_ready = sum(1 for p in products.get("products", {}).values() if p.get("content_ready")) if isinstance(products.get("products"), dict) else 0

    top_hubs_html = ""
    for h in graph.get("top_hubs", [])[:10]:
        top_hubs_html += f"<div class='node'><strong>{h['name']}</strong> -- {h['connections']} connections</div>"

    top_edges_html = ""
    for e in poly.get("top_edges", [])[:5]:
        top_edges_html += f"<div class='node'>{e.get('question', '?')[:80]} | YES: {e.get('yes_pct', '?')}% | Score: {e.get('edge_score', 0)}</div>"

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Meeko Nerve Center: Mission Control</title>
<style>
    body {{ background: #0a0e14; color: #00ffcc; font-family: 'Courier New', monospace; padding: 30px; }}
    .node {{ border-left: 3px solid #00ffcc; padding-left: 15px; margin-bottom: 12px; font-size: 13px; }}
    h1 {{ text-transform: uppercase; letter-spacing: 5px; text-align: center; }}
    h2 {{ color: #4cff8c; font-size: 14px; text-transform: uppercase; letter-spacing: 2px; margin-top: 30px; }}
    .grid {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; }}
    .stat {{ background: #111820; border: 1px solid #1a3a2a; border-radius: 8px; padding: 15px; text-align: center; }}
    .stat .val {{ font-size: 32px; font-weight: bold; }}
    .stat .label {{ font-size: 11px; color: #668877; margin-top: 5px; }}
    .hemi {{ display: grid; grid-template-columns: 1fr auto 1fr; gap: 10px; align-items: center; text-align: center; margin: 20px 0; }}
    .hemi-node {{ background: #111820; border: 1px solid #1a3a2a; border-radius: 50%; width: 120px; height: 120px; display: flex; align-items: center; justify-content: center; flex-direction: column; margin: 0 auto; }}
    .sync-arrow {{ color: #4cff8c; font-size: 24px; }}
    .sub {{ color: #668877; font-size: 11px; }}
    hr {{ border: none; border-top: 1px solid #1a3a2a; margin: 25px 0; }}
</style>
</head>
<body>
<h1>Meeko Nerve Center: Mission Control</h1>
<p style="text-align:center" class="sub">{now} | Generation {gen}</p>

<div class="grid">
  <div class="stat"><div class="val">{wire_stats.get('total_engines', 0)}</div><div class="label">Engines</div></div>
  <div class="stat"><div class="val">{wire_stats.get('total_wires_discovered', 0)}</div><div class="label">Live Wires</div></div>
  <div class="stat"><div class="val">{wire_stats.get('zero_secret_chains', 0)}</div><div class="label">Zero-Secret Chains</div></div>
  <div class="stat"><div class="val">{score}/100</div><div class="label">Evolution Score (best: {best})</div></div>
  <div class="stat"><div class="val">{nanobot.get('syntax_ok', 0)}/{nanobot.get('scanned', 0)}</div><div class="label">Health (clean/total)</div></div>
  <div class="stat"><div class="val">{prod_ready}/{prod_count}</div><div class="label">Products Ready</div></div>
</div>

<h2>Hemisphere Brain</h2>
<div class="hemi">
  <div class="hemi-node">
    <div style="font-size:14px">LEFT</div>
    <div style="font-size:11px">Local Machine</div>
    <div class="sub">{hemi_left}</div>
  </div>
  <div class="sync-arrow">&lt;-- SYNC --&gt;</div>
  <div class="hemi-node">
    <div style="font-size:14px">RIGHT</div>
    <div style="font-size:11px">GitHub Repo</div>
    <div class="sub">{hemi_right}</div>
  </div>
</div>
<p class="sub" style="text-align:center">Last sync: {hemi_sync} | Relay: {relay_holder} ({relay_tasks} tasks)</p>

<hr>
<h2>Knowledge Graph: Top Hubs</h2>
{top_hubs_html if top_hubs_html else '<div class="node">Run LIVE_WIRE + BRIDGE_BUILDER to populate</div>'}

<hr>
<h2>Market Intelligence ({poly_markets} markets, {poly_edges} edges)</h2>
{top_edges_html if top_edges_html else '<div class="node">Run POLYMARKET_SCANNER to populate</div>'}

<hr>
<p class="sub" style="text-align:center">
  Ethics: 99% mutual aid / 1% node fuel |
  <a href="https://github.com/meekotharaccoon-cell/meeko-nerve-center" style="color:#4cff8c">Source Code</a> |
  <a href="evolution.html" style="color:#4cff8c">Evolution Dashboard</a> |
  <a href="api/vital.json" style="color:#4cff8c">Vital Sign API</a>
</p>
</body>
</html>"""

    DOCS.mkdir(exist_ok=True)
    with open(DOCS / "index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Mission Control Updated: docs/index.html (gen {gen}, {wire_stats.get('total_engines', 0)} engines, score {score}/100)")


if __name__ == "__main__":
    rebuild_mission_control()

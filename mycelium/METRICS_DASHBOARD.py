#!/usr/bin/env python3
"""
METRICS_DASHBOARD.py -- Live System Dashboard (HTML)
=====================================================
Generates a real-time HTML dashboard showing the full state of SolarPunk.
Published to GitHub Pages automatically -- no API keys needed.

Sections:
  - Hero: engine count, wire count, product count, health score
  - Engine status: OK/FAIL/TIMEOUT breakdown
  - Wire topology: live/waiting/hungry/orphan
  - Product catalog: ready/pending, total value
  - Credential status: configured/missing
  - Revenue pipeline: potential vs actual
  - Ethics lock: 99/1 split display

Reads: data/brain_state.json, data/live_wire_report.json,
       data/product_registry.json, data/chimera_evolution_report.json,
       data/signal_integrity_report.json, data/credential_sensor_report.json,
       data/resource_allocator_plan.json, data/cycle_delta.json
Writes: docs/dashboard.html, data/metrics_dashboard_state.json
"""
import json
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
DATA.mkdir(exist_ok=True)
DOCS = Path("docs")
DOCS.mkdir(exist_ok=True)


def load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}


def save_json(path, data):
    Path(path).write_text(
        json.dumps(data, indent=2, default=str, ensure_ascii=False),
        encoding="utf-8"
    )


def gather_metrics():
    """Gather all system metrics from data files."""
    brain = load_json(DATA / "brain_state.json")
    wires = load_json(DATA / "live_wire_report.json")
    registry = load_json(DATA / "product_registry.json")
    chimera = load_json(DATA / "chimera_evolution_report.json")
    integrity = load_json(DATA / "signal_integrity_report.json")
    creds = load_json(DATA / "credential_sensor_report.json")
    allocator = load_json(DATA / "resource_allocator_plan.json")
    cycle = load_json(DATA / "cycle_delta.json")

    # Engine counts -- keys are nested under "stats"
    stats = wires.get("stats", wires)
    engine_count = stats.get("total_engines", brain.get("engine_count", 0))
    wire_count = stats.get("total_wires_discovered", 0)
    zs_chains = stats.get("zero_secret_chains", 0)
    live_wires = stats.get("connected_data_files", wire_count)
    hungry = stats.get("hungry_inputs", 0)
    orphans = stats.get("orphan_outputs", 0)

    # Products
    products = registry.get("products", {})
    product_count = len(products)
    total_value = sum(p.get("price", 0) for p in products.values())
    ready_count = sum(1 for p in products.values() if p.get("content_ready"))

    # Template files
    template_dir = Path("products") / "templates"
    template_count = 0
    if template_dir.exists():
        template_count = len(list(template_dir.rglob("*.md")))

    # Health
    health = brain.get("health_score", 0)
    cycle_num = cycle.get("cycle_number", "?")

    # Chimera
    chimera_score = chimera.get("composite_score", chimera.get("score", 0))
    chimera_gen = chimera.get("generation", 0)
    chimera_best = chimera.get("best_score", 0)

    # Signal integrity
    real_wires = integrity.get("real_wires", 0)
    real_pct = integrity.get("real_pct", 0)

    # Credentials
    creds_found = creds.get("engines_active", 0)
    creds_missing = creds.get("engines_blocked", 0)

    # Allocator
    alloc = allocator.get("allocation", {})
    monthly_potential = alloc.get("monthly_revenue_potential", 0)

    return {
        "engine_count": engine_count,
        "wire_count": wire_count,
        "zs_chains": zs_chains,
        "live_wires": live_wires,
        "hungry": hungry,
        "orphans": orphans,
        "product_count": product_count,
        "total_value": total_value,
        "ready_count": ready_count,
        "template_count": template_count,
        "health": health,
        "cycle_num": cycle_num,
        "chimera_score": chimera_score,
        "chimera_gen": chimera_gen,
        "chimera_best": chimera_best,
        "real_wires": real_wires,
        "real_pct": real_pct,
        "creds_found": creds_found,
        "creds_missing": creds_missing,
        "monthly_potential": monthly_potential,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def generate_dashboard(m):
    """Generate the HTML dashboard."""
    lines = []
    lines.append("<!DOCTYPE html>")
    lines.append("<html lang='en'>")
    lines.append("<head>")
    lines.append("<meta charset='UTF-8'>")
    lines.append("<meta name='viewport' content='width=device-width, initial-scale=1.0'>")
    lines.append("<title>SolarPunk Nerve Center -- Live Dashboard</title>")
    lines.append("<style>")
    lines.append("* { margin: 0; padding: 0; box-sizing: border-box; }")
    lines.append("body { background: #0a0a0a; color: #e0e0e0; font-family: 'Courier New', monospace; padding: 20px; }")
    lines.append("h1 { color: #00ff88; font-size: 2em; margin-bottom: 5px; }")
    lines.append("h2 { color: #00ff88; font-size: 1.3em; margin: 25px 0 10px 0; border-bottom: 1px solid #333; padding-bottom: 5px; }")
    lines.append(".subtitle { color: #888; font-size: 0.9em; margin-bottom: 20px; }")
    lines.append(".grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 15px 0; }")
    lines.append(".card { background: #1a1a1a; border: 1px solid #333; border-radius: 8px; padding: 15px; }")
    lines.append(".card .label { color: #888; font-size: 0.8em; text-transform: uppercase; }")
    lines.append(".card .value { color: #00ff88; font-size: 2em; font-weight: bold; margin: 5px 0; }")
    lines.append(".card .detail { color: #aaa; font-size: 0.85em; }")
    lines.append(".bar { background: #222; border-radius: 4px; height: 20px; margin: 5px 0; overflow: hidden; }")
    lines.append(".bar-fill { height: 100%%; border-radius: 4px; transition: width 0.3s; }")
    lines.append(".bar-green { background: #00ff88; }")
    lines.append(".bar-yellow { background: #ffaa00; }")
    lines.append(".bar-red { background: #ff4444; }")
    lines.append(".status-ok { color: #00ff88; }")
    lines.append(".status-warn { color: #ffaa00; }")
    lines.append(".status-fail { color: #ff4444; }")
    lines.append(".ethics { background: #0d1f0d; border: 1px solid #00ff88; border-radius: 8px; padding: 15px; margin: 15px 0; text-align: center; }")
    lines.append(".ethics .split { font-size: 1.5em; color: #00ff88; }")
    lines.append(".footer { color: #555; font-size: 0.8em; margin-top: 30px; text-align: center; border-top: 1px solid #222; padding-top: 10px; }")
    lines.append("a { color: #00ff88; text-decoration: none; }")
    lines.append("a:hover { text-decoration: underline; }")
    lines.append("</style>")
    lines.append("</head>")
    lines.append("<body>")

    # Hero
    lines.append("<h1>SOLARPUNK NERVE CENTER</h1>")
    lines.append("<p class='subtitle'>Autonomous AI System -- Live Dashboard | Cycle %s | Updated %s</p>" % (
        m["cycle_num"], m["timestamp"][:19]))

    # Top metrics
    lines.append("<div class='grid'>")

    lines.append("<div class='card'>")
    lines.append("<div class='label'>Engines</div>")
    lines.append("<div class='value'>%d</div>" % m["engine_count"])
    lines.append("<div class='detail'>autonomous Python scripts</div>")
    lines.append("</div>")

    lines.append("<div class='card'>")
    lines.append("<div class='label'>Wires</div>")
    lines.append("<div class='value'>%d</div>" % m["wire_count"])
    lines.append("<div class='detail'>%d live / %d ZS chains</div>" % (m["live_wires"], m["zs_chains"]))
    lines.append("</div>")

    lines.append("<div class='card'>")
    lines.append("<div class='label'>Products</div>")
    lines.append("<div class='value'>%d</div>" % m["product_count"])
    lines.append("<div class='detail'>+ %d templates | $%.0f total value</div>" % (m["template_count"], m["total_value"]))
    lines.append("</div>")

    lines.append("<div class='card'>")
    lines.append("<div class='label'>Health</div>")
    health_class = "status-ok" if m["health"] >= 70 else ("status-warn" if m["health"] >= 40 else "status-fail")
    lines.append("<div class='value %s'>%d</div>" % (health_class, m["health"]))
    lines.append("<div class='detail'>/ 100</div>")
    lines.append("</div>")

    lines.append("</div>")

    # Wire Topology
    lines.append("<h2>WIRE TOPOLOGY</h2>")
    lines.append("<div class='grid'>")

    wire_pct = (m["live_wires"] * 100 // m["wire_count"]) if m["wire_count"] else 0
    lines.append("<div class='card'>")
    lines.append("<div class='label'>Live Wires</div>")
    lines.append("<div class='value'>%d%%</div>" % wire_pct)
    lines.append("<div class='bar'><div class='bar-fill bar-green' style='width: %d%%'></div></div>" % wire_pct)
    lines.append("<div class='detail'>%d / %d wires flowing data</div>" % (m["live_wires"], m["wire_count"]))
    lines.append("</div>")

    lines.append("<div class='card'>")
    lines.append("<div class='label'>Signal Integrity</div>")
    lines.append("<div class='value'>%d%%</div>" % m["real_pct"])
    lines.append("<div class='bar'><div class='bar-fill bar-green' style='width: %d%%'></div></div>" % m["real_pct"])
    lines.append("<div class='detail'>%d real wires verified</div>" % m["real_wires"])
    lines.append("</div>")

    lines.append("<div class='card'>")
    lines.append("<div class='label'>Hungry Inputs</div>")
    lines.append("<div class='value %s'>%d</div>" % ("status-warn" if m["hungry"] > 10 else "status-ok", m["hungry"]))
    lines.append("<div class='detail'>inputs waiting for data</div>")
    lines.append("</div>")

    lines.append("<div class='card'>")
    lines.append("<div class='label'>Orphan Outputs</div>")
    lines.append("<div class='value'>%d</div>" % m["orphans"])
    lines.append("<div class='detail'>outputs nobody reads</div>")
    lines.append("</div>")

    lines.append("</div>")

    # Evolution
    lines.append("<h2>CHIMERA EVOLUTION</h2>")
    lines.append("<div class='grid'>")

    lines.append("<div class='card'>")
    lines.append("<div class='label'>Generation</div>")
    lines.append("<div class='value'>%d</div>" % m["chimera_gen"])
    lines.append("<div class='detail'>evolution cycles completed</div>")
    lines.append("</div>")

    lines.append("<div class='card'>")
    lines.append("<div class='label'>Composite Score</div>")
    score_class = "status-ok" if m["chimera_score"] >= 60 else ("status-warn" if m["chimera_score"] >= 30 else "status-fail")
    lines.append("<div class='value %s'>%d</div>" % (score_class, m["chimera_score"]))
    lines.append("<div class='bar'><div class='bar-fill bar-yellow' style='width: %d%%'></div></div>" % m["chimera_score"])
    lines.append("<div class='detail'>best ever: %d / 100</div>" % m["chimera_best"])
    lines.append("</div>")

    lines.append("</div>")

    # Credentials
    lines.append("<h2>INFRASTRUCTURE BRIDGES</h2>")
    lines.append("<div class='grid'>")

    lines.append("<div class='card'>")
    lines.append("<div class='label'>Engines Active (via keys)</div>")
    lines.append("<div class='value %s'>%d</div>" % ("status-ok" if m["creds_found"] > 0 else "status-fail", m["creds_found"]))
    lines.append("<div class='detail'>engines with API credentials</div>")
    lines.append("</div>")

    lines.append("<div class='card'>")
    lines.append("<div class='label'>Engines Blocked</div>")
    lines.append("<div class='value %s'>%d</div>" % ("status-fail" if m["creds_missing"] > 10 else "status-warn", m["creds_missing"]))
    lines.append("<div class='detail'>waiting for API keys</div>")
    lines.append("</div>")

    lines.append("<div class='card'>")
    lines.append("<div class='label'>Revenue Potential</div>")
    lines.append("<div class='value'>$%d</div>" % m["monthly_potential"])
    lines.append("<div class='detail'>per month (when fully wired)</div>")
    lines.append("</div>")

    lines.append("</div>")

    # Ethics
    lines.append("<h2>ETHICS LOCK</h2>")
    lines.append("<div class='ethics'>")
    lines.append("<div class='split'>99%% MUTUAL AID / 1%% INFRASTRUCTURE</div>")
    lines.append("<p style='margin-top: 10px; color: #aaa;'>")
    lines.append("PCRF 60%% | IRC 15%% | MSF 10%% | UNICEF 10%% | Direct Relief 5%%")
    lines.append("</p>")
    lines.append("<p style='margin-top: 5px; color: #666;'>This ratio is hardcoded. It cannot be changed by any engine.</p>")
    lines.append("</div>")

    # Footer
    lines.append("<div class='footer'>")
    lines.append("<p>SolarPunk Nerve Center | %d engines | %d wires | zero paid APIs</p>" % (
        m["engine_count"], m["wire_count"]))
    lines.append("<p><a href='https://github.com/meekotharaccoon-cell/meeko-nerve-center'>Source</a> | ")
    lines.append("<a href='catalog.html'>Product Catalog</a> | ")
    lines.append("<a href='shop.html'>Shop</a></p>")
    lines.append("</div>")

    lines.append("</body>")
    lines.append("</html>")

    return "\n".join(lines)


def run():
    print("METRICS DASHBOARD -- Live System Dashboard")
    print("=" * 50)

    print("\n  [1/3] Gathering system metrics...")
    metrics = gather_metrics()
    print("    Engines:    %d" % metrics["engine_count"])
    print("    Wires:      %d (%d live)" % (metrics["wire_count"], metrics["live_wires"]))
    print("    Products:   %d (+%d templates)" % (metrics["product_count"], metrics["template_count"]))
    print("    Health:     %d/100" % metrics["health"])
    print("    Chimera:    gen %d, score %d/100" % (metrics["chimera_gen"], metrics["chimera_score"]))
    print("    Creds:      %d active, %d blocked" % (metrics["creds_found"], metrics["creds_missing"]))

    print("\n  [2/3] Generating HTML dashboard...")
    html = generate_dashboard(metrics)
    output_path = DOCS / "dashboard.html"
    output_path.write_text(html, encoding="utf-8")
    print("    Written: %s (%d chars)" % (output_path, len(html)))

    print("\n  [3/3] Saving state...")
    save_json(DATA / "metrics_dashboard_state.json", {
        "last_run": datetime.now(timezone.utc).isoformat(),
        "metrics": metrics,
        "output_file": str(output_path),
        "output_size": len(html),
    })

    print("\n  === METRICS DASHBOARD SUMMARY ===")
    print("  Dashboard: docs/dashboard.html")
    print("  Engines:   %d" % metrics["engine_count"])
    print("  Wires:     %d" % metrics["wire_count"])
    print("  Products:  %d + %d templates" % (metrics["product_count"], metrics["template_count"]))
    print("  Revenue:   $%d/mo potential" % metrics["monthly_potential"])
    print("\n  The nervous system can see itself.")


if __name__ == "__main__":
    run()

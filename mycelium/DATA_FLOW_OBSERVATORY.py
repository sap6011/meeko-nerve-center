#!/usr/bin/env python3
"""
DATA_FLOW_OBSERVATORY.py -- God's-Eye View of the Nervous System
================================================================
Gemini was right: holding 4,030 wires in your head is impossible.
This engine lets you SEE what's actually flowing through them.

What it does:
  1. Reads the live wire topology (who writes what, who reads what)
  2. Opens every data file that wires pass through
  3. Extracts the ACTUAL PAYLOAD -- what data is moving between engines
  4. Builds a readable flow matrix: Engine A -> [payload summary] -> Engine B
  5. Identifies high-value flows (revenue data, knowledge, signals)
  6. Identifies dead flows (empty files, stale data, zero-content wires)
  7. Generates an HTML observatory dashboard you can view in a browser

Biology: The thalamus -- the brain's relay station. Every sensory
signal passes through it. This is SolarPunk's thalamus.

Reads: data/live_wire_report.json, data/*.json (all flowing data)
Writes: data/observatory_report.json, docs/observatory.html
Zero secrets needed.
"""
import json
import os
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
        return None


def summarize_payload(data, max_depth=2):
    """Extract a human-readable summary of what a data file contains."""
    if data is None:
        return {"type": "null", "summary": "empty/missing", "size": 0}

    if isinstance(data, dict):
        keys = list(data.keys())[:15]
        # Look for high-value signals
        signals = []
        if "revenue" in str(keys).lower() or "total" in str(keys).lower():
            signals.append("REVENUE")
        if "wires" in str(keys).lower() or "engines" in str(keys).lower():
            signals.append("TOPOLOGY")
        if "knowledge" in str(keys).lower() or "nodes" in str(keys).lower():
            signals.append("KNOWLEDGE")
        if "health" in str(keys).lower() or "heal" in str(keys).lower():
            signals.append("HEALTH")
        if "social" in str(keys).lower() or "post" in str(keys).lower():
            signals.append("SOCIAL")
        if "sentinel" in str(keys).lower() or "security" in str(keys).lower():
            signals.append("SECURITY")
        if "mutation" in str(keys).lower() or "evolution" in str(keys).lower():
            signals.append("EVOLUTION")

        # Sample values
        samples = {}
        for k in keys[:5]:
            v = data[k]
            if isinstance(v, (str, int, float, bool)):
                samples[k] = str(v)[:80]
            elif isinstance(v, list):
                samples[k] = f"list[{len(v)}]"
            elif isinstance(v, dict):
                samples[k] = f"dict({', '.join(list(v.keys())[:3])})"

        return {
            "type": "object",
            "keys": len(data),
            "top_keys": keys,
            "signals": signals,
            "samples": samples,
            "size": len(json.dumps(data)),
        }

    elif isinstance(data, list):
        return {
            "type": "array",
            "length": len(data),
            "signals": ["COLLECTION"],
            "sample": str(data[0])[:100] if data else "empty",
            "size": len(json.dumps(data)),
        }

    else:
        return {"type": type(data).__name__, "summary": str(data)[:100], "size": len(str(data))}


def classify_flow(payload_summary):
    """Classify a data flow by its real-world value."""
    signals = payload_summary.get("signals", [])
    size = payload_summary.get("size", 0)

    if "REVENUE" in signals:
        return "revenue", "high"
    if "KNOWLEDGE" in signals:
        return "knowledge", "high"
    if "TOPOLOGY" in signals:
        return "meta", "medium"
    if "EVOLUTION" in signals:
        return "evolution", "medium"
    if "SOCIAL" in signals:
        return "social", "medium"
    if "SECURITY" in signals:
        return "security", "high"
    if "HEALTH" in signals:
        return "health", "medium"
    if size < 50:
        return "seed", "low"
    return "data", "medium"


def build_flow_matrix(wire_report):
    """Build the full flow matrix: who sends what to whom."""
    engines = wire_report.get("engines", {})
    wires = wire_report.get("wires", [])

    # Map every data file to its payload summary
    file_payloads = {}
    for f in sorted(DATA.glob("*.json")):
        data = load_json(f)
        file_payloads[f.name] = summarize_payload(data)

    # Build flow entries
    flows = []
    for wire in wires:
        via = wire.get("via", "")
        payload = file_payloads.get(via, {"type": "unknown", "signals": [], "size": 0})
        category, priority = classify_flow(payload)

        flows.append({
            "from": wire["from"],
            "to": wire["to"],
            "via": via,
            "category": category,
            "priority": priority,
            "payload_type": payload.get("type", "unknown"),
            "payload_size": payload.get("size", 0),
            "signals": payload.get("signals", []),
            "samples": payload.get("samples", {}),
        })

    return flows, file_payloads


def find_dead_flows(flows):
    """Find wires carrying nothing useful."""
    dead = []
    for f in flows:
        if f["payload_size"] < 50 and f["category"] == "seed":
            dead.append(f)
    return dead


def find_high_value_flows(flows):
    """Find the most valuable data flows."""
    return [f for f in flows if f["priority"] == "high"]


def build_hub_analysis(flows):
    """Which engines are the biggest data hubs?"""
    hub_in = {}   # engine -> count of incoming flows
    hub_out = {}  # engine -> count of outgoing flows

    for f in flows:
        hub_out[f["from"]] = hub_out.get(f["from"], 0) + 1
        hub_in[f["to"]] = hub_in.get(f["to"], 0) + 1

    # Top producers (most outgoing)
    top_producers = sorted(hub_out.items(), key=lambda x: -x[1])[:20]
    # Top consumers (most incoming)
    top_consumers = sorted(hub_in.items(), key=lambda x: -x[1])[:20]

    return top_producers, top_consumers


def build_html_dashboard(report):
    """Generate the observatory HTML dashboard."""
    flows = report["flows"]
    hv = report["high_value_flows"]
    dead = report["dead_flows"]
    producers = report["top_producers"]
    consumers = report["top_consumers"]
    cats = report["category_breakdown"]

    hv_rows = ""
    for f in hv[:30]:
        samples_str = ", ".join(f"{k}: {v}" for k, v in list(f.get("samples", {}).items())[:3])
        hv_rows += f"""<tr>
            <td>{f['from']}</td>
            <td>{f['via']}</td>
            <td>{f['to']}</td>
            <td><span class="signal">{', '.join(f['signals'])}</span></td>
            <td>{f['payload_size']:,}</td>
            <td class="samples">{samples_str[:120]}</td>
        </tr>\n"""

    dead_rows = ""
    for f in dead[:20]:
        dead_rows += f"<tr><td>{f['from']}</td><td>{f['via']}</td><td>{f['to']}</td><td>{f['payload_size']}</td></tr>\n"

    prod_rows = ""
    for name, count in producers:
        prod_rows += f"<tr><td>{name}</td><td>{count}</td></tr>\n"

    cons_rows = ""
    for name, count in consumers:
        cons_rows += f"<tr><td>{name}</td><td>{count}</td></tr>\n"

    cat_rows = ""
    for cat, info in sorted(cats.items(), key=lambda x: -x[1]["count"]):
        cat_rows += f"<tr><td>{cat}</td><td>{info['count']}</td><td>{info['priority']}</td></tr>\n"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>SolarPunk Observatory -- Data Flow Map</title>
<style>
body {{ background: #0a0a0a; color: #e0e0e0; font-family: 'Courier New', monospace; margin: 20px; }}
h1 {{ color: #00ff88; text-align: center; }}
h2 {{ color: #00ccff; border-bottom: 1px solid #333; padding-bottom: 5px; }}
.stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
.stat {{ background: #1a1a2e; border: 1px solid #333; border-radius: 8px; padding: 15px; text-align: center; }}
.stat .num {{ font-size: 2em; color: #00ff88; font-weight: bold; }}
.stat .label {{ color: #888; font-size: 0.9em; }}
table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
th {{ background: #1a1a2e; color: #00ccff; padding: 8px; text-align: left; }}
td {{ padding: 6px 8px; border-bottom: 1px solid #222; }}
tr:hover {{ background: #1a1a2e; }}
.signal {{ background: #003322; color: #00ff88; padding: 2px 6px; border-radius: 3px; font-size: 0.85em; }}
.samples {{ color: #888; font-size: 0.85em; max-width: 300px; overflow: hidden; text-overflow: ellipsis; }}
.high {{ color: #ff4444; }} .medium {{ color: #ffaa00; }} .low {{ color: #666; }}
.grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
</style>
</head>
<body>
<h1>SolarPunk Data Flow Observatory</h1>
<p style="text-align:center;color:#888;">Generated: {report['timestamp']} | God's-eye view of the nervous system</p>

<div class="stats">
  <div class="stat"><div class="num">{report['total_flows']}</div><div class="label">Total Flows</div></div>
  <div class="stat"><div class="num">{len(hv)}</div><div class="label">High-Value Flows</div></div>
  <div class="stat"><div class="num">{len(dead)}</div><div class="label">Dead Flows</div></div>
  <div class="stat"><div class="num">{report['unique_data_files']}</div><div class="label">Data Files Active</div></div>
  <div class="stat"><div class="num">{report['total_payload_bytes']:,}</div><div class="label">Total Bytes Flowing</div></div>
</div>

<h2>Flow Categories</h2>
<table><tr><th>Category</th><th>Flows</th><th>Priority</th></tr>{cat_rows}</table>

<h2>High-Value Flows (Revenue, Knowledge, Security)</h2>
<table><tr><th>From</th><th>Via</th><th>To</th><th>Signals</th><th>Bytes</th><th>Sample Data</th></tr>{hv_rows}</table>

<div class="grid">
<div>
<h2>Top Data Producers</h2>
<table><tr><th>Engine</th><th>Outgoing Flows</th></tr>{prod_rows}</table>
</div>
<div>
<h2>Top Data Consumers</h2>
<table><tr><th>Engine</th><th>Incoming Flows</th></tr>{cons_rows}</table>
</div>
</div>

<h2>Dead Flows (< 50 bytes, seed only)</h2>
<table><tr><th>From</th><th>Via</th><th>To</th><th>Bytes</th></tr>{dead_rows}</table>

<p style="text-align:center;color:#444;margin-top:30px;">
Observatory built by DATA_FLOW_OBSERVATORY | Ethics: 99% mutual aid / 1% infrastructure
</p>
</body></html>"""

    return html


def run():
    print("DATA FLOW OBSERVATORY -- God's-Eye View")
    print("=" * 50)

    wire_report = load_json(DATA / "live_wire_report.json")
    if not wire_report:
        print("  No live_wire_report.json -- run LIVE_WIRE first")
        return

    stats = wire_report.get("stats", {})
    print(f"  Topology: {stats.get('total_engines', 0)} engines, {stats.get('total_wires_discovered', 0)} wires")

    # Build flow matrix
    print("\n  [1/5] Mapping all data flows...")
    flows, file_payloads = build_flow_matrix(wire_report)
    print(f"    Mapped {len(flows)} flows across {len(file_payloads)} data files")

    # Classify flows
    print("\n  [2/5] Classifying flow values...")
    categories = {}
    for f in flows:
        cat = f["category"]
        if cat not in categories:
            categories[cat] = {"count": 0, "priority": f["priority"]}
        categories[cat]["count"] += 1

    for cat, info in sorted(categories.items(), key=lambda x: -x[1]["count"]):
        print(f"    {cat}: {info['count']} flows ({info['priority']} priority)")

    # Find high-value flows
    print("\n  [3/5] Identifying high-value flows...")
    high_value = find_high_value_flows(flows)
    print(f"    Found {len(high_value)} high-value flows (revenue, knowledge, security)")
    for f in high_value[:5]:
        print(f"    {f['from']} -> [{', '.join(f['signals'])}] -> {f['to']}")

    # Find dead flows
    print("\n  [4/5] Finding dead flows...")
    dead = find_dead_flows(flows)
    print(f"    Found {len(dead)} dead flows (< 50 bytes, seed only)")

    # Hub analysis
    print("\n  [5/5] Analyzing data hubs...")
    top_producers, top_consumers = build_hub_analysis(flows)
    print(f"    Top producer: {top_producers[0][0]} ({top_producers[0][1]} outgoing)")
    print(f"    Top consumer: {top_consumers[0][0]} ({top_consumers[0][1]} incoming)")

    # Total payload
    total_bytes = sum(f["payload_size"] for f in flows)
    unique_files = len(set(f["via"] for f in flows))

    # Build report
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_flows": len(flows),
        "high_value_flows": high_value[:50],
        "dead_flows": dead[:30],
        "category_breakdown": categories,
        "top_producers": top_producers,
        "top_consumers": top_consumers,
        "total_payload_bytes": total_bytes,
        "unique_data_files": unique_files,
        "flows": flows[:200],  # Cap for file size
    }

    (DATA / "observatory_report.json").write_text(
        json.dumps(report, indent=2, default=str, ensure_ascii=False),
        encoding="utf-8"
    )

    # Build HTML dashboard
    html = build_html_dashboard(report)
    (DOCS / "observatory.html").write_text(html, encoding="utf-8")

    print(f"\n  === OBSERVATORY REPORT ===")
    print(f"  Total flows mapped:     {len(flows)}")
    print(f"  High-value flows:       {len(high_value)}")
    print(f"  Dead flows:             {len(dead)}")
    print(f"  Total bytes flowing:    {total_bytes:,}")
    print(f"  Unique data files:      {unique_files}")
    print(f"  Report: data/observatory_report.json")
    print(f"  Dashboard: docs/observatory.html")
    print(f"\n  The thalamus sees everything. Now YOU can too.")


if __name__ == "__main__":
    run()

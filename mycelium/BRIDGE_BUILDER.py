#!/usr/bin/env python3
"""
BRIDGE_BUILDER.py — Self-Wiring Nervous System
===============================================
Reads the LIVE_WIRE report, finds the hungry inputs (data files that
engines want to read but nobody writes), and builds bridges to feed them.

Biology: When a neuron reaches out and finds nothing, the nervous system
grows a new dendrite to connect it. BRIDGE_BUILDER is that growth signal.

What this does:
  1. Reads data/live_wire_report.json (from LIVE_WIRE scan)
  2. Identifies hungry inputs and their starving engines
  3. For each hungry input, checks if related data exists elsewhere
  4. Builds bridge files by transforming existing data into the format
     the starving engines expect
  5. Documents every bridge attempt — successes AND failures

The bridges it knows how to build:
  - grants_found.json      <- from fund_scout_results.json
  - sentinel_report.json   <- from local syntax check of engines
  - knowledge_graph.json   <- from live_wire_report.json (the wiring IS the graph)
  - quick_revenue.json     <- seed from revenue_inbox.json or brain_state.json

If it can't build a bridge, it documents WHY and what data would be needed.
That failure report is itself useful — it tells the mutation lottery what to build next.

Zero secrets needed.
"""
import json
import os
import py_compile
import sys
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
DATA.mkdir(exist_ok=True)
MYCELIUM = Path("mycelium")


def load_json(path):
    """Load a JSON file, return None on failure."""
    try:
        return json.loads(Path(path).read_text())
    except Exception:
        return None


def bridge_grants_found():
    """
    Bridge: fund_scout_results.json -> grants_found.json
    FUND_SCOUT writes results; GRANT_APPLICANT, GRANT_HUNTER, and
    VITAL_SIGN_API all read grants_found.json.
    """
    source = load_json(DATA / "fund_scout_results.json")
    if not source:
        return {"status": "NO_SOURCE", "detail": "fund_scout_results.json missing or empty"}

    # Transform: extract the grants list from fund_scout results
    grants = []
    if isinstance(source, dict):
        for key in ("grants", "results", "opportunities", "funders"):
            val = source.get(key)
            if isinstance(val, list):
                grants.extend(val)

        # If it's a flat dict with grant-like fields, wrap it
        if not grants and source.get("name"):
            grants = [source]

    if isinstance(source, list):
        grants = source

    if not grants:
        grants = []

    out = DATA / "grants_found.json"
    out.write_text(json.dumps(grants, indent=2))
    return {
        "status": "BRIDGED",
        "detail": f"Transformed fund_scout_results -> grants_found ({len(grants)} grants)",
        "grants_count": len(grants)
    }


def bridge_sentinel_report():
    """
    Bridge: run local syntax check -> sentinel_report.json
    VITAL_SIGN_API reads this to show system health.
    """
    if not MYCELIUM.exists():
        return {"status": "NO_SOURCE", "detail": "mycelium/ directory not found"}

    engines = list(MYCELIUM.glob("*.py"))
    syntax_pass = 0
    syntax_fail = 0
    failures = []

    for engine in engines:
        if engine.name.startswith("__"):
            continue
        try:
            py_compile.compile(str(engine), doraise=True)
            syntax_pass += 1
        except py_compile.PyCompileError as e:
            syntax_fail += 1
            failures.append({"engine": engine.name, "error": str(e)[:200]})

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_engines": len(engines),
        "syntax_pass": syntax_pass,
        "syntax_fail": syntax_fail,
        "failures": failures[:10],
        "source": "BRIDGE_BUILDER local syntax check"
    }

    out = DATA / "sentinel_report.json"
    out.write_text(json.dumps(report, indent=2))
    return {
        "status": "BRIDGED",
        "detail": f"Local sentinel: {syntax_pass} pass, {syntax_fail} fail out of {len(engines)} engines",
        "pass": syntax_pass,
        "fail": syntax_fail
    }


def bridge_knowledge_graph():
    """
    Bridge: live_wire_report.json -> knowledge_graph.json
    The wiring topology IS the knowledge graph.
    Feeds: MISSION_CONTROL, SYNAPSE_BUILDER, SYNERGY_SCOUT, VALUE_GENERATOR
    """
    wire_report = load_json(DATA / "live_wire_report.json")
    if not wire_report:
        return {"status": "NO_SOURCE", "detail": "live_wire_report.json missing -- run LIVE_WIRE first"}

    nodes = {}
    edges = []

    for name, info in wire_report.get("engines", {}).items():
        nodes[name] = {
            "type": "engine",
            "zero_secrets": info.get("zero_secrets", False),
            "has_run": info.get("has_run", False),
            "lines": info.get("lines", 0),
            "reads": info.get("reads", []),
            "writes": info.get("writes", []),
        }

    for wire in wire_report.get("wires", []):
        edges.append({
            "from": wire["from"],
            "to": wire["to"],
            "via": wire["via"],
            "zero_secrets": wire.get("chain_zero_secrets", False),
        })

    data_files = set()
    for wire in wire_report.get("wires", []):
        data_files.add(wire["via"])
    for df in data_files:
        nodes[f"data/{df}"] = {"type": "data_file"}

    # Hub scores — most connected nodes
    hub_scores = {}
    for edge in edges:
        hub_scores[edge["from"]] = hub_scores.get(edge["from"], 0) + 1
        hub_scores[edge["to"]] = hub_scores.get(edge["to"], 0) + 1

    top_hubs = sorted(hub_scores.items(), key=lambda x: x[1], reverse=True)[:15]

    graph = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "top_hubs": [{"name": n, "connections": c} for n, c in top_hubs],
        "nodes": nodes,
        "edges": edges[:500],
        "source": "BRIDGE_BUILDER from LIVE_WIRE topology",
        "note": "The wiring IS the knowledge. This graph shows how engines connect."
    }

    out = DATA / "knowledge_graph.json"
    out.write_text(json.dumps(graph, indent=2))
    return {
        "status": "BRIDGED",
        "detail": f"Knowledge graph: {len(nodes)} nodes, {len(edges)} edges, top hub: {top_hubs[0][0] if top_hubs else 'none'}",
        "nodes": len(nodes),
        "edges": len(edges),
        "top_hubs": top_hubs[:5]
    }


def bridge_quick_revenue():
    """
    Bridge: brain_state.json + revenue_inbox.json -> quick_revenue.json
    Feeds: QUICK_REVENUE, RESONANCE_CONVERTER
    """
    brain = load_json(DATA / "brain_state.json")
    revenue = load_json(DATA / "revenue_inbox.json")

    if not brain and not revenue:
        return {"status": "NO_SOURCE", "detail": "Neither brain_state nor revenue_inbox found"}

    qr = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_revenue": 0,
        "pending_actions": [],
        "source": "BRIDGE_BUILDER synthesis"
    }

    if isinstance(revenue, dict):
        qr["total_revenue"] = revenue.get("total", 0)
        qr["transactions"] = revenue.get("transactions", [])[:10]
    elif isinstance(revenue, list):
        qr["transactions"] = revenue[:10]
        qr["total_revenue"] = sum(t.get("amount", 0) for t in revenue if isinstance(t, dict))

    if isinstance(brain, dict):
        qr["system_health"] = brain.get("health", 0)
        qr["brain_cycles"] = brain.get("cycles", 0)

    out = DATA / "quick_revenue.json"
    out.write_text(json.dumps(qr, indent=2))
    return {
        "status": "BRIDGED",
        "detail": f"Quick revenue synthesized from brain_state + revenue_inbox",
        "revenue": qr["total_revenue"]
    }


BRIDGES = {
    "grants_found.json": bridge_grants_found,
    "sentinel_report.json": bridge_sentinel_report,
    "knowledge_graph.json": bridge_knowledge_graph,
    "quick_revenue.json": bridge_quick_revenue,
}


def run():
    print("BRIDGE BUILDER -- Self-Wiring Nervous System")
    print("=" * 50)

    wire_report = load_json(DATA / "live_wire_report.json")
    if wire_report:
        hungry = wire_report.get("orphans", {}).get("hungry_inputs", [])
        print(f"  Hungry inputs found: {len(hungry)}")
    else:
        hungry = list(BRIDGES.keys())
        print(f"  No live_wire_report -- running all known bridges")

    results = []
    bridges_built = 0
    bridges_failed = 0

    for data_file, bridge_fn in BRIDGES.items():
        print(f"\n  Bridge: {data_file}")
        try:
            result = bridge_fn()
            result["target"] = data_file
            results.append(result)

            if result["status"] == "BRIDGED":
                bridges_built += 1
                print(f"    CONNECTED: {result['detail']}")
            else:
                bridges_failed += 1
                print(f"    FAILED: {result['detail']}")
        except Exception as e:
            bridges_failed += 1
            result = {
                "target": data_file,
                "status": "ERROR",
                "detail": str(e)[:200]
            }
            results.append(result)
            print(f"    ERROR: {e}")

    # Check for unbridged hungry inputs
    unbridged = []
    for h in hungry:
        if h not in BRIDGES and h != "something" and not h.startswith("|"):
            unbridged.append(h)

    if unbridged:
        print(f"\n  Unbridged hungry inputs ({len(unbridged)}):")
        for u in unbridged:
            print(f"    - {u} (no bridge function yet)")

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "bridges_attempted": len(results),
        "bridges_built": bridges_built,
        "bridges_failed": bridges_failed,
        "unbridged_inputs": unbridged,
        "results": results,
        "note": "Successes AND failures documented. Both are useful."
    }

    out = DATA / "bridge_report.json"
    out.write_text(json.dumps(report, indent=2))
    print(f"\n  Report saved: {out}")

    print(f"\n  === BRIDGE REPORT ===")
    print(f"  Bridges built:    {bridges_built}")
    print(f"  Bridges failed:   {bridges_failed}")
    print(f"  Still unbridged:  {len(unbridged)}")
    print(f"  New synapses:     {bridges_built} hungry inputs now have data")
    print(f"\n  The nervous system just grew new dendrites.")


if __name__ == "__main__":
    run()

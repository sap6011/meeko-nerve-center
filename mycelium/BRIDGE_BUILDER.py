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


def seed_json(filename, content):
    """Create a seed file if it doesn't exist or is empty."""
    out = DATA / filename
    if out.exists() and out.stat().st_size > 5:
        return {"status": "ALREADY_EXISTS", "detail": f"{filename} already has data"}
    out.write_text(json.dumps(content, indent=2))
    return {"status": "BRIDGED", "detail": f"Seeded {filename}"}


def seed_text(filename, content):
    """Create a seed text file if it doesn't exist or is empty."""
    out = DATA / filename
    if out.exists() and out.stat().st_size > 2:
        return {"status": "ALREADY_EXISTS", "detail": f"{filename} already has data"}
    out.write_text(content)
    return {"status": "BRIDGED", "detail": f"Seeded {filename}"}


def bridge_social_queue():
    """Seed SOCIAL_QUEUE.txt for SOCIAL_ECHO."""
    return seed_text("SOCIAL_QUEUE.txt", "")


def bridge_brave_browser_state():
    """Seed brave_browser_state.json for BRAVE_BROWSER_ENGINE."""
    return seed_json("brave_browser_state.json", {
        "initialized": True,
        "last_run": None,
        "source": "BRIDGE_BUILDER seed"
    })


def bridge_conversion_log():
    """Seed conversion_log.json for RESONANCE_CONVERTER."""
    return seed_json("conversion_log.json", {
        "conversions": [],
        "total": 0,
        "source": "BRIDGE_BUILDER seed"
    })


def bridge_desktop_daemon_state():
    """Seed desktop_daemon_state.json for DESKTOP_DAEMON."""
    return seed_json("desktop_daemon_state.json", {
        "running": False,
        "last_cycle": None,
        "tasks_completed": 0,
        "source": "BRIDGE_BUILDER seed"
    })


def bridge_knowledge_bank():
    """
    Bridge: synthesize knowledge_bank.txt from live_wire + research data.
    Feeds: GMAIL_INTAKE, NETWORK_SENTRY, NEWS_HARVESTER (3 engines)
    """
    lines = ["# SolarPunk Knowledge Bank", "# Auto-generated by BRIDGE_BUILDER", ""]

    # Pull from knowledge graph if available
    kg = load_json(DATA / "knowledge_graph.json")
    if kg:
        hubs = kg.get("top_hubs", [])
        lines.append(f"## Top Hub Engines ({len(hubs)} most connected)")
        for h in hubs[:10]:
            lines.append(f"- {h['name']}: {h['connections']} connections")
        lines.append("")

    # Pull from bridge report
    br = load_json(DATA / "bridge_report.json")
    if br:
        lines.append(f"## System Bridges: {br.get('bridges_built', 0)} active")
        lines.append("")

    # Pull from sentinel
    sr = load_json(DATA / "sentinel_report.json")
    if sr:
        lines.append(f"## Health: {sr.get('syntax_pass', 0)}/{sr.get('total_engines', 0)} engines passing")
        lines.append("")

    out = DATA / "knowledge_bank.txt"
    out.write_text("\n".join(lines))
    return {"status": "BRIDGED", "detail": f"Knowledge bank synthesized ({len(lines)} lines, feeds 3 engines)"}


def bridge_neuron_reports():
    """
    Seed neuron_a_report.json and neuron_b_report.json for cross-neuron comms.
    Feeds: NEURON_A, NEURON_B
    """
    for name in ["neuron_a_report.json", "neuron_b_report.json"]:
        out = DATA / name
        if not out.exists() or out.stat().st_size < 5:
            out.write_text(json.dumps({
                "neuron": name.replace("_report.json", ""),
                "status": "awaiting_first_activation",
                "signals": [],
                "source": "BRIDGE_BUILDER seed"
            }, indent=2))
    return {"status": "BRIDGED", "detail": "Neuron A+B reports seeded for cross-neuron comms"}


def bridge_newsletter_subscribers():
    """Seed newsletter_subscribers.json for NEWSLETTER_ENGINE."""
    return seed_json("newsletter_subscribers.json", {
        "subscribers": [],
        "total": 0,
        "source": "BRIDGE_BUILDER seed — add subscribers via work.html tasks"
    })


def bridge_pending_publication():
    """Seed pending_publication.txt for VALUE_GENERATOR."""
    return seed_text("pending_publication.txt", "")


def bridge_resurrections():
    """Seed resurrections.json for DESKTOP_ORCHESTRATOR."""
    return seed_json("resurrections.json", {
        "resurrected": [],
        "total": 0,
        "source": "BRIDGE_BUILDER seed"
    })


def bridge_sponsors_inbox():
    """Seed sponsors_inbox.json for GITHUB_SPONSORS_ENGINE."""
    return seed_json("sponsors_inbox.json", {
        "sponsors": [],
        "total": 0,
        "source": "BRIDGE_BUILDER seed — activate via GitHub Sponsors"
    })


def bridge_storefront_builder_state():
    """Seed storefront_builder_state.json for STOREFRONT_BUILDER."""
    return seed_json("storefront_builder_state.json", {
        "initialized": True,
        "products": [],
        "last_build": None,
        "source": "BRIDGE_BUILDER seed"
    })


def bridge_synergy_mutations():
    """
    Seed synergy_mutations.txt for SYNERGY_FORGE.
    Pull from mutation_vault if available.
    """
    mv = load_json(DATA / "mutation_vault.json")
    lines = ["# Synergy Mutations Log", "# Auto-generated by BRIDGE_BUILDER", ""]
    if mv and isinstance(mv, dict):
        mutations = mv.get("mutations", [])
        for m in mutations[:20]:
            lines.append(f"- {m.get('name', 'unknown')}: {m.get('parents', 'n/a')}")
    elif mv and isinstance(mv, list):
        for m in mv[:20]:
            if isinstance(m, dict):
                lines.append(f"- {m.get('name', 'unknown')}")
    out = DATA / "synergy_mutations.txt"
    out.write_text("\n".join(lines))
    return {"status": "BRIDGED", "detail": f"Synergy mutations seeded ({len(lines)} lines)"}


def bridge_system_directive():
    """Seed system_directive.json for GUMROAD_PRODUCT_PUBLISHER."""
    return seed_json("system_directive.json", {
        "directive": "publish",
        "auto_approve": False,
        "revenue_routing": {"food_bank": 0.20, "operations": 0.80},
        "source": "BRIDGE_BUILDER seed — 20% food bank hard-coded"
    })


def bridge_newsletter_archive():
    """
    Bridge: product_registry.json + brain_state -> newsletter_archive.json
    Feeds: RSS_PUBLISHER
    """
    products = load_json(DATA / "product_registry.json")
    brain = load_json(DATA / "brain_state.json")

    entries = []
    if isinstance(products, dict):
        for slug, prod in products.items():
            if isinstance(prod, dict) and prod.get("status") == "ready":
                entries.append({
                    "title": prod.get("title", slug),
                    "type": "product_launch",
                    "words": prod.get("word_count", 0),
                })

    archive = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "newsletters": entries,
        "total_sent": 0,
        "brain_cycles": brain.get("cycles", 0) if isinstance(brain, dict) else 0,
        "source": "BRIDGE_BUILDER synthesis from product_registry + brain_state"
    }
    (DATA / "newsletter_archive.json").write_text(json.dumps(archive, indent=2))
    return {"status": "BRIDGED", "detail": f"Newsletter archive: {len(entries)} entries from product registry"}


def bridge_river_watch():
    """
    Bridge: fund_scout_results + sentinel -> river_watch.json
    Feeds: VITAL_SIGN_API, ECOLOGICAL_GRANT_SYNTHESIZER
    """
    sentinel = load_json(DATA / "sentinel_report.json")
    fund = load_json(DATA / "fund_scout_results.json")

    watch = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "waterways": [],
        "alerts": [],
        "status": "monitoring",
        "source": "BRIDGE_BUILDER synthesis"
    }

    if isinstance(sentinel, dict) and sentinel.get("syntax_fail", 0) > 0:
        watch["alerts"].append({
            "type": "code_health",
            "message": f"{sentinel['syntax_fail']} engines have syntax errors",
            "severity": "warning"
        })

    if isinstance(fund, dict):
        grants = fund.get("grants", fund.get("results", []))
        if isinstance(grants, list):
            for g in grants[:5]:
                if isinstance(g, dict) and any(k in str(g).lower() for k in ["water", "river", "ecology", "environment"]):
                    watch["waterways"].append(g)

    (DATA / "river_watch.json").write_text(json.dumps(watch, indent=2))
    return {"status": "BRIDGED", "detail": f"River watch: {len(watch['alerts'])} alerts, {len(watch['waterways'])} waterways"}


def bridge_desktop_blueprints():
    """
    Bridge: sentinel_report + live_wire -> desktop_blueprints.json
    Feeds: BRAVE_BRIDGE, DESKTOP_BLUEPRINT_SCANNER, DESKTOP_ORCHESTRATOR
    """
    sentinel = load_json(DATA / "sentinel_report.json")

    blueprints = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "blueprints": [],
        "scripts_found": 0,
        "note": "Populated from sentinel data. Full scan requires local run.",
        "source": "BRIDGE_BUILDER synthesis"
    }

    if isinstance(sentinel, dict):
        blueprints["scripts_found"] = sentinel.get("total_engines", 0)
        for fail in sentinel.get("failures", []):
            blueprints["blueprints"].append({
                "name": fail.get("engine", "unknown"),
                "status": "needs_repair",
                "error": fail.get("error", "")[:100]
            })

    (DATA / "desktop_blueprints.json").write_text(json.dumps(blueprints, indent=2))
    return {"status": "BRIDGED", "detail": f"Desktop blueprints: {blueprints['scripts_found']} scripts, {len(blueprints['blueprints'])} need repair"}


def bridge_orphan_tweets():
    """
    Bridge: tweets_queue.txt -> social_queue.json (connect orphan output)
    tweets_queue.txt is written but never read. Route it into social_queue.json.
    """
    tweets_path = DATA / "tweets_queue.txt"
    if not tweets_path.exists():
        return {"status": "NO_SOURCE", "detail": "tweets_queue.txt not found"}

    tweets_text = tweets_path.read_text().strip()
    if not tweets_text:
        return {"status": "ALREADY_EXISTS", "detail": "tweets_queue.txt is empty"}

    # Append to social_queue.json
    sq = load_json(DATA / "social_queue.json") or {"posts": [], "source": "aggregated"}
    if isinstance(sq, list):
        sq = {"posts": sq, "source": "aggregated"}

    tweets = [t.strip() for t in tweets_text.split("\n") if t.strip()]
    for t in tweets[:10]:
        sq.setdefault("posts", []).append({"text": t, "source": "tweets_queue", "status": "pending"})

    (DATA / "social_queue.json").write_text(json.dumps(sq, indent=2))
    return {"status": "BRIDGED", "detail": f"Routed {len(tweets)} tweets from orphan tweets_queue.txt -> social_queue.json"}


def bridge_orphan_daemon_task():
    """
    Bridge: daemon_task.xml -> desktop_daemon_state.json (connect orphan output)
    daemon_task.xml is written but never read. Extract info into daemon state.
    """
    xml_path = DATA / "daemon_task.xml"
    if not xml_path.exists():
        return {"status": "NO_SOURCE", "detail": "daemon_task.xml not found"}

    content = xml_path.read_text().strip()
    if not content:
        return {"status": "ALREADY_EXISTS", "detail": "daemon_task.xml is empty"}

    state = load_json(DATA / "desktop_daemon_state.json") or {}
    state["last_task_xml"] = content[:500]
    state["xml_present"] = True
    state["updated_by_bridge"] = datetime.now(timezone.utc).isoformat()

    (DATA / "desktop_daemon_state.json").write_text(json.dumps(state, indent=2))
    return {"status": "BRIDGED", "detail": "Routed daemon_task.xml content -> desktop_daemon_state.json"}


BRIDGES = {
    "grants_found.json": bridge_grants_found,
    "sentinel_report.json": bridge_sentinel_report,
    "knowledge_graph.json": bridge_knowledge_graph,
    "quick_revenue.json": bridge_quick_revenue,
    # --- Waiting Wire Bridges (make 8 waiting wires go LIVE) ---
    "newsletter_archive.json": bridge_newsletter_archive,
    "river_watch.json": bridge_river_watch,
    "desktop_blueprints.json": bridge_desktop_blueprints,
    # --- Orphan Output Bridges (connect 2 dead ends) ---
    "tweets_queue.txt": bridge_orphan_tweets,
    "daemon_task.xml": bridge_orphan_daemon_task,
    # --- The 14 Hunger Bridges ---
    "SOCIAL_QUEUE.txt": bridge_social_queue,
    "brave_browser_state.json": bridge_brave_browser_state,
    "conversion_log.json": bridge_conversion_log,
    "desktop_daemon_state.json": bridge_desktop_daemon_state,
    "knowledge_bank.txt": bridge_knowledge_bank,
    "neuron_a_report.json": bridge_neuron_reports,
    "neuron_b_report.json": bridge_neuron_reports,
    "newsletter_subscribers.json": bridge_newsletter_subscribers,
    "pending_publication.txt": bridge_pending_publication,
    "resurrections.json": bridge_resurrections,
    "sponsors_inbox.json": bridge_sponsors_inbox,
    "storefront_builder_state.json": bridge_storefront_builder_state,
    "synergy_mutations.txt": bridge_synergy_mutations,
    "system_directive.json": bridge_system_directive,
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

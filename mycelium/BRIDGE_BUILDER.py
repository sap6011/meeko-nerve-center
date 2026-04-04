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

    tweets_text = tweets_path.read_text(encoding="utf-8", errors="replace").strip()
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


def bridge_chimera_evolution():
    """Bridge: chimera_evolution_report.json -> consumed by VITAL_SIGN_API + EVOLUTION_VIEWER."""
    chimera = load_json(DATA / "chimera_evolution_report.json")
    if not chimera:
        return {"status": "NO_SOURCE", "detail": "chimera_evolution_report.json not found -- run CHIMERA_EVOLUTION_ENGINE"}
    return {"status": "ALREADY_EXISTS", "detail": f"Chimera gen {chimera.get('generation', '?')}, score {chimera.get('composite_score', '?')}/100"}


def bridge_nanobot_heal():
    """Bridge: nanobot_heal_report.json -> consumed by VITAL_SIGN_API + CHIMERA_EVOLUTION."""
    report = load_json(DATA / "nanobot_heal_report.json")
    if not report:
        return {"status": "NO_SOURCE", "detail": "nanobot_heal_report.json not found -- run NANOBOT_HEALER"}
    return {"status": "ALREADY_EXISTS", "detail": f"Healed {report.get('healed', 0)}, scanned {report.get('scanned', 0)}"}


def bridge_mutation_leaderboard():
    """Bridge: mutation_leaderboard.json -> consumed by EVOLUTION_VIEWER dashboard."""
    lb = load_json(DATA / "mutation_leaderboard.json")
    if not lb:
        return {"status": "NO_SOURCE", "detail": "mutation_leaderboard.json not found -- run MUTATION_VAULT"}
    return {"status": "ALREADY_EXISTS", "detail": f"Leaderboard: {lb.get('total_mutations', 0)} mutations, {lb.get('total_generations', 0)} gens"}


def bridge_polymarket_scan():
    """Bridge: polymarket_scan.json -> consumed by dashboard + KNOWLEDGE_CHAIN."""
    scan = load_json(DATA / "polymarket_scan.json")
    if not scan:
        return {"status": "NO_SOURCE", "detail": "polymarket_scan.json not found -- run POLYMARKET_SCANNER"}
    return {"status": "ALREADY_EXISTS", "detail": f"Markets scanned: {scan.get('total_markets_scanned', 0)}, edges: {scan.get('edges_found', 0)}"}


def bridge_hemisphere_state():
    """Seed hemisphere_state.json for HEMISPHERE_SYNC."""
    return seed_json("hemisphere_state.json", {
        "left": {"name": "local_machine", "status": "active"},
        "right": {"name": "github_repo", "status": "active"},
        "last_sync": None,
        "source": "BRIDGE_BUILDER seed"
    })


def bridge_relay_baton():
    """Seed relay_baton.json for RELAY_BATON."""
    return seed_json("relay_baton.json", {
        "holder": "idle",
        "tasks": [],
        "last_handoff": None,
        "source": "BRIDGE_BUILDER seed"
    })


def bridge_amplification_posts():
    """Seed amplification_posts.json for AMPLIFY_ENGINE."""
    return seed_json("amplification_posts.json", {
        "posts": [], "platforms": ["twitter", "bluesky", "mastodon", "reddit"],
        "source": "BRIDGE_BUILDER seed"
    })


def bridge_amplify_cooldown():
    """Seed amplify_cooldown.json for AMPLIFY_ENGINE rate limiting."""
    return seed_json("amplify_cooldown.json", {
        "cooldowns": {}, "last_post": None,
        "source": "BRIDGE_BUILDER seed"
    })


def bridge_murmuration_trap():
    """Seed murmuration_trap_state.json for MURMURATION_RELAY."""
    return seed_json("murmuration_trap_state.json", {
        "active": False, "traps": [], "last_check": None,
        "source": "BRIDGE_BUILDER seed"
    })


def bridge_revenue_state():
    """Seed revenue_state.json from flywheel + brain state."""
    brain = load_json(DATA / "brain_state.json")
    flywheel = load_json(DATA / "flywheel_summary.json")
    state = {
        "total_revenue": flywheel.get("current_balance", 0) if flywheel else 0,
        "health_score": brain.get("health_score", 0) if brain else 0,
        "active": True,
        "source": "BRIDGE_BUILDER synthesis from brain_state + flywheel"
    }
    return seed_json("revenue_state.json", state)


def bridge_sentinel_scan():
    """Bridge: sentinel_report.json -> sentinel_scan.json (alias bridge)."""
    sentinel = load_json(DATA / "sentinel_report.json")
    if not sentinel:
        return seed_json("sentinel_scan.json", {"scanned": 0, "source": "BRIDGE_BUILDER seed"})
    # Copy sentinel data with alias name
    (DATA / "sentinel_scan.json").write_text(json.dumps(sentinel, indent=2))
    return {"status": "BRIDGED", "detail": f"Aliased sentinel_report -> sentinel_scan ({sentinel.get('syntax_pass', 0)} pass)"}


def bridge_sovereignty_state():
    """Seed sovereignty_state.json for AUTONOMY_PROOF."""
    return seed_json("sovereignty_state.json", {
        "sovereign": True, "ethics_lock": "99/1",
        "revenue_split": 0.99, "node": "SolarPunk Node-01",
        "source": "BRIDGE_BUILDER seed"
    })


def bridge_stress_backup_river_watch():
    """Bridge: river_watch.json -> _stress_backup_river_watch.json."""
    rw = load_json(DATA / "river_watch.json")
    if not rw:
        return seed_json("_stress_backup_river_watch.json", {"backup": True, "source": "BRIDGE_BUILDER seed"})
    (DATA / "_stress_backup_river_watch.json").write_text(json.dumps(rw, indent=2))
    return {"status": "BRIDGED", "detail": "Backed up river_watch -> _stress_backup_river_watch"}


def bridge_public_ledger():
    """Seed PUBLIC_LEDGER.json -- public transparency ledger."""
    return seed_json("PUBLIC_LEDGER.json", {
        "entries": [], "total_in": 0, "total_out": 0,
        "source": "BRIDGE_BUILDER seed", "note": "All transactions public"
    })


def bridge_agent_link_verifier_state():
    """Seed agent_link_verifier_state.json."""
    return seed_json("agent_link_verifier_state.json", {
        "last_run": None, "links_checked": 0, "broken": [],
        "source": "BRIDGE_BUILDER seed"
    })


def bridge_ai_council_report():
    """Bridge: knowledge_graph -> ai_council_report.json."""
    kg = load_json(DATA / "knowledge_graph.json")
    nodes = kg.get("nodes", []) if kg else []
    return seed_json("ai_council_report.json", {
        "council_members": ["ollama:mistral", "ollama:llama3", "ollama:codellama"],
        "topics_available": len(nodes),
        "last_session": None, "decisions": [],
        "source": "BRIDGE_BUILDER seed"
    })


def bridge_art_log():
    """Seed art_log.json for ART_GENERATOR."""
    catalog = load_json(DATA / "art_catalog.json")
    items = catalog.get("items", []) if catalog else []
    return seed_json("art_log.json", {
        "generated": len(items), "entries": [],
        "source": "BRIDGE_BUILDER seed"
    })


def bridge_atomizer_state():
    """Seed atomizer_state.json for TASK_ATOMIZER."""
    return seed_json("atomizer_state.json", {
        "tasks_split": 0, "last_run": None,
        "source": "BRIDGE_BUILDER seed"
    })


def bridge_claude_autonomous_report():
    """Seed claude_autonomous_report.json."""
    return seed_json("claude_autonomous_report.json", {
        "sessions": 0, "tasks_completed": 0, "engines_built": 0,
        "last_session": None, "source": "BRIDGE_BUILDER seed"
    })


def bridge_compound_tracker():
    """Seed compound_tracker.json for revenue compounding."""
    return seed_json("compound_tracker.json", {
        "compounds": [], "total_reinvested": 0,
        "source": "BRIDGE_BUILDER seed"
    })


def bridge_cycle_memory():
    """Bridge: chimera evolution -> cycle_memory.json."""
    chimera = load_json(DATA / "chimera_evolution_report.json")
    if chimera:
        return seed_json("cycle_memory.json", {
            "cycles": [{"generation": chimera.get("generation", 0),
                        "score": chimera.get("composite_score", 0),
                        "timestamp": chimera.get("timestamp")}],
            "source": "BRIDGE_BUILDER from chimera"
        })
    return seed_json("cycle_memory.json", {"cycles": [], "source": "BRIDGE_BUILDER seed"})


def bridge_desktop_agent_log():
    """Seed desktop_agent_log.json."""
    return seed_json("desktop_agent_log.json", {
        "actions": [], "errors": [], "last_action": None,
        "source": "BRIDGE_BUILDER seed"
    })


def bridge_dual_brain_conversation():
    """Seed dual_brain_conversation.json for hemisphere sync."""
    hemi = load_json(DATA / "hemisphere_state.json")
    return seed_json("dual_brain_conversation.json", {
        "messages": [],
        "left_status": hemi.get("left", {}).get("status", "unknown") if hemi else "unknown",
        "right_status": hemi.get("right", {}).get("status", "unknown") if hemi else "unknown",
        "source": "BRIDGE_BUILDER seed"
    })


def bridge_external_signals():
    """Seed external_signals.txt."""
    return seed_text("external_signals.txt",
                     "# External signals detected by SolarPunk\n# Format: TIMESTAMP | SOURCE | SIGNAL\n")


def bridge_finance_ledger():
    """Bridge: revenue data -> finance_ledger.json."""
    rev = load_json(DATA / "revenue_inbox.json")
    balance = rev.get("total_revenue", 0) if rev else 0
    return seed_json("finance_ledger.json", {
        "balance": balance, "transactions": [], "currency": "USD",
        "ethics_lock": 0.99, "source": "BRIDGE_BUILDER seed"
    })


def bridge_handshake_results():
    """Seed handshake_results.json for EXTERNAL_HANDSHAKE."""
    return seed_json("handshake_results.json", {
        "handshakes": [], "verified": 0, "failed": 0,
        "source": "BRIDGE_BUILDER seed"
    })


def bridge_kimi_conductor_report():
    """Seed kimi_conductor_report.json."""
    return seed_json("kimi_conductor_report.json", {
        "sessions": [], "orchestrations": 0, "last_run": None,
        "source": "BRIDGE_BUILDER seed"
    })


def bridge_known_devices():
    """Seed known_devices.json for mesh network."""
    return seed_json("known_devices.json", {
        "devices": [{"name": "meeko-desktop", "type": "primary", "status": "online"}],
        "source": "BRIDGE_BUILDER seed"
    })


def bridge_local_needs_radar():
    """Seed local_needs_radar.json for community needs tracking."""
    return seed_json("local_needs_radar.json", {
        "needs": [], "ward": "ward8", "last_scan": None,
        "source": "BRIDGE_BUILDER seed"
    })


def bridge_master_config():
    """Seed master_config.json with system defaults."""
    return seed_json("master_config.json", {
        "system": "SolarPunk Nerve Center",
        "ethics_lock": 0.99, "revenue_split": {"mutual_aid": 0.99, "infrastructure": 0.01},
        "ollama_models": ["mistral", "llama3", "codellama"],
        "source": "BRIDGE_BUILDER seed"
    })


def bridge_mutual_aid_routing():
    """Seed mutual_aid_routing.json with distribution rules."""
    return seed_json("mutual_aid_routing.json", {
        "routes": [
            {"org": "PCRF", "share": 0.60},
            {"org": "IRC", "share": 0.15},
            {"org": "MSF", "share": 0.10},
            {"org": "UNICEF", "share": 0.10},
            {"org": "Direct Relief", "share": 0.05}
        ],
        "source": "BRIDGE_BUILDER seed"
    })


def bridge_neural_weights():
    """Seed neural_weights.json for NEURAL_PREFERENCE."""
    return seed_json("neural_weights.json", {
        "weights": {}, "reinforcements": 0, "last_update": None,
        "source": "BRIDGE_BUILDER seed"
    })


def bridge_open_loops():
    """Seed open_loops.json for task tracking."""
    baton = load_json(DATA / "relay_baton.json")
    pending = [t for t in baton.get("tasks", []) if t.get("status") == "pending"] if baton else []
    return seed_json("open_loops.json", {
        "loops": [{"desc": t.get("description", ""), "from": "relay_baton"} for t in pending[:10]],
        "source": "BRIDGE_BUILDER seed"
    })


def bridge_product_ideas():
    """Seed product_ideas.txt from knowledge graph."""
    return seed_text("product_ideas.txt",
                     "# SolarPunk Product Ideas\n# Auto-generated by BRIDGE_BUILDER\n"
                     "1. Palestine Solidarity Art Pack\n"
                     "2. AI Side Income Blueprint\n"
                     "3. Grant Writing Templates\n"
                     "4. GitHub Actions for Beginners\n")


def bridge_reminders():
    """Seed reminders.json."""
    return seed_json("reminders.json", {"reminders": [], "source": "BRIDGE_BUILDER seed"})


def bridge_revenue_data():
    """Bridge: revenue_inbox -> revenue_data.json."""
    rev = load_json(DATA / "revenue_inbox.json")
    return seed_json("revenue_data.json", {
        "total": rev.get("total_revenue", 0) if rev else 0,
        "streams": rev.get("streams", []) if rev else [],
        "source": "BRIDGE_BUILDER seed"
    })


def bridge_secrets():
    """Seed secrets.json (no actual secrets -- just structure)."""
    return seed_json("secrets.json", {
        "note": "API keys loaded from environment variables, not stored here",
        "env_keys_needed": ["GROQ_API_KEY", "OPENAI_API_KEY"],
        "source": "BRIDGE_BUILDER seed"
    })


def bridge_self_wiring_report():
    """self_wiring_report.json is written by SELF_WIRING_ENGINE -- skip."""
    out = DATA / "self_wiring_report.json"
    if out.exists():
        return {"status": "ALREADY_EXISTS", "detail": "Written by SELF_WIRING_ENGINE"}
    return {"status": "SKIPPED", "detail": "Run SELF_WIRING_ENGINE to generate"}


def bridge_system_manifest():
    """Bridge: live_wire_report -> system_manifest.json."""
    wire = load_json(DATA / "live_wire_report.json")
    stats = wire.get("stats", {}) if wire else {}
    return seed_json("system_manifest.json", {
        "name": "SolarPunk Nerve Center",
        "engines": stats.get("total_engines", 0),
        "wires": stats.get("total_wires_discovered", 0),
        "zero_secret_chains": stats.get("zero_secret_chains", 0),
        "source": "BRIDGE_BUILDER from live_wire"
    })


def bridge_system_wants_next():
    """Bridge: self_wiring_report -> system_wants_next.json."""
    sw = load_json(DATA / "self_wiring_report.json")
    wirable = sw.get("wirable_engines", []) if sw else []
    return seed_json("system_wants_next.json", {
        "wants": [{"action": "wire", "engine": e} for e in wirable[:10]],
        "source": "BRIDGE_BUILDER from self_wiring"
    })


def bridge_workflow_health():
    """Bridge: nanobot_heal -> workflow_health.json."""
    heal = load_json(DATA / "nanobot_heal_report.json")
    return seed_json("workflow_health.json", {
        "healthy": heal.get("healthy_count", 0) if heal else 0,
        "broken": heal.get("broken_count", 0) if heal else 0,
        "healed": heal.get("healed_count", 0) if heal else 0,
        "source": "BRIDGE_BUILDER from nanobot_heal"
    })


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
    # --- v29: Chimera Evolution Bridges ---
    "chimera_evolution_report.json": bridge_chimera_evolution,
    "nanobot_heal_report.json": bridge_nanobot_heal,
    "mutation_leaderboard.json": bridge_mutation_leaderboard,
    "polymarket_scan.json": bridge_polymarket_scan,
    "hemisphere_state.json": bridge_hemisphere_state,
    "relay_baton.json": bridge_relay_baton,
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
    # --- v29: Last 7 unbridged hungry inputs ---
    "amplification_posts.json": bridge_amplification_posts,
    "amplify_cooldown.json": bridge_amplify_cooldown,
    "murmuration_trap_state.json": bridge_murmuration_trap,
    "revenue_state.json": bridge_revenue_state,
    "sentinel_scan.json": bridge_sentinel_scan,
    "sovereignty_state.json": bridge_sovereignty_state,
    "_stress_backup_river_watch.json": bridge_stress_backup_river_watch,
    # --- v30: 28 remaining hungry inputs ---
    "PUBLIC_LEDGER.json": bridge_public_ledger,
    "agent_link_verifier_state.json": bridge_agent_link_verifier_state,
    "ai_council_report.json": bridge_ai_council_report,
    "art_log.json": bridge_art_log,
    "atomizer_state.json": bridge_atomizer_state,
    "claude_autonomous_report.json": bridge_claude_autonomous_report,
    "compound_tracker.json": bridge_compound_tracker,
    "cycle_memory.json": bridge_cycle_memory,
    "desktop_agent_log.json": bridge_desktop_agent_log,
    "dual_brain_conversation.json": bridge_dual_brain_conversation,
    "external_signals.txt": bridge_external_signals,
    "finance_ledger.json": bridge_finance_ledger,
    "handshake_results.json": bridge_handshake_results,
    "kimi_conductor_report.json": bridge_kimi_conductor_report,
    "known_devices.json": bridge_known_devices,
    "local_needs_radar.json": bridge_local_needs_radar,
    "master_config.json": bridge_master_config,
    "mutual_aid_routing.json": bridge_mutual_aid_routing,
    "neural_weights.json": bridge_neural_weights,
    "open_loops.json": bridge_open_loops,
    "product_ideas.txt": bridge_product_ideas,
    "reminders.json": bridge_reminders,
    "revenue_data.json": bridge_revenue_data,
    "secrets.json": bridge_secrets,
    "self_wiring_report.json": bridge_self_wiring_report,
    "system_manifest.json": bridge_system_manifest,
    "system_wants_next.json": bridge_system_wants_next,
    "workflow_health.json": bridge_workflow_health,
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

#!/usr/bin/env python3
"""
KNOWLEDGE_SYNTHESIZER.py — Connects every knowledge source into one living map.

Reads from:
  - data/consolidated_knowledge.json      (master KB, mission data)
  - knowledge_ingest/processed/MYCELIUM_KNOWLEDGE_BASE.json
  - data/lessons.json                     (what failed / was learned)
  - data/capability_map.json              (what's blocked vs active)
  - data/harvested_knowledge/             (recent harvested code/data)
  - data/brain_state.json                 (current health)
  - data/loop_state.json                  (last cycle summary)
  - data/bottleneck_report.json           (bottlenecks)
  - data/neuron_a_report.json             (builder insights)
  - data/neuron_b_report.json             (skeptic insights)
  - saves/last_good_state.json            (last stable snapshot)
  - data/analytics_state.json            (what's performing)

Writes:
  - data/knowledge_map.json              (unified knowledge snapshot, used by all engines)
  - data/knowledge_graph.json            (nodes + edges graph for visualization)
  - data/consolidated_knowledge.json     (updated with new patterns)
"""
import json, os, re
from pathlib import Path
from datetime import datetime, timezone

DATA  = Path("data")
DATA.mkdir(exist_ok=True)

def load_json(p, default=None):
    try:
        f = Path(p)
        if f.exists():
            return json.loads(f.read_text(encoding="utf-8", errors="ignore"))
    except Exception: pass
    return default or {}

# ─── 1. Load all knowledge sources ────────────────────────────────────────────
def gather_all_knowledge():
    sources = {}

    # Core mission knowledge
    ck = load_json("data/consolidated_knowledge.json")
    mkb = load_json("knowledge_ingest/processed/MYCELIUM_KNOWLEDGE_BASE.json")
    sources["mission"] = ck.get("mycelium_kb", mkb).get("mission", {})
    sources["github_org"] = ck.get("mycelium_kb", mkb).get("github_organism", {})
    sources["revenue_streams"] = ck.get("mycelium_kb", mkb).get("revenue_streams", {})
    sources["grants"] = ck.get("mycelium_kb", mkb).get("grants", {})
    sources["contacts"] = ck.get("mycelium_kb", mkb).get("contacts", {})
    sources["legal"] = ck.get("mycelium_kb", mkb).get("legal", {})

    # System health
    brain = load_json("data/brain_state.json")
    sources["health_score"] = brain.get("health_score", 0)
    sources["total_engines"] = brain.get("stats", {}).get("engines_total", 0)
    sources["total_loops"] = brain.get("total_loops_completed", 0)
    sources["revenue_usd"] = brain.get("stats", {}).get("revenue", 0)

    # Capabilities
    cap = load_json("data/capability_map.json")
    sources["capabilities"] = {
        k: {"status": v.get("status","unknown"), "fix": v.get("fix",""), "blocks": v.get("blocks",[])}
        for k, v in cap.get("capabilities", {}).items()
    }
    sources["blocked_count"] = cap.get("blocked", 0)
    sources["active_count"] = cap.get("active", 0)

    # Lessons learned
    lessons = load_json("data/lessons.json", [])
    if isinstance(lessons, list):
        sources["lessons"] = [
            {"text": l.get("lesson",""), "priority": l.get("priority",""), "added": l.get("added_at","")}
            for l in lessons[:10]
        ]
    else:
        sources["lessons"] = []

    # Bottlenecks
    bn = load_json("data/bottleneck_report.json")
    sources["bottlenecks"] = bn.get("bottlenecks", [])[:5]

    # Last cycle
    loop = load_json("data/loop_state.json")
    sources["last_cycle"] = {
        "number": loop.get("cycle_number", 0),
        "summary": loop.get("cycle_summary", ""),
        "succeeded": len(loop.get("succeeded_engines", [])),
        "failed": len(loop.get("failed_engines", [])),
    }

    # Archive intelligence (from ARCHIVE_BRAIN)
    archive = load_json("data/archive_intelligence.json")
    sources["archive_guides"]   = list(archive.get("guides", {}).keys())
    sources["archive_snapshot"] = archive.get("last_good_state", {}).get("snapshot_timestamp","")

    # NEURON insights
    na = load_json("data/neuron_a_report.json")
    nb = load_json("data/neuron_b_report.json")
    sources["builder_thesis"] = na.get("builder_thesis", "")
    sources["skeptic_thesis"] = nb.get("skeptic_thesis", "")
    sources["priority_build"] = na.get("priority_build", "")
    sources["vetted_opportunities"] = nb.get("vetted_opportunities", [])[:3]

    # Analytics
    analytics = load_json("data/analytics_state.json")
    sources["analytics"] = {
        "total_posts": analytics.get("total_posts", 0),
        "top_performing": analytics.get("top_performing", [])[:3],
        "growth_rate": analytics.get("growth_rate", 0),
    }

    return sources

# ─── 2. Build knowledge graph nodes + edges ───────────────────────────────────
def build_knowledge_graph(sources):
    """Create a graph of what connects to what in this system."""
    nodes = []
    edges = []
    nid = 0

    def add_node(label, ntype, data=None):
        nonlocal nid
        nid += 1
        nodes.append({"id": nid, "label": label, "type": ntype, "data": data or {}})
        return nid

    def add_edge(src, dst, rel):
        edges.append({"source": src, "target": dst, "relation": rel})

    # Mission node
    mission_id = add_node("SolarPunk Mission", "mission", {
        "goal": "Autonomous humanitarian AI system",
        "charity": "PCRF (70% revenue)",
        "operator": "Meeko",
    })

    # Revenue chain
    gumroad_id = add_node("Gumroad", "platform", {"status": sources["capabilities"].get("gumroad",{}).get("status","unknown")})
    flywheel_id = add_node("Revenue Flywheel", "engine", {"revenue": sources["revenue_usd"]})
    kofi_id = add_node("Ko-fi", "platform", {})
    pcrf_id = add_node("PCRF", "charity", {"ein": "93-1057665", "rating": "4-star"})
    add_edge(gumroad_id, flywheel_id, "feeds_revenue")
    add_edge(kofi_id, flywheel_id, "feeds_revenue")
    add_edge(flywheel_id, pcrf_id, "donates_70pct")
    add_edge(flywheel_id, mission_id, "funds")

    # Brain chain
    neuron_a_id = add_node("NEURON_A", "engine", {"role": "builder brain"})
    neuron_b_id = add_node("NEURON_B", "engine", {"role": "skeptic brain"})
    synapse_id  = add_node("SYNAPSE", "engine", {"role": "resolver"})
    synthesis_id = add_node("SYNTHESIS_FACTORY", "engine", {"role": "build new engines"})
    add_edge(neuron_a_id, synapse_id, "reports_to")
    add_edge(neuron_b_id, synapse_id, "reports_to")
    add_edge(synapse_id, synthesis_id, "seeds")
    add_edge(synthesis_id, mission_id, "builds_toward")

    # Loop chain
    opener_id   = add_node("CYCLE_OPENER", "engine", {"role": "start each cycle"})
    conductor_id = add_node("LOOP_CONDUCTOR", "engine", {"role": "close each cycle"})
    add_edge(conductor_id, opener_id, "feeds_next_cycle")
    add_edge(opener_id, neuron_a_id, "briefs")
    add_edge(opener_id, synthesis_id, "briefs")

    # Content chain
    content_id = add_node("CONTENT_HARVESTER", "engine", {})
    substack_id = add_node("SUBSTACK_ENGINE", "engine", {})
    social_id   = add_node("SOCIAL_PROMOTER", "engine", {})
    analytics_id = add_node("ANALYTICS_ENGINE", "engine", {})
    add_edge(content_id, substack_id, "feeds")
    add_edge(content_id, social_id, "feeds")
    add_edge(social_id, analytics_id, "generates_data")
    add_edge(analytics_id, neuron_a_id, "informs")

    # Capability nodes
    for cap_name, cap_data in sources["capabilities"].items():
        status = cap_data.get("status", "unknown")
        cap_id = add_node(cap_name, "capability", {"status": status})
        if status == "active":
            add_edge(cap_id, mission_id, "enables")
        elif status == "blocked":
            add_edge(mission_id, cap_id, "blocked_by")

    # Lesson nodes
    for i, lesson in enumerate(sources["lessons"][:5]):
        lesson_id = add_node(f"Lesson {i+1}", "lesson", {"text": lesson.get("text","")[:100]})
        add_edge(lesson_id, synthesis_id, "informs")
        add_edge(lesson_id, neuron_a_id, "informs")

    return {"nodes": nodes, "edges": edges, "generated_at": datetime.now(timezone.utc).isoformat()}

# ─── 3. Scan recent harvested knowledge for patterns ─────────────────────────
def extract_harvest_patterns():
    hk = Path("data/harvested_knowledge")
    patterns = []
    if not hk.exists():
        return patterns

    # Read most recently modified .py files (ENGINE_SANITIZER's corrected copies)
    recent = sorted(hk.glob("*.py"), key=lambda f: f.stat().st_mtime, reverse=True)[:20]
    for f in recent:
        try:
            code = f.read_text(encoding="utf-8", errors="ignore")
            # Extract docstrings as patterns
            doc = re.search(r'"""(.*?)"""', code, re.DOTALL)
            if doc:
                text = doc.group(1).strip()[:200]
                if len(text) > 30:
                    patterns.append({"source": f.name, "pattern": text})
        except Exception:
            pass
    return patterns[:10]

# ─── 4. Update consolidated_knowledge.json with fresh data ────────────────────
def update_consolidated(sources, patterns):
    ck = load_json("data/consolidated_knowledge.json")
    ck.setdefault("mycelium_kb", {})
    ck["last_synthesized"] = datetime.now(timezone.utc).isoformat()
    ck["mycelium_kb"]["current_state"] = {
        "health_score": sources["health_score"],
        "total_engines": sources["total_engines"],
        "total_loops": sources["total_loops"],
        "revenue_usd": sources["revenue_usd"],
        "blocked_capabilities": sources["blocked_count"],
        "last_cycle": sources["last_cycle"],
    }
    ck["mycelium_kb"]["active_lessons"] = sources["lessons"]
    ck["mycelium_kb"]["harvest_patterns"] = patterns
    ck["mycelium_kb"]["priority_build"] = sources.get("priority_build", "")
    ck["mycelium_kb"]["builder_thesis"] = sources.get("builder_thesis", "")
    ck["mycelium_kb"]["vetted_opportunities"] = sources.get("vetted_opportunities", [])
    Path("data/consolidated_knowledge.json").write_text(
        json.dumps(ck, indent=2), encoding="utf-8"
    )
    return ck

# ─── 5. Write the unified knowledge_map.json ──────────────────────────────────
def write_knowledge_map(sources, patterns, graph):
    knowledge_map = {
        "generated_at": datetime.now(timezone.utc).isoformat(),

        # Mission
        "mission": {
            "goal": "Autonomous humanitarian art + knowledge system",
            "charity": "Palestine Children's Relief Fund (PCRF)",
            "charity_ein": "93-1057665",
            "revenue_split": "70% PCRF / 30% Meeko",
        },

        # Current state snapshot
        "system_state": {
            "health_score": sources["health_score"],
            "total_engines": sources["total_engines"],
            "total_loops": sources["total_loops"],
            "revenue_usd": sources["revenue_usd"],
            "last_cycle": sources["last_cycle"],
        },

        # Capabilities
        "capabilities": {
            "active": [k for k,v in sources["capabilities"].items() if v.get("status")=="active"],
            "blocked": [k for k,v in sources["capabilities"].items() if v.get("status")=="blocked"],
            "degraded": [k for k,v in sources["capabilities"].items() if v.get("status")=="degraded"],
        },

        # Wisdom
        "lessons": sources["lessons"],
        "bottlenecks": sources["bottlenecks"],

        # Intelligence
        "builder_thesis": sources["builder_thesis"],
        "skeptic_thesis": sources["skeptic_thesis"],
        "priority_build": sources["priority_build"],
        "opportunities": sources["vetted_opportunities"],

        # Contacts + grants (for outreach engines)
        "contacts": sources.get("contacts", {}),
        "grants": sources.get("grants", {}),
        "revenue_streams": sources.get("revenue_streams", {}),

        # Harvested patterns
        "harvest_patterns": patterns,

        # Analytics
        "analytics": sources["analytics"],

        # Graph summary
        "graph_summary": {
            "nodes": len(graph["nodes"]),
            "edges": len(graph["edges"]),
        }
    }
    Path("data/knowledge_map.json").write_text(
        json.dumps(knowledge_map, indent=2), encoding="utf-8"
    )
    return knowledge_map

def main():
    print("🧠 KNOWLEDGE_SYNTHESIZER — building unified knowledge map...")

    sources  = gather_all_knowledge()
    patterns = extract_harvest_patterns()
    graph    = build_knowledge_graph(sources)

    # Write outputs
    Path("data/knowledge_graph.json").write_text(
        json.dumps(graph, indent=2), encoding="utf-8"
    )
    print(f"   Knowledge graph: {len(graph['nodes'])} nodes, {len(graph['edges'])} edges")

    knowledge_map = write_knowledge_map(sources, patterns, graph)
    update_consolidated(sources, patterns)

    print(f"   Health: {sources['health_score']}/100 | Engines: {sources['total_engines']} | Loops: {sources['total_loops']}")
    print(f"   Capabilities: {sources['active_count']} active, {sources['blocked_count']} blocked")
    print(f"   Lessons: {len(sources['lessons'])} | Patterns from harvest: {len(patterns)}")
    print(f"   knowledge_map.json + knowledge_graph.json written")
    if sources.get("priority_build"):
        print(f"   Priority build: {sources['priority_build'][:80]}")

if __name__ == "__main__":
    main()

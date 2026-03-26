#!/usr/bin/env python3
"""
CYCLE_OPENER.py — First engine every cycle. Reads last cycle's results.
Writes data/cycle_brief.json — every engine can read this for context.

THE LOOP:
  LOOP_CONDUCTOR (end of cycle N) → loop_state.json
  CYCLE_OPENER   (start of cycle N+1) → cycle_brief.json
  All engines read cycle_brief.json → informed decisions
  LOOP_CONDUCTOR (end of cycle N+1) → loop_state.json (updated)
  ... forever
"""
import json, os
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
DATA.mkdir(exist_ok=True)

def load_json(path, default=None):
    try:
        f = Path(path)
        if f.exists():
            return json.loads(f.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        pass
    return default or {}

def build_cycle_brief():
    loop_state   = load_json("data/loop_state.json")
    brain_state  = load_json("data/brain_state.json")
    flywheel     = load_json("data/flywheel_state.json")
    omniseed     = load_json("data/omnibrain_seed.json")
    lessons      = load_json("data/lessons.json", [])
    # Knowledge ecosystem
    knowledge_map    = load_json("data/knowledge_map.json")       # from KNOWLEDGE_SYNTHESIZER
    active_caps      = load_json("data/active_capabilities.json") # from CAPABILITY_BROKER
    product_registry = load_json("data/product_registry.json")   # from PRODUCT_REGISTRY
    repo_index       = load_json("data/repo_index.json")          # from REPO_LIBRARIAN
    # OpenClaw / A2A / Physical World
    a2a_state        = load_json("data/a2a_bridge_state.json")    # from A2A_BRIDGE
    wisdom_library   = load_json("data/wisdom_library.json")      # from OPENCLAW_SKILL_SYNC
    print_state      = load_json("data/print_relay_state.json")   # from PRINT_RELAY_ENGINE
    labor_state      = load_json("data/labor_dispatch_state.json")# from LABOR_DISPATCH_ENGINE

    # Pull critical context from last cycle
    last_cycle_summary = loop_state.get("cycle_summary", "")
    succeeded_engines  = loop_state.get("succeeded_engines", [])
    failed_engines     = loop_state.get("failed_engines", [])
    top_actions        = loop_state.get("top_actions", [])
    revenue            = flywheel.get("current_balance", 0.0)
    health_score       = brain_state.get("health_score", 0)
    cycle_number       = loop_state.get("cycle_number", 0) + 1
    total_loops        = brain_state.get("total_loops_completed", 0)
    seed_instructions  = omniseed.get("instructions", [])
    key_insight        = omniseed.get("key_insight", "")

    # Critical lessons (not to repeat)
    critical_lessons = []
    if isinstance(lessons, list):
        critical_lessons = [l.get("lesson","") for l in lessons
                           if l.get("priority") in ("critical", "high")][:5]

    # Determine current phase / urgency
    if revenue == 0:
        phase = "PRE_REVENUE"
        focus = "Get first dollar. Gumroad product → publish → promote."
    elif revenue < 20:
        phase = "EARLY_REVENUE"
        focus = "Scale to $20 (Claude Pro unlock). More products, more posts."
    elif revenue < 100:
        phase = "GROWTH"
        focus = "Diversify income streams. Newsletter + affiliate + digital products."
    else:
        phase = "SCALE"
        focus = "Automate everything. Hire help. Expand Gaza Rose Gallery."

    # Capability context
    active_secrets  = active_caps.get("summary", {}).get("active_secrets", 0)
    missing_secrets = active_caps.get("summary", {}).get("missing_secrets", 0)
    priority_actions = active_caps.get("priority_actions", [])[:3]
    can_run_engines = active_caps.get("can_run_engines", [])

    # Product context
    prod_summary = product_registry.get("summary", {})
    pending_gumroad = prod_summary.get("pending_gumroad_publish", [])

    # Knowledge context
    km_state = knowledge_map.get("system_state", {})
    km_lessons = knowledge_map.get("lessons", [])
    priority_build = knowledge_map.get("priority_build","")

    # Repo health
    repo_gaps = repo_index.get("gaps", {})

    # Merge lessons from all sources
    all_lessons = list(critical_lessons)
    for l in km_lessons[:3]:
        txt = l.get("text","") if isinstance(l, dict) else str(l)
        if txt and txt not in all_lessons:
            all_lessons.append(txt)

    # Build the brief
    brief = {
        "cycle_number":      cycle_number,
        "total_loops":       total_loops,
        "generated_at":      datetime.now(timezone.utc).isoformat(),
        "phase":             phase,
        "revenue_usd":       revenue,
        "health_score":      health_score,
        "focus_this_cycle":  focus,
        "seed_instructions": seed_instructions,
        "key_insight":       key_insight,
        "top_actions":       top_actions[:5],
        "critical_lessons":  all_lessons[:5],
        "last_cycle": {
            "summary":    last_cycle_summary,
            "succeeded":  succeeded_engines[:20],
            "failed":     failed_engines[:10],
        },
        # Capability context (from CAPABILITY_BROKER)
        "capabilities": {
            "active_secrets":   active_secrets,
            "missing_secrets":  missing_secrets,
            "priority_actions": priority_actions,
            "can_run":          can_run_engines[:20],
        },
        # Product context (from PRODUCT_REGISTRY)
        "products": {
            "total":              prod_summary.get("total_products", 0),
            "deployed_to_docs":   prod_summary.get("deployed_to_docs", 0),
            "live_on_gumroad":    prod_summary.get("live_on_gumroad", 0),
            "pending_publish":    pending_gumroad[:5],
        },
        # Knowledge context (from KNOWLEDGE_SYNTHESIZER)
        "knowledge": {
            "priority_build":     priority_build,
            "graph_nodes":        knowledge_map.get("graph_summary", {}).get("nodes", 0),
        },
        # Repo health (from REPO_LIBRARIAN)
        "repo": {
            "total_engines":      repo_index.get("summary", {}).get("total_engines", 0),
            "stale_data_files":   repo_index.get("summary", {}).get("stale_data_files", 0),
            "engines_no_output":  len(repo_gaps.get("engines_with_no_output", [])),
        },
        # OpenClaw / A2A / Physical World context
        "openclaw": {
            "peers_found":         a2a_state.get("peers_found", []),
            "skills_installed":    a2a_state.get("skills_installed", []),
            "wisdom_library_size": wisdom_library.get("total_skills", 0),
            "prints_in_queue":     len(print_state.get("print_queue", [])),
            "prints_completed":    len(print_state.get("jobs_completed", [])),
            "labor_tasks_posted":  len(labor_state.get("posted_tasks", [])),
            "labor_tasks_done":    len(labor_state.get("completed_tasks", [])),
            "octo_available":      print_state.get("octo_available", False),
            "rentahuman_available": labor_state.get("rentahuman_available", False),
        },
        # Chain signals: what each major subsystem should do
        "chain_signals": {
            "revenue":   "publish product → gumroad → social → audit → flywheel",
            "content":   "generate → substack + medium → social queue → analytics",
            "brain":     "neuron_a → neuron_b → synapse → synthesis_factory → evolve",
            "health":    "health_booster → bottleneck → auto_healer → integrity check",
            "knowledge": "knowledge_synthesizer → orphan_connector → knowledge_weaver → memory_palace",
            "openclaw":  "agent_discovery → A2A_BRIDGE → swarm_healer → skill_siphon → OPENCLAW_SKILL_SYNC → SKILL_PACKAGER → PRINT_RELAY → LABOR_DISPATCH → gaza_emergency",
        }
    }

    (DATA / "cycle_brief.json").write_text(
        json.dumps(brief, indent=2), encoding="utf-8"
    )
    return brief

def main():
    print("🌅 CYCLE_OPENER — opening new cycle...")
    brief = build_cycle_brief()
    cycle = brief["cycle_number"]
    phase = brief["phase"]
    rev   = brief["revenue_usd"]
    focus = brief["focus_this_cycle"]
    prev_success = len(brief["last_cycle"]["succeeded"])
    prev_fail    = len(brief["last_cycle"]["failed"])

    print(f"   Cycle #{cycle} | Phase: {phase} | Revenue: ${rev:.2f}")
    print(f"   Last cycle: {prev_success} succeeded, {prev_fail} failed")
    print(f"   Focus: {focus}")
    if brief["seed_instructions"]:
        print(f"   Seed: {brief['seed_instructions'][0]}")
    print(f"   cycle_brief.json written → all engines can read for context")

if __name__ == "__main__":
    main()

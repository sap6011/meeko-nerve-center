#!/usr/bin/env python3
"""
LOOP_CONDUCTOR.py — Last engine every cycle. Closes the loop.
Reads ALL engine outputs. Synthesizes loop_state.json.
CYCLE_OPENER reads loop_state.json at the start of the next cycle.

THE LOOP:
  CYCLE_OPENER → (brief for all engines)
  [...all engines run...]
  LOOP_CONDUCTOR → loop_state.json → CYCLE_OPENER (next cycle)
  ... forever

This is what makes SolarPunk self-aware between cycles.
"""
import json, os, re
from pathlib import Path
from datetime import datetime, timezone

DATA    = Path("data")
MYCELIUM = Path("mycelium")
DATA.mkdir(exist_ok=True)

# ─── Engine output file map ───────────────────────────────────────────────────
# Maps engine names to the data files they write.
# LOOP_CONDUCTOR reads all of these to determine what worked this cycle.
ENGINE_OUTPUTS = {
    # Revenue chain
    "HEALTH_BOOSTER":           ["data/health_report.json"],
    "GUMROAD_ENGINE":           ["data/gumroad_state.json"],
    "GUMROAD_AUTO_QUEUE":       ["data/gumroad_auto_queue.json"],
    "GUMROAD_PRODUCT_PUBLISHER":["data/gumroad_publisher_state.json"],
    "PRODUCT_DELIVERY_ENGINE":  ["data/delivery_engine_state.json"],
    "FIRST_SALE_NOTIFIER":      ["data/first_sale_state.json"],
    "REVENUE_FLYWHEEL":         ["data/flywheel_state.json"],
    "REVENUE_AUDIT":            ["data/revenue_audit.json"],
    "PASSIVE_INCOME_ARCHITECT": ["data/passive_income_plan.json"],
    "REVENUE_LOOP":             ["data/revenue_loop_state.json"],
    "REVENUE_ENGINE":           ["data/revenue_engine_state.json"],
    "REVENUE_MONITOR":          ["data/revenue_monitor_state.json"],
    "REVENUE_RECYCLER":         ["data/revenue_recycler_state.json"],
    "revenue_aggregator":       ["data/revenue_aggregator_state.json"],

    # Brain chain
    "NEURON_A":                 ["data/neuron_a_report.json"],
    "NEURON_B":                 ["data/neuron_b_report.json"],
    "SYNAPSE":                  ["data/brain_state.json"],
    "MEMORY_PALACE":            ["data/loop_memory.json"],
    "KNOWLEDGE_WEAVER":         ["data/knowledge_graph.json"],
    "SYNAPSE_BUILDER":          ["data/knowledge_graph.json"],
    "SYNTHESIS_FACTORY":        ["data/synthesis_log.json"],
    "EVOLUTION_AGENT":          ["data/evolution_log.json"],

    # Content chain
    "CONTENT_HARVESTER":        ["data/content_harvest.json"],
    "SUBSTACK_ENGINE":          ["data/substack_state.json"],
    "MEDIUM_ENGINE":            ["data/medium_state.json"],
    "BRIEFING_ENGINE":          ["data/briefing_state.json"],
    "VIRALITY_ENGINE":          ["data/virality_report.json"],
    "GROWTH_CHAIN":             ["data/growth_curve.json"],
    "ANALYTICS_ENGINE":         ["data/analytics_state.json"],
    "NEWSLETTER_ENGINE":        ["data/newsletter_state.json"],

    # Social chain
    "SOCIAL_PROMOTER":          ["data/social_post_log.json"],
    "AGENT_TWEET_WRITER":       ["data/agent_tweet_writer_state.json"],
    "BLUESKY_ENGINE":           ["data/bluesky_engine_state.json"],
    "MASTODON_ENGINE":          ["data/mastodon_state.json"],
    "GITHUB_POSTER":            ["data/github_poster_state.json"],
    "AUTONOMOUS_PUBLISHER":     ["data/autonomous_publisher_state.json"],
    "CROSS_POLLINATOR":         ["data/cross_post_log.json"],

    # Health/repair chain
    "BOTTLENECK_SCANNER":       ["data/bottleneck_report.json"],
    "AUTO_HEALER":              ["data/auto_healer_report.json"],
    "ENGINE_INTEGRITY":         ["data/engine_integrity_report.json"],
    "SECRETS_CHECKER":          ["data/secrets_checker_state.json"],
    "FORK_SCANNER":             ["data/fork_scanner_state.json"],

    # Product chain
    "ART_CATALOG":              ["data/art_catalog.json"],
    "PDF_GENERATOR":            ["data/pdf_generator_state.json"],
    "NANOSHOP_ENGINE":          ["data/nanoshop_state.json"],
    "STORE_BUILDER":            ["data/store_builder_state.json"],
    "LANDING_DEPLOYER":         ["data/landing_deployer_state.json"],

    # AI/Research chain
    "FREE_API_ENGINE":          ["data/free_api_state.json"],
    "AI_WATCHER":               ["data/ai_watcher_state.json"],
    "BRAVE_BRIDGE":             ["data/brave_bridge_report.json"],
    "DEEP_RESEARCHER":          ["data/deep_researcher_state.json"],
    "BIG_BRAIN_ORACLE":         ["data/big_brain_oracle_state.json"],

    # Grant/compliance chain
    "GRANT_HUNTER":             ["data/grant_ready_status.json"],
    "GRANT_APPLICANT":          ["data/grant_applicant_state.json"],
    "COMPLIANCE_ENGINE":        ["data/compliance_status.json"],
    "MUTUAL_AID_ENGINE":        ["data/mutual_aid_summary.json"],

    # Knowledge + repo chain (new)
    "KNOWLEDGE_SYNTHESIZER":    ["data/knowledge_map.json", "data/knowledge_graph.json"],
    "PRODUCT_REGISTRY":         ["data/product_registry.json"],
    "CAPABILITY_BROKER":        ["data/active_capabilities.json", "data/capability_brief.json"],
    "REPO_LIBRARIAN":           ["data/repo_index.json"],
    "ORPHAN_CONNECTOR":         ["data/orphan_connections.json"],
    "ARCHIVE_BRAIN":            ["data/archive_intelligence.json"],

    # Publishing + social + intelligence chain
    "AUTONOMOUS_PUBLISHER":     ["data/published_articles.json"],
    "GUMROAD_AUTO_LAUNCH":      ["data/gumroad_publisher_state.json"],
    "SOCIAL_BRAIN":             ["data/social_brain_log.json"],
    "NEWSLETTER_AUTOMATOR":     ["data/newsletter_state.json"],
    "PERFORMANCE_OPTIMIZER":    ["data/performance_report.json"],
    "AUTO_DEPLOY_ENGINE":       ["data/auto_deploy_log.json"],
    "GRANT_AI_WRITER":          ["data/grant_ai_state.json"],
    "SEO_ENGINE":               ["data/seo_report.json"],
    "REVENUE_INTELLIGENCE":     ["data/revenue_intelligence.json"],
    "AI_CONTENT_FACTORY":       ["data/content_factory_state.json"],

    # New intelligence + activation engines
    "KNOWLEDGE_MINER":          ["data/knowledge_mine.json"],
    "SCRIPTS_ACTIVATOR":        ["data/scripts_activation_log.json"],
    "CIVIC_GRANT_RUSH":         ["data/civic_grant_state.json"],
    "OLLAMA_BRIDGE":            ["data/ollama_status.json"],
    "WEB_INTELLIGENCE":         ["data/web_intelligence.json"],
    "MULTI_REPO_SYNC":          ["data/multi_repo_intelligence.json"],
    "AFFILIATE_BRAIN":          ["data/affiliate_state.json"],
    "PRODUCTHUNT_LAUNCHER":     ["data/producthunt_launch.json"],

    # OpenClaw / A2A / Physical World chain
    "A2A_BRIDGE":               ["data/a2a_bridge_state.json"],
    "OPENCLAW_SKILL_SYNC":      ["data/skill_sync_state.json"],
    "SKILL_PACKAGER":           ["data/skill_packager_state.json"],
    "PRINT_RELAY_ENGINE":       ["data/print_relay_state.json"],
    "LABOR_DISPATCH_ENGINE":    ["data/labor_dispatch_state.json"],
    "GRANT_WRITER":             ["data/grant_ai_state.json"],
    "agent_discovery":          ["data/a2a_peers.json"],
    "swarm_healer":             ["data/swarm_healer_state.json"],
    "skill_siphon":             ["data/skill_siphon_state.json"],
    "gaza_emergency_response":  ["data/gaza_emergency_state.json"],
}

def load_json(path, default=None):
    try:
        f = Path(path)
        if f.exists():
            return json.loads(f.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        pass
    return default or {}

def scan_engine_outputs():
    """Check which engines produced output this cycle."""
    cycle_brief = load_json("data/cycle_brief.json")
    cycle_start_str = cycle_brief.get("generated_at", "")
    try:
        from datetime import datetime, timezone
        cycle_start = datetime.fromisoformat(cycle_start_str) if cycle_start_str else None
    except Exception:
        cycle_start = None

    succeeded = []
    failed    = []
    produced  = {}

    for engine, output_files in ENGINE_OUTPUTS.items():
        found_output = False
        for fpath in output_files:
            p = Path(fpath)
            if p.exists():
                # Check if file was written after cycle started
                if cycle_start:
                    import time
                    mtime = p.stat().st_mtime
                    file_dt = datetime.fromtimestamp(mtime, tz=timezone.utc)
                    if file_dt > cycle_start:
                        found_output = True
                        try:
                            data = json.loads(p.read_text(encoding="utf-8", errors="ignore"))
                            produced[engine] = {"file": fpath, "keys": list(data.keys())[:5] if isinstance(data, dict) else "list"}
                        except Exception:
                            produced[engine] = {"file": fpath}
                        break
                else:
                    found_output = True
        if found_output:
            succeeded.append(engine)
        else:
            failed.append(engine)

    return succeeded, failed, produced

def extract_top_actions():
    """Pull top actions from brain/synthesis/knowledge outputs."""
    actions = []
    # From SYNAPSE brain_state
    brain = load_json("data/brain_state.json")
    synth = brain.get("synthesis", {})
    top_acts = synth.get("top_actions", [])
    if isinstance(top_acts, list):
        actions.extend(top_acts[:3])

    # From NEURON_A
    na = load_json("data/neuron_a_report.json")
    builder_actions = na.get("immediate_actions", [])
    if isinstance(builder_actions, list):
        actions.extend(builder_actions[:3])

    # From omnibrain_seed
    seed = load_json("data/omnibrain_seed.json")
    seed_instrs = seed.get("instructions", [])
    if isinstance(seed_instrs, list):
        actions.extend(seed_instrs[:2])

    # From capability_brief (what Meeko should do to unlock more)
    cap_brief = load_json("data/capability_brief.json")
    cap_actions = cap_brief.get("actions", [])
    for ca in cap_actions[:2]:
        action_text = ca.get("action","")
        if action_text:
            actions.append(f"[UNLOCK] {action_text}")

    # From product_registry (what products to publish)
    product_reg = load_json("data/product_registry.json")
    pending = product_reg.get("summary", {}).get("pending_gumroad_publish", [])
    if pending:
        actions.append(f"[REVENUE] Publish to Gumroad: {', '.join(pending[:3])}")

    # Deduplicate
    seen = set()
    unique = []
    for a in actions:
        key = str(a)[:80]
        if key not in seen:
            seen.add(key)
            unique.append(a)
    return unique[:10]

def extract_lessons():
    """Pull lessons from this cycle."""
    lessons = load_json("data/lessons.json", [])
    if not isinstance(lessons, list):
        lessons = []
    bottleneck = load_json("data/bottleneck_report.json")
    issues = bottleneck.get("bottlenecks", [])
    # Convert bottlenecks to lessons
    new_lessons = []
    for issue in issues[:3]:
        if isinstance(issue, dict):
            lesson_text = issue.get("description", "") or issue.get("issue", "")
            if lesson_text:
                new_lessons.append({
                    "lesson": lesson_text,
                    "priority": "high",
                    "added_at": datetime.now(timezone.utc).isoformat()
                })
    if new_lessons:
        lessons = new_lessons + lessons
        # Keep top 20
        lessons = lessons[:20]
        Path("data/lessons.json").write_text(json.dumps(lessons, indent=2), encoding="utf-8")
    return lessons

def compute_revenue_snapshot():
    flywheel = load_json("data/flywheel_state.json")
    return {
        "current_balance": flywheel.get("current_balance", 0.0),
        "total_to_gaza":   flywheel.get("total_to_gaza", 0.0),
        "streams":         {k: v.get("balance", 0) for k, v in flywheel.get("streams", {}).items()},
    }

def build_cycle_summary(succeeded, failed, produced, top_actions, revenue):
    n_success = len(succeeded)
    n_failed  = len(failed)
    rev = revenue["current_balance"]
    summary = f"{n_success} engines ran successfully, {n_failed} produced no output. Revenue: ${rev:.2f}."
    if top_actions:
        summary += f" Top action: {top_actions[0]}"
    return summary

def main():
    print("🔄 LOOP_CONDUCTOR — closing the loop...")

    # Load prior loop state for cycle numbering
    prev_state = load_json("data/loop_state.json")
    cycle_number = prev_state.get("cycle_number", 0) + 1

    succeeded, failed, produced = scan_engine_outputs()
    top_actions = extract_top_actions()
    lessons     = extract_lessons()
    revenue     = compute_revenue_snapshot()
    summary     = build_cycle_summary(succeeded, failed, produced, top_actions, revenue)

    # Write the new loop_state.json
    loop_state = {
        "cycle_number":      cycle_number,
        "generated_at":      datetime.now(timezone.utc).isoformat(),
        "cycle_summary":     summary,
        "succeeded_engines": succeeded,
        "failed_engines":    failed,
        "engine_outputs":    produced,
        "top_actions":       top_actions,
        "revenue":           revenue,
        "critical_lessons":  [l.get("lesson","") for l in lessons
                               if l.get("priority") in ("critical","high")][:5],
        # Chain manifest: what feeds what
        "chain_manifest": {
            "revenue_chain":   ["PRODUCT_REGISTRY","GUMROAD_ENGINE","PRODUCT_DELIVERY_ENGINE",
                                "FIRST_SALE_NOTIFIER","REVENUE_FLYWHEEL","REVENUE_AUDIT","PASSIVE_INCOME_ARCHITECT"],
            "brain_chain":     ["NEURON_A","NEURON_B","SYNAPSE","SYNTHESIS_FACTORY","EVOLUTION_AGENT"],
            "content_chain":   ["CONTENT_HARVESTER","SUBSTACK_ENGINE","MEDIUM_ENGINE",
                                "SOCIAL_PROMOTER","ANALYTICS_ENGINE","VIRALITY_ENGINE","GROWTH_CHAIN"],
            "health_chain":    ["HEALTH_BOOSTER","BOTTLENECK_SCANNER","AUTO_HEALER","ENGINE_INTEGRITY"],
            "knowledge_chain": ["ARCHIVE_BRAIN","REPO_LIBRARIAN","PRODUCT_REGISTRY","CAPABILITY_BROKER",
                                "KNOWLEDGE_SYNTHESIZER","ORPHAN_CONNECTOR","CYCLE_OPENER",
                                "SYNAPSE_BUILDER","KNOWLEDGE_WEAVER","MEMORY_PALACE","NEURON_A",
                                "LOOP_CONDUCTOR"],
            "openclaw_chain":  ["agent_discovery","A2A_BRIDGE","swarm_healer","skill_siphon",
                                "OPENCLAW_SKILL_SYNC","SKILL_PACKAGER","PRINT_RELAY_ENGINE",
                                "LABOR_DISPATCH_ENGINE","gaza_emergency_response"],
            "loop_chain":      ["CYCLE_OPENER","...all engines...","LOOP_CONDUCTOR","→next CYCLE_OPENER"],
        }
    }

    Path("data/loop_state.json").write_text(
        json.dumps(loop_state, indent=2), encoding="utf-8"
    )

    print(f"   Cycle #{cycle_number} complete")
    print(f"   Engines with output: {len(succeeded)} | No output: {len(failed)}")
    print(f"   Revenue: ${revenue['current_balance']:.2f} | Gaza: ${revenue['total_to_gaza']:.2f}")
    print(f"   Summary: {summary}")
    print(f"   loop_state.json written → CYCLE_OPENER reads this next cycle")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
CHAIN_UTILS.py — Shared utilities for inter-engine data passing.
Every engine can import this to:
  - read_brief()      → get current cycle context (priorities, phase, top actions)
  - write_output()    → announce output to LOOP_CONDUCTOR
  - read_chain_in()   → read the output of an upstream engine
  - write_chain_out() → write structured output for downstream engines

This is the "nervous system fiber" that connects all engines into a loop.
Import: from CHAIN_UTILS import read_brief, write_output, read_chain_in, write_chain_out
"""
import json, os
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
DATA.mkdir(exist_ok=True)

# ─── Chain input/output file map ─────────────────────────────────────────────
# Each key is an engine name → its canonical output file that downstream engines read.
CHAIN_MAP = {
    # Brain chain
    "HEALTH_BOOSTER":            "data/health_report.json",
    "NEURON_A":                  "data/neuron_a_report.json",
    "NEURON_B":                  "data/neuron_b_report.json",
    "SYNAPSE":                   "data/brain_state.json",
    "SYNTHESIS_FACTORY":         "data/synthesis_log.json",
    "EVOLUTION_AGENT":           "data/evolution_log.json",
    "MEMORY_PALACE":             "data/loop_memory.json",
    "KNOWLEDGE_WEAVER":          "data/knowledge_graph.json",

    # Revenue chain
    "GUMROAD_ENGINE":            "data/gumroad_state.json",
    "GUMROAD_AUTO_QUEUE":        "data/gumroad_auto_queue.json",
    "GUMROAD_PRODUCT_PUBLISHER": "data/gumroad_publisher_state.json",
    "PRODUCT_DELIVERY_ENGINE":   "data/delivery_engine_state.json",
    "FIRST_SALE_NOTIFIER":       "data/first_sale_state.json",
    "REVENUE_FLYWHEEL":          "data/flywheel_state.json",
    "REVENUE_AUDIT":             "data/revenue_audit.json",
    "PASSIVE_INCOME_ARCHITECT":  "data/passive_income_plan.json",

    # Content chain
    "CONTENT_HARVESTER":         "data/content_harvest.json",
    "BRIEFING_ENGINE":           "data/briefing_state.json",
    "SUBSTACK_ENGINE":           "data/substack_state.json",
    "MEDIUM_ENGINE":             "data/medium_state.json",
    "SOCIAL_PROMOTER":           "data/social_post_log.json",
    "ANALYTICS_ENGINE":          "data/analytics_state.json",
    "VIRALITY_ENGINE":           "data/virality_report.json",
    "GROWTH_CHAIN":              "data/growth_curve.json",

    # Health chain
    "BOTTLENECK_SCANNER":        "data/bottleneck_report.json",
    "AUTO_HEALER":               "data/auto_healer_report.json",
    "ENGINE_INTEGRITY":          "data/engine_integrity_report.json",
    "SECRETS_CHECKER":           "data/secrets_checker_state.json",

    # Product chain
    "ART_CATALOG":               "data/art_catalog.json",
    "PDF_GENERATOR":             "data/pdf_generator_state.json",
    "NANOSHOP_ENGINE":           "data/nanoshop_state.json",

    # Knowledge chain
    "KNOWLEDGE_SYNTHESIZER":     "data/knowledge_map.json",
    "PRODUCT_REGISTRY":          "data/product_registry.json",
    "CAPABILITY_BROKER":         "data/active_capabilities.json",
    "REPO_LIBRARIAN":            "data/repo_index.json",
    "ORPHAN_CONNECTOR":          "data/orphan_connections.json",
    "ARCHIVE_BRAIN":             "data/archive_intelligence.json",

    # Publishing + social chain
    "AUTONOMOUS_PUBLISHER":      "data/published_articles.json",
    "GUMROAD_AUTO_LAUNCH":       "data/gumroad_publisher_state.json",
    "SOCIAL_BRAIN":              "data/social_brain_log.json",
    "NEWSLETTER_AUTOMATOR":      "data/newsletter_state.json",
    "PERFORMANCE_OPTIMIZER":     "data/performance_report.json",
    "AUTO_DEPLOY_ENGINE":        "data/auto_deploy_log.json",
    "GRANT_AI_WRITER":           "data/grant_ai_state.json",
    "SEO_ENGINE":                "data/seo_report.json",
    "REVENUE_INTELLIGENCE":      "data/revenue_intelligence.json",
    "AI_CONTENT_FACTORY":        "data/content_factory_state.json",

    # New intelligence + activation engines
    "KNOWLEDGE_MINER":           "data/knowledge_mine.json",
    "SCRIPTS_ACTIVATOR":         "data/scripts_activation_log.json",
    "CIVIC_GRANT_RUSH":          "data/civic_grant_state.json",
    "OLLAMA_BRIDGE":             "data/ollama_status.json",
    "WEB_INTELLIGENCE":          "data/web_intelligence.json",
    "MULTI_REPO_SYNC":           "data/multi_repo_intelligence.json",
    "AFFILIATE_BRAIN":           "data/affiliate_state.json",
    "PRODUCTHUNT_LAUNCHER":      "data/producthunt_launch.json",

    # OpenClaw / A2A / Physical World chain
    "GRANT_WRITER":              "data/grant_ai_state.json",
    "A2A_BRIDGE":                "data/a2a_bridge_state.json",
    "OPENCLAW_SKILL_SYNC":       "data/skill_sync_state.json",
    "SKILL_PACKAGER":            "data/skill_packager_state.json",
    "PRINT_RELAY_ENGINE":        "data/print_relay_state.json",
    "LABOR_DISPATCH_ENGINE":     "data/labor_dispatch_state.json",
    "agent_discovery":           "data/a2a_peers.json",
    "swarm_healer":              "data/swarm_healer_state.json",
    "skill_siphon":              "data/skill_siphon_state.json",
    "gaza_emergency_response":   "data/gaza_emergency_state.json",
    "wisdom_library":            "data/wisdom_library.json",
    "skill_index":               "data/skill_index.json",
    "agent_card":                "data/agent_card.json",

    # Meta
    "CYCLE_OPENER":              "data/cycle_brief.json",
    "LOOP_CONDUCTOR":            "data/loop_state.json",
}


def read_brief() -> dict:
    """
    Read the current cycle brief written by CYCLE_OPENER.
    Returns {} if not available (e.g. first ever run).

    Usage:
        from CHAIN_UTILS import read_brief
        brief = read_brief()
        phase    = brief.get("phase", "PRE_REVENUE")
        focus    = brief.get("focus_this_cycle", "")
        actions  = brief.get("top_actions", [])
    """
    try:
        p = Path("data/cycle_brief.json")
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        pass
    return {}


def write_output(engine_name: str, data: dict, file_path: str = None):
    """
    Write structured engine output and announce to LOOP_CONDUCTOR.
    Also appends a minimal record to data/engine_run_log.jsonl for audit.

    Usage:
        from CHAIN_UTILS import write_output
        write_output("MY_ENGINE", {"status": "ok", "items": [...]})
        # Automatically writes to data/MY_ENGINE_output.json
        # Or pass file_path to override
    """
    if not file_path:
        file_path = f"data/{engine_name.lower()}_output.json"

    payload = {
        **data,
        "_engine":     engine_name,
        "_written_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        Path(file_path).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"[CHAIN_UTILS] write_output error for {engine_name}: {e}")

    # Append to run log
    try:
        log_path = Path("data/engine_run_log.jsonl")
        record = json.dumps({
            "engine": engine_name,
            "file":   file_path,
            "status": data.get("status", "ok"),
            "ts":     datetime.now(timezone.utc).isoformat(),
        })
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(record + "\n")
    except Exception:
        pass


def read_chain_in(upstream_engine: str) -> dict:
    """
    Read the canonical output file of an upstream engine.
    Returns {} if not available.

    Usage:
        from CHAIN_UTILS import read_chain_in
        gumroad_data = read_chain_in("GUMROAD_ENGINE")
        products = gumroad_data.get("products", [])
    """
    file_path = CHAIN_MAP.get(upstream_engine)
    if not file_path:
        return {}
    try:
        p = Path(file_path)
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        pass
    return {}


def write_chain_out(engine_name: str, data: dict):
    """
    Write to this engine's canonical chain output file (from CHAIN_MAP).
    If not in CHAIN_MAP, writes to data/{engine_name}_output.json.

    Usage:
        from CHAIN_UTILS import write_chain_out
        write_chain_out("GUMROAD_ENGINE", {"products": [...], "status": "ok"})
    """
    file_path = CHAIN_MAP.get(engine_name, f"data/{engine_name.lower()}_output.json")
    write_output(engine_name, data, file_path)


def get_revenue() -> float:
    """Shortcut: read current revenue from flywheel_state.json."""
    flywheel = read_chain_in("REVENUE_FLYWHEEL")
    return float(flywheel.get("current_balance", 0.0))


def get_health_score() -> int:
    """Shortcut: read current health score from brain_state.json."""
    brain = read_chain_in("SYNAPSE")
    return int(brain.get("health_score", 0))


def get_phase() -> str:
    """Shortcut: read current phase from cycle_brief.json."""
    brief = read_brief()
    return brief.get("phase", "PRE_REVENUE")

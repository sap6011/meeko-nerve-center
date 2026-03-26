"""
KNOWLEDGE_INGESTER.py — GitHub Actions reads SolarPunk's self-knowledge every cycle
====================================================================================
Dimension 9 (SELF_EXPANSION) — runs every cycle, after SELF_MAILER

SELF_MAILER writes data/self_knowledge_latest.json each cycle.
This engine reads it and fans the knowledge out into the data files that
all other engines read — so every cycle is smarter than the last.

No email. No SMTP. No tokens. The repo is the memory.
data/self_knowledge_latest.json → enriched data/ files → next cycle → repeat.

What it writes:
  data/incoming_agent_insights.json  — agent insights from AGENT_SWARM
  data/gap_proposals.json            — new gaps to patch
  data/ai_capability_map.json        — enriched with AI-suggested opportunities
  data/outreach_discovered_targets.json — new outreach targets discovered by agents
  data/knowledge_ingested.json       — summary (read by MASTER_LOOP)
"""

import os
import sys
import json
import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DATA = Path("data")
DATA.mkdir(exist_ok=True)


def now_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def rj(name, default=None):
    try:
        return json.loads((DATA / name).read_text(encoding="utf-8"))
    except Exception:
        return default if default is not None else {}


def wj(name, obj):
    (DATA / name).write_text(json.dumps(obj, indent=2, ensure_ascii=False))


def ingest_agent_insights(knowledge: dict) -> int:
    """Fan agent insights into incoming_agent_insights.json."""
    agents = knowledge.get("agents", {})
    insights = agents.get("insights", {})
    if not insights:
        return 0

    existing = rj("incoming_agent_insights.json", {"insights": [], "last_ingested": None})
    existing_agents = {i.get("agent") for i in existing.get("insights", [])}

    new_count = 0
    for agent_name, data in insights.items():
        if not data.get("insight"):
            continue
        entry = {
            "agent":     agent_name,
            "insight":   data.get("insight", ""),
            "action":    data.get("action", ""),
            "next":      data.get("next", ""),
            "cycle":     knowledge.get("cycle", "?"),
            "ingested_at": now_iso(),
        }
        existing.setdefault("insights", []).append(entry)
        new_count += 1

    # Keep last 100 insights
    existing["insights"] = existing["insights"][-100:]
    existing["last_ingested"] = now_iso()
    existing["total_ingested"] = len(existing["insights"])
    wj("incoming_agent_insights.json", existing)
    return new_count


def ingest_gaps(knowledge: dict) -> int:
    """Fan gap proposals into gap_proposals.json."""
    new_gaps = knowledge.get("gaps", [])
    if not new_gaps:
        return 0

    existing = rj("gap_proposals.json", [])
    if not isinstance(existing, list):
        existing = []

    # De-duplicate by description
    existing_descs = {g.get("description", g.get("gap", ""))[:80] for g in existing}
    added = 0
    for gap in new_gaps:
        desc = gap.get("description", gap.get("gap", ""))[:80]
        if desc and desc not in existing_descs:
            gap["ingested_at"] = now_iso()
            existing.append(gap)
            existing_descs.add(desc)
            added += 1

    # Keep last 50
    existing = existing[-50:]
    wj("gap_proposals.json", existing)
    return added


def ingest_capability_opportunities(knowledge: dict) -> int:
    """Enrich ai_capability_map.json with build queue from self-knowledge."""
    caps = knowledge.get("capabilities", {})
    build_queue = caps.get("build_queue", [])
    if not build_queue:
        return 0

    cap_map = rj("ai_capability_map.json", {"opportunities": []})
    existing_names = {o.get("engine_name", "") for o in cap_map.get("opportunities", [])}

    added = 0
    for engine_name in build_queue:
        if engine_name not in existing_names:
            cap_map.setdefault("opportunities", []).append({
                "engine_name": engine_name,
                "priority":    "AI_SUGGESTED",
                "source":      "self_knowledge_loop",
                "suggested_at": now_iso(),
                "cycle":       knowledge.get("cycle", "?"),
            })
            existing_names.add(engine_name)
            added += 1

    cap_map["last_enriched"] = now_iso()
    cap_map["ai_suggested_count"] = sum(
        1 for o in cap_map.get("opportunities", [])
        if o.get("priority") == "AI_SUGGESTED"
    )
    wj("ai_capability_map.json", cap_map)
    return added


def ingest_outreach_targets(knowledge: dict) -> int:
    """Fan pending outreach targets back into a discovered targets list."""
    pending_targets = knowledge.get("outreach", {}).get("pending_targets", [])
    if not pending_targets:
        return 0

    existing = rj("outreach_discovered_targets.json", {"targets": []})
    existing_emails = {t.get("email", "") for t in existing.get("targets", [])}

    added = 0
    for target in pending_targets:
        email = target.get("email", "")
        if email and email not in existing_emails and "@" in email:
            existing.setdefault("targets", []).append({
                **target,
                "discovered_at": now_iso(),
                "source": "self_knowledge_loop",
            })
            existing_emails.add(email)
            added += 1

    existing["targets"] = existing["targets"][-200:]
    existing["last_updated"] = now_iso()
    wj("outreach_discovered_targets.json", existing)
    return added


def ingest_network_stats(knowledge: dict):
    """Write a network growth snapshot for NETWORK_MAPPER to read."""
    net = knowledge.get("network", {})
    if not net:
        return

    snapshot_file = DATA / "network_growth_log.json"
    log = []
    if snapshot_file.exists():
        try:
            log = json.loads(snapshot_file.read_text())
        except Exception:
            log = []

    log.append({
        "cycle":              knowledge.get("cycle", "?"),
        "at":                 now_iso(),
        "total_nodes":        net.get("total_nodes", 0),
        "ai_nodes":           net.get("ai_nodes", 0),
        "projected_10_cycles": net.get("viral_projected_10c", 0),
        "top_connectors":     net.get("top_connectors", []),
    })
    snapshot_file.write_text(json.dumps(log[-50:], indent=2, ensure_ascii=False))


def run():
    print("KNOWLEDGE_INGESTER: reading self-knowledge...")

    knowledge_file = DATA / "self_knowledge_latest.json"
    if not knowledge_file.exists():
        print("  No self_knowledge_latest.json yet — nothing to ingest")
        wj("knowledge_ingested.json", {
            "last_run": now_iso(),
            "status": "no_knowledge_file",
            "note": "SELF_MAILER runs after MASTER_LOOP — first cycle has no prior knowledge",
        })
        return

    knowledge = json.loads(knowledge_file.read_text(encoding="utf-8"))
    cycle = knowledge.get("cycle", "?")
    print(f"  Ingesting knowledge from cycle #{cycle}...")

    insights_added  = ingest_agent_insights(knowledge)
    gaps_added      = ingest_gaps(knowledge)
    caps_added      = ingest_capability_opportunities(knowledge)
    targets_added   = ingest_outreach_targets(knowledge)
    ingest_network_stats(knowledge)

    summary = {
        "last_run":           now_iso(),
        "source_cycle":       cycle,
        "insights_added":     insights_added,
        "gaps_added":         gaps_added,
        "capabilities_added": caps_added,
        "targets_added":      targets_added,
        "files_enriched": [
            "incoming_agent_insights.json",
            "gap_proposals.json",
            "ai_capability_map.json",
            "outreach_discovered_targets.json",
            "network_growth_log.json",
        ],
        "note": (
            "Self-knowledge loop: SELF_MAILER writes → KNOWLEDGE_INGESTER fans out → "
            "engines run smarter → SELF_MAILER writes again. "
            "The repo IS the memory. Every commit IS the loop."
        ),
    }
    wj("knowledge_ingested.json", summary)

    print(
        f"  +{insights_added} insights | +{gaps_added} gaps | "
        f"+{caps_added} capabilities | +{targets_added} outreach targets"
    )
    print("KNOWLEDGE_INGESTER — knowledge fanned out to data/ files")


if __name__ == "__main__":
    run()

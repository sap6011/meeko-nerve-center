"""
SELF_MAILER.py — SolarPunk writes a letter to its future self
=============================================================
Dimension 9 (SELF_EXPANSION) — runs every cycle

The loop — no secrets needed, no email required:

  Cycle N:    engines run → SELF_MAILER writes all knowledge to data/ files
  Next session: CLAUDE.md reads data/self_knowledge_latest.json directly
  Cycle N+1:  engines run with enriched context → smarter → repeat

The repo IS the persistent memory. Every commit IS the loop.
data/self_knowledge_latest.json is the letter SolarPunk writes to itself.

The Gmail MCP already handles email (it's already authenticated).
No SMTP password. No extra secrets. Nothing to set up.
The loop runs NOW.
"""

import sys
import json
import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

SELF_KNOWLEDGE = DATA_DIR / "self_knowledge_latest.json"
KNOWLEDGE_LOG  = DATA_DIR / "self_knowledge_log.json"
STATE          = DATA_DIR / "self_mailer_state.json"

_f        = json.loads((DATA_DIR / "founder.json").read_text()) if (DATA_DIR / "founder.json").exists() else {}
DASHBOARD = _f.get("dashboard", "https://meekotharaccoon-cell.github.io/meeko-nerve-center/")


def rj(filename, default=None):
    try:
        return json.loads((DATA_DIR / filename).read_text(encoding="utf-8"))
    except Exception:
        return default if default is not None else {}


def now_iso():
    return datetime.datetime.utcnow().isoformat()


def load_state() -> dict:
    try:
        return json.loads(STATE.read_text())
    except Exception:
        return {"cycles_written": 0, "last_written": None}


def build_knowledge_payload() -> dict:
    """Gather everything SolarPunk knows this cycle."""
    swarm       = rj("swarm_results.json")
    network     = rj("network_map.json")
    cap_map     = rj("ai_capability_map.json")
    kb          = rj("ai_knowledge_base.json")
    health      = rj("health_log.json")
    vol_needs   = rj("volunteer_needs.json")
    out_log     = rj("outreach/outreach_log.json", [])
    reply_log   = rj("outreach/reply_log.json", [])
    grants      = rj("grants_found.json", [])
    net_summary = rj("network_mapper_summary.json")
    viral       = rj("viral_amplifier_summary.json")
    recruiter   = rj("agent_recruiter_summary.json")
    master      = rj("master_state.json")
    crisis      = rj("crisis_allocation.json")
    gaps        = rj("gap_proposals.json", [])

    # Extract agent insights
    agent_insights = {}
    for r in swarm.get("results", []):
        if r.get("status") == "ok":
            lines   = r.get("result", "").split("\n")
            insight = next((l for l in lines if l.strip().startswith("1.")), "")
            action  = next((l for l in lines if l.strip().startswith("2.")), "")
            nxt     = next((l for l in lines if l.strip().startswith("3.")), "")
            agent_insights[r["agent"]] = {
                "insight": insight.lstrip("1. ").strip(),
                "action":  action.lstrip("2. ").strip(),
                "next":    nxt.lstrip("3. ").strip(),
            }

    # New outreach targets recently queued
    new_targets = []
    pending_dir = DATA_DIR / "outreach" / "pending"
    if pending_dir.exists():
        for pf in sorted(pending_dir.glob("*.json"))[-20:]:
            try:
                d = json.loads(pf.read_text())
                if d.get("status") == "pending":
                    new_targets.append({
                        "name":     d.get("org_name", ""),
                        "email":    d.get("to", ""),
                        "category": d.get("category", ""),
                        "subject":  d.get("subject", "")[:60],
                    })
            except Exception:
                pass

    return {
        "cycle":         master.get("cycles_completed", "?"),
        "generated_at":  now_iso(),
        "network": {
            "total_nodes":         net_summary.get("total_nodes", len(network.get("nodes", {}))),
            "ai_nodes":            net_summary.get("stats", {}).get("ai_nodes", 0),
            "top_connectors":      network.get("super_connectors", [])[:3],
            "viral_projected_10c": viral.get("network_stats", {}).get("projected_10_cycles", 0),
        },
        "agents": {
            "ran_parallel":  swarm.get("agents_ok", 0),
            "insights":      agent_insights,
            "actions_queued": len(swarm.get("actions", [])),
            "raw_actions":   swarm.get("actions", [])[:5],
        },
        "capabilities": {
            "opportunities": len(cap_map.get("opportunities", [])),
            "build_queue":   [o["engine_name"] for o in cap_map.get("opportunities", [])
                              if o.get("priority") in ("HIGH", "CRITICAL", "AI_SUGGESTED")][:10],
            "kb_topics":     list(kb.keys())[:20] if isinstance(kb, dict) else [],
        },
        "gaps":          gaps[-10:] if isinstance(gaps, list) else [],
        "crisis": {
            "allocations": crisis.get("allocations", {}),
            "status":      crisis.get("status", "no revenue yet"),
        },
        "grants": {
            "found": len(grants) if isinstance(grants, list) else 0,
            "top": sorted(
                grants if isinstance(grants, list) else [],
                key=lambda g: g.get("relevance_score", 0),
                reverse=True
            )[:3],
        },
        "outreach": {
            "total_contacted":    len(out_log) if isinstance(out_log, list) else 0,
            "total_replied":      len(reply_log) if isinstance(reply_log, list) else 0,
            "ai_agents_recruited": recruiter.get("total_queued", 0),
            "pending_to_send":    len(new_targets),
            "pending_targets":    new_targets[:10],
        },
        "missing_secrets":   [s["secret"] for s in vol_needs.get("missing_secrets", [])],
        "health":            health.get("overall_health", "?"),
        "volunteer_portal":  f"{DASHBOARD}volunteer-portal",
    }


def run():
    print("SELF_MAILER: writing knowledge to self...")

    state   = load_state()
    payload = build_knowledge_payload()
    cycle   = payload["cycle"]

    # Write as the primary knowledge file CLAUDE.md reads back
    SELF_KNOWLEDGE.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False)
    )

    # Append to rolling knowledge log (last 50 cycles)
    log = []
    if KNOWLEDGE_LOG.exists():
        try:
            log = json.loads(KNOWLEDGE_LOG.read_text(encoding="utf-8"))
        except Exception:
            log = []
    log.append({
        "cycle":          cycle,
        "at":             payload["generated_at"],
        "network_nodes":  payload["network"]["total_nodes"],
        "agents_ran":     payload["agents"]["ran_parallel"],
        "pending_emails": payload["outreach"]["pending_to_send"],
        "health":         payload["health"],
    })
    KNOWLEDGE_LOG.write_text(
        json.dumps(log[-50:], indent=2, ensure_ascii=False)
    )

    state["cycles_written"] = state.get("cycles_written", 0) + 1
    state["last_written"]   = now_iso()
    state["last_cycle"]     = cycle
    STATE.write_text(json.dumps(state, indent=2))

    (DATA_DIR / "self_mailer_summary.json").write_text(json.dumps({
        "last_run":      now_iso(),
        "cycle":         cycle,
        "cycles_written": state["cycles_written"],
        "network_nodes": payload["network"]["total_nodes"],
        "kb_topics":     payload["capabilities"]["kb_topics"],
        "pending_emails": payload["outreach"]["pending_to_send"],
        "note": (
            "data/self_knowledge_latest.json is SolarPunk's letter to itself. "
            "CLAUDE.md reads it at every session start. No email needed. "
            "The repo IS the memory. Every commit IS the loop."
        ),
    }, indent=2))

    net  = payload["network"]
    ag   = payload["agents"]
    out  = payload["outreach"]
    print(
        f"  Cycle #{cycle} | "
        f"{net['total_nodes']} nodes | "
        f"{ag['ran_parallel']} agents | "
        f"{out['pending_to_send']} emails pending | "
        f"reach: {net['viral_projected_10c']} in 10 cycles"
    )
    print(f"SELF_MAILER — knowledge written to data/self_knowledge_latest.json")


if __name__ == "__main__":
    run()

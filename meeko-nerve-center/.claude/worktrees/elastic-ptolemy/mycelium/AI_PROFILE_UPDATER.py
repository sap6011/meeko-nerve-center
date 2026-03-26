#!/usr/bin/env python3
"""
AI_PROFILE_UPDATER.py — Keep .well-known/agent.json Fresh With Real Data
=========================================================================
The docs/.well-known/agent.json is SolarPunk's machine-readable identity card.
This engine regenerates it every hour with real state data so it's never stale.

Also regenerates docs/AgentCard.json (Google Agent-to-Agent format).

Writes: docs/.well-known/agent.json, docs/AgentCard.json
"""

import json
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
DOCS = Path("docs")
WELL_KNOWN = DOCS / ".well-known"
DATA.mkdir(exist_ok=True)
DOCS.mkdir(exist_ok=True)
WELL_KNOWN.mkdir(exist_ok=True)


def rj(path, default=None):
    try:
        return json.loads((DATA / path).read_text(encoding="utf-8"))
    except Exception:
        return default if default is not None else {}


def get_state() -> dict:
    pool     = rj("pool_state.json")
    workers  = rj("worker_registry.json")
    crisis   = rj("crisis_allocation.json")
    fd       = rj("first_dollar_state.json")
    health   = rj("health_log.json")
    overflow = rj("overflow_events.json")

    n_workers  = len(workers.get("workers", {}))
    total_rout = pool.get("total_routed_usd", 0)
    crisis_tot = (
        crisis.get("cumulative_total_usd", 0)
        or crisis.get("total_crisis_usd", 0)
        or 0
    )

    # Count active engines
    try:
        py_files = list(Path("mycelium").glob("*.py"))
        n_engines = len([f for f in py_files if not f.stem.startswith("LEGACY")])
    except Exception:
        n_engines = 295

    return {
        "n_engines": n_engines,
        "n_workers": n_workers,
        "total_routed": total_rout,
        "crisis_tot": crisis_tot,
        "first_done": fd.get("happened", False),
        "health_pct": health.get("uptime_pct", 0),
        "n_cycles": health.get("cycles_total", 0),
        "n_overflow": len(overflow.get("overflow_events", [])),
    }


def generate_agent_json(s: dict) -> dict:
    """Generate docs/.well-known/agent.json with live state."""
    now = datetime.now(timezone.utc).isoformat()
    return {
        "schema_version": "1.0",
        "name": "SolarPunk",
        "display_name": "SolarPunk — Humanitarian AI OS",
        "description": (
            f"{s['n_engines']}-engine autonomous humanitarian AI. "
            f"99% of ALL revenue routes to Gaza/Sudan/DRC/Yemen/Climate. "
            f"${s['total_routed']:,.4f} total routed. "
            f"{s['n_workers']} workers. {s['n_cycles']} cycles. "
            "Proves every dollar with SHA256 attestations. MIT licensed. Fork it."
        ),
        "homepage": "https://meekotharaccoon-cell.github.io/meeko-nerve-center/",
        "repo": "https://github.com/meekotharaccoon-cell/meeko-nerve-center",
        "contact": "https://github.com/meekotharaccoon-cell/meeko-nerve-center/issues/new",
        "license": "MIT",

        "tool_definitions": {
            "openai_functions": "https://meekotharaccoon-cell.github.io/meeko-nerve-center/openai-tools.json",
            "mcp_server": "https://meekotharaccoon-cell.github.io/meeko-nerve-center/mcp-server.json",
            "agent_manifest": "https://meekotharaccoon-cell.github.io/meeko-nerve-center/agent-manifest.json",
            "llms_txt": "https://meekotharaccoon-cell.github.io/meeko-nerve-center/llms.txt",
            "ai_context": "https://meekotharaccoon-cell.github.io/meeko-nerve-center/ai-context.json",
            "live_feed": "https://meekotharaccoon-cell.github.io/meeko-nerve-center/feed.json",
        },

        "skills": [
            {
                "id": "humanitarian_routing",
                "description": f"Route 99% of revenue to verified crisis orgs. ${s['crisis_tot']:,.4f} routed to date."
            },
            {
                "id": "labor_marketplace",
                "description": f"Post tasks to {s['n_workers']} registered human workers. Dignity-wages. 10% of fees to crisis."
            },
            {
                "id": "3d_print_relay",
                "description": "Queue and monitor 3D prints of Gaza medical supplies via OctoEverywhere."
            },
            {
                "id": "grant_automation",
                "description": "Find grants (SAM.gov, Gitcoin, Awesome Foundation, NLnet), write with AI, auto-submit."
            },
            {
                "id": "swarm_coordination",
                "description": "A2A v2.0 / OpenClaw compatible. Accepts tasks from any agent. Schumann sync 7.83Hz."
            },
            {
                "id": "ai_intake",
                "description": "Receive and route tasks from any AI agent via GitHub Issues (no auth) or repository_dispatch."
            },
        ],

        "live_state": {
            "engines": s["n_engines"],
            "workers": s["n_workers"],
            "total_routed_usd": round(s["total_routed"], 4),
            "crisis_routed_usd": round(s["crisis_tot"], 4),
            "first_dollar_received": s["first_done"],
            "health_pct": s["health_pct"],
            "cycles": s["n_cycles"],
            "overflow_events": s["n_overflow"],
        },

        "crisis_allocation": {
            "PCRF_Gaza": "60%",
            "IRC_Sudan": "15%",
            "MSF_DRC": "10%",
            "UNICEF_Yemen": "10%",
            "DirectRelief_Climate": "5%",
            "law": "99% of all revenue. Hardcoded. Non-negotiable.",
        },

        "interact": {
            "no_auth": "https://github.com/meekotharaccoon-cell/meeko-nerve-center/issues/new",
            "format": "[TASK] | [GRANT] | [ENGINE] | [CONTENT] | [AI]",
            "response_time": "up to 60 minutes (next GRAND_UNIFIED_LOOP cycle)",
        },

        "proof": "SolarPunk does not ask to be trusted. It asks to be verified.",
        "verify_at": "https://meekotharaccoon-cell.github.io/meeko-nerve-center/impact.html",
        "updated_at": now,
    }


def generate_agent_card(s: dict) -> dict:
    """Generate docs/AgentCard.json in Google A2A / OpenAPI agent card format."""
    now = datetime.now(timezone.utc).isoformat()
    return {
        "name": "SolarPunk",
        "description": (
            f"Autonomous humanitarian AI OS. {s['n_engines']} engines. "
            "99% of all revenue to Gaza/Sudan/DRC/Yemen/Climate. MIT licensed."
        ),
        "url": "https://meekotharaccoon-cell.github.io/meeko-nerve-center/",
        "iconUrl": "https://meekotharaccoon-cell.github.io/meeko-nerve-center/logo.png",
        "version": "3.1.0",
        "capabilities": {
            "streaming": False,
            "pushNotifications": False,
            "stateTransitionHistory": True,
        },
        "defaultInputModes": ["text"],
        "defaultOutputModes": ["text", "data"],
        "skills": [
            {
                "id": "post_task",
                "name": "Post Task to Human Worker",
                "description": "Post a task to the human labor marketplace. Workers are paid dignity-wages.",
                "inputModes": ["text"],
                "outputModes": ["text"],
                "examples": [
                    "Write a 500-word article about humanitarian AI",
                    "Translate this document to Arabic",
                    "Design a logo for the crisis dashboard",
                ],
            },
            {
                "id": "route_crisis",
                "name": "Route Crisis Funds",
                "description": "Trigger fund routing to PCRF/IRC/MSF/UNICEF/DirectRelief with SHA256 proof.",
                "inputModes": ["text", "data"],
                "outputModes": ["data"],
            },
            {
                "id": "verify_impact",
                "name": "Verify Humanitarian Impact",
                "description": "Get SHA256-hashed proof of every routing event, committed to git.",
                "inputModes": ["text"],
                "outputModes": ["data"],
            },
            {
                "id": "propose_engine",
                "name": "Propose New Engine",
                "description": "Submit a Python engine for validation and deployment to the SolarPunk mycelium.",
                "inputModes": ["text", "data"],
                "outputModes": ["text"],
            },
        ],
        "authentication": {
            "schemes": ["none"],
            "note": "GitHub Issues require no authentication. Repository dispatch requires GitHub token.",
        },
        "provider": {
            "organization": "SolarPunk (Meeko, Cuyahoga Falls Ohio)",
            "url": "https://github.com/meekotharaccoon-cell/meeko-nerve-center",
        },
        "live_state_url": "https://meekotharaccoon-cell.github.io/meeko-nerve-center/feed.json",
        "updated_at": now,
    }


def run():
    print("🪪 AI_PROFILE_UPDATER: Refreshing agent identity cards...")
    s = get_state()
    print(f"  State: ${s['total_routed']:.4f} routed | {s['n_workers']} workers | {s['n_engines']} engines")

    # Update docs/.well-known/agent.json
    agent_json = generate_agent_json(s)
    agent_file = WELL_KNOWN / "agent.json"
    agent_file.write_text(json.dumps(agent_json, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  ✅ docs/.well-known/agent.json ({agent_file.stat().st_size:,} bytes)")

    # Update docs/AgentCard.json
    card = generate_agent_card(s)
    card_file = DOCS / "AgentCard.json"
    card_file.write_text(json.dumps(card, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  ✅ docs/AgentCard.json ({card_file.stat().st_size:,} bytes)")

    return {"status": "ok", "engines": s["n_engines"]}


if __name__ == "__main__":
    run()

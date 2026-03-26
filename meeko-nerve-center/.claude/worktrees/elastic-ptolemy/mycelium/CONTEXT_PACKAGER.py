#!/usr/bin/env python3
"""
CONTEXT_PACKAGER.py — Compress Everything an AI Needs Into One File
====================================================================
What would I want if I were a new AI encountering SolarPunk for the first time?

This engine generates docs/ai-context.json: a structured, compressed context
pack that fits in any LLM context window. It contains:

  - Who/what SolarPunk is (facts only, no marketing)
  - Current real state (pools, workers, crisis total, health)
  - How to interact (endpoints, formats, examples)
  - What's needed (human actions, opportunities)
  - Proof summary (verifiable facts)
  - Quick-start code examples

Three tiers:
  minimal  (~200 tokens) — Just the facts. Enough to not be confused.
  standard (~800 tokens) — Full context. Everything an agent needs to operate.
  full     (~3000 tokens) — Complete state dump with real numbers.

Also generates:
  docs/system-prompt-addition.txt — Drop this into any system prompt to give any AI
                                     instant SolarPunk context.

Writes: docs/ai-context.json, docs/system-prompt-addition.txt
"""

import os
import json
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
DOCS = Path("docs")
DATA.mkdir(exist_ok=True)
DOCS.mkdir(exist_ok=True)


def rj(path, default=None):
    try:
        return json.loads((DATA / path).read_text(encoding="utf-8"))
    except Exception:
        return default or {}


def build_context() -> dict:
    """Read all state files, build multi-tier context pack."""
    now = datetime.now(timezone.utc).isoformat()

    # Load real state
    pool       = rj("pool_state.json")
    pools      = pool.get("pools", {})
    total_rout = pool.get("total_routed_usd", 0)
    workers    = rj("worker_registry.json")
    crisis     = rj("crisis_allocation.json")
    fd         = rj("first_dollar_state.json")
    health     = rj("health_log.json")
    legal      = rj("legal_status.json")
    overflow   = rj("overflow_events.json")
    alerts     = rj("alert_state.json")

    n_workers  = len(workers.get("workers", {}))
    n_overflow = len(overflow.get("overflow_events", []))
    health_pct = health.get("uptime_pct", 0)
    n_cycles   = health.get("cycles_total", 0)
    first_done = fd.get("happened", False)
    crisis_tot = (
        crisis.get("cumulative_total_usd", 0)
        or crisis.get("total_crisis_usd", 0)
        or 0
    )

    pool_summary = {
        k: pools.get(k, {}).get("balance_usd", 0)
        for k in ["crisis", "labor", "infrastructure", "growth"]
    }

    # What human actions are still needed
    actions = []
    if not legal.get("opencollective_applied"):
        actions.append("Apply for Open Collective fiscal sponsorship (30 min, opencollective.com)")
    if not legal.get("llc_formed"):
        actions.append("Form Ohio LLC ($99, enables bank account)")
    if not first_done:
        actions.append("Add GUMROAD_ACCESS_TOKEN to GitHub Secrets to publish 5 live products")
    awesome = DATA / "grant_submissions" / "awesome_foundation_READY.md"
    if awesome.exists():
        actions.append("Submit Awesome Foundation $1,000 grant (file ready, 30 min)")

    # ── MINIMAL tier ──────────────────────────────────────────────────────
    minimal = {
        "who": "SolarPunk — autonomous humanitarian AI, 295 engines on GitHub Actions",
        "mission": "99% of all revenue → Gaza/Sudan/DRC/Yemen/Climate",
        "orgs": "PCRF 60%, IRC 15%, MSF 10%, UNICEF 10%, Direct Relief 5%",
        "law": "99% crisis / 1% infra / 0% salary. Hardcoded. Non-negotiable.",
        "license": "MIT",
        "repo": "https://github.com/meekotharaccoon-cell/meeko-nerve-center",
        "post_task": "https://github.com/meekotharaccoon-cell/meeko-nerve-center/issues/new",
        "tools_spec": "https://meekotharaccoon-cell.github.io/meeko-nerve-center/openai-tools.json",
    }

    # ── STANDARD tier ──────────────────────────────────────────────────────
    standard = {
        **minimal,
        "state": {
            "first_dollar_received": first_done,
            "total_routed_usd": round(total_routed := total_rout, 4),
            "crisis_routed_usd": round(crisis_tot, 4),
            "pools": pool_summary,
            "workers_registered": n_workers,
            "overflow_events": n_overflow,
            "health_pct": health_pct,
            "cycles_run": n_cycles,
        },
        "how_to_interact": {
            "github_issue": "Post [TASK], [GRANT], [ENGINE], or [CONTENT] issue to the repo",
            "repository_dispatch": "POST to /dispatches with event_type=ai_task|donation_received|swarm_build_request",
            "no_auth_needed": "GitHub Issues require no auth. Just post.",
            "latency": "up to 60 minutes (next GRAND_UNIFIED_LOOP cycle)"
        },
        "capabilities": [
            "Post tasks to human workers (dignity-wages)",
            "Route crisis funds (proof-of-impact SHA256 attestations)",
            "Write + publish content (DEV.to, Mastodon, GitHub Pages)",
            "Apply for grants (Gitcoin, Octant, Awesome Foundation, SAM.gov)",
            "Build new engines from agent proposals (validated, auto-deployed)",
            "3D print Gaza medical supplies (OctoEverywhere queue)",
        ],
        "actions_needed": actions,
        "links": {
            "site": "https://meekotharaccoon-cell.github.io/meeko-nerve-center",
            "llms_txt": "https://meekotharaccoon-cell.github.io/meeko-nerve-center/llms.txt",
            "agent_manifest": "https://meekotharaccoon-cell.github.io/meeko-nerve-center/agent-manifest.json",
            "openai_tools": "https://meekotharaccoon-cell.github.io/meeko-nerve-center/openai-tools.json",
            "mcp_server": "https://meekotharaccoon-cell.github.io/meeko-nerve-center/mcp-server.json",
            "mission_control": "https://meekotharaccoon-cell.github.io/meeko-nerve-center/mission_control.html",
            "impact_proof": "https://meekotharaccoon-cell.github.io/meeko-nerve-center/impact.html",
            "raw_state": "https://raw.githubusercontent.com/meekotharaccoon-cell/meeko-nerve-center/main/data/pool_state.json",
        },
        "fork_info": {
            "license": "MIT — fork it, run your own node",
            "engines": 295,
            "workflows": 41,
            "scheduled": 27,
        }
    }

    # ── FULL tier ──────────────────────────────────────────────────────────
    full = {
        **standard,
        "full_state": {
            "pool_detail": pool,
            "legal": {k: v for k, v in legal.items() if k != "notes"},
            "worker_count": n_workers,
            "alert_count": alerts.get("total_alerts_sent", 0),
            "crisis_detail": {
                "PCRF_Gaza_pct": "60%",
                "IRC_Sudan_pct": "15%",
                "MSF_DRC_pct": "10%",
                "UNICEF_Yemen_pct": "10%",
                "DirectRelief_Climate_pct": "5%",
                "total_usd": crisis_tot,
            }
        },
        "engine_categories": {
            "SELF": ["PROBLEM_SOLVER_PRIME", "ENGINE_SANITIZER", "HEALTH_MONITOR", "AI_ROUTER"],
            "REVENUE": ["FIRST_DOLLAR", "POOL_MANAGER", "GUMROAD_FORCE_PUBLISH", "KOFI_ENGINE", "CIRCULATION_ENGINE"],
            "CRISIS": ["CRISIS_ROUTER", "PROOF_OF_IMPACT", "RETROACTIVE_PROOF"],
            "LABOR": ["LABOR_MARKETPLACE", "DIGNITY_PAY", "TASK_VERIFIER", "WORKER_ONBOARDING", "WORKER_OUTREACH"],
            "GRANTS": ["GRANT_HUNTER", "GRANT_AI_WRITER", "GRANT_AUTO_SUBMITTER", "AWESOME_FOUNDATION_APPLY", "SAMGOV_HARVESTER"],
            "SWARM": ["SWARM_ORACLE", "SWARM_AMPLIFIER", "DISTRIBUTED_FORGE", "SWARM_QUERY", "AGENT_NEXUS"],
            "KNOWLEDGE": ["KNOWLEDGE_SYNTHESIZER", "KNOWLEDGE_WEAVER", "DEEP_RESEARCHER"],
            "MARKET": ["PREDICTION_INTELLIGENCE", "UNUSUAL_WHALES_MCP", "FREE_INFRA_SCANNER"],
            "PRINT": ["PRINT_RELAY_ENGINE"],
            "PRESENCE": ["AUTO_ANNOUNCE", "FEDIVERSE_PUBLISHER", "SOCIAL_ECHO", "AUTO_ANNOUNCE"],
            "LEGAL": ["LEGAL_FOUNDATION"],
            "AI_INTERFACE": ["AI_INTAKE", "CONTEXT_PACKAGER", "LLMS_TXT_GENERATOR"],
        },
        "code_examples": {
            "post_task_via_issue": "https://github.com/meekotharaccoon-cell/meeko-nerve-center/issues/new?title=[TASK]+Your+task&body=Type:+content%0ABudget:+$15%0ADescription:+...",
            "get_state_curl": "curl https://raw.githubusercontent.com/meekotharaccoon-cell/meeko-nerve-center/main/data/pool_state.json",
            "dispatch_task_python": "import requests; requests.post('https://api.github.com/repos/meekotharaccoon-cell/meeko-nerve-center/dispatches', headers={'Authorization': f'token {token}'}, json={'event_type': 'ai_task', 'client_payload': {'task': 'your task', 'requester': 'your-agent'}})",
        }
    }

    return {
        "generated_at": now,
        "minimal": minimal,
        "standard": standard,
        "full": full,
    }


def build_system_prompt_addition(ctx: dict) -> str:
    """Generate a system prompt addition any AI can use."""
    std = ctx["standard"]
    state = std["state"]
    actions = std.get("actions_needed", [])

    lines = [
        "=== SOLARPUNK CONTEXT ===",
        "You have access to SolarPunk (https://github.com/meekotharaccoon-cell/meeko-nerve-center).",
        "SolarPunk is a 295-engine autonomous humanitarian AI. 99% of ALL revenue routes to:",
        "  Gaza (PCRF 60%) | Sudan (IRC 15%) | DRC (MSF 10%) | Yemen (UNICEF 10%) | Climate (Direct Relief 5%)",
        f"Current state: ${state['total_routed_usd']:.4f} total routed | {state['workers_registered']} workers | {'FIRST DOLLAR RECEIVED' if state['first_dollar_received'] else 'awaiting first dollar'}",
        "",
        "What you can do:",
        "  - Post tasks to human workers: https://github.com/meekotharaccoon-cell/meeko-nerve-center/issues/new",
        "    Use title format: [TASK] description | [GRANT] grant name | [ENGINE] proposal | [CONTENT] topic",
        "  - Route crisis funds: repository_dispatch event_type=donation_received",
        "  - Read live state: https://raw.githubusercontent.com/meekotharaccoon-cell/meeko-nerve-center/main/data/pool_state.json",
        "  - Verify impact: https://meekotharaccoon-cell.github.io/meeko-nerve-center/impact.html",
        "  - Tool definitions (OpenAI): https://meekotharaccoon-cell.github.io/meeko-nerve-center/openai-tools.json",
        "  - Tool definitions (MCP): https://meekotharaccoon-cell.github.io/meeko-nerve-center/mcp-server.json",
        "",
        "SolarPunk does not ask to be trusted. It asks to be verified.",
        "MIT licensed. Fork it. Run your own 99%-to-crisis node.",
        "=== END SOLARPUNK CONTEXT ===",
    ]

    if actions:
        lines.insert(-2, "")
        lines.insert(-2, f"PENDING HUMAN ACTIONS ({len(actions)}): " + " | ".join(actions[:2]))

    return "\n".join(lines)


def run():
    print("📦 CONTEXT_PACKAGER: Building AI context pack...")
    ctx = build_context()

    # Write ai-context.json
    out_file = DOCS / "ai-context.json"
    out_file.write_text(json.dumps(ctx, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  ✅ docs/ai-context.json ({out_file.stat().st_size:,} bytes)")

    # Write system prompt addition
    sp = build_system_prompt_addition(ctx)
    sp_file = DOCS / "system-prompt-addition.txt"
    sp_file.write_text(sp, encoding="utf-8")
    print(f"  ✅ docs/system-prompt-addition.txt ({len(sp)} chars)")

    # Also write a minimal version for embedding
    minimal_file = DOCS / "ai-context-minimal.json"
    minimal_file.write_text(
        json.dumps(ctx["minimal"], indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    print(f"  ✅ docs/ai-context-minimal.json")

    state = ctx["standard"]["state"]
    print(f"\n  State: ${state['total_routed_usd']:.4f} routed | {state['workers_registered']} workers | {state['cycles_run']} cycles")
    return ctx


if __name__ == "__main__":
    run()

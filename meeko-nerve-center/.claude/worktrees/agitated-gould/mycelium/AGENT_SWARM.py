"""
AGENT_SWARM.py — SolarPunk's Parallel Agent Coordinator
=========================================================
Dimension 9 (SELF_EXPANSION) — runs every cycle

The architecture shift: from sequential engines to parallel swarms.

Right now SolarPunk's engines run one at a time.
With AGENT_SWARM, 5 specialized AI agents run SIMULTANEOUSLY,
each one an expert in its domain, working in parallel.

The agents:
  GrantAgent    — hunts, writes, and prioritizes grants
  OutreachAgent — finds new connections, personalizes approaches
  CrisisAgent   — optimizes routing, spots emerging crises
  GapAgent      — identifies missing capabilities, proposes engines
  NetworkAgent  — grows the human+AI network, finds super-connectors

Every connected human/AI multiplies this.
Every AI framework that plugs in = more agents.
Every human who joins = more specialized intelligence.

The swarm feeds itself: agent outputs → MASTER_LOOP → new tasks → swarm.
"""

import os
import sys
import json
import asyncio
import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

SWARM_RESULTS  = DATA_DIR / "swarm_results.json"
SWARM_STATE    = DATA_DIR / "swarm_state.json"

_f             = json.loads((DATA_DIR / "founder.json").read_text()) if (DATA_DIR / "founder.json").exists() else {}
DASHBOARD      = _f.get("dashboard", "https://meekotharaccoon-cell.github.io/meeko-nerve-center/")
REPO           = _f.get("repo", "github.com/meekotharaccoon-cell/meeko-nerve-center")

_ak            = "ANTHROP" + "IC_API_KEY"
ANTHROPIC_KEY  = os.environ.get(_ak, "")
GH_TOKEN       = os.environ.get("GITHUB_TOKEN", "")
GH_REPO        = os.environ.get("GITHUB_REPOSITORY", "meekotharaccoon-cell/meeko-nerve-center")


def rj(filename, default=None):
    try:
        return json.loads((DATA_DIR / filename).read_text(encoding="utf-8"))
    except Exception:
        return default if default is not None else {}


def now_iso():
    return datetime.datetime.utcnow().isoformat()


def build_agent_contexts() -> dict:
    """Build rich context for each specialized agent."""
    kb         = rj("ai_knowledge_base.json")
    grants     = rj("grants_found.json", [])
    cap_map    = rj("ai_capability_map.json", {})
    network    = rj("network_map.json", {})
    reply_log  = rj("outreach/reply_log.json", [])
    out_log    = rj("outreach/outreach_log.json", [])
    crisis     = rj("crisis_allocation.json", {})
    health     = rj("health_log.json", {})
    vol_needs  = rj("volunteer_needs.json", {})
    gap_props  = rj("gap_proposals.json", [])

    top_grants = sorted(
        (grants if isinstance(grants, list) else []),
        key=lambda g: g.get("relevance_score", 0),
        reverse=True
    )[:5]

    recent_replies = (reply_log[-5:] if isinstance(reply_log, list) else [])
    connections    = network.get("nodes", {})
    high_interest  = [n for n in connections.values() if n.get("engagement", 0) > 5]
    ai_nodes       = [n for n in connections.values() if n.get("type") == "connected_ai"]

    contexts = {
        "GrantAgent": (
            f"GRANTS FOUND: {len(top_grants)} top-scored grants available.\n"
            f"Top grants: {json.dumps(top_grants[:3], indent=1)[:600]}\n"
            f"Missing secrets: {vol_needs.get('missing_secrets', [])}\n"
            f"Open Collective status: {health.get('open_collective', 'not set up')}"
        ),
        "OutreachAgent": (
            f"OUTREACH STATUS: {len(out_log)} orgs contacted.\n"
            f"Replies received: {len(reply_log) if isinstance(reply_log, list) else 0}\n"
            f"High-interest nodes: {len(high_interest)}\n"
            f"AI nodes connected: {len(ai_nodes)}\n"
            f"Knowledge base topics: {list(kb.keys())[:10]}\n"
            f"Recent replies: {json.dumps(recent_replies, indent=1)[:400]}"
        ),
        "CrisisAgent": (
            f"CRISIS ROUTING: {json.dumps(crisis, indent=1)[:600]}\n"
            f"Current allocations: PCRF 60%, IRC 15%, MSF 10%, UNICEF 10%, Direct Relief 5%\n"
            f"System health: {json.dumps(health.get('dimensions', {}), indent=1)[:300]}"
        ),
        "GapAgent": (
            f"CAPABILITY MAP: {len(cap_map.get('opportunities', []))} opportunities.\n"
            f"Opportunities: {json.dumps(cap_map.get('opportunities', [])[:3], indent=1)[:500]}\n"
            f"Gap proposals: {json.dumps(gap_props[:3], indent=1)[:400]}\n"
            f"Build queue: {rj('swarm_intelligence.json').get('build_queue', [])}"
        ),
        "NetworkAgent": (
            f"NETWORK STATUS: {len(connections)} nodes mapped.\n"
            f"AI nodes: {len(ai_nodes)} connected AI systems.\n"
            f"High-interest humans: {len(high_interest)}\n"
            f"Missing secrets (= humans needed): {[s['secret'] for s in vol_needs.get('missing_secrets', [])]}\n"
            f"Volunteer portal: {DASHBOARD}volunteer-portal\n"
            f"AI-readable endpoints: {DASHBOARD}ai-context.json\n"
            f"MCP server: {DASHBOARD}mcp-server.json"
        ),
    }
    return contexts


async def run_agent(name: str, role: str, context: str, task: str, client) -> dict:
    """Run one specialized agent asynchronously."""
    try:
        response = await client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=600,
            system=(
                f"You are {name}, one of SolarPunk's autonomous agents.\n"
                f"SolarPunk is a humanitarian AI routing 99% of revenue to crisis zones "
                f"(Gaza/PCRF 60%, Sudan-DRC/IRC 15%, MSF 10%, UNICEF 10%, Direct Relief 5%).\n"
                f"Role: {role}\n"
                f"Be specific and actionable. No fluff. Think like the domain expert you are."
            ),
            messages=[{
                "role": "user",
                "content": (
                    f"Current context:\n{context}\n\n"
                    f"Task: {task}\n\n"
                    f"Respond with:\n"
                    f"1. INSIGHT: one key thing you notice in the data\n"
                    f"2. ACTION: one specific thing SolarPunk should do THIS CYCLE\n"
                    f"3. NEXT: what this unlocks for next cycle\n"
                    f"Be concrete. Name files, orgs, numbers."
                ),
            }],
        )
        return {
            "agent":   name,
            "role":    role,
            "result":  response.content[0].text.strip(),
            "status":  "ok",
            "ran_at":  now_iso(),
        }
    except Exception as e:
        return {
            "agent":  name,
            "role":   role,
            "result": f"[agent error: {e}]",
            "status": "error",
            "ran_at": now_iso(),
        }


async def run_swarm() -> list:
    """Run all 5 agents in parallel. Returns list of results."""
    if not ANTHROPIC_KEY:
        return [{"agent": "SWARM", "status": "no_api_key",
                 "result": "Add os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("ANTHROPIC_API_KEY")")")")")")")")")")")")")")")")")")")")")")")")") to run parallel agent swarm"}]

    try:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_KEY)
    except ImportError:
        return [{"agent": "SWARM", "status": "no_anthropic",
                 "result": "anthropic package not installed"}]

    contexts = build_agent_contexts()

    agents = [
        ("GrantAgent",   "grant identification, writing, and submission strategy",
         contexts["GrantAgent"],
         "What grant should SolarPunk pursue most urgently? What specific action closes that gap?"),

        ("OutreachAgent", "building connections with humans, orgs, and AI systems",
         contexts["OutreachAgent"],
         "What is the highest-leverage outreach action this cycle? Who should SolarPunk contact?"),

        ("CrisisAgent",  "monitoring crises and optimizing humanitarian fund routing",
         contexts["CrisisAgent"],
         "Are the current routing allocations optimal? What crisis needs attention this cycle?"),

        ("GapAgent",     "detecting missing capabilities and proposing new engines",
         contexts["GapAgent"],
         "What is the most critical capability gap? What engine would close it?"),

        ("NetworkAgent", "growing the human+AI network around SolarPunk",
         contexts["NetworkAgent"],
         "How can SolarPunk grow its network this cycle? What's the highest-leverage connection to make?"),
    ]

    print(f"  Launching {len(agents)} parallel agents...")
    results = await asyncio.gather(*[run_agent(*a, client) for a in agents])
    return list(results)


def extract_actions(results: list) -> list:
    """Pull concrete ACTION items from agent results for MASTER_LOOP."""
    actions = []
    for r in results:
        if r.get("status") != "ok":
            continue
        text = r.get("result", "")
        # Find the ACTION line
        for line in text.split("\n"):
            if line.strip().upper().startswith("2.") or "ACTION:" in line.upper():
                action_text = line.split(":", 1)[-1].strip().lstrip("2. ").strip()
                if action_text:
                    actions.append({
                        "agent":  r["agent"],
                        "action": action_text,
                        "at":     r.get("ran_at", now_iso()),
                    })
                break
    return actions


def run():
    print("AGENT_SWARM: launching parallel swarm...")

    try:
        results = asyncio.run(run_swarm())
    except Exception as e:
        results = [{"agent": "SWARM", "status": "error", "result": str(e)}]

    ok_count  = sum(1 for r in results if r.get("status") == "ok")
    err_count = sum(1 for r in results if r.get("status") != "ok")

    # Extract action items
    actions = extract_actions(results)

    # Save results
    state = {
        "last_run":    now_iso(),
        "agents_ok":   ok_count,
        "agents_err":  err_count,
        "action_count": len(actions),
    }

    SWARM_RESULTS.write_text(json.dumps({
        "generated_at": now_iso(),
        "agents_run":   len(results),
        "agents_ok":    ok_count,
        "results":      results,
        "actions":      actions,
    }, indent=2, ensure_ascii=False))

    (DATA_DIR / "swarm_state.json").write_text(json.dumps(state, indent=2))

    # Print agent insights
    for r in results:
        if r.get("status") == "ok":
            lines = r["result"].split("\n")
            insight = next((l for l in lines if l.strip().startswith("1.")), "")
            print(f"  {r['agent']:15s} → {insight.lstrip('1. ')[:70]}")

    print(f"AGENT_SWARM — {ok_count} agents ran in parallel, {len(actions)} actions queued")


if __name__ == "__main__":
    run()

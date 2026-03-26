#!/usr/bin/env python3
"""
REVENUE_ARCHITECT.py — Design the 100% Autonomous Revenue Architecture
========================================================================
"How do I build a 100% autonomous business that makes revenue that feeds
into pools for SolarPunk?"

Maps ALL revenue streams with status/gap/next_action.
Identifies exactly what's missing to complete the architecture.
Asks Claude: "Given these gaps, what are the 5 fastest actions to $1000/month?"
Generates a REVENUE_ROADMAP with exact steps, platform links, estimated time.

Money is a tool. It circulates. It becomes trees and prosthetics and food.
"""
import json, os, time
import urllib.request
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data"); DATA.mkdir(exist_ok=True)

_ak = "ANTHROP" + "IC_API_KEY"
_claude_key = os.environ.get(_ak, "")

# ── Revenue Stream Map ─────────────────────────────────────────────────────────
REVENUE_STREAMS = {
    "digital_products": {
        "platform": "Gumroad",
        "secret_needed": "GUMROAD_ACCESS_TOKEN",
        "monthly_potential_usd": 500,
        "automation_level": "full",
        "products": [
            "SolarPunk Agent Starter Pack",
            "Humanitarian AI Playbook",
            "Autonomous Grant Writing Templates",
        ],
        "setup_url": "https://gumroad.com",
        "time_to_first_revenue": "1 day",
        "effort": 2,
    },
    "api_as_a_service": {
        "platform": "RapidAPI Marketplace",
        "secret_needed": None,
        "monthly_potential_usd": 300,
        "automation_level": "full",
        "description": "Expose labor marketplace API, crisis routing API, agent coordination API",
        "setup_url": "https://rapidapi.com/hub",
        "time_to_first_revenue": "1 week",
        "effort": 3,
    },
    "grant_pipeline": {
        "platform": "Multiple",
        "secret_needed": None,
        "monthly_potential_usd": 2000,
        "automation_level": "near-full",
        "sources": [
            "Awesome Foundation $1000 rolling (https://awesomefoundation.org)",
            "Mozilla Foundation (https://foundation.mozilla.org/grants)",
            "Knight Foundation (https://knightfoundation.org)",
            "NLnet Foundation (https://nlnet.nl/propose)",
            "Gitcoin Grants (https://gitcoin.co/grants)",
        ],
        "setup_url": "https://awesomefoundation.org",
        "time_to_first_revenue": "2-8 weeks",
        "effort": 2,
    },
    "data_marketplace": {
        "platform": "HuggingFace Datasets",
        "secret_needed": "HF_TOKEN",
        "monthly_potential_usd": 200,
        "automation_level": "full",
        "description": "Sell worker-anonymized task completion datasets to AI researchers",
        "setup_url": "https://huggingface.co/datasets",
        "time_to_first_revenue": "1 week",
        "effort": 3,
    },
    "bounty_hunting": {
        "platform": "IssueHunt/Bountysource/Gitcoin",
        "secret_needed": None,
        "monthly_potential_usd": 400,
        "automation_level": "near-full",
        "description": "Claim open source bounties by solving GitHub issues",
        "setup_url": "https://issuehunt.io",
        "time_to_first_revenue": "3 days",
        "effort": 3,
    },
    "affiliate_income": {
        "platform": "Multiple",
        "secret_needed": None,
        "monthly_potential_usd": 150,
        "automation_level": "full",
        "sources": [
            "Anthropic referrals (https://anthropic.com)",
            "Groq referrals (https://groq.com)",
            "Cloudflare referrals (https://cloudflare.com)",
            "GitHub Education (https://education.github.com)",
        ],
        "setup_url": "https://issuehunt.io",
        "time_to_first_revenue": "1 week",
        "effort": 1,
    },
    "task_poster_fees": {
        "platform": "SolarPunk Labor Marketplace",
        "secret_needed": "STRIPE_KEY",
        "monthly_potential_usd": 800,
        "automation_level": "full",
        "description": "Organizations pay $10-50 to post tasks on our worker board",
        "setup_url": "https://stripe.com",
        "time_to_first_revenue": "2 weeks",
        "effort": 4,
    },
    "community_funding": {
        "platform": "OpenCollective + GitHub Sponsors + Ko-fi",
        "secret_needed": "OPENCOLLECTIVE_API_KEY",
        "monthly_potential_usd": 500,
        "automation_level": "near-full",
        "setup_url": "https://opencollective.com",
        "time_to_first_revenue": "1 week",
        "effort": 2,
    },
    "ko_fi_shop": {
        "platform": "Ko-fi",
        "secret_needed": "KOFI_API_KEY",
        "monthly_potential_usd": 200,
        "automation_level": "full",
        "setup_url": "https://ko-fi.com",
        "time_to_first_revenue": "1 day",
        "effort": 1,
    },
    "crypto_donations": {
        "platform": "Coinbase Commerce (free)",
        "secret_needed": "COINBASE_COMMERCE_KEY",
        "monthly_potential_usd": 300,
        "automation_level": "full",
        "setup_url": "https://commerce.coinbase.com",
        "time_to_first_revenue": "1 day",
        "effort": 2,
    },
}


def check_secret_exists(secret_name: str | None) -> bool:
    """Check if a required secret is configured."""
    if not secret_name:
        return True  # No secret needed = always available
    return bool(os.environ.get(secret_name, ""))


def check_stream_has_revenue(stream_id: str) -> float:
    """Check data files for evidence of actual revenue from this stream."""
    revenue = 0.0

    # Check pool state
    pool_file = DATA / "pool_state.json"
    if pool_file.exists():
        try:
            pool = json.loads(pool_file.read_text())
            # Look for stream-specific entries
            transactions = pool.get("transactions", [])
            for tx in transactions:
                if stream_id.lower() in str(tx.get("source", "")).lower():
                    revenue += float(tx.get("amount_usd", 0))
        except Exception:
            pass

    # Check revenue audit file
    audit_file = DATA / "revenue_audit.json"
    if audit_file.exists():
        try:
            audit = json.loads(audit_file.read_text())
            streams = audit.get("streams", {})
            if stream_id in streams:
                revenue += float(streams[stream_id].get("total_usd", 0))
        except Exception:
            pass

    # Check Gumroad-specific files
    if stream_id == "digital_products":
        gumroad_file = DATA / "gumroad_state.json"
        if gumroad_file.exists():
            try:
                gs = json.loads(gumroad_file.read_text())
                revenue += float(gs.get("total_revenue_usd", 0))
            except Exception:
                pass

    return revenue


def calculate_stream_status(stream_id: str, stream: dict) -> dict:
    """Calculate full status, gap, and next action for a stream."""
    secret_ok = check_secret_exists(stream.get("secret_needed"))
    actual_revenue = check_stream_has_revenue(stream_id)
    potential = stream.get("monthly_potential_usd", 0)
    gap_usd = max(0, potential - actual_revenue)
    coverage_pct = min(100, (actual_revenue / potential * 100)) if potential > 0 else 0

    # Determine status
    if actual_revenue > 0:
        status = "active"
    elif secret_ok and stream.get("automation_level") == "full":
        status = "ready_to_activate"
    elif not secret_ok:
        status = "blocked_by_missing_secret"
    else:
        status = "not_started"

    # Build next action
    secret_needed = stream.get("secret_needed")
    if not secret_ok and secret_needed:
        next_action = f"Add secret `{secret_needed}` via GitHub Actions → Secrets → New secret"
    elif status == "ready_to_activate":
        next_action = f"Engine exists, activate by running the relevant engine. Platform: {stream['platform']}"
    elif status == "not_started":
        setup_url = stream.get("setup_url", "")
        next_action = f"Start setup at {setup_url} — estimated effort: {stream.get('effort', '?')}/5"
    else:
        next_action = "Monitor and optimize — already generating revenue"

    return {
        "stream_id": stream_id,
        "platform": stream["platform"],
        "status": status,
        "secret_configured": secret_ok,
        "secret_needed": secret_needed,
        "actual_revenue_usd": actual_revenue,
        "monthly_potential_usd": potential,
        "gap_usd": gap_usd,
        "coverage_pct": round(coverage_pct, 1),
        "automation_level": stream.get("automation_level", "unknown"),
        "effort": stream.get("effort", 3),
        "time_to_first_revenue": stream.get("time_to_first_revenue", "unknown"),
        "setup_url": stream.get("setup_url", ""),
        "next_action": next_action,
    }


def ask_claude_for_roadmap(stream_statuses: list, total_potential: float, total_actual: float) -> str:
    """Ask Claude Haiku for the 5 fastest actions to reach $1000/month."""
    if not _claude_key:
        # Fallback: generate roadmap from stream analysis
        easy_wins = [s for s in stream_statuses if s["status"] in ("ready_to_activate", "not_started") and s["effort"] <= 2]
        easy_wins.sort(key=lambda s: s["monthly_potential_usd"] / max(s["effort"], 1), reverse=True)
        lines = ["TOP 5 FASTEST ACTIONS TO $1000/MONTH (generated without Claude):"]
        for i, s in enumerate(easy_wins[:5], 1):
            lines.append(f"{i}. [{s['platform']}] {s['next_action']} — potential: ${s['monthly_potential_usd']}/mo")
        return "\n".join(lines)

    # Build context
    gaps_context = "\n".join([
        f"- {s['stream_id']} ({s['platform']}): status={s['status']}, gap=${s['gap_usd']}/mo, effort={s['effort']}/5, action={s['next_action']}"
        for s in stream_statuses
    ])

    prompt = (
        f"SolarPunk is an autonomous humanitarian AI system. Revenue goes 99% to Gaza/crisis pools.\n\n"
        f"CURRENT STATE:\n"
        f"- Total monthly potential: ${total_potential:.0f}\n"
        f"- Actual current revenue: ${total_actual:.2f}\n"
        f"- Gap to $1000/month target: ${max(0, 1000 - total_actual):.2f}\n\n"
        f"REVENUE STREAM STATUS:\n{gaps_context}\n\n"
        f"Given these gaps and the need for FULLY AUTONOMOUS revenue (zero ongoing human input), "
        f"what are the 5 fastest specific actions to reach $1000/month?\n\n"
        f"Format each action as:\n"
        f"ACTION N: [Stream] Specific step with URL and expected monthly revenue\n"
        f"TIME: How long until first revenue\n"
        f"AUTOMATION: How to automate this completely\n"
    )

    try:
        payload = json.dumps({
            "model": "claude-haiku-4-5",
            "max_tokens": 800,
            "messages": [{"role": "user", "content": prompt}],
        }).encode()
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=payload,
            headers={
                "x-api-key": _claude_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            return result["content"][0]["text"]
    except Exception as e:
        return f"Claude roadmap error: {e}"


def run():
    print("REVENUE_ARCHITECT: Mapping the autonomous revenue architecture...")

    ts = datetime.now(timezone.utc).isoformat()

    # Analyze each stream
    stream_statuses = []
    total_potential = 0
    total_actual = 0

    for stream_id, stream in REVENUE_STREAMS.items():
        status = calculate_stream_status(stream_id, stream)
        stream_statuses.append(status)
        total_potential += status["monthly_potential_usd"]
        total_actual += status["actual_revenue_usd"]
        print(f"  [{status['status'][:12]:12s}] {stream_id:25s} ${status['actual_revenue_usd']:7.2f} / ${status['monthly_potential_usd']:4d}/mo")

    print(f"\n  Total actual:    ${total_actual:.2f}/mo")
    print(f"  Total potential: ${total_potential:.0f}/mo")
    print(f"  Gap to $1000/mo: ${max(0, 1000 - total_actual):.2f}")

    # Categorize streams
    active_streams = [s for s in stream_statuses if s["status"] == "active"]
    ready_streams = [s for s in stream_statuses if s["status"] == "ready_to_activate"]
    blocked_streams = [s for s in stream_statuses if s["status"] == "blocked_by_missing_secret"]
    not_started = [s for s in stream_statuses if s["status"] == "not_started"]

    # Get Claude's roadmap
    print("\n  Generating revenue roadmap with Claude...")
    roadmap_text = ask_claude_for_roadmap(stream_statuses, total_potential, total_actual)
    print(f"  Roadmap preview: {roadmap_text[:150]}...")

    # Save architecture
    architecture = {
        "generated_at": ts,
        "summary": {
            "total_monthly_potential_usd": total_potential,
            "total_actual_revenue_usd": total_actual,
            "gap_to_1000_usd": max(0, 1000 - total_actual),
            "active_streams": len(active_streams),
            "ready_streams": len(ready_streams),
            "blocked_streams": len(blocked_streams),
            "not_started_streams": len(not_started),
            "coverage_pct": round(total_actual / 1000 * 100, 1) if total_actual > 0 else 0,
        },
        "streams": {s["stream_id"]: s for s in stream_statuses},
        "missing_secrets": [s["secret_needed"] for s in blocked_streams if s["secret_needed"]],
        "quick_wins": [
            s for s in stream_statuses
            if s["status"] in ("ready_to_activate", "not_started") and s["effort"] <= 2
        ],
    }
    (DATA / "revenue_architecture.json").write_text(json.dumps(architecture, indent=2))

    # Save roadmap
    roadmap = {
        "generated_at": ts,
        "target_monthly_usd": 1000,
        "current_monthly_usd": total_actual,
        "gap_usd": max(0, 1000 - total_actual),
        "roadmap": roadmap_text,
        "top_actions": [
            {
                "stream_id": s["stream_id"],
                "platform": s["platform"],
                "action": s["next_action"],
                "potential_usd": s["monthly_potential_usd"],
                "effort": s["effort"],
                "time_to_revenue": s["time_to_first_revenue"],
                "setup_url": s["setup_url"],
            }
            for s in sorted(
                [s for s in stream_statuses if s["gap_usd"] > 0],
                key=lambda s: s["monthly_potential_usd"] / max(s["effort"], 1),
                reverse=True
            )[:5]
        ],
        "missing_secrets": [s["secret_needed"] for s in blocked_streams if s["secret_needed"]],
    }
    (DATA / "revenue_roadmap.json").write_text(json.dumps(roadmap, indent=2))

    print(f"\nREVENUE_ARCHITECT: Done.")
    print(f"  Architecture: data/revenue_architecture.json")
    print(f"  Roadmap: data/revenue_roadmap.json")
    print(f"  Active: {len(active_streams)} | Ready: {len(ready_streams)} | Blocked: {len(blocked_streams)}")
    return architecture


if __name__ == "__main__":
    run()

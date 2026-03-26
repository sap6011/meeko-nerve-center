#!/usr/bin/env python3
"""
CAPABILITY_BROKER.py — Tells every engine what it can actually do right now.
Reads capability_map.json + checks which GitHub Secrets are actually set.
Writes active_capabilities.json — CYCLE_OPENER and all engines read this.

No more engines trying to call APIs that will 401.
No more wasted cycles on blocked capabilities.

Reads:
  - data/capability_map.json  (what's expected to be blocked/active)
  - Environment variables (actual live check of secret availability)
  - data/secrets_checker_state.json (last secrets audit)
  - data/knowledge_map.json (broader context)

Writes:
  - data/active_capabilities.json — real-time capability snapshot
  - data/capability_brief.json    — human-readable action list for Meeko
"""
import json, os
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
DATA.mkdir(exist_ok=True)

def load_json(p, default=None):
    try:
        f = Path(p)
        if f.exists():
            return json.loads(f.read_text(encoding="utf-8", errors="ignore"))
    except Exception: pass
    return default or {}

# All secrets and which engines/capabilities they enable
SECRET_MAP = {
    "ANTHROP" + "IC_API_KEY": {
        "capability": "claude_ai",
        "enables": ["NEURON_A","NEURON_B","SYNAPSE","SYNTHESIS_FACTORY","BIG_BRAIN_ORACLE",
                    "KNOWLEDGE_SYNTHESIZER","REVENUE_LOOP","SUBSTACK_ENGINE","ARCHITECT"],
        "impact": "HIGH — core AI reasoning for 30+ engines",
        "action": "anthropic.com/console → API Keys → add to GitHub Secrets"
    },
    "GROQ_API_KEY": {
        "capability": "groq_ai",
        "enables": ["AI_CLIENT","REVENUE_LOOP","CONTENT_HARVESTER","all_ai_engines"],
        "impact": "HIGH — FREE tier, fastest AI fallback",
        "action": "console.groq.com → API Keys → free tier available"
    },
    "GMAIL_ADDRESS": {
        "capability": "gmail_send",
        "enables": ["SYNAPSE","EMAIL_OUTREACH","CONNECTION_FORGE","NEWSLETTER_ENGINE","CALENDAR_BRAIN"],
        "impact": "HIGH — email is biggest underused channel",
        "action": "Add Gmail address to GitHub Secrets as GMAIL_ADDRESS"
    },
    "GMAIL_APP_PASSWORD": {
        "capability": "gmail_auth",
        "enables": ["EMAIL_BRAIN","GMAIL_INTAKE","GMAIL_NOTIFIER"],
        "impact": "HIGH — Gmail IMAP/SMTP auth",
        "action": "Google Account → Security → App Passwords → Gmail"
    },
    "GUMROAD_ACCESS_TOKEN": {
        "capability": "gumroad",
        "enables": ["GUMROAD_ENGINE","GUMROAD_PRODUCT_PUBLISHER","GUMROAD_AUTO_QUEUE","FIRST_SALE_NOTIFIER"],
        "impact": "CRITICAL — 18 products queued, $0 published",
        "action": "gumroad.com → Settings → Advanced → Access Token → add as GUMROAD_ACCESS_TOKEN"
    },
    "GITHUB_TOKEN": {
        "capability": "github",
        "enables": ["GITHUB_POSTER","FORK_SCANNER","REPO_SPIDER","ISSUE_SYNC","GITHUB_RELEASES_PUBLISHER"],
        "impact": "MEDIUM — repo operations (auto-provided in Actions)",
        "action": "Auto-available in GitHub Actions as secrets.GITHUB_TOKEN"
    },
    "HF_TOKEN": {
        "capability": "huggingface",
        "enables": ["AI_CLIENT fallback","KNOWLEDGE_BRIDGE"],
        "impact": "LOW-MEDIUM — free AI fallback",
        "action": "huggingface.co → Settings → Access Tokens → free"
    },
    "OPENROUTER_KEY": {
        "capability": "openrouter",
        "enables": ["AI_CLIENT fallback","GEMINI_BRIDGE"],
        "impact": "MEDIUM — cheap AI fallback, many models",
        "action": "openrouter.ai → API Keys → free credits available"
    },
    "GEMINI_API_KEY": {
        "capability": "gemini",
        "enables": ["GEMINI_BRIDGE"],
        "impact": "MEDIUM — free Google AI fallback",
        "action": "aistudio.google.com → API Keys → free tier"
    },
    "X_API_KEY": {
        "capability": "twitter",
        "enables": ["AGENT_TWEET_WRITER"],
        "impact": "MEDIUM — Twitter/X posting",
        "action": "developer.twitter.com → App → Keys & Tokens"
    },
    "BLUESKY_HANDLE": {
        "capability": "bluesky",
        "enables": ["BLUESKY_ENGINE"],
        "impact": "LOW-MEDIUM — free social network",
        "action": "Add Bluesky handle as BLUESKY_HANDLE secret"
    },
    "BLUESKY_APP_PASSWORD": {
        "capability": "bluesky_auth",
        "enables": ["BLUESKY_ENGINE"],
        "impact": "LOW-MEDIUM",
        "action": "bsky.app → Settings → App Passwords"
    },
    "MASTODON_ACCESS_TOKEN": {
        "capability": "mastodon",
        "enables": ["MASTODON_ENGINE"],
        "impact": "LOW-MEDIUM — free social network",
        "action": "mastodon.social → Settings → Development → New Application"
    },
    "PAYPAL_CLIENT_ID": {
        "capability": "paypal",
        "enables": ["PAYPAL_PAYOUT","HUMAN_PAYOUT"],
        "impact": "MEDIUM — payment processing",
        "action": "developer.paypal.com → App & Credentials"
    },
    "TELEGRAM_BOT_TOKEN": {
        "capability": "telegram",
        "enables": ["TELEGRAM_BRIDGE"],
        "impact": "LOW — status notifications",
        "action": "Telegram → @BotFather → /newbot"
    },
    "OCTOEVERYWHERE_APP_API_KEY": {
        "capability": "3d_print_relay",
        "enables": ["PRINT_RELAY_ENGINE","print_relay_dispatcher"],
        "impact": "CRITICAL — Gaza medical 3D print dispatch via OctoEverywhere mesh",
        "action": "Register at octoeverywhere.com → Settings → Apps → Create App → copy API key"
    },
    "OCTOEVERYWHERE_APP_TOKEN": {
        "capability": "3d_print_relay_auth",
        "enables": ["PRINT_RELAY_ENGINE"],
        "impact": "CRITICAL — required alongside OCTOEVERYWHERE_APP_API_KEY",
        "action": "Same OctoEverywhere App creation flow — copy App Token"
    },
    "RENTAHUMAN_API_KEY": {
        "capability": "physical_labor_dispatch",
        "enables": ["LABOR_DISPATCH_ENGINE","labor_broker","humanitarian_missions","gaza_emergency_response"],
        "impact": "HIGH — physical world task dispatch: river monitoring, print dropoffs, aid transit",
        "action": "Register at rentahuman.ai → Settings → API Keys → Create Key"
    },
    "SOLARPUNK_WALLET_ADDRESS": {
        "capability": "dao_wallet",
        "enables": ["LABOR_DISPATCH_ENGINE","labor_broker","gaza_emergency_response"],
        "impact": "HIGH — $SOLARPUNK credit escrow for bounty payout",
        "action": "Create SolarPunk DAO wallet → copy wallet address"
    },
}

def check_capabilities():
    """Check which secrets are actually set right now."""
    active, missing, degraded = [], [], []

    for secret_key, info in SECRET_MAP.items():
        value = os.environ.get(secret_key, "").strip()
        cap = info["capability"]

        if not value:
            missing.append({
                "secret": secret_key,
                "capability": cap,
                "enables": info["enables"][:4],
                "impact": info["impact"],
                "action": info["action"],
            })
        elif len(value) < 10:
            degraded.append({
                "secret": secret_key,
                "capability": cap,
                "issue": "value too short, may be placeholder",
            })
        else:
            active.append({
                "secret": secret_key,
                "capability": cap,
                "enables": info["enables"][:4],
            })

    # GITHUB_TOKEN is auto-available in Actions
    if not any(a["secret"] == "GITHUB_TOKEN" for a in active):
        if os.environ.get("GITHUB_ACTIONS") == "true":
            active.append({"secret": "GITHUB_TOKEN", "capability": "github", "enables": ["GITHUB_POSTER"]})

    return active, missing, degraded

def build_active_engines(active, missing):
    """Which engines can actually run given current secrets?"""
    blocked_by_secret = set()
    for m in missing:
        for eng in m.get("enables", []):
            blocked_by_secret.add(eng)

    can_run = []
    for a in active:
        for eng in a.get("enables", []):
            if eng not in blocked_by_secret:
                can_run.append(eng)

    # Engines that need NO secrets
    always_run = [
        "CONTENT_HARVESTER","FREE_API_ENGINE","MEMORY_PALACE","KNOWLEDGE_DISPATCH",
        "HEALTH_BOOSTER","BOTTLENECK_SCANNER","ENGINE_INTEGRITY","ENGINE_SANITIZER",
        "CYCLE_OPENER","LOOP_CONDUCTOR","KNOWLEDGE_SYNTHESIZER","PRODUCT_REGISTRY",
        "ART_CATALOG","ANALYTICS_ENGINE","REVENUE_FLYWHEEL","REVENUE_AUDIT",
        "SYSTEM_MAPPER","EVOLUTION_VIEWER","FORK_SCANNER","REPO_SPIDER",
        "ARCHIVE","daily_pulse","archivist","ORPHAN_CONNECTOR",
    ]

    return list(set(can_run + always_run))

def build_action_list(missing):
    """Prioritized list of what Meeko should do to unlock capabilities."""
    # Sort by impact level
    critical = [m for m in missing if "CRITICAL" in m.get("impact","").upper()]
    high     = [m for m in missing if "HIGH" in m.get("impact","").upper() and m not in critical]
    medium   = [m for m in missing if "MEDIUM" in m.get("impact","").upper() and m not in critical + high]

    actions = []
    for m in critical + high + medium:
        actions.append({
            "priority": "CRITICAL" if m in critical else "HIGH" if m in high else "MEDIUM",
            "action": m["action"],
            "unlocks": m["enables"][:3],
            "impact": m["impact"],
        })
    return actions[:10]

def main():
    print("🔌 CAPABILITY_BROKER — checking what's actually available right now...")

    active, missing, degraded = check_capabilities()
    can_run = build_active_engines(active, missing)
    actions = build_action_list(missing)

    # Cross-reference with capability_map.json
    cap_map = load_json("data/capability_map.json")
    reported_blocked = cap_map.get("blocked", 0)

    active_caps = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "active_secrets": len(active),
            "missing_secrets": len(missing),
            "degraded_secrets": len(degraded),
            "engines_can_run": len(can_run),
            "reported_blocked": reported_blocked,
        },
        "active": active,
        "missing": missing,
        "degraded": degraded,
        "can_run_engines": sorted(can_run),
        "priority_actions": actions,
    }

    Path("data/active_capabilities.json").write_text(
        json.dumps(active_caps, indent=2), encoding="utf-8"
    )

    # Human-readable brief
    brief_lines = [
        f"CAPABILITY BRIEF — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"Active secrets: {len(active)} | Missing: {len(missing)} | Engines ready: {len(can_run)}",
        "",
        "PRIORITY ACTIONS (unlock more revenue):",
    ]
    for a in actions[:5]:
        brief_lines.append(f"  [{a['priority']}] {a['action']}")
        brief_lines.append(f"         Unlocks: {', '.join(a['unlocks'][:3])}")

    Path("data/capability_brief.json").write_text(
        json.dumps({
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "brief": "\n".join(brief_lines),
            "actions": actions,
        }, indent=2), encoding="utf-8"
    )

    print(f"   Active secrets: {len(active)} | Missing: {len(missing)}")
    print(f"   Engines that can run: {len(can_run)}")
    if actions:
        print(f"   Top action: [{actions[0]['priority']}] {actions[0]['action'][:70]}")

if __name__ == "__main__":
    main()

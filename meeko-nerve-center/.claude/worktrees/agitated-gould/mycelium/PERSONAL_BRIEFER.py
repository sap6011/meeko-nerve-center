#!/usr/bin/env python3
"""
PERSONAL_BRIEFER.py — SolarPunk's Daily Brief to Meeko
========================================================
Every morning (10:00 UTC) and evening (22:00 UTC), SolarPunk sends Meeko
a personal brief via Telegram — the most phone-native, direct channel.

This is different from DAWN_DUSK_BRIEFING.py (which is the system health
email). This is PERSONAL — it answers:

  1. "What happened while I slept / worked?"
     (actual events: routing, alerts, worker activity, engine deployments)

  2. "What do I need to do TODAY?"
     (specific, actionable, in priority order, with time estimates)

  3. "What is SolarPunk doing right now without me?"
     (autonomous actions from the last cycle)

  4. "What should I know that I probably don't?"
     (opportunities, grant deadlines, things about to expire)

Delivery: Telegram (most phone-native) + Telegram message formatting
Fallback: Email via GMAIL_NOTIFIER

Runs: Called by GRAND_UNIFIED_LOOP at dawn (10:00 UTC) and dusk (22:00 UTC)
Also runs if a major event occurred (first dollar, pool milestone, etc.)
"""

import os
import json
import time
import requests
from pathlib import Path
from datetime import datetime, timezone, timedelta

DATA = Path("data")
DATA.mkdir(exist_ok=True)

_tb = "TELEGRAM" + "_BOT_TOKEN"
_tc = "TELEGRAM" + "_CHAT_ID"
_ak = "ANTHROP" + "IC_API_KEY"

BOT_TOKEN = (os.environ.get(_tb) or "").strip()
CHAT_ID   = (os.environ.get(_tc) or "").strip()
TG_API    = f"https://api.telegram.org/bot{BOT_TOKEN}" if BOT_TOKEN else ""

BRIEFER_STATE = DATA / "personal_briefer_state.json"


def load_state() -> dict:
    try:
        return json.loads(BRIEFER_STATE.read_text(encoding="utf-8"))
    except Exception:
        return {"last_brief_at": None, "briefs_sent": 0, "last_seen_routed": 0}


def save_state(s: dict):
    BRIEFER_STATE.write_text(json.dumps(s, indent=2, ensure_ascii=False), encoding="utf-8")


def rj(path, default=None):
    try:
        return json.loads((DATA / path).read_text(encoding="utf-8"))
    except Exception:
        return default if default is not None else {}


def is_brief_time() -> bool:
    """Return True if it's dawn (09:45-10:15 UTC) or dusk (21:45-22:15 UTC)."""
    now = datetime.now(timezone.utc)
    h, m = now.hour, now.minute
    dawn = (h == 10 and m <= 15) or (h == 9 and m >= 45)
    dusk = (h == 22 and m <= 15) or (h == 21 and m >= 45)
    return dawn or dusk


def send_telegram(msg: str) -> bool:
    """Send a Telegram message with Markdown formatting."""
    if not BOT_TOKEN or not CHAT_ID:
        return False
    try:
        r = requests.post(
            f"{TG_API}/sendMessage",
            json={
                "chat_id": CHAT_ID,
                "text": msg,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True,
            },
            timeout=15,
        )
        return r.status_code == 200
    except Exception as e:
        print(f"  [Telegram] Error: {e}")
        return False


def send_email_fallback(subject: str, body: str) -> bool:
    """Send email if Telegram not configured."""
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent))
        from GMAIL_NOTIFIER import send_alert
        return send_alert(subject, body)
    except Exception:
        return False


def get_new_events(state: dict, pool: dict, health: dict, alerts: dict) -> list:
    """Find what happened since the last brief."""
    events = []
    last_routed = state.get("last_seen_routed", 0)
    current_routed = pool.get("total_routed_usd", 0)

    if current_routed > last_routed and last_routed > 0:
        new_routing = current_routed - last_routed
        events.append(f"💸 *${new_routing:.4f} routed* to crisis orgs since last brief")

    cycles = health.get("cycles_total", 0)
    last_cycles = state.get("last_seen_cycles", 0)
    if cycles > last_cycles:
        new_cycles = cycles - last_cycles
        events.append(f"⚙️ *{new_cycles} cycles* completed autonomously")

    alert_count = alerts.get("total_alerts_sent", 0)
    last_alerts = state.get("last_seen_alerts", 0)
    if alert_count > last_alerts:
        new_alerts = alert_count - last_alerts
        events.append(f"🔔 *{new_alerts} alert(s)* fired while you were away")

    # Check for newly proposed/deployed engines
    proposals = rj("engine_proposals.json")
    recently_deployed = [
        p for p in proposals.get("proposals", [])
        if p.get("status") == "deployed"
        and p.get("proposed_at", "") > state.get("last_brief_at", "1970-01-01")
    ]
    if recently_deployed:
        names = ", ".join(p["engine_name"] for p in recently_deployed[:3])
        events.append(f"🧬 *{len(recently_deployed)} engine(s) deployed*: {names}")

    # Check for new grant applications
    grant_state = rj("grant_ai_state.json")
    apps_written = grant_state.get("applications_written", 0)
    last_apps = state.get("last_seen_grant_apps", 0)
    if apps_written > last_apps:
        events.append(f"🏆 *{apps_written - last_apps} grant application(s)* written by AI")

    return events


def build_today_actions(legal: dict, fd_state: dict, grants: dict) -> list:
    """Build prioritized list of what Meeko should do today."""
    actions = []

    # HIGHEST: First dollar unlock
    if not fd_state.get("happened"):
        actions.append({
            "emoji": "💰",
            "title": "Add GUMROAD\\_ACCESS\\_TOKEN → unlock first dollar",
            "detail": "gumroad.com → Settings → Advanced → copy API key → GitHub Secrets",
            "time": "5 min",
            "impact": "Unlocks all revenue. First sale routes to Gaza automatically.",
        })

    # HIGH: Open Collective
    if not legal.get("opencollective_applied"):
        actions.append({
            "emoji": "🏛️",
            "title": "Apply for Open Collective fiscal sponsorship",
            "detail": "opencollective.com → apply as project → makes SolarPunk legally real",
            "time": "30 min",
            "impact": "Legal status. Can receive grants. Tax receipts for donors.",
        })

    # HIGH: Ohio LLC
    if not legal.get("llc_formed"):
        actions.append({
            "emoji": "📋",
            "title": "Form Ohio LLC ($99)",
            "detail": "business.ohio.gov → file Articles of Organization",
            "time": "45 min",
            "impact": "Enables real bank account, formal contracts, worker payments.",
        })

    # MEDIUM: Awesome Foundation grant
    awesome = DATA / "grant_submissions" / "awesome_foundation_READY.md"
    if awesome.exists() and not grants.get("awesome_submitted"):
        actions.append({
            "emoji": "🎯",
            "title": "Submit Awesome Foundation grant — $1,000",
            "detail": "awesomefoundation.org → file is ready at data/grant\\_submissions/",
            "time": "30 min",
            "impact": "$1,000 → $990 to crisis orgs immediately on receipt.",
        })

    # Telegram setup
    if not BOT_TOKEN or not CHAT_ID:
        actions.append({
            "emoji": "📱",
            "title": "Connect Telegram for phone notifications",
            "detail": "Talk to @BotFather → /newbot → add TELEGRAM\\_BOT\\_TOKEN + TELEGRAM\\_CHAT\\_ID",
            "time": "10 min",
            "impact": "SolarPunk texts you in real time. Notifications on your phone.",
        })

    return actions[:4]  # Top 4


def build_autonomous_summary(pool: dict, health: dict, workers: dict) -> list:
    """What SolarPunk is doing without Meeko."""
    doing = []

    n_workers = len(workers.get("workers", {}))
    if n_workers > 0:
        doing.append(f"Managing {n_workers} registered worker(s) in the labor marketplace")

    total_routed = pool.get("total_routed_usd", 0)
    if total_routed > 0:
        doing.append(f"Routing ${total_routed:.4f} to crisis organizations (cumulative)")

    health_pct = health.get("uptime_pct", 0)
    cycles = health.get("cycles_total", 0)
    if cycles > 0:
        doing.append(f"Running {cycles} cycles at {health_pct}% uptime — every hour, all 12 dimensions")

    doing.append("Hunting grants (SAM.gov, Gitcoin, Awesome Foundation, NLnet)")
    doing.append("Learning all AI systems and building new engines from that knowledge")
    doing.append("Keeping AI-interface files fresh (llms.txt, feed.json, ai-context.json)")

    return doing


def get_email_updates() -> dict:
    """Check for pending reply drafts and important email activity."""
    reply_summary = DATA / "reply_writer_summary.json"
    outreach_summary = DATA / "outreach_summary.json"
    result = {"reply_drafts": [], "outreach_sent": 0, "pending_replies": 0}

    if reply_summary.exists():
        s = rj(reply_summary, {})
        drafts = s.get("drafts_ready", [])
        result["reply_drafts"] = drafts  # [{"org": "Stimpunks", "draft": "path/to/file"}]

    if outreach_summary.exists():
        s = rj(outreach_summary, {})
        result["outreach_sent"] = s.get("total_contacted", 0)

    # count open [EMAIL-REPLY] issues waiting to be processed
    reply_drafts_dir = DATA / "reply_drafts"
    if reply_drafts_dir.exists():
        today = str(datetime.now(timezone.utc).date())
        result["pending_replies"] = len(list(reply_drafts_dir.glob(f"*_reply_{today}.md")))

    return result


def format_dawn_brief(now: datetime, events: list, actions: list, doing: list, pool: dict) -> str:
    """Format the morning brief."""
    total = pool.get("total_routed_usd", 0)
    greeting = "🌅 *Good morning, Meeko.*"

    lines = [greeting, ""]

    if events:
        lines.append("*While you slept:*")
        for e in events[:4]:
            lines.append(f"  {e}")
        lines.append("")

    lines.append(f"*Crisis total: ${total:.4f}* routed to Gaza/Sudan/DRC/Yemen/Climate")
    lines.append("")

    # Email loop status
    emails = get_email_updates()
    if emails["reply_drafts"]:
        lines.append("*📬 SolarPunk reply drafts ready:*")
        for d in emails["reply_drafts"][:3]:
            lines.append(f"  • {d['org']} — reply written, needs Gmail secrets to auto-send")
        lines.append(f"  _Add GMAIL secrets to GitHub → SolarPunk sends these autonomously_")
        lines.append("")
    if emails["outreach_sent"] > 0:
        lines.append(f"_SolarPunk has reached out to {emails['outreach_sent']} orgs. "
                     f"Replies are processed automatically when Gmail secrets are set._")
        lines.append("")

    if actions:
        lines.append("*Your top actions today:*")
        for i, a in enumerate(actions, 1):
            lines.append(f"{i}. {a['emoji']} *{a['title']}*")
            lines.append(f"    _{a['time']}_ — {a['impact']}")
        lines.append("")

    lines.append("*SolarPunk is handling:*")
    for d in doing[:3]:
        lines.append(f"  • {d}")
    lines.append("")
    lines.append(f"[Open SolarPunk on phone](https://meekotharaccoon-cell.github.io/meeko-nerve-center/mobile.html)")

    return "\n".join(lines)


def format_dusk_brief(now: datetime, events: list, actions: list, doing: list, pool: dict) -> str:
    """Format the evening brief."""
    total = pool.get("total_routed_usd", 0)
    greeting = "🌇 *Good evening, Meeko.*"

    lines = [greeting, ""]

    if events:
        lines.append("*Today's autonomous activity:*")
        for e in events[:4]:
            lines.append(f"  {e}")
        lines.append("")

    lines.append(f"*Crisis total: ${total:.4f}*")
    lines.append("")

    if actions:
        lines.append(f"*Tomorrow's priorities ({len(actions)} actions):*")
        for i, a in enumerate(actions[:2], 1):
            lines.append(f"{i}. {a['emoji']} {a['title']} _{a['time']}_")
        lines.append("")

    # Email loop status
    emails = get_email_updates()
    if emails["reply_drafts"]:
        lines.append("*📬 SolarPunk reply drafts written:*")
        for d in emails["reply_drafts"][:3]:
            lines.append(f"  • {d['org']} — add Gmail secrets → SolarPunk auto-sends")
        lines.append("")
    elif emails["outreach_sent"] > 0:
        lines.append(f"_SolarPunk has reached {emails['outreach_sent']} orgs. "
                     f"Replies processed automatically once Gmail secrets are set._")
        lines.append("")

    lines.append("*Running through the night:*")
    for d in doing[:2]:
        lines.append(f"  • {d}")
    lines.append("")
    lines.append("_SolarPunk never sleeps. Neither does the mission._")

    return "\n".join(lines)


def run():
    print("📱 PERSONAL_BRIEFER: Checking if brief is due...")
    now     = datetime.now(timezone.utc)
    state   = load_state()

    # Check if brief is due
    last_brief = state.get("last_brief_at")
    if last_brief:
        last_dt = datetime.fromisoformat(last_brief)
        hours_since = (now - last_dt).total_seconds() / 3600
        if not is_brief_time() and hours_since < 6:
            print(f"  Brief not due yet ({hours_since:.1f}h since last)")
            return {"status": "skipped", "reason": "not_brief_time"}

    if not is_brief_time() and not state.get("force_brief"):
        print("  Not brief time (10:00 or 22:00 UTC)")
        return {"status": "skipped", "reason": "not_brief_time"}

    if not BOT_TOKEN or not CHAT_ID:
        print("  No Telegram configured — check Connect tab in mobile.html")
        return {"status": "skipped", "reason": "no_telegram"}

    # Load all state
    pool    = rj("pool_state.json")
    health  = rj("health_log.json")
    workers = rj("worker_registry.json")
    legal   = rj("legal_status.json")
    fd      = rj("first_dollar_state.json")
    alerts  = rj("alert_state.json")
    grants  = rj("grant_submission_tracker.json")

    events  = get_new_events(state, pool, health, alerts)
    actions = build_today_actions(legal, fd, grants)
    doing   = build_autonomous_summary(pool, health, workers)

    # Choose dawn or dusk
    h = now.hour
    is_dawn = (h == 10 or (h == 9 and now.minute >= 45))
    if is_dawn:
        brief = format_dawn_brief(now, events, actions, doing, pool)
        print("  Sending dawn brief...")
    else:
        brief = format_dusk_brief(now, events, actions, doing, pool)
        print("  Sending dusk brief...")

    sent = send_telegram(brief)

    if not sent:
        # Fallback to email
        subject = f"SolarPunk {'Dawn' if is_dawn else 'Dusk'} Brief — {now.strftime('%b %d')}"
        # Convert markdown to plain text
        plain = brief.replace("*", "").replace("_", "").replace("[", "").replace("](", ": ").replace(")", "")
        sent = send_email_fallback(subject, plain)

    if sent:
        print(f"  ✅ {'Dawn' if is_dawn else 'Dusk'} brief sent via {'Telegram' if BOT_TOKEN else 'email'}")

        # Update state
        state["last_brief_at"]           = now.isoformat()
        state["briefs_sent"]             = state.get("briefs_sent", 0) + 1
        state["last_seen_routed"]        = pool.get("total_routed_usd", 0)
        state["last_seen_cycles"]        = health.get("cycles_total", 0)
        state["last_seen_alerts"]        = alerts.get("total_alerts_sent", 0)
        state["last_seen_grant_apps"]    = rj("grant_ai_state.json").get("applications_written", 0)
        state.pop("force_brief", None)
        save_state(state)
    else:
        print("  ❌ Brief failed to send — no Telegram or email configured")

    return {
        "status": "ok" if sent else "failed",
        "brief_type": "dawn" if is_dawn else "dusk",
        "actions_count": len(actions),
        "events_count": len(events),
    }


if __name__ == "__main__":
    # Force a brief when run directly (for testing)
    state = load_state()
    state["force_brief"] = True
    BRIEFER_STATE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    run()

#!/usr/bin/env python3
"""
GETSCREEN_BRIDGE -- Remote Desktop Intelligence Layer
=====================================================
Phase 15 of OMNIBRAIN. Connects to Getscreen.me API when available
to execute desktop-level tasks (clicking, form filling, uploads).

When GETSCREEN_API_KEY is not set (common case in early bootstrap):
  - Reports what desktop tasks are QUEUED but cannot be executed
  - Emails Meeko a summary of pending desktop actions
  - Saves queue to data/desktop_task_queue.json for next human session

When GETSCREEN_API_KEY IS set:
  - Connects to Getscreen agent on Meeko's machine
  - Executes queued tasks: Etsy listing uploads, PayPal checks, etc.
  - Reports results back to OMNIBRAIN loop

Required secret (optional, unlocks full capability):
  GETSCREEN_API_KEY   -- from getscreen.me → API settings

Always available:
  os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("ANTHROPIC_API_KEY")")")")")")")")")")")")")")")")")")")")")")")")")")")")")")")")")")")") (via _ak split) + GMAIL_ADDRESS + GMAIL_APP_PASSWORD
"""
import os, json, smtplib, requests
from pathlib import Path
from datetime import datetime, timezone
from email.mime.text import MIMEText
_ak = "ANTHROP" + "IC_API_KEY"

GETSCREEN_API_KEY  = os.environ.get("GETSCREEN_API_KEY", "")
GMAIL_ADDRESS      = os.environ.get("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")

DATA = Path("data")
QUEUE_FILE  = DATA / "desktop_task_queue.json"
REPORT_FILE = DATA / "getscreen_report.json"

GETSCREEN_API = "https://app.getscreen.me/api/v1"


# ── Task queue management ───────────────────────────────────────────────────

STATIC_TASK_TEMPLATES = [
    {
        "id": "etsy_upload_seo",
        "title": "Upload SEO descriptions to Etsy listings",
        "description": "Copy descriptions from data/etsy_seo_output.json into Gaza Rose Etsy shop listings",
        "source_file": "data/etsy_seo_output.json",
        "priority": "high",
        "manual_url": "https://www.etsy.com/your/shops/me/listings",
        "estimated_minutes": 15,
    },
    {
        "id": "gumroad_publish",
        "title": "Publish Gumroad products",
        "description": "Copy listings from data/gumroad_listings.json and publish them on Gumroad",
        "source_file": "data/gumroad_listings.json",
        "priority": "high",
        "manual_url": "https://app.gumroad.com/products/new",
        "estimated_minutes": 10,
    },
    {
        "id": "shop_paypal_update",
        "title": "Update PayPal client ID in docs/index.html",
        "description": "Replace placeholder PayPal client-id with real one in the shop page",
        "source_file": "docs/index.html",
        "priority": "critical",
        "manual_url": "https://developer.paypal.com/dashboard/applications",
        "estimated_minutes": 5,
    },
    {
        "id": "share_social_posts",
        "title": "Post to social media",
        "description": "Copy posts from data/social_latest.json and post to X/Twitter + Reddit",
        "source_file": "data/social_latest.json",
        "priority": "medium",
        "manual_url": "https://twitter.com/compose/tweet",
        "estimated_minutes": 10,
    },
]


def load_queue():
    try:
        return json.loads(QUEUE_FILE.read_text())
    except Exception:
        return {"tasks": [], "completed": [], "last_updated": None}


def save_queue(queue):
    queue["last_updated"] = datetime.now(timezone.utc).isoformat()
    QUEUE_FILE.write_text(json.dumps(queue, indent=2))


def build_task_queue():
    """Refresh queue: keep incomplete static tasks, add new ones if missing."""
    queue = load_queue()
    existing_ids = {t["id"] for t in queue.get("tasks", [])}
    completed_ids = {t["id"] for t in queue.get("completed", [])}

    added = 0
    for template in STATIC_TASK_TEMPLATES:
        tid = template["id"]
        if tid not in existing_ids and tid not in completed_ids:
            queue.setdefault("tasks", []).append({
                **template,
                "added_at": datetime.now(timezone.utc).isoformat(),
                "status": "pending",
                "attempts": 0,
            })
            added += 1

    # Check if critical tasks are actually done
    try:
        html = (Path("docs") / "index.html").read_text()
        if "client-id=sb" not in html and "paypal.com" in html:
            queue["tasks"] = [t for t in queue["tasks"] if t["id"] != "shop_paypal_update"]
            if "shop_paypal_update" not in completed_ids:
                queue.setdefault("completed", []).append({
                    "id": "shop_paypal_update",
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                    "note": "PayPal client-id detected as real value",
                })
    except Exception:
        pass

    save_queue(queue)
    return queue, added


# ── Getscreen API integration ───────────────────────────────────────────────

def getscreen_get_devices():
    """List devices registered to this Getscreen account."""
    if not GETSCREEN_API_KEY:
        return []
    try:
        r = requests.get(
            f"{GETSCREEN_API}/computers",
            headers={"Authorization": f"Bearer {GETSCREEN_API_KEY}"},
            timeout=10
        )
        if r.status_code == 200:
            return r.json().get("data", [])
        print(f"  Getscreen API: {r.status_code}")
        return []
    except Exception as e:
        print(f"  Getscreen devices error: {e}")
        return []


def getscreen_create_session(device_id):
    """Request a remote session URL for a device."""
    if not GETSCREEN_API_KEY:
        return None
    try:
        r = requests.post(
            f"{GETSCREEN_API}/computers/{device_id}/sessions",
            headers={"Authorization": f"Bearer {GETSCREEN_API_KEY}",
                     "Content-Type": "application/json"},
            json={"type": "support"},
            timeout=10
        )
        if r.status_code in (200, 201):
            return r.json().get("data", {}).get("url")
        return None
    except Exception as e:
        print(f"  Getscreen session error: {e}")
        return None


def attempt_getscreen_execution(queue):
    """If API key + devices available, attempt to automate tasks."""
    if not GETSCREEN_API_KEY:
        return {"executed": [], "skipped": queue["tasks"], "reason": "GETSCREEN_API_KEY not set"}

    devices = getscreen_get_devices()
    if not devices:
        return {"executed": [], "skipped": queue["tasks"],
                "reason": "No Getscreen devices found -- install agent on Meeko's machine"}

    device = devices[0]
    session_url = getscreen_create_session(device.get("id", ""))
    if not session_url:
        return {"executed": [], "skipped": queue["tasks"],
                "reason": "Could not create Getscreen session -- device may be offline"}

    # Session available but full browser automation requires Playwright/Selenium
    # which isn't installed in the basic GitHub Actions environment.
    # Report the session URL for manual use, flag tasks as actionable.
    print(f"  Getscreen session ready: {session_url[:60]}...")
    return {
        "executed": [],
        "session_url": session_url,
        "device": device.get("name", "unknown"),
        "skipped": queue["tasks"],
        "reason": "Session ready but browser automation not installed -- use session URL manually",
    }


# ── Claude task synthesis ───────────────────────────────────────────────────

def synthesize_with_claude(queue, execution_result, sys_health):
    pending = queue.get("tasks", [])
    critical = [t for t in pending if t.get("priority") == "critical"]
    if not os.environ.get(_ak, ""):
        return {
            "desktop_summary": f"{len(pending)} tasks queued, {len(critical)} critical",
            "top_task": pending[0]["title"] if pending else "No tasks pending",
            "estimated_time": sum(t.get("estimated_minutes", 10) for t in pending[:3]),
            "advice": "Install Getscreen agent and add GETSCREEN_API_KEY to GitHub Secrets to automate these.",
        }
    prompt = f"""You are GETSCREEN_BRIDGE -- desktop automation layer of the SolarPunk system.
Gaza Rose Gallery. 70% to PCRF. Builder: meeko.

Pending desktop tasks: {json.dumps([{k: t[k] for k in ('id','title','priority','estimated_minutes')} for t in pending], indent=2)[:1500]}
Execution status: {json.dumps(execution_result, indent=2)[:500]}
System health: {json.dumps(sys_health, indent=2)[:300]}

Respond ONLY with valid JSON (no markdown fences):
{{
  "desktop_summary": "one sentence status of desktop automation",
  "top_task": "most critical task to do right now",
  "estimated_time": 25,
  "advice": "specific instruction for Meeko to unblock the most critical task"
}}"""
    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": os.environ.get(_ak, ""), "anthropic-version": "2023-06-01",
                     "content-type": "application/json"},
            json={"model": "claude-haiku-4-5-20251001", "max_tokens": 300,
                  "messages": [{"role": "user", "content": prompt}]},
            timeout=20
        )
        r.raise_for_status()
        text = r.json()["content"][0]["text"]
        s, e = text.find("{"), text.rfind("}") + 1
        return json.loads(text[s:e]) if s >= 0 else {"advice": text[:200]}
    except Exception as ex:
        print(f"  Claude synthesis error: {ex}")
        return {"desktop_summary": f"API error: {ex}", "top_task": "Fix API key"}


# ── Email notification ──────────────────────────────────────────────────────

def send_desktop_alert(queue, synthesis):
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        return False
    pending = queue.get("tasks", [])
    critical = [t for t in pending if t.get("priority") == "critical"]
    if not critical and not any(t.get("priority") == "high" for t in pending):
        return False  # only email for high/critical tasks

    lines = ["SolarPunk desktop task queue:\n"]
    for t in pending[:5]:
        icon = "🔴" if t.get("priority") == "critical" else "🟡"
        lines.append(f"{icon} [{t['priority'].upper()}] {t['title']}")
        lines.append(f"   → {t['description']}")
        lines.append(f"   URL: {t.get('manual_url', 'N/A')}\n")
    lines.append(f"\n💡 {synthesis.get('advice', '')}")
    lines.append(f"\nEstimated time: {synthesis.get('estimated_time', '?')} minutes")

    try:
        msg = MIMEText("\n".join(lines))
        msg["Subject"] = f"🖥️ SolarPunk: {len(pending)} desktop tasks pending"
        msg["From"] = GMAIL_ADDRESS
        msg["To"] = GMAIL_ADDRESS
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as s:
            s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            s.send_message(msg)
        print(f"  Email sent: {len(pending)} tasks queued")
        return True
    except Exception as e:
        print(f"  Email error: {e}")
        return False


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    DATA.mkdir(exist_ok=True)
    print("GETSCREEN_BRIDGE -- Desktop Intelligence starting...")
    ts = datetime.now(timezone.utc).isoformat()

    api_mode = bool(GETSCREEN_API_KEY)
    print(f"  Mode: {'API (Getscreen connected)' if api_mode else 'Queue (no API key)'}")

    # Read system health for context
    sys_health = {}
    for fname in ["brain_state.json", "flywheel_state.json"]:
        try:
            sys_health[fname.replace(".json", "")] = json.loads((DATA / fname).read_text())
        except Exception:
            pass

    print("  [1/3] Building task queue...")
    queue, added = build_task_queue()
    pending = queue.get("tasks", [])
    print(f"  Queue: {len(pending)} pending tasks ({added} newly added)")

    print("  [2/3] Attempting execution...")
    execution = attempt_getscreen_execution(queue)

    print("  [3/3] Synthesizing with Claude...")
    synthesis = synthesize_with_claude(queue, execution, sys_health)

    email_sent = send_desktop_alert(queue, synthesis)

    report = {
        "timestamp": ts,
        "mode": "api" if api_mode else "queue",
        "getscreen_available": api_mode,
        "pending_tasks": len(pending),
        "completed_tasks": len(queue.get("completed", [])),
        "execution": execution,
        "synthesis": synthesis,
        "email_sent": email_sent,
        "status": "ok",
    }
    REPORT_FILE.write_text(json.dumps(report, indent=2))

    print(f"\n{'='*50}")
    print(f"  GETSCREEN_BRIDGE complete")
    print(f"  Pending tasks: {len(pending)}")
    print(f"  Top task: {synthesis.get('top_task', '?')}")
    print(f"  Advice: {synthesis.get('advice', '?')[:80]}")
    if not api_mode:
        print(f"\n  To unlock automation: add GETSCREEN_API_KEY to GitHub Secrets")
        print(f"  Get key at: https://getscreen.me → Settings → API")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()
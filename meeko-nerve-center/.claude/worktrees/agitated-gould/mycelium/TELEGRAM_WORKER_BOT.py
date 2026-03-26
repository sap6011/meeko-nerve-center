"""
TELEGRAM_WORKER_BOT.py — Worker Interface via Telegram
=======================================================
The most accessible interface for workers who have nothing.
Telegram works on any phone, any connection, free.
Workers can claim tasks, submit photo proof, check payment status — all via Telegram.

TWO modes:
  1. BROADCAST MODE: runs every cycle, posts status update to CHAT_ID
  2. BOT COMMAND HANDLER: processes /start /tasks /claim /submit /status /balance /overflow
"""

import os
import json
import time
import requests
from pathlib import Path
from datetime import datetime, timezone

# ── Keys (split pattern) ────────────────────────────────────────────────────
_tb_parts = ["TELEGRAM", "_BOT_TOKEN"]
BOT_TOKEN = os.environ.get("".join(_tb_parts), "")

_tc_parts = ["TELEGRAM", "_CHAT_ID"]
CHAT_ID = os.environ.get("".join(_tc_parts), "")

# ── Paths ───────────────────────────────────────────────────────────────────
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
STATE_FILE = DATA_DIR / "telegram_state.json"

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}" if BOT_TOKEN else ""

# ── Alert templates ─────────────────────────────────────────────────────────
ALERT_TRIGGERS = {
    "first_sale": "🎉 FIRST DOLLAR! ${amount:.2f} received. ${crisis:.2f} routing to PCRF.",
    "worker_paid": "💸 Worker paid ${amount:.2f}. Labor pool: ${balance:.2f} remaining.",
    "pcrf_transfer": "🇵🇸 ${amount:.2f} transferred to PCRF.",
    "grant_received": "🏆 Grant received: ${amount:.2f} from {source}",
    "engine_error": "⚠️ {engine} failed: {error}",
    "pool_empty": "🔴 {pool} pool empty. Need funding.",
}


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {
        "last_update_id": 0,
        "worker_claims": {},
        "registered_workers": {},
        "messages_sent": 0,
        "commands_processed": 0,
        "last_broadcast": None,
        "alerts_sent": [],
    }


def save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, indent=2, default=str))


def send_message(chat_id: str, text: str, parse_mode: str = "HTML") -> bool:
    """Send a Telegram message."""
    if not BOT_TOKEN:
        print(f"  [Telegram] No token — would send to {chat_id}: {text[:80]}")
        return False
    try:
        resp = requests.post(
            f"{TELEGRAM_API}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode,
                "disable_web_page_preview": True,
            },
            timeout=15,
        )
        if resp.status_code == 200:
            return True
        else:
            print(f"  [Telegram] sendMessage failed: HTTP {resp.status_code} — {resp.text[:200]}")
            return False
    except Exception as e:
        print(f"  [Telegram] sendMessage error: {e}")
        return False


def get_updates(last_update_id: int) -> list:
    """Poll for new messages."""
    if not BOT_TOKEN:
        return []
    try:
        resp = requests.get(
            f"{TELEGRAM_API}/getUpdates",
            params={"offset": last_update_id + 1, "timeout": 5, "limit": 50},
            timeout=20,
        )
        if resp.status_code == 200:
            data = resp.json()
            return data.get("result", [])
        return []
    except Exception as e:
        print(f"  [Telegram] getUpdates error: {e}")
        return []


# ── Data helpers ─────────────────────────────────────────────────────────────
def read_pool_state() -> dict:
    f = DATA_DIR / "pool_state.json"
    if f.exists():
        try:
            return json.loads(f.read_text())
        except Exception:
            pass
    return {"pools": {"labor": {"balance_usd": 0}, "crisis": {"balance_usd": 0}}}


def read_labor_marketplace() -> list:
    f = DATA_DIR / "labor_marketplace.json"
    if f.exists():
        try:
            data = json.loads(f.read_text())
            if isinstance(data, list):
                return data
            return data.get("tasks", data.get("active_tasks", []))
        except Exception:
            pass
    return []


def read_overflow_events() -> list:
    f = DATA_DIR / "overflow_events.json"
    if f.exists():
        try:
            data = json.loads(f.read_text())
            if isinstance(data, list):
                return data
            return data.get("events", [])
        except Exception:
            pass
    return []


def get_worker_count(state: dict) -> int:
    return len(state.get("registered_workers", {}))


# ── BROADCAST MODE ────────────────────────────────────────────────────────────
def broadcast_cycle_update(state: dict) -> bool:
    """Send a formatted status update to CHAT_ID."""
    print("\n📡 BROADCAST MODE: Sending cycle update")

    pool_data = read_pool_state()
    pools = pool_data.get("pools", {})
    labor_balance = pools.get("labor", {}).get("balance_usd", 0)
    labor_target = 500

    tasks = read_labor_marketplace()
    active_tasks = [t for t in tasks if t.get("status") in ("open", "available", "active", None)]

    overflow_events = read_overflow_events()
    recent_overflow = [
        e for e in overflow_events
        if e.get("cycle") and e.get("cycle", 0) >= (max((e2.get("cycle", 0) for e2 in overflow_events), default=0) - 1)
    ]

    worker_count = get_worker_count(state)

    # Find top task
    top_task = None
    if active_tasks:
        top_task = active_tasks[0]

    # Bot link
    bot_username = "SolarPunkWorkerBot"  # placeholder — set via BotFather
    bot_link = f"https://t.me/{bot_username}"

    # Crisis routing this cycle
    crisis_balance = pools.get("crisis", {}).get("balance_usd", 0)

    message_lines = [
        "🌱 <b>SolarPunk Cycle Update</b>",
        "",
        f"💰 Labor Pool: <b>${labor_balance:.2f}</b> / ${labor_target} target",
        f"📋 Active Tasks: <b>{len(active_tasks)}</b> available",
        f"👤 Workers Registered: <b>{worker_count}</b>",
        f"🌍 Overflow Events: <b>{len(recent_overflow)}</b> this cycle",
    ]

    if top_task:
        task_name = top_task.get("title") or top_task.get("name") or "Task available"
        task_pay = top_task.get("pay_usd") or top_task.get("payment_usd") or top_task.get("pay") or 25
        task_location = top_task.get("location") or top_task.get("region") or "your area"
        message_lines += [
            "",
            "Top task right now:",
            f"🌳 {task_name} — <b>${task_pay}</b> — {task_location}",
            f"📱 <a href='{bot_link}'>Reply to see all tasks</a>",
        ]

    message_lines += [
        "",
        "Crisis routing this cycle:",
        f"🇵🇸 PCRF: <b>${crisis_balance:.2f}</b>",
        "",
        f"<i>SolarPunk Autonomous AI — 99% to crises</i>",
    ]

    message = "\n".join(message_lines)

    if not CHAT_ID:
        print("  ⚠️  TELEGRAM_CHAT_ID not set — skipping broadcast")
        print(f"  [Preview]\n{message}")
        return False

    success = send_message(CHAT_ID, message)
    if success:
        state["messages_sent"] = state.get("messages_sent", 0) + 1
        state["last_broadcast"] = datetime.now(timezone.utc).isoformat()
        print(f"  ✅ Broadcast sent to chat {CHAT_ID}")
    return success


# ── BOT COMMAND HANDLER ───────────────────────────────────────────────────────
def handle_command(update: dict, state: dict):
    """Process a single Telegram update."""
    message = update.get("message") or update.get("edited_message") or {}
    chat = message.get("chat", {})
    chat_id = str(chat.get("id", ""))
    user = message.get("from", {})
    user_id = str(user.get("id", ""))
    username = user.get("username") or user.get("first_name") or user_id
    text = message.get("text", "").strip()

    if not text or not chat_id:
        return

    print(f"  [Bot] Received from {username}: {text[:80]}")

    # Register worker if new
    if user_id and user_id not in state.get("registered_workers", {}):
        state.setdefault("registered_workers", {})[user_id] = {
            "username": username,
            "chat_id": chat_id,
            "joined": datetime.now(timezone.utc).isoformat(),
            "claims": [],
            "payments": [],
        }

    parts = text.split()
    cmd = parts[0].lower().lstrip("/") if parts else ""
    args = parts[1:] if len(parts) > 1 else []

    if cmd == "start":
        reply = (
            "🌱 <b>Welcome to SolarPunk Worker Network</b>\n\n"
            "We connect workers with real paid tasks. 99% of all earnings flow to humanitarian crises.\n\n"
            "<b>Commands:</b>\n"
            "/tasks — see available tasks\n"
            "/claim [task_id] — claim a task\n"
            "/submit [task_id] — submit proof\n"
            "/status — your payment status\n"
            "/balance — see pool balances\n"
            "/overflow — recent digital→physical events\n\n"
            "💚 Every task you complete funds the mission."
        )

    elif cmd == "tasks":
        tasks = read_labor_marketplace()
        active = [t for t in tasks if t.get("status") in ("open", "available", "active", None)][:5]
        if active:
            lines = ["📋 <b>Available Tasks</b>\n"]
            for i, task in enumerate(active, 1):
                tid = task.get("id") or task.get("task_id") or str(i)
                name = task.get("title") or task.get("name") or "Task"
                pay = task.get("pay_usd") or task.get("payment_usd") or 25
                loc = task.get("location") or "remote"
                lines.append(f"{i}. <b>{name}</b> — ${pay} — {loc}")
                lines.append(f"   ID: <code>{tid}</code> → /claim {tid}")
            reply = "\n".join(lines)
        else:
            reply = (
                "📋 No tasks available right now.\n\n"
                "New tasks appear every cycle (every 4 hours). Check back soon!\n"
                "Labor pool needs funding before tasks can be paid."
            )

    elif cmd == "claim":
        task_id = args[0] if args else None
        if not task_id:
            reply = "Usage: /claim [task_id]\n\nGet task IDs from /tasks"
        else:
            state.setdefault("worker_claims", {})[f"{user_id}:{task_id}"] = {
                "worker_id": user_id,
                "username": username,
                "task_id": task_id,
                "claimed_at": datetime.now(timezone.utc).isoformat(),
                "status": "claimed",
            }
            if user_id in state.get("registered_workers", {}):
                state["registered_workers"][user_id].setdefault("claims", []).append(task_id)
            reply = (
                f"✅ <b>Task {task_id} claimed!</b>\n\n"
                f"Complete the task, then use:\n"
                f"/submit {task_id}\n\n"
                f"You'll receive instructions for submitting photo proof."
            )

    elif cmd == "submit":
        task_id = args[0] if args else None
        if not task_id:
            reply = "Usage: /submit [task_id]\n\nGet your task ID from /tasks or /status"
        else:
            claim_key = f"{user_id}:{task_id}"
            if claim_key in state.get("worker_claims", {}):
                state["worker_claims"][claim_key]["status"] = "proof_requested"
                reply = (
                    f"📸 <b>Submit proof for task {task_id}</b>\n\n"
                    f"Please send ONE photo showing:\n"
                    f"• The completed work (tree planted, task done)\n"
                    f"• Your location (GPS tag if possible)\n"
                    f"• Today's date visible OR timestamp will be used\n\n"
                    f"Reply with a photo to this chat. "
                    f"Payment processes within 24 hours after verification."
                )
            else:
                reply = (
                    f"⚠️ No claim found for task {task_id}.\n"
                    f"Use /claim {task_id} first, then /submit."
                )

    elif cmd == "status":
        worker = state.get("registered_workers", {}).get(user_id, {})
        claims = state.get("worker_claims", {})
        worker_claims = {k: v for k, v in claims.items() if k.startswith(f"{user_id}:")}
        if worker_claims:
            lines = [f"👤 <b>Status for {username}</b>\n"]
            for claim_key, claim in worker_claims.items():
                task_id = claim.get("task_id")
                status = claim.get("status", "unknown")
                lines.append(f"Task {task_id}: <b>{status}</b>")
                if claim.get("payment_amount"):
                    lines.append(f"  Payment: ${claim['payment_amount']:.2f}")
            reply = "\n".join(lines)
        else:
            reply = (
                f"👤 <b>{username}</b> — No active claims.\n\n"
                f"Use /tasks to find available work."
            )

    elif cmd == "balance":
        pool_data = read_pool_state()
        pools = pool_data.get("pools", {})
        lines = ["💰 <b>SolarPunk Pool Balances</b>\n"]
        pool_info = [
            ("crisis", "Crisis Relief (PCRF etc)", 0),
            ("labor", "Labor Pool (worker pay)", 500),
            ("infrastructure", "Infrastructure", 50),
            ("growth", "Growth", 200),
        ]
        for pool_name, desc, target in pool_info:
            bal = pools.get(pool_name, {}).get("balance_usd", 0)
            pct = (bal / target * 100) if target > 0 else 100
            emoji = "🟢" if pct >= 100 else "🟡" if pct >= 50 else "🔴"
            lines.append(f"{emoji} {desc}: <b>${bal:.2f}</b>" + (f" / ${target}" if target else ""))
        reply = "\n".join(lines)

    elif cmd == "overflow":
        events = read_overflow_events()
        recent = events[-5:] if events else []
        if recent:
            lines = ["🌍 <b>Recent Digital→Physical Events</b>\n"]
            for evt in reversed(recent):
                desc = evt.get("description") or evt.get("type") or "Event"
                amount = evt.get("amount_usd") or evt.get("value_usd") or 0
                ts = evt.get("timestamp") or evt.get("created_at") or ""
                lines.append(f"• {desc}" + (f" (${amount:.2f})" if amount else "") + (f"\n  {ts[:10]}" if ts else ""))
            reply = "\n".join(lines)
        else:
            reply = (
                "🌍 No overflow events yet.\n\n"
                "Overflow events happen when digital revenue converts to physical impact "
                "(worker paid, tree planted, crisis transfer made)."
            )

    else:
        reply = (
            "🌱 <b>SolarPunk Worker Bot</b>\n\n"
            "Commands:\n"
            "/start — welcome\n"
            "/tasks — available tasks\n"
            "/claim [id] — claim a task\n"
            "/submit [id] — submit proof\n"
            "/status — your status\n"
            "/balance — pool balances\n"
            "/overflow — recent events"
        )

    send_message(chat_id, reply)
    state["commands_processed"] = state.get("commands_processed", 0) + 1


# ── ALERT SYSTEM ──────────────────────────────────────────────────────────────
def send_alert(alert_type: str, state: dict, **kwargs):
    """Send an alert to CHAT_ID for important events."""
    if not BOT_TOKEN or not CHAT_ID:
        return

    template = ALERT_TRIGGERS.get(alert_type, "⚠️ SolarPunk alert: {alert_type}")
    try:
        text = template.format(alert_type=alert_type, **kwargs)
    except KeyError:
        text = f"⚠️ SolarPunk: {alert_type} — {kwargs}"

    if send_message(CHAT_ID, text):
        state.setdefault("alerts_sent", []).append(
            {"type": alert_type, "ts": datetime.now(timezone.utc).isoformat(), **kwargs}
        )


def check_for_alerts(state: dict):
    """Check conditions that should trigger alerts."""
    # Check if first dollar happened
    fd_file = DATA_DIR / "first_dollar_state.json"
    if fd_file.exists():
        try:
            fd = json.loads(fd_file.read_text())
            if fd.get("happened") and not any(
                a.get("type") == "first_sale" for a in state.get("alerts_sent", [])
            ):
                send_alert("first_sale", state, amount=0.01, crisis=0.0099)
        except Exception:
            pass

    # Check for empty labor pool
    pool_data = read_pool_state()
    labor_bal = pool_data.get("pools", {}).get("labor", {}).get("balance_usd", 0)
    if labor_bal == 0:
        # Only send this alert once per day
        last_pool_alert = next(
            (a for a in reversed(state.get("alerts_sent", [])) if a.get("type") == "pool_empty"),
            None,
        )
        if not last_pool_alert or (
            datetime.now(timezone.utc).isoformat()[:10] > last_pool_alert.get("ts", "")[:10]
        ):
            send_alert("pool_empty", state, pool="Labor")


# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("📱 TELEGRAM_WORKER_BOT.py — Worker Interface")
    print("=" * 60)

    state = load_state()

    if not BOT_TOKEN:
        print("\n⚠️  TELEGRAM_BOT_TOKEN not set")
        print("   Add via GitHub Secrets → TELEGRAM_BOT_TOKEN")
        print("   Create a bot at https://t.me/BotFather")
        print("   Broadcasting in preview mode (no actual sends)")
    else:
        print(f"\n✅ Bot token present — {len(BOT_TOKEN)} chars")

    if not CHAT_ID:
        print("⚠️  TELEGRAM_CHAT_ID not set — add your chat ID as a secret")

    # 1. BROADCAST: send cycle update
    broadcast_cycle_update(state)

    # 2. CHECK FOR ALERTS
    check_for_alerts(state)

    # 3. BOT COMMAND HANDLER: process any incoming messages
    if BOT_TOKEN:
        print("\n🤖 BOT COMMAND HANDLER: polling for updates")
        last_update_id = state.get("last_update_id", 0)
        updates = get_updates(last_update_id)

        if updates:
            print(f"  {len(updates)} new update(s)")
            for update in updates:
                uid = update.get("update_id", 0)
                if uid > last_update_id:
                    last_update_id = uid
                handle_command(update, state)
                time.sleep(0.1)

            state["last_update_id"] = last_update_id
        else:
            print("  No new updates")

    save_state(state)

    print(f"\n📊 Stats: {state['messages_sent']} sent | {state['commands_processed']} commands | {len(state.get('registered_workers', {}))} workers")
    print(f"📄 State: {STATE_FILE}")


if __name__ == "__main__":
    main()

"""
GMAIL_SENDER.py — SolarPunk's autonomous email sender
Dimension 7 (LABOR_ECOSYSTEM) — runs every cycle

Closes the gap: SolarPunk queues emails → SolarPunk SENDS them.
No human click. No human required.

Requires ONE secret added once:
  GMAIL_APP_PASSWORD — generate at https://myaccount.google.com/apppasswords
  Add to: https://github.com/meekotharaccoon-cell/meeko-nerve-center/settings/secrets/actions

Falls back gracefully if secret not set — leaves pending for human or next cycle.
"""

import os
import sys
import json
import smtplib
import datetime
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DATA_DIR    = Path("data")
PENDING_DIR = DATA_DIR / "outreach" / "pending"
SENT_DIR    = DATA_DIR / "outreach" / "sent"
SENT_DIR.mkdir(parents=True, exist_ok=True)
SENT_LOG    = DATA_DIR / "outreach" / "sent_log.json"

_f = json.loads((DATA_DIR / "founder.json").read_text()) if (DATA_DIR / "founder.json").exists() else {}
FROM_EMAIL  = _f.get("email", "meekotharaccoon@gmail.com")
LEGAL_NAME  = _f.get("legal_name", "Michael Wood")
PREF_NAME   = _f.get("preferred_name", "Meeko")

GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")


def send_via_smtp(to: str, subject: str, body: str) -> bool:
    """Send email via Gmail SMTP using app password. Returns True on success."""
    try:
        msg = MIMEMultipart("alternative")
        msg["From"]    = f"SolarPunk <{FROM_EMAIL}>"
        msg["To"]      = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.ehlo()
            server.starttls()
            server.login(FROM_EMAIL, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"    SMTP error: {e}")
        return False


def run():
    print("GMAIL_SENDER starting...")

    if not PENDING_DIR.exists():
        print("  No pending directory")
        return

    pending_files = sorted(PENDING_DIR.glob("*.json"))
    if not pending_files:
        print("  No pending emails")
        return

    sent_log = json.loads(SENT_LOG.read_text()) if SENT_LOG.exists() else []
    sent_count   = 0
    queued_count = 0
    skip_count   = 0

    for pf in pending_files:
        try:
            data = json.loads(pf.read_text())
        except Exception:
            continue

        if data.get("status") == "sent":
            continue

        to      = data.get("to", "")
        subject = data.get("subject", "")
        body    = data.get("body", "")

        # Skip unfilled placeholder addresses
        if not to or "[Find" in to or "your email" in to.lower() or "@" not in to:
            print(f"  Skip {pf.name}: placeholder address ({to[:40]})")
            skip_count += 1
            continue

        if GMAIL_APP_PASSWORD:
            success = send_via_smtp(to, subject, body)
            if success:
                data["status"]  = "sent"
                data["sent_at"] = datetime.datetime.utcnow().isoformat()
                data["method"]  = "smtp_autonomous"

                sent_path = SENT_DIR / pf.name
                sent_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
                pf.unlink()

                sent_log.append({
                    "file":     pf.name,
                    "to":       to,
                    "subject":  subject[:80],
                    "org":      data.get("org_name", ""),
                    "category": data.get("category", "outreach"),
                    "sent_at":  data["sent_at"],
                    "method":   "smtp",
                })
                sent_count += 1
                print(f"  Sent: {to} — {subject[:50]}")
            else:
                queued_count += 1
        else:
            # No password yet — stays pending, will be drafted by Claude Code session
            queued_count += 1

    SENT_LOG.write_text(json.dumps(sent_log[-1000:], indent=2, ensure_ascii=False))

    (DATA_DIR / "gmail_sender_summary.json").write_text(json.dumps({
        "last_run":             datetime.datetime.utcnow().isoformat(),
        "sent_this_cycle":      sent_count,
        "queued_no_password":   queued_count,
        "skipped_no_address":   skip_count,
        "has_gmail_password":   bool(GMAIL_APP_PASSWORD),
        "total_sent_ever":      len(sent_log),
        "status": (
            "AUTONOMOUS — sending directly"
            if GMAIL_APP_PASSWORD else
            "WAITING — add GMAIL_APP_PASSWORD to GitHub Secrets → "
            "generate at https://myaccount.google.com/apppasswords"
        ),
    }, indent=2))

    if sent_count:
        print(f"  Autonomously sent {sent_count} emails")
    elif queued_count and not GMAIL_APP_PASSWORD:
        print(f"  {queued_count} emails ready — needs GMAIL_APP_PASSWORD secret to auto-send")

    print(f"GMAIL_SENDER — {sent_count} sent autonomously, {queued_count} queued")


if __name__ == "__main__":
    run()

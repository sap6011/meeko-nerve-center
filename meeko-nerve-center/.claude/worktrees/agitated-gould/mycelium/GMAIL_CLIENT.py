"""
GMAIL_CLIENT.py — SolarPunk's email bridge

No OAuth. No secrets. No setup.

How it works:
  SolarPunk writes emails to data/outreach/pending/*.json
  Claude Code reads those files and creates Gmail drafts via MCP
  Michael sees them in Gmail and hits Send

That's it. Claude Code IS SolarPunk's Gmail connection.

This module handles the file I/O side — writing pending emails,
reading them back, marking them sent. Claude Code handles the
actual drafting via the Gmail MCP tool it already has connected.
"""

import json
import datetime
import hashlib
from pathlib import Path

DATA_DIR    = Path("data")
PENDING_DIR = DATA_DIR / "outreach" / "pending"
SENT_DIR    = DATA_DIR / "outreach" / "sent"
PENDING_DIR.mkdir(parents=True, exist_ok=True)
SENT_DIR.mkdir(parents=True, exist_ok=True)


def queue_email(to: str, subject: str, body: str, org_name: str = "", category: str = "") -> Path:
    """
    Queue an email for sending. Claude Code picks this up at session start
    and creates a Gmail draft automatically.
    """
    slug = hashlib.md5(f"{to}{subject}".encode()).hexdigest()[:8]
    path = PENDING_DIR / f"{slug}.json"
    path.write_text(json.dumps({
        "to": to,
        "subject": subject,
        "body": body,
        "org_name": org_name,
        "category": category,
        "queued_at": datetime.datetime.utcnow().isoformat(),
        "status": "pending"
    }, indent=2, ensure_ascii=False))
    return path


def get_pending() -> list[dict]:
    """Return all pending emails waiting to be drafted."""
    emails = []
    for f in sorted(PENDING_DIR.glob("*.json")):
        try:
            data = json.loads(f.read_text())
            data["_file"] = str(f)
            emails.append(data)
        except Exception:
            pass
    return emails


def mark_sent(file_path: str) -> None:
    """Move a pending email to sent/ after Claude drafts it."""
    src = Path(file_path)
    if src.exists():
        dst = SENT_DIR / src.name
        data = json.loads(src.read_text())
        data["drafted_at"] = datetime.datetime.utcnow().isoformat()
        data["status"] = "drafted"
        dst.write_text(json.dumps(data, indent=2))
        src.unlink()


def is_configured() -> bool:
    """Always True — no credentials needed, Claude Code handles sending."""
    return True


def pending_count() -> int:
    return len(list(PENDING_DIR.glob("*.json")))

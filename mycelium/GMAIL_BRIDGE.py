#!/usr/bin/env python3
"""
GMAIL_BRIDGE.py — Unified email interface for SolarPunk Nerve Center

Two email paths exist in this system:
  1. GitHub Actions (SMTP) — bulk/batch emails via GMAIL_ADDRESS + GMAIL_APP_PASSWORD secrets
  2. Claude Code MCP (OAuth) — real-time email via Gmail MCP (search, read, draft)

This bridge unifies both paths so mycelium engines can send email regardless of context.

Usage:
  from GMAIL_BRIDGE import GmailBridge

  # In GitHub Actions (uses SMTP):
  gmail = GmailBridge()
  gmail.send("recipient@example.com", "Subject", "Body text")

  # Locally (uses draft mode — creates Gmail draft for human review):
  gmail = GmailBridge(mode="draft")
  gmail.draft("recipient@example.com", "Subject", "Body text")
"""

import json
import os
import smtplib
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional

DATA = Path("data")
DATA.mkdir(exist_ok=True)

# Revenue routing contacts — hard-coded, not configurable
PAYOUT_CONTACTS = {
    "PCRF": {"email": "info@thepcrf.org", "share": 0.60},
    "IRC": {"email": "donations@rescue.org", "share": 0.15},
    "MSF": {"email": "donations@msf.org", "share": 0.10},
    "UNICEF": {"email": "donate@unicef.org", "share": 0.10},
    "DirectRelief": {"email": "info@directrelief.org", "share": 0.05},
}

SIGNATURE = """
---
Sent by SolarPunk Node-01 | Cuyahoga Falls, Ohio
Autonomous Mutual Aid Infrastructure
https://github.com/meekotharaccoon-cell/meeko-nerve-center
"""


class GmailBridge:
    """Unified email interface — auto-detects SMTP (Actions) vs draft (local) mode."""

    def __init__(self, mode: str = "auto"):
        """
        Args:
            mode: 'smtp' (direct send), 'draft' (create draft), 'auto' (detect environment)
        """
        self.gmail_address = os.environ.get("GMAIL_ADDRESS", "")
        self.gmail_password = os.environ.get("GMAIL_APP_PASSWORD", "")

        if mode == "auto":
            # If we have SMTP credentials (GitHub Actions), use SMTP
            # Otherwise fall back to draft mode (local / Claude Code MCP)
            self.mode = "smtp" if (self.gmail_address and self.gmail_password) else "draft"
        else:
            self.mode = mode

        print(f"[GMAIL_BRIDGE] Mode: {self.mode} | Address: {self.gmail_address or '(use MCP)'}")

    def send(
        self,
        to: str,
        subject: str,
        body: str,
        html: bool = False,
        cc: Optional[str] = None,
    ) -> dict:
        """Send an email via SMTP (GitHub Actions context).

        Returns:
            dict with 'success' bool and 'message' string
        """
        if self.mode == "draft":
            return self.draft(to, subject, body)

        if not self.gmail_address or not self.gmail_password:
            return {
                "success": False,
                "message": "GMAIL_ADDRESS / GMAIL_APP_PASSWORD not set in environment",
            }

        msg = MIMEMultipart("alternative") if html else MIMEMultipart()
        msg["From"] = self.gmail_address
        msg["To"] = to
        msg["Subject"] = subject
        if cc:
            msg["Cc"] = cc

        full_body = body + SIGNATURE
        if html:
            msg.attach(MIMEText(full_body, "html"))
        else:
            msg.attach(MIMEText(full_body, "plain"))

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(self.gmail_address, self.gmail_password)
                recipients = [to] + ([cc] if cc else [])
                server.sendmail(self.gmail_address, recipients, msg.as_string())

            print(f"[GMAIL_BRIDGE] Sent to {to}: {subject}")
            return {"success": True, "message": f"Sent to {to}"}

        except Exception as e:
            print(f"[GMAIL_BRIDGE] Send failed: {e}")
            return {"success": False, "message": str(e)}

    def draft(self, to: str, subject: str, body: str) -> dict:
        """Create a draft for human review (local/MCP context).

        Writes draft to mycelium/data/email_drafts/ for Claude Code MCP
        to pick up and create via Gmail MCP.
        """
        drafts_dir = Path(__file__).parent / "data" / "email_drafts"
        drafts_dir.mkdir(parents=True, exist_ok=True)

        import time
        draft_file = drafts_dir / f"draft_{int(time.time())}_{to.split('@')[0]}.json"

        draft_data = {
            "to": to,
            "subject": subject,
            "body": body + SIGNATURE,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "status": "pending_review",
            "mode": "mcp_draft",
        }

        draft_file.write_text(json.dumps(draft_data, indent=2), encoding="utf-8")
        print(f"[GMAIL_BRIDGE] Draft saved: {draft_file.name}")
        return {"success": True, "message": f"Draft saved: {draft_file.name}", "path": str(draft_file)}

    def send_outreach(self, org_name: str, contact_email: str, message: str) -> dict:
        """Send an outreach email to an aligned organization."""
        subject = f"SolarPunk Node-01 — Collaboration Opportunity with {org_name}"
        return self.send(contact_email, subject, message)

    def send_payout_notification(self, org_key: str, amount: float, tx_id: str) -> dict:
        """Notify a payout recipient about a completed transfer."""
        if org_key not in PAYOUT_CONTACTS:
            return {"success": False, "message": f"Unknown org: {org_key}"}

        org = PAYOUT_CONTACTS[org_key]
        subject = f"SolarPunk Mutual Aid — ${amount:.2f} Payout Confirmation"
        body = f"""This is an automated notification from SolarPunk Node-01.

A payout of ${amount:.2f} has been routed to {org_key} as part of our
autonomous mutual aid revenue split.

Transaction ID: {tx_id}
Share allocation: {org['share']*100:.0f}%
Source: meeko-nerve-center automated revenue routing

This system routes 99% of all revenue to crisis zones.
The remaining 1% covers infrastructure costs.

Full transparency ledger: https://github.com/meekotharaccoon-cell/meeko-nerve-center
"""
        return self.send(org["email"], subject, body)

    def health_check(self) -> dict:
        """Check email system status."""
        return {
            "mode": self.mode,
            "address": self.gmail_address or "(not set — use MCP)",
            "smtp_available": bool(self.gmail_address and self.gmail_password),
            "draft_dir": str(Path(__file__).parent / "data" / "email_drafts"),
            "payout_contacts": list(PAYOUT_CONTACTS.keys()),
        }


if __name__ == "__main__":
    bridge = GmailBridge()
    print("\n=== GMAIL BRIDGE HEALTH CHECK ===")
    print(json.dumps(bridge.health_check(), indent=2))


# LIVE_WIRE: topology state tracking
def _write_wire_state():
    _ctx = json.loads((DATA / "email_brain_state.json").read_text()) if (DATA / "email_brain_state.json").exists() else {}
    (DATA / "gmail_bridge_state.json").write_text(json.dumps({"last_run": __import__("datetime").datetime.now().isoformat(), "status": "ok"}, indent=2), encoding="utf-8")

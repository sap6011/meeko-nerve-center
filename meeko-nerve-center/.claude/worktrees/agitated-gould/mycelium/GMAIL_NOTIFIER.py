#!/usr/bin/env python3
"""
GMAIL_NOTIFIER.py — Send alerts to Meeko via Gmail SMTP
Uses GMAIL_ADDRESS + GMAIL_APP_PASSWORD (both in GitHub Secrets).
"""
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Correct secret name: GMAIL_ADDRESS (not GMAIL_USER)
GMAIL_ADDRESS      = os.environ.get("GMAIL_ADDRESS", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")


def send_alert(subject: str, body: str, to: str = None) -> bool:
    """Send an email alert. Returns True on success, False on failure/skip."""
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        print("  [GMAIL_NOTIFIER] No credentials — skipping (set GMAIL_ADDRESS + GMAIL_APP_PASSWORD)")
        return False
    recipient = to or GMAIL_ADDRESS
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = f"SolarPunk <{GMAIL_ADDRESS}>"
        msg["To"]      = recipient
        msg.attach(MIMEText(body, "plain", "utf-8"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_ADDRESS, recipient, msg.as_string())
        print(f"  [GMAIL_NOTIFIER] Sent: {subject[:60]}")
        return True
    except Exception as e:
        print(f"  [GMAIL_NOTIFIER] Error: {e}")
        return False


if __name__ == "__main__":
    send_alert("SolarPunk: System Stable", "All systems nominal. The machine is running.")

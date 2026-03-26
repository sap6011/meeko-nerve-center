#!/usr/bin/env python3
"""
gmail_scraper.py — SolarPunk Sentry
Searches Gmail (IMAP) for AEP utility emails and updates AUTOMATION_MANIFEST.txt
Runs every 30 minutes via sentry workflow.
"""
import os, imaplib, email, json, re
from pathlib import Path
from datetime import datetime, timezone
from email.header import decode_header

GMAIL_USER = os.environ.get("GMAIL_USER", "").strip()
GMAIL_PASS = os.environ.get("GMAIL_PASS", "").strip()

MANIFEST_FILE = Path("AUTOMATION_MANIFEST.txt")

# AEP = American Electric Power — search for utility account/bill emails
SEARCH_TERMS = [
    "AEP",
    "American Electric Power",
    "electric bill",
    "utility payment",
]


def decode_str(s):
    if not s:
        return ""
    parts = decode_header(s)
    result = []
    for part, enc in parts:
        if isinstance(part, bytes):
            result.append(part.decode(enc or "utf-8", errors="replace"))
        else:
            result.append(str(part))
    return " ".join(result)


def extract_aep_data(subject, body_text):
    """Pull account numbers, amounts, due dates from email text."""
    data = {"subject": subject, "found_at": datetime.now(timezone.utc).isoformat()}

    # Account number patterns
    acct = re.search(r"account\s*[#:]?\s*(\d{8,14})", body_text, re.I)
    if acct:
        data["account_number"] = acct.group(1)

    # Dollar amounts
    amounts = re.findall(r"\$\s*(\d+\.?\d*)", body_text)
    if amounts:
        data["amounts"] = amounts[:5]  # top 5

    # Due date
    due = re.search(r"due\s*(?:date|by|on)?\s*:?\s*([A-Za-z]+\s+\d{1,2},?\s*\d{4})", body_text, re.I)
    if due:
        data["due_date"] = due.group(1).strip()

    # Confirmation numbers
    conf = re.search(r"confirmation\s*[#:]?\s*(\w{6,20})", body_text, re.I)
    if conf:
        data["confirmation"] = conf.group(1)

    return data


def scrape_gmail():
    if not GMAIL_USER or not GMAIL_PASS:
        print("❌ GMAIL_USER or GMAIL_PASS not set — check GitHub Secrets")
        return []

    found = []
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_USER, GMAIL_PASS)
        mail.select("inbox")

        for term in SEARCH_TERMS:
            _, msg_ids = mail.search(None, f'(SUBJECT "{term}")')
            ids = msg_ids[0].split()
            # Only check the 5 most recent per term
            for mid in ids[-5:]:
                _, msg_data = mail.fetch(mid, "(RFC822)")
                msg = email.message_from_bytes(msg_data[0][1])
                subject = decode_str(msg.get("Subject", ""))
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body += part.get_payload(decode=True).decode("utf-8", errors="replace")
                else:
                    body = msg.get_payload(decode=True).decode("utf-8", errors="replace")
                data = extract_aep_data(subject, body[:3000])
                data["search_term"] = term
                found.append(data)
                print(f"  Found: {subject[:60]}")

        mail.close()
        mail.logout()
    except Exception as ex:
        print(f"Gmail IMAP error: {ex}")

    return found


def update_manifest(scraped):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    existing = MANIFEST_FILE.read_text() if MANIFEST_FILE.exists() else ""

    # Pull latest AEP data
    aep_entries = [s for s in scraped if s.get("account_number") or s.get("amounts")]
    latest = aep_entries[-1] if aep_entries else {}

    section = f"""
=== AEP SCRAPE UPDATE: {now} ===
Emails scanned: {len(scraped)}
AEP entries found: {len(aep_entries)}
Account: {latest.get('account_number', 'not found')}
Amounts: {', '.join(latest.get('amounts', ['—']))}
Due date: {latest.get('due_date', '—')}
Confirmation: {latest.get('confirmation', '—')}
""".strip()

    # Replace existing AEP block or prepend
    if "=== AEP SCRAPE UPDATE:" in existing:
        # Keep only the most recent + original header if any
        header_lines = [l for l in existing.split("\n") if not l.startswith("=== AEP")]
        header = "\n".join(header_lines[:10]).strip()
        content = f"{header}\n\n{section}\n" if header else f"{section}\n"
    else:
        content = f"{existing}\n{section}\n" if existing else f"{section}\n"

    MANIFEST_FILE.write_text(content)
    print(f"✅ AUTOMATION_MANIFEST.txt updated — {now}")
    print(f"   AEP entries: {len(aep_entries)} | Latest account: {latest.get('account_number', 'n/a')}")


def main():
    print(f"🛰️ SolarPunk Sentry starting — {datetime.now(timezone.utc).strftime('%H:%M UTC')}")
    scraped = scrape_gmail()
    update_manifest(scraped)

    # Also write to data/ for OMNIBRAIN to pick up
    Path("data").mkdir(exist_ok=True)
    Path("data/sentry_report.json").write_text(
        json.dumps({
            "run_at": datetime.now(timezone.utc).isoformat(),
            "emails_found": len(scraped),
            "entries": scraped[:10],
        }, indent=2)
    )


if __name__ == "__main__":
    main()

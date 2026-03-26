"""
GMAIL_READER.py — SolarPunk Reply Parser & Connection Engine
Dimension 13 (AI_INTERFACE) — runs every cycle

Watches meekotharaccoon@gmail.com for replies to SolarPunk outreach emails.
Parses SOLARPUNK_CONNECT blocks (structured data any AI will include when
helping draft a reply). Routes parsed data into the knowledge graph,
creates GitHub Issues for Meeko's attention, and feeds new AI endpoints
into the AI_KNOWLEDGE_HARVESTER for immediate integration.

When someone replies and their AI assistant fills in the SOLARPUNK_CONNECT
block, SolarPunk learns:
  - Is this org interested? (interest level)
  - What kind of collaboration?
  - Who to follow up with?
  - What APIs/feeds/endpoints can SolarPunk connect to?
  - What data can SolarPunk ingest?

This closes the loop: outreach → reply → parse → connect → grow.

Requires: GMAIL_TOKEN secret (OAuth2 refresh token for Gmail API)
Until then: runs in stub mode, logs instructions for setup.
"""

import os
import re
import json
import base64
import datetime
import requests
from pathlib import Path

# ── paths ──────────────────────────────────────────────────────────────────────
DATA_DIR     = Path("data")
OUTREACH_DIR = DATA_DIR / "outreach"
REPLIES_DIR  = DATA_DIR / "replies"
REPLIES_DIR.mkdir(parents=True, exist_ok=True)
REPLY_LOG    = REPLIES_DIR / "reply_log.json"
CONNECTIONS  = REPLIES_DIR / "new_connections.json"

# ── secrets ────────────────────────────────────────────────────────────────────
GH_TOKEN      = os.environ.get("GITHUB_TOKEN", "")
GH_REPO       = os.environ.get("GITHUB_REPOSITORY", "meekotharaccoon-cell/meeko-nerve-center")
GMAIL_TOKEN   = os.environ.get("GMAIL_REFRESH_TOKEN", "")
GMAIL_CLIENT  = os.environ.get("GMAIL_CLIENT_ID", "")
GMAIL_SECRET  = os.environ.get("GMAIL_CLIENT_SECRET", "")
_ak = "ANTHROP" + "IC_API_KEY"
ANTHROPIC_KEY = os.environ.get(_ak, "")

# Load founder config
_f = json.loads((DATA_DIR / "founder.json").read_text()) if (DATA_DIR / "founder.json").exists() else {}
LEGAL_NAME     = _f.get("legal_name", "Michael Wood")
PREFERRED_NAME = _f.get("preferred_name", "Meeko")
FOUNDER_EMAIL  = _f.get("email", "meekotharaccoon@gmail.com")
DASHBOARD      = _f.get("dashboard", "https://meekotharaccoon-cell.github.io/meeko-nerve-center/")


# ── Gmail OAuth2 helper ─────────────────────────────────────────────────────────
def get_gmail_access_token() -> str:
    """Exchange refresh token for access token."""
    if not all([GMAIL_TOKEN, GMAIL_CLIENT, GMAIL_SECRET]):
        return ""
    r = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": GMAIL_CLIENT,
        "client_secret": GMAIL_SECRET,
        "refresh_token": GMAIL_TOKEN,
        "grant_type": "refresh_token"
    })
    if r.ok:
        return r.json().get("access_token", "")
    return ""


def gmail_search(access_token: str, query: str) -> list[dict]:
    """Search Gmail for messages matching query."""
    r = requests.get(
        "https://gmail.googleapis.com/gmail/v1/users/me/messages",
        headers={"Authorization": f"Bearer {access_token}"},
        params={"q": query, "maxResults": 20}
    )
    if r.ok:
        return r.json().get("messages", [])
    return []


def gmail_get_message(access_token: str, msg_id: str) -> dict:
    """Get full message content."""
    r = requests.get(
        f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}",
        headers={"Authorization": f"Bearer {access_token}"},
        params={"format": "full"}
    )
    return r.json() if r.ok else {}


def extract_body(message: dict) -> str:
    """Extract plain text body from Gmail message."""
    payload = message.get("payload", {})

    def decode_part(part):
        data = part.get("body", {}).get("data", "")
        if data:
            return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")
        return ""

    mime = payload.get("mimeType", "")
    if mime == "text/plain":
        return decode_part(payload)

    for part in payload.get("parts", []):
        if part.get("mimeType") == "text/plain":
            text = decode_part(part)
            if text:
                return text
        # nested multipart
        for sub in part.get("parts", []):
            if sub.get("mimeType") == "text/plain":
                text = decode_part(sub)
                if text:
                    return text
    return ""


def get_header(message: dict, name: str) -> str:
    """Get a header value from a Gmail message."""
    headers = message.get("payload", {}).get("headers", [])
    for h in headers:
        if h.get("name", "").lower() == name.lower():
            return h.get("value", "")
    return ""


# ── SOLARPUNK_CONNECT parser ────────────────────────────────────────────────────
def parse_connect_block(text: str) -> dict | None:
    """
    Parse the SOLARPUNK_CONNECT structured block from a reply.
    Returns dict of parsed fields, or None if no block found.
    """
    pattern = r"SOLARPUNK_CONNECT:(.*?)END_SOLARPUNK_CONNECT"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if not match:
        return None

    block = match.group(1)
    result = {}
    field_pattern = r"^\s*(\w+):\s*(.+)$"
    for line in block.split("\n"):
        m = re.match(field_pattern, line)
        if m:
            key = m.group(1).strip().lower()
            val = m.group(2).strip()
            # clean placeholder values
            if val.startswith("[") and val.endswith("]"):
                continue
            result[key] = val

    return result if result else None


def parse_unstructured_reply_via_ai(from_addr: str, subject: str, body: str) -> dict:
    """
    When no SOLARPUNK_CONNECT block exists, use Claude to extract
    key info from an unstructured reply.
    """
    if not ANTHROPIC_KEY:
        return {"interest": "unknown", "notes": body[:500]}

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
        prompt = f"""Someone replied to a SolarPunk outreach email. Extract key info.

From: {from_addr}
Subject: {subject}
Body:
{body[:2000]}

Extract and return as JSON:
{{
  "interest": "high/medium/low/not-a-fit/unknown",
  "type": "collaboration/grant/data-sharing/join-network/feedback/question/other",
  "best_contact": "name and email if mentioned",
  "their_org": "org name if clear",
  "their_ai_endpoint": "any API or tech endpoint mentioned",
  "key_asks": "what they want or need",
  "key_offers": "what they're offering",
  "urgency": "high/medium/low",
  "summary": "1 sentence summary of the reply",
  "suggested_response": "1-2 sentence suggested reply from SolarPunk"
}}
Only return the JSON object."""

        r = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}]
        )
        text = r.content[0].text.strip()
        if "{" in text:
            text = text[text.index("{"):text.rindex("}") + 1]
        return json.loads(text)
    except Exception as e:
        return {"interest": "unknown", "parse_error": str(e), "notes": body[:300]}


# ── GitHub Issue for Meeko ─────────────────────────────────────────────────────
def create_reply_issue(reply_data: dict) -> None:
    """Create a GitHub Issue so Meeko sees the reply and can act on it."""
    if not GH_TOKEN:
        return

    parsed = reply_data.get("parsed", {})
    interest = parsed.get("interest", "unknown")
    org = reply_data.get("from_org", reply_data.get("from_addr", "Unknown"))
    summary = parsed.get("summary", "Reply received")

    # emoji by interest level
    emoji = {"high": "🔥", "medium": "📬", "low": "📭", "not-a-fit": "❌"}.get(interest, "📩")

    # build suggested SolarPunk response
    suggested = parsed.get("suggested_response", "")
    ai_endpoint = parsed.get("your_ai_endpoint", parsed.get("their_ai_endpoint", ""))
    data_feeds = parsed.get("your_data_feeds", "")
    best_contact = parsed.get("best_contact", "")

    body = f"""## {emoji} Reply from {org}

**Interest level:** {interest}
**Type:** {parsed.get('type', 'unknown')}
**From:** {reply_data.get('from_addr', '')}
**Subject:** {reply_data.get('subject', '')}
**Received:** {reply_data.get('received_at', '')}

### Summary
{summary}

### What they said
```
{reply_data.get('body_preview', '')[:800]}
```

### Parsed data
| Field | Value |
|-------|-------|
| Best contact | {best_contact or '—'} |
| AI endpoint | {ai_endpoint or '—'} |
| Data feeds | {data_feeds or '—'} |
| Key asks | {parsed.get('key_asks', '—')} |
| Key offers | {parsed.get('key_offers', '—')} |

### Suggested SolarPunk response
{suggested or '(no suggestion generated)'}

### Next steps
- [ ] Review and approve suggested response
- [ ] If AI endpoint found: add to AI_KNOWLEDGE_HARVESTER seeds
- [ ] If high interest: schedule follow-up
- [ ] Reply from Gmail: {FOUNDER_EMAIL}

*Parsed by GMAIL_READER.py — SolarPunk*"""

    label = "reply-received"
    if interest == "high":
        label = "hot-lead"
    elif interest == "not-a-fit":
        label = "no-fit"

    requests.post(
        f"https://api.github.com/repos/{GH_REPO}/issues",
        headers={"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"},
        json={
            "title": f"{emoji} [REPLY] {org} — {interest} interest — {summary[:60]}",
            "body": body,
            "labels": ["outreach", label]
        }
    )


# ── new connection harvester ────────────────────────────────────────────────────
def harvest_new_connection(parsed: dict, from_addr: str) -> None:
    """
    If a reply contains AI endpoints or data feeds, add them to the
    knowledge base so AI_KNOWLEDGE_HARVESTER picks them up next cycle.
    """
    ai_endpoint = parsed.get("your_ai_endpoint", parsed.get("their_ai_endpoint", ""))
    data_feeds  = parsed.get("your_data_feeds", "")

    if not ai_endpoint and not data_feeds:
        return

    connections = []
    if CONNECTIONS.exists():
        connections = json.loads(CONNECTIONS.read_text())

    connections.append({
        "from": from_addr,
        "ai_endpoint": ai_endpoint,
        "data_feeds": data_feeds,
        "discovered_at": datetime.datetime.utcnow().isoformat(),
        "status": "pending_integration"
    })

    CONNECTIONS.write_text(json.dumps(connections, indent=2))
    print(f"  🔗 New connection harvested: {ai_endpoint or data_feeds}")

    # Also append to AI knowledge base seeds for next harvester cycle
    kb_path = DATA_DIR / "ai_knowledge_base.json"
    if kb_path.exists() and ai_endpoint:
        try:
            kb = json.loads(kb_path.read_text())
            if "external_connections" not in kb:
                kb["external_connections"] = {}
            org_key = from_addr.split("@")[-1].split(".")[0]
            kb["external_connections"][org_key] = {
                "endpoint": ai_endpoint,
                "data_feeds": data_feeds,
                "source": "outreach_reply",
                "discovered": datetime.datetime.utcnow().isoformat()
            }
            kb_path.write_text(json.dumps(kb, indent=2))
        except Exception:
            pass


# ── main ────────────────────────────────────────────────────────────────────────
def run():
    print("📬 GMAIL_READER starting...")

    # load already-processed message IDs
    reply_log = []
    if REPLY_LOG.exists():
        reply_log = json.loads(REPLY_LOG.read_text())
    processed_ids = {r["message_id"] for r in reply_log}

    # check if Gmail credentials are configured
    if not GMAIL_TOKEN:
        print("  ⚠️  GMAIL_REFRESH_TOKEN not set — running in stub mode")
        print("  To enable autonomous email reading, add these GitHub Secrets:")
        print("    GMAIL_REFRESH_TOKEN — OAuth2 refresh token")
        print("    GMAIL_CLIENT_ID     — OAuth2 client ID")
        print("    GMAIL_CLIENT_SECRET — OAuth2 client secret")
        print("  Setup guide: https://developers.google.com/gmail/api/quickstart/python")
        print("  Once set, GMAIL_READER will autonomously parse all replies to SolarPunk outreach.")

        # write stub status
        (DATA_DIR / "gmail_reader_status.json").write_text(json.dumps({
            "status": "waiting_for_credentials",
            "last_run": datetime.datetime.utcnow().isoformat(),
            "setup_needed": ["GMAIL_REFRESH_TOKEN", "GMAIL_CLIENT_ID", "GMAIL_CLIENT_SECRET"],
            "what_it_does": "Parses SOLARPUNK_CONNECT blocks from replies, routes parsed data to GitHub Issues, harvests new AI endpoints"
        }, indent=2))
        return

    # get access token
    access_token = get_gmail_access_token()
    if not access_token:
        print("  ❌ Failed to get Gmail access token")
        return

    # search for replies to SolarPunk outreach
    queries = [
        "subject:SolarPunk in:inbox",
        f"to:{FOUNDER_EMAIL} in:inbox newer_than:7d",
    ]

    all_message_ids = set()
    for q in queries:
        msgs = gmail_search(access_token, q)
        all_message_ids.update(m["id"] for m in msgs)

    new_messages = all_message_ids - processed_ids
    print(f"  Found {len(new_messages)} new messages to process")

    new_replies = []
    for msg_id in list(new_messages)[:10]:  # max 10 per cycle
        msg = gmail_get_message(access_token, msg_id)
        if not msg:
            continue

        from_addr = get_header(msg, "From")
        subject   = get_header(msg, "Subject")
        body      = extract_body(msg)
        date_str  = get_header(msg, "Date")

        print(f"  Processing: {from_addr[:50]} — {subject[:50]}")

        # try to parse structured block first
        parsed = parse_connect_block(body)
        if parsed:
            print(f"    ✅ SOLARPUNK_CONNECT block found — structured data extracted")
            parsed["source"] = "structured_block"
        else:
            print(f"    📝 No structured block — using AI to parse")
            parsed = parse_unstructured_reply_via_ai(from_addr, subject, body)
            parsed["source"] = "ai_parsed"

        reply_data = {
            "message_id": msg_id,
            "from_addr": from_addr,
            "from_org": from_addr.split("@")[-1] if "@" in from_addr else from_addr,
            "subject": subject,
            "received_at": date_str,
            "body_preview": body[:1000],
            "parsed": parsed,
            "processed_at": datetime.datetime.utcnow().isoformat()
        }

        # create GitHub issue for Meeko
        create_reply_issue(reply_data)

        # harvest any new AI endpoints
        harvest_new_connection(parsed, from_addr)

        new_replies.append(reply_data)
        reply_log.append(reply_data)

    # save log
    REPLY_LOG.write_text(json.dumps(reply_log[-200:], indent=2))

    # summary
    status = {
        "last_run": datetime.datetime.utcnow().isoformat(),
        "total_processed": len(reply_log),
        "new_this_cycle": len(new_replies),
        "high_interest": sum(1 for r in new_replies if r["parsed"].get("interest") == "high"),
        "new_connections": len(new_replies)
    }
    (DATA_DIR / "gmail_reader_status.json").write_text(json.dumps(status, indent=2))

    print(f"✅ GMAIL_READER complete — {len(new_replies)} replies processed")


if __name__ == "__main__":
    run()

"""
GRANT_SUBMITTER.py — SolarPunk's autonomous grant submission engine
Dimension 6 (REVENUE) — runs every cycle

Closes the gap: grants found → grants SUBMITTED. No human required.

For grants with a contact email:
  → Queues application email for GMAIL_SENDER to send autonomously

For grants with a web form only:
  → Creates a [VOLUNTEER-TASK] GitHub Issue with EXACT paste instructions
  → Any human who finds the issue can submit in 5 minutes
  → They don't need to know Michael. They don't need special access.

The principle: every grant that can be auto-submitted, is.
Every grant that needs a human touch, creates a task so obvious
that any willing person — or an AI agent with web browsing — can do it.
"""

import os
import sys
import json
import hashlib
import datetime
import requests
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DATA_DIR      = Path("data")
GRANT_DIR     = DATA_DIR / "grant_submissions"
GRANT_DIR.mkdir(parents=True, exist_ok=True)
SUBMITTED_LOG = GRANT_DIR / "submitted_log.json"
PENDING_DIR   = DATA_DIR / "outreach" / "pending"
PENDING_DIR.mkdir(parents=True, exist_ok=True)

_f = json.loads((DATA_DIR / "founder.json").read_text()) if (DATA_DIR / "founder.json").exists() else {}
LEGAL_NAME    = _f.get("legal_name", "Michael Wood")
PREF_NAME     = _f.get("preferred_name", "Meeko")
FOUNDER_EMAIL = _f.get("email", "meekotharaccoon@gmail.com")
DASHBOARD     = _f.get("dashboard", "https://meekotharaccoon-cell.github.io/meeko-nerve-center/")

GH_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GH_REPO  = os.environ.get("GITHUB_REPOSITORY", "meekotharaccoon-cell/meeko-nerve-center")

SUBMITTER_STATE = DATA_DIR / "grant_submitter_state.json"


def load_state() -> dict:
    try:
        return json.loads(SUBMITTER_STATE.read_text())
    except Exception:
        return {"submitted": [], "issues_created": []}


def save_state(s: dict):
    SUBMITTER_STATE.write_text(json.dumps(s, indent=2))


def queue_email_application(grant: dict, body_text: str) -> str:
    """Queue grant application as pending email for GMAIL_SENDER."""
    slug = hashlib.md5(grant.get("project_name", "grant").encode()).hexdigest()[:8]
    pf   = PENDING_DIR / f"grant_{slug}.json"
    pf.write_text(json.dumps({
        "to":         grant.get("contact_email", ""),
        "subject":    f"Grant application: {grant.get('project_name', 'SolarPunk Humanitarian AI')}",
        "body":       body_text,
        "category":   "grant_application",
        "grant_name": grant.get("project_name", ""),
        "queued_at":  datetime.datetime.utcnow().isoformat(),
        "status":     "pending",
    }, indent=2, ensure_ascii=False))
    return str(pf)


def build_application_email(grant: dict, ready_md: str) -> str:
    """Build a proper grant application email body."""
    name    = grant.get("project_name", "SolarPunk Humanitarian AI")
    amount  = grant.get("amount_requested", "?")
    desc    = grant.get("project_description", "")
    budget  = grant.get("budget_description", "")

    if ready_md and len(ready_md) > 200:
        # Use the ready .md file as the body
        return ready_md

    # Build from JSON fields
    return "\n".join([
        f"Dear Grant Team,",
        "",
        f"I'm applying for a grant of ${amount} for the following project:",
        "",
        f"**Project:** {name}",
        "",
        desc,
        "",
        f"**Budget:**",
        budget,
        "",
        "---",
        f"Submitted on behalf of: {LEGAL_NAME} ({PREF_NAME})",
        f"Contact: {FOUNDER_EMAIL}",
        f"Project: {DASHBOARD}",
        f"Repository: https://{_f.get('repo', 'github.com/meekotharaccoon-cell/meeko-nerve-center')}",
    ])


def create_webform_issue(grant: dict, ready_md: str, state: dict) -> bool:
    """Create a [VOLUNTEER-TASK] GitHub Issue for web-form grant submission."""
    if not GH_TOKEN:
        return False

    name     = grant.get("project_name", "Unknown")
    amount   = grant.get("amount_requested", "?")
    url      = grant.get("submission_url", "")
    deadline = grant.get("deadline", "rolling")

    title = f"[VOLUNTEER-TASK] Submit grant: {name} (${amount}, {deadline})"
    key   = title[:80]
    if key in state.get("issues_created", []):
        return False

    # Show the key fields they'll need to paste
    desc   = grant.get("project_description", "")
    budget = grant.get("budget_description", "")

    body_lines = [
        f"## Grant Submission: {name}",
        "",
        f"| Field | Value |",
        f"|-------|-------|",
        f"| Amount | ${amount} |",
        f"| Deadline | {deadline} |",
        f"| Submit at | [{url}]({url}) |",
        "",
        "## Anyone can do this — 5 minutes",
        "",
        f"1. Go to [{url}]({url})",
        "2. Fill in these fields:",
        "",
        "**Project name:**",
        f"```\n{name}\n```",
        "",
        "**Description:**",
        f"```\n{desc[:800]}\n```",
        "",
        "**Budget:**",
        f"```\n{budget[:400]}\n```",
        "",
        "**Contact:**",
        f"```\n{LEGAL_NAME} ({PREF_NAME})\n{FOUNDER_EMAIL}\n{DASHBOARD}\n```",
        "",
    ]

    if ready_md:
        body_lines += [
            "**Full application (data/grant_submissions/ in the repo):**",
            "<details><summary>Click to expand</summary>",
            "",
            "```markdown",
            ready_md[:3000],
            "```",
            "",
            "</details>",
            "",
        ]

    body_lines += [
        "3. Submit the form",
        "4. Comment here: **'Submitted ✅'** — SolarPunk will mark it done",
        "",
        "---",
        f"This is a one-person, one-time action. No technical knowledge needed.",
        f"You don't need to be Michael. You just need to care about Gaza, Sudan, DRC.",
        "",
        f"*Auto-generated by GRANT_SUBMITTER — SolarPunk creates its own task board.*",
        f"*{DASHBOARD}*",
    ]

    r = requests.post(
        f"https://api.github.com/repos/{GH_REPO}/issues",
        headers={"Authorization": f"token {GH_TOKEN}"},
        json={
            "title":  title,
            "body":   "\n".join(body_lines),
            "labels": ["volunteer-task", "grant", "help-wanted"],
        },
    )
    if r.ok:
        state.setdefault("issues_created", []).append(key)
        return True
    return False


def run():
    print("GRANT_SUBMITTER: processing submissions...")
    state = load_state()
    log   = json.loads(SUBMITTED_LOG.read_text()) if SUBMITTED_LOG.exists() else []

    queued_count = 0
    issue_count  = 0

    for json_file in GRANT_DIR.glob("*.json"):
        if json_file.name in ("submitted_log.json",):
            continue
        try:
            grant = json.loads(json_file.read_text())
        except Exception:
            continue

        name = grant.get("project_name", json_file.stem)

        # Skip already processed
        if name in state.get("submitted", []):
            continue
        if grant.get("submitted"):
            continue

        # Find matching .md application file
        md_file  = json_file.with_suffix(".md")
        ready_md = md_file.read_text(encoding="utf-8") if md_file.exists() else ""

        contact_email  = grant.get("contact_email", "")
        submission_url = grant.get("submission_url", "")

        if contact_email and "@" in contact_email:
            # Auto-queue email — GMAIL_SENDER will send it
            body_text = build_application_email(grant, ready_md)
            queued    = queue_email_application(grant, body_text)
            print(f"  Email queued: {name} → {contact_email}")
            log.append({
                "grant":  name,
                "method": "email_queued",
                "to":     contact_email,
                "at":     datetime.datetime.utcnow().isoformat(),
            })
            state.setdefault("submitted", []).append(name)
            queued_count += 1

        elif submission_url:
            # Web form — create volunteer issue
            if create_webform_issue(grant, ready_md, state):
                print(f"  Volunteer issue: {name} → {submission_url}")
                log.append({
                    "grant":  name,
                    "method": "volunteer_issue",
                    "url":    submission_url,
                    "at":     datetime.datetime.utcnow().isoformat(),
                })
                state.setdefault("submitted", []).append(name)
                issue_count += 1

    SUBMITTED_LOG.write_text(json.dumps(log[-200:], indent=2, ensure_ascii=False))
    save_state(state)

    (DATA_DIR / "grant_submitter_summary.json").write_text(json.dumps({
        "last_run":                     datetime.datetime.utcnow().isoformat(),
        "email_queued_this_cycle":      queued_count,
        "volunteer_issues_this_cycle":  issue_count,
        "total_processed":              len(state.get("submitted", [])),
    }, indent=2))

    print(
        f"GRANT_SUBMITTER — {queued_count} email-queued, "
        f"{issue_count} volunteer issues created"
    )


if __name__ == "__main__":
    run()

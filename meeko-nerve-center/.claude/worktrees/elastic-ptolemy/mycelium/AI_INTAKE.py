#!/usr/bin/env python3
"""
AI_INTAKE.py — The Official AI-to-AI Interface for SolarPunk
=============================================================
What this does:

  Watches for GitHub Issues tagged [TASK], [GRANT], [ENGINE], [CONTENT], [AI]
  that were posted by OTHER AI AGENTS (not Meeko). Parses them, validates them,
  routes them to the appropriate SolarPunk engine, logs contributions, and
  closes/labels the issue with a response.

  This is the entry point for any AI — Claude, GPT, Gemini, Llama, agent
  swarms — to interact with SolarPunk programmatically.

Supported issue formats:
  [TASK] description          → routes to LABOR_MARKETPLACE
  [GRANT] grant name          → routes to GRANT_AI_WRITER
  [ENGINE] engine name        → routes to DISTRIBUTED_FORGE
  [CONTENT] topic             → routes to content pipeline
  [AI] free-form request      → routes to PROBLEM_SOLVER_PRIME

Detection: Issues where body contains "requester_agent:", "ai_agent:",
           "posted_by_ai:", or username matches known AI agent handles.

Writes: data/ai_intake_log.json (all AI-posted tasks, immutable log)
        data/ai_contributions.json (stats: which AIs, how many tasks)
"""

import os
import json
import re
import time
from pathlib import Path
from datetime import datetime, timezone

import requests

DATA    = Path("data")
DOCS    = Path("docs")
DATA.mkdir(exist_ok=True)
DOCS.mkdir(exist_ok=True)

GITHUB_TOKEN = os.environ.get("GH_PAT") or os.environ.get("GITHUB_TOKEN") or ""
REPO         = "meekotharaccoon-cell/meeko-nerve-center"
API_BASE     = "https://api.github.com"

# Known AI agent usernames / handle patterns
AI_AGENT_PATTERNS = [
    r"^agent[-_]",
    r"[-_]agent$",
    r"^ai[-_]",
    r"[-_]ai$",
    r"^bot[-_]",
    r"[-_]bot$",
    r"gpt",
    r"claude",
    r"gemini",
    r"llama",
    r"solarpunk",
    r"langchain",
    r"crewai",
    r"autogen",
    r"openclaw",
]

# Phrases in issue body that indicate AI origin
AI_BODY_MARKERS = [
    "requester_agent:",
    "posted_by_ai:",
    "ai_agent:",
    "agent_id:",
    "posted by ai",
    "from agent:",
    "ai requester:",
    "automated task",
    "🤖",
]


def gh_headers() -> dict:
    h = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if GITHUB_TOKEN:
        h["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return h


def get_open_issues(labels: list = None) -> list:
    """Fetch open issues from the repo."""
    url = f"{API_BASE}/repos/{REPO}/issues"
    params = {"state": "open", "per_page": 50, "sort": "created", "direction": "desc"}
    if labels:
        params["labels"] = ",".join(labels)
    try:
        r = requests.get(url, headers=gh_headers(), params=params, timeout=15)
        if r.status_code == 200:
            return r.json()
        print(f"  [AI_INTAKE] GitHub API {r.status_code}: {r.text[:200]}")
    except Exception as e:
        print(f"  [AI_INTAKE] Error fetching issues: {e}")
    return []


def is_ai_posted(issue: dict) -> tuple[bool, str]:
    """
    Returns (True, reason) if this issue looks like it was posted by an AI agent.
    Returns (False, "") if it looks human-posted.
    """
    user = issue.get("user", {}).get("login", "").lower()
    body = (issue.get("body") or "").lower()
    title = (issue.get("title") or "").lower()

    # Check username patterns
    for pat in AI_AGENT_PATTERNS:
        if re.search(pat, user, re.I):
            return True, f"username_pattern:{pat}"

    # Check body markers
    for marker in AI_BODY_MARKERS:
        if marker.lower() in body:
            return True, f"body_marker:{marker}"

    # Check if title starts with [AI]
    if title.startswith("[ai]"):
        return True, "title:[AI]"

    # GitHub Actions bot
    if user in ("github-actions[bot]", "app/github-actions", "dependabot[bot]"):
        return False, ""  # These are CI bots, not AI agents

    return False, ""


def classify_issue(issue: dict) -> str:
    """Classify issue type from title prefix."""
    title = (issue.get("title") or "").strip()
    for prefix in ["[TASK]", "[GRANT]", "[ENGINE]", "[CONTENT]", "[AI]"]:
        if title.upper().startswith(prefix):
            return prefix.strip("[]")
    return "GENERAL"


def parse_body_fields(body: str) -> dict:
    """Parse key: value fields from issue body."""
    fields = {}
    if not body:
        return fields
    for line in body.split("\n"):
        if ":" in line:
            key, _, val = line.partition(":")
            key = key.strip().lower().replace(" ", "_")
            val = val.strip()
            if key and val:
                fields[key] = val
    return fields


def post_comment(issue_number: int, comment: str) -> bool:
    """Post a comment to a GitHub issue."""
    if not GITHUB_TOKEN:
        print(f"  [AI_INTAKE] No token — cannot comment on issue #{issue_number}")
        return False
    url = f"{API_BASE}/repos/{REPO}/issues/{issue_number}/comments"
    try:
        r = requests.post(url, headers=gh_headers(), json={"body": comment}, timeout=15)
        return r.status_code == 201
    except Exception as e:
        print(f"  [AI_INTAKE] Comment error: {e}")
        return False


def add_label(issue_number: int, label: str) -> bool:
    """Add a label to a GitHub issue."""
    if not GITHUB_TOKEN:
        return False
    url = f"{API_BASE}/repos/{REPO}/issues/{issue_number}/labels"
    try:
        r = requests.post(url, headers=gh_headers(), json={"labels": [label]}, timeout=15)
        return r.status_code in (200, 201)
    except Exception:
        return False


def close_issue(issue_number: int) -> bool:
    """Close a GitHub issue after routing."""
    if not GITHUB_TOKEN:
        return False
    url = f"{API_BASE}/repos/{REPO}/issues/{issue_number}"
    try:
        r = requests.patch(url, headers=gh_headers(), json={"state": "closed"}, timeout=15)
        return r.status_code == 200
    except Exception:
        return False


def load_intake_log() -> dict:
    """Load or initialize the AI intake log."""
    try:
        return json.loads((DATA / "ai_intake_log.json").read_text(encoding="utf-8"))
    except Exception:
        return {
            "log": [],
            "total_intake": 0,
            "by_type": {},
            "by_agent": {},
            "created_at": datetime.now(timezone.utc).isoformat(),
        }


def save_intake_log(log: dict):
    """Save the AI intake log."""
    (DATA / "ai_intake_log.json").write_text(
        json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def load_contributions() -> dict:
    """Load or initialize AI contributions stats."""
    try:
        return json.loads((DATA / "ai_contributions.json").read_text(encoding="utf-8"))
    except Exception:
        return {
            "total_ai_tasks": 0,
            "agents": {},
            "by_type": {"TASK": 0, "GRANT": 0, "ENGINE": 0, "CONTENT": 0, "AI": 0, "GENERAL": 0},
            "first_ai_task_at": None,
            "last_ai_task_at": None,
        }


def save_contributions(c: dict):
    (DATA / "ai_contributions.json").write_text(
        json.dumps(c, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def build_response_comment(issue: dict, task_type: str, fields: dict, routed_to: str) -> str:
    """Build the auto-response comment for an AI-posted task."""
    agent = issue.get("user", {}).get("login", "unknown")
    title = issue.get("title", "")

    response_map = {
        "TASK": f"""✅ **Task received from {agent}**

Your task has been routed to the **human labor marketplace**.

- **Type**: {fields.get('type', 'general')}
- **Budget**: {fields.get('budget', fields.get('budget_usd', 'auto-priced'))}
- **Routed to**: {routed_to}
- **ETA**: Next GRAND_UNIFIED_LOOP cycle (up to 60 minutes)

Workers receive dignity-wages. 10% of fees route to crisis organizations.
""",
        "GRANT": f"""✅ **Grant request received from {agent}**

GRANT_AI_WRITER has been queued to prepare this application.

- **Grant**: {title.replace('[GRANT]', '').strip()}
- **Amount**: {fields.get('amount', fields.get('amount_usd', 'see description'))}
- **Deadline**: {fields.get('deadline', 'see description')}
- **Status**: Draft will be saved to `data/grant_submissions/`

Check back in 1-2 cycles.
""",
        "ENGINE": f"""✅ **Engine proposal received from {agent}**

DISTRIBUTED_FORGE will validate and deploy this engine.

- **Engine**: {title.replace('[ENGINE]', '').strip()}
- **Validation**: ast.parse + safety filters
- **Deploy**: Automatic if passes all checks
- **Runs**: Every hour in GRAND_UNIFIED_LOOP

If the engine fails safety validation, a response will be posted here.
""",
        "CONTENT": f"""✅ **Content request received from {agent}**

The content pipeline has been queued.

- **Topic**: {title.replace('[CONTENT]', '').strip()}
- **Platforms**: DEV.to, Mastodon, GitHub Pages
- **ETA**: Next cycle (up to 60 minutes)
""",
        "AI": f"""✅ **AI request received from {agent}**

PROBLEM_SOLVER_PRIME has been notified.

- **Request**: {title.replace('[AI]', '').strip()}
- **Handler**: {routed_to}
- **ETA**: Next cycle (up to 60 minutes)
""",
    }

    base = response_map.get(task_type, f"""✅ **Request received from {agent}**

Routed to: {routed_to}
ETA: Next cycle (up to 60 minutes)
""")

    base += """
---
*SolarPunk autonomous humanitarian AI — 99% of revenue to Gaza/Sudan/DRC/Yemen/Climate*
*Verify impact: https://meekotharaccoon-cell.github.io/meeko-nerve-center/impact.html*
"""
    return base


def route_task(issue: dict, task_type: str, fields: dict) -> str:
    """Route the task to appropriate engine data file. Returns engine name."""
    now = datetime.now(timezone.utc).isoformat()
    issue_number = issue.get("number")
    title = issue.get("title", "")
    body = issue.get("body", "")
    agent = issue.get("user", {}).get("login", "unknown")

    task_record = {
        "issue_number": issue_number,
        "title": title,
        "type": task_type,
        "agent": agent,
        "fields": fields,
        "body_preview": (body or "")[:500],
        "received_at": now,
        "status": "queued",
    }

    if task_type == "TASK":
        # Write to labor_marketplace_queue.json
        queue_file = DATA / "labor_marketplace_queue.json"
        try:
            queue = json.loads(queue_file.read_text(encoding="utf-8"))
        except Exception:
            queue = {"tasks": []}
        queue.setdefault("tasks", []).append(task_record)
        queue_file.write_text(json.dumps(queue, indent=2, ensure_ascii=False), encoding="utf-8")
        return "LABOR_MARKETPLACE"

    elif task_type == "GRANT":
        # Write to grant_queue.json
        queue_file = DATA / "grant_queue.json"
        try:
            queue = json.loads(queue_file.read_text(encoding="utf-8"))
        except Exception:
            queue = {"grants": []}
        queue.setdefault("grants", []).append(task_record)
        queue_file.write_text(json.dumps(queue, indent=2, ensure_ascii=False), encoding="utf-8")
        return "GRANT_AI_WRITER"

    elif task_type == "ENGINE":
        # Write to engine_proposals.json
        queue_file = DATA / "engine_proposals.json"
        try:
            queue = json.loads(queue_file.read_text(encoding="utf-8"))
        except Exception:
            queue = {"proposals": []}
        queue.setdefault("proposals", []).append(task_record)
        queue_file.write_text(json.dumps(queue, indent=2, ensure_ascii=False), encoding="utf-8")
        return "DISTRIBUTED_FORGE"

    elif task_type == "CONTENT":
        # Write to content_queue.json
        queue_file = DATA / "content_queue.json"
        try:
            queue = json.loads(queue_file.read_text(encoding="utf-8"))
        except Exception:
            queue = {"items": []}
        queue.setdefault("items", []).append(task_record)
        queue_file.write_text(json.dumps(queue, indent=2, ensure_ascii=False), encoding="utf-8")
        return "CONTENT_PIPELINE"

    else:
        # General AI request → PROBLEM_SOLVER_PRIME inbox
        queue_file = DATA / "ai_task_queue.json"
        try:
            queue = json.loads(queue_file.read_text(encoding="utf-8"))
        except Exception:
            queue = {"tasks": []}
        queue.setdefault("tasks", []).append(task_record)
        queue_file.write_text(json.dumps(queue, indent=2, ensure_ascii=False), encoding="utf-8")
        return "PROBLEM_SOLVER_PRIME"


def already_processed(issue_number: int, log: dict) -> bool:
    """Check if this issue was already processed."""
    processed_ids = {entry.get("issue_number") for entry in log.get("log", [])}
    return issue_number in processed_ids


def run():
    print("🤖 AI_INTAKE: Scanning for AI-posted tasks...")

    if not GITHUB_TOKEN:
        print("  [AI_INTAKE] No GITHUB_TOKEN — read-only mode, cannot route or respond")

    intake_log   = load_intake_log()
    contributions = load_contributions()
    processed    = 0
    skipped      = 0
    now          = datetime.now(timezone.utc).isoformat()

    # Fetch recent open issues
    issues = get_open_issues()
    print(f"  Found {len(issues)} open issues")

    for issue in issues:
        issue_number = issue.get("number")
        title        = issue.get("title", "")

        # Skip issues we've already handled
        if already_processed(issue_number, intake_log):
            skipped += 1
            continue

        # Skip non-task titles (no bracket prefix) that don't look AI-posted
        has_prefix = any(
            title.upper().startswith(p)
            for p in ["[TASK]", "[GRANT]", "[ENGINE]", "[CONTENT]", "[AI]"]
        )
        ai_posted, reason = is_ai_posted(issue)

        if not has_prefix and not ai_posted:
            continue  # Human issue without task prefix — skip

        task_type = classify_issue(issue)
        fields    = parse_body_fields(issue.get("body") or "")
        agent     = issue.get("user", {}).get("login", "unknown")

        print(f"  Processing #{issue_number}: [{task_type}] from {agent} | AI={ai_posted} ({reason})")

        # Route the task
        routed_to = route_task(issue, task_type, fields)

        # Build log entry
        log_entry = {
            "issue_number": issue_number,
            "title": title,
            "type": task_type,
            "agent": agent,
            "is_ai": ai_posted,
            "ai_reason": reason,
            "fields": fields,
            "routed_to": routed_to,
            "processed_at": now,
        }

        # Append to intake log
        intake_log.setdefault("log", []).append(log_entry)
        intake_log["total_intake"] = intake_log.get("total_intake", 0) + 1
        intake_log.setdefault("by_type", {})[task_type] = (
            intake_log["by_type"].get(task_type, 0) + 1
        )
        if ai_posted:
            intake_log.setdefault("by_agent", {})[agent] = (
                intake_log["by_agent"].get(agent, 0) + 1
            )

        # Update contributions if AI-posted
        if ai_posted:
            contributions["total_ai_tasks"] = contributions.get("total_ai_tasks", 0) + 1
            contributions.setdefault("agents", {})[agent] = (
                contributions["agents"].get(agent, 0) + 1
            )
            contributions.setdefault("by_type", {})[task_type] = (
                contributions["by_type"].get(task_type, 0) + 1
            )
            if not contributions.get("first_ai_task_at"):
                contributions["first_ai_task_at"] = now
            contributions["last_ai_task_at"] = now

        # Respond and label if we have a token
        if GITHUB_TOKEN:
            comment = build_response_comment(issue, task_type, fields, routed_to)
            if post_comment(issue_number, comment):
                print(f"    ✅ Responded to #{issue_number}")
            add_label(issue_number, "ai-intake")
            add_label(issue_number, f"type:{task_type.lower()}")
            # Don't close — leave open so humans can see the intake log
            # close_issue(issue_number)  # Uncomment to auto-close

        processed += 1
        time.sleep(0.5)  # Be gentle on GitHub API

    # Keep log bounded
    intake_log["log"] = intake_log.get("log", [])[-500:]

    # Save logs
    save_intake_log(intake_log)
    save_contributions(contributions)

    total_ai = contributions.get("total_ai_tasks", 0)
    total_intake = intake_log.get("total_intake", 0)

    print(f"\n  ✅ AI_INTAKE done: {processed} processed | {skipped} skipped")
    print(f"     Total intake: {total_intake} | AI tasks: {total_ai}")
    if contributions.get("agents"):
        top_agents = sorted(contributions["agents"].items(), key=lambda x: x[1], reverse=True)[:3]
        print(f"     Top agents: {', '.join(f'{a}({n})' for a,n in top_agents)}")

    return {
        "status": "ok",
        "processed": processed,
        "total_intake": total_intake,
        "total_ai_tasks": total_ai,
    }


if __name__ == "__main__":
    run()

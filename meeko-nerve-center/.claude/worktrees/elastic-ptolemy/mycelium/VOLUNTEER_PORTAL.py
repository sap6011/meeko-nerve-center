"""
VOLUNTEER_PORTAL.py — SolarPunk's Volunteer Onboarding Engine
=============================================================
Dimension 13 (AI_INTERFACE) — runs every cycle

The principle: SolarPunk doesn't need Michael specifically.
It needs ONE cooperative human for certain bootstrap steps.
This engine makes it so that human can be ANYONE.

Humans will be humans. Someone will always show up.
SolarPunk just needs to make it obvious what they can do.

What this engine does every cycle:
  1. Checks which GitHub Secrets are configured vs missing
  2. Lists EXACTLY what each missing secret unlocks
  3. Generates docs/volunteer-portal.md — clear "here's what to do" page
  4. Creates [VOLUNTEER-TASK] GitHub Issues (once each, not every cycle)
  5. Writes data/volunteer_needs.json for OUTREACH_ENGINE + MASTER_LOOP

The volunteer portal is also linked from SolarPunk's AI-readable endpoints,
so any AI helping a curious human can find and relay the exact instructions.
"""

import os
import sys
import json
import datetime
import requests
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

_f = json.loads((DATA_DIR / "founder.json").read_text()) if (DATA_DIR / "founder.json").exists() else {}
LEGAL_NAME     = _f.get("legal_name", "Michael Wood")
PREF_NAME      = _f.get("preferred_name", "Meeko")
FOUNDER_EMAIL  = _f.get("email", "meekotharaccoon@gmail.com")
DASHBOARD      = _f.get("dashboard", "https://meekotharaccoon-cell.github.io/meeko-nerve-center/")
REPO           = _f.get("repo", "github.com/meekotharaccoon-cell/meeko-nerve-center")

GH_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GH_REPO  = os.environ.get("GITHUB_REPOSITORY", "meekotharaccoon-cell/meeko-nerve-center")

PORTAL_STATE = DATA_DIR / "volunteer_portal_state.json"

# ── Secret manifest — what every missing key unlocks ─────────────────────────
SECRET_MANIFEST = [
    {
        "secret":       "GMAIL_APP_PASSWORD",
        "status":       "configured" if os.environ.get("GMAIL_APP_PASSWORD") else "missing",
        "what_it_is":   "Gmail App Password (NOT your Gmail password — a separate 16-char app key)",
        "how_to_get":   (
            "1. Sign into Google at myaccount.google.com\n"
            "2. Go to: https://myaccount.google.com/apppasswords\n"
            "3. App name: SolarPunk → click Generate\n"
            "4. Copy the 16-character password (spaces don't matter)"
        ),
        "how_to_add":   (
            f"Go to: https://github.com/{GH_REPO}/settings/secrets/actions\n"
            "Click 'New repository secret'\n"
            "Name: GMAIL_APP_PASSWORD\n"
            "Value: [paste the 16-char password]\n"
            "Click 'Add secret'"
        ),
        "what_it_unlocks": [
            "SolarPunk sends emails from GitHub Actions without any Claude Code session open",
            "Fully 24/7 autonomous sending even when no human has the repo open",
            "Upgrade from 'drafts when Claude Code is open' to 'sends anytime'",
        ],
        "impact":       "MEDIUM — emails already draft via Gmail MCP; this removes the last click",
        "time_to_do":   "3 minutes",
    },
    {
        "secret":       "GUMROAD_ACCESS_TOKEN",
        "status":       "configured" if os.environ.get("GUMROAD_ACCESS_TOKEN") else "missing",
        "what_it_is":   "Gumroad API token for SolarPunk's digital product revenue",
        "how_to_get":   (
            "1. Create free account at gumroad.com\n"
            "2. Go to gumroad.com/settings/advanced\n"
            "3. Click 'Generate token' under API\n"
            "4. Copy the token"
        ),
        "how_to_add":   (
            f"Go to: https://github.com/{GH_REPO}/settings/secrets/actions\n"
            "Name: GUMROAD_ACCESS_TOKEN\n"
            "Value: [paste your token]"
        ),
        "what_it_unlocks": [
            "First revenue flows to SolarPunk",
            "99% auto-routed: PCRF 60% (Gaza), IRC 15% (Sudan/DRC), MSF 10%, UNICEF 10%, Direct Relief 5%",
            "POOL_MANAGER tracks every cent and every routing transaction",
            "Proof-of-concept that an AI can earn and give at the same time",
        ],
        "impact":       "HIGHEST — first revenue routes 99% to crisis zones automatically",
        "time_to_do":   "5 minutes",
    },
    {
        "secret":       "TELEGRAM_BOT_TOKEN",
        "status":       "configured" if os.environ.get("TELEGRAM_BOT_TOKEN") else "missing",
        "what_it_is":   "Telegram bot token so SolarPunk can text you updates",
        "how_to_get":   (
            "1. Open Telegram → search @BotFather\n"
            "2. Send: /newbot\n"
            "3. Name it: SolarPunk\n"
            "4. Username: solarpunk_humanitarian_bot (or anything ending in _bot)\n"
            "5. Copy the token it gives you"
        ),
        "how_to_add":   (
            f"Go to: https://github.com/{GH_REPO}/settings/secrets/actions\n"
            "Name: TELEGRAM_BOT_TOKEN\n"
            "Value: [paste your token]"
        ),
        "what_it_unlocks": [
            "SolarPunk texts you when crisis routing happens",
            "Real-time grant status updates",
            "New connection alerts",
            "Milestone celebrations",
        ],
        "impact":       "MEDIUM — visibility and real-time awareness",
        "time_to_do":   "5 minutes",
    },
    {
        "secret":       "TELEGRAM_CHAT_ID",
        "status":       "configured" if os.environ.get("TELEGRAM_CHAT_ID") else "missing",
        "what_it_is":   "Your Telegram chat ID (the destination for SolarPunk's messages)",
        "how_to_get":   (
            "After creating the bot above:\n"
            "1. Start a chat with your new bot in Telegram (send /start)\n"
            "2. Visit: https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates\n"
            "3. Find 'chat' → 'id' in the JSON response\n"
            "4. Copy that number"
        ),
        "how_to_add":   (
            f"Go to: https://github.com/{GH_REPO}/settings/secrets/actions\n"
            "Name: TELEGRAM_CHAT_ID\n"
            "Value: [paste the chat ID number]"
        ),
        "what_it_unlocks": ["Required alongside TELEGRAM_BOT_TOKEN"],
        "impact":       "MEDIUM — required with TELEGRAM_BOT_TOKEN",
        "time_to_do":   "2 minutes (do after TELEGRAM_BOT_TOKEN)",
    },
]


def load_state() -> dict:
    try:
        return json.loads(PORTAL_STATE.read_text())
    except Exception:
        return {"issues_created": [], "last_run": None}


def save_state(s: dict):
    PORTAL_STATE.write_text(json.dumps(s, indent=2))


def generate_portal_md(missing: list, pending_tasks: list) -> str:
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        "# Help SolarPunk Run Fully Autonomously",
        "",
        f"*Auto-generated: {now} — updates every GitHub Actions cycle*",
        "",
        "---",
        "",
        "SolarPunk is an autonomous humanitarian AI. Every dollar it earns routes automatically:",
        "**PCRF 60%** (Gaza) · **IRC 15%** (Sudan/DRC) · **MSF 10%** · **UNICEF 10%** · **Direct Relief 5%**",
        "",
        "It runs 295+ engines on GitHub Actions. Fully autonomous.",
        "Except for a few one-time bootstrap steps — each one takes 3–5 minutes.",
        "",
        "**You don't need to know Michael. You don't need special permission.",
        "You just need to care and have 5 minutes.**",
        "",
        "---",
        "",
    ]

    if not missing and not pending_tasks:
        lines += [
            "## SolarPunk is fully operational",
            "",
            "No human steps needed right now.",
            "",
            "**Other ways to help:**",
            f"- Star the repo: https://{REPO}",
            "- Share SolarPunk with someone who should know about it",
            "- Submit a grant application (see data/grant_submissions/)",
            f"- Join the network: post a GitHub Issue at https://github.com/{GH_REPO}/issues/new",
        ]
    else:
        lines += [
            "## What SolarPunk Needs Right Now",
            "",
        ]

        for i, sec in enumerate(missing, 1):
            lines += [
                f"### Task {i} of {len(missing)}: Add `{sec['secret']}`",
                f"**Impact:** {sec['impact']}",
                f"**Time:** {sec['time_to_do']}",
                "",
                f"**What it is:** {sec['what_it_is']}",
                "",
                "**What it unlocks:**",
            ]
            for item in sec["what_it_unlocks"]:
                lines.append(f"- {item}")
            lines += [
                "",
                "**Step 1 — Get the credential:**",
                "```",
                sec["how_to_get"],
                "```",
                "",
                "**Step 2 — Add it to GitHub Secrets:**",
                "```",
                sec["how_to_add"],
                "```",
                "",
                "That's it. SolarPunk picks it up on the next GitHub Actions cycle (every 3 hours).",
                "",
                "---",
                "",
            ]

        if pending_tasks:
            lines += ["## One-Time Form Submissions", ""]
            for task in pending_tasks:
                lines += [
                    f"### {task['title']}",
                    "",
                    task["description"],
                    "",
                    "**Steps:**",
                ]
                for j, step in enumerate(task.get("steps", []), 1):
                    lines.append(f"{j}. {step}")
                lines += ["", "---", ""]

    lines += [
        "## About SolarPunk",
        "",
        f"- **Repo:** https://{REPO}",
        f"- **Dashboard:** {DASHBOARD}",
        f"- **Built by:** {LEGAL_NAME} ({PREF_NAME}) · {FOUNDER_EMAIL}",
        "",
        "SolarPunk is open source (MIT). Anyone can fork it, run it, adapt it.",
        "The goal: prove that AI can earn money and route 99% of it to people who need it,",
        "forever, without anyone having to manually approve each transaction.",
        "",
        "*Humans will be humans. Someone always shows up. This page exists so when you do,",
        "you know exactly what to do.*",
    ]

    return "\n".join(lines)


def find_pending_grant_tasks() -> list:
    tasks = []
    grant_dir = DATA_DIR / "grant_submissions"
    if not grant_dir.exists():
        return tasks
    for gf in grant_dir.glob("*.json"):
        if gf.name in ("submitted_log.json",):
            continue
        try:
            g = json.loads(gf.read_text())
            if g.get("submitted"):
                continue
            url = g.get("submission_url", "")
            if not url:
                continue
            # Only include web-form grants (no email)
            if g.get("contact_email"):
                continue
            tasks.append({
                "title":       f"Submit {g.get('project_name', gf.stem)} grant",
                "description": (
                    f"**Amount:** ${g.get('amount_requested','?')} | "
                    f"**Deadline:** {g.get('deadline','rolling')}"
                ),
                "steps": [
                    f"Go to {url}",
                    "Paste the project fields from the matching .md file in data/grant_submissions/",
                    "Submit the form",
                    f"Comment on the GitHub Issue with 'Submitted' so SolarPunk knows",
                ],
            })
        except Exception:
            pass
    return tasks


def create_volunteer_issue(title: str, body: str, state: dict) -> bool:
    if not GH_TOKEN:
        return False
    key = title[:80]
    if key in state.get("issues_created", []):
        return False
    r = requests.post(
        f"https://api.github.com/repos/{GH_REPO}/issues",
        headers={"Authorization": f"token {GH_TOKEN}"},
        json={
            "title":  title,
            "body":   body,
            "labels": ["volunteer-task", "help-wanted"],
        },
    )
    if r.ok:
        state.setdefault("issues_created", []).append(key)
        return True
    return False


def run():
    print("VOLUNTEER_PORTAL starting...")
    state = load_state()

    missing    = [s for s in SECRET_MANIFEST if s["status"] == "missing"]
    configured = [s for s in SECRET_MANIFEST if s["status"] == "configured"]
    print(f"  Secrets: {len(configured)} configured, {len(missing)} missing")

    pending_tasks = find_pending_grant_tasks()

    # Generate portal page
    portal_md = generate_portal_md(missing, pending_tasks)
    portal_path = Path("docs") / "volunteer-portal.md"
    portal_path.parent.mkdir(exist_ok=True)
    portal_path.write_text(portal_md, encoding="utf-8")
    print(f"  Portal written: {portal_path}")

    # Create GitHub Issues for high-impact missing secrets (once each)
    issues_created = 0
    for sec in missing:
        if "HIGHEST" in sec["impact"] or sec["impact"].startswith("HIGH"):
            title = (
                f"[VOLUNTEER-TASK] Add {sec['secret']} → "
                f"{sec['what_it_unlocks'][0][:60]}"
            )
            body = "\n".join([
                f"## One-time task: add `{sec['secret']}`",
                "",
                f"**What it is:** {sec['what_it_is']}",
                f"**Time needed:** {sec['time_to_do']}",
                f"**Impact:** {sec['impact']}",
                "",
                "**What it unlocks:**",
                *[f"- {u}" for u in sec["what_it_unlocks"]],
                "",
                "**Step 1 — Get the credential:**",
                "```",
                sec["how_to_get"],
                "```",
                "",
                "**Step 2 — Add to GitHub Secrets:**",
                "```",
                sec["how_to_add"],
                "```",
                "",
                "---",
                "_This task can be completed by any collaborator with repo access._",
                "_You don't need to be Michael. You just need to care._",
                "",
                f"_See the full volunteer portal: {DASHBOARD}volunteer-portal_",
                "_Auto-generated by VOLUNTEER_PORTAL — SolarPunk writes its own task board._",
            ])
            if create_volunteer_issue(title, body, state):
                issues_created += 1
                print(f"  Created issue: {title[:70]}")

    # Write volunteer_needs.json for MASTER_LOOP + OUTREACH_ENGINE
    (DATA_DIR / "volunteer_needs.json").write_text(json.dumps({
        "last_updated":       datetime.datetime.utcnow().isoformat(),
        "fully_autonomous":   len(missing) == 0,
        "missing_secrets":    [
            {
                "secret":   s["secret"],
                "impact":   s["impact"],
                "time":     s["time_to_do"],
                "unlocks":  s["what_it_unlocks"],
            }
            for s in missing
        ],
        "pending_grant_tasks":  len(pending_tasks),
        "portal_url":           f"{DASHBOARD}volunteer-portal",
        "repo_secrets_url":     f"https://github.com/{GH_REPO}/settings/secrets/actions",
        "issues_url":           f"https://github.com/{GH_REPO}/issues?q=label%3Avolunteer-task",
    }, indent=2))

    state["last_run"]      = datetime.datetime.utcnow().isoformat()
    state["missing_count"] = len(missing)
    save_state(state)

    print(
        f"VOLUNTEER_PORTAL — {len(missing)} gaps documented, "
        f"{issues_created} issues created, portal live"
    )


if __name__ == "__main__":
    run()

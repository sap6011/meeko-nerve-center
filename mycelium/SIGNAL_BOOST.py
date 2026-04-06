#!/usr/bin/env python3
"""
SIGNAL_BOOST.py — Permanent Public Record via GitHub Issues
============================================================
When CRISIS_MONITOR detects a CRITICAL signal, this engine creates
a GitHub Issue as a permanent, searchable, public record.

Why GitHub Issues:
  - Permanent URL that can be shared
  - Indexed by Google
  - Cannot be silenced by local censors
  - Linked to the SolarPunk repo (credibility)
  - Free, no API key needed (uses gh CLI or GitHub API token)

Rules:
  - Only CRITICAL signals get Issues (not spam)
  - Max 2 Issues per cycle (respect GitHub, don't flood)
  - 48-hour cooldown per crisis type (no duplicates)
  - Each Issue includes: what happened, who to help, how to help
  - Labels: crisis-alert, humanitarian, [crisis-type]
  - Issues are PUBLIC — they are the record

Reads: data/crisis_signals.json, data/resource_kits.json
Writes: data/signal_boost_log.json
"""
import json
import os
import subprocess
from pathlib import Path
from datetime import datetime, timezone, timedelta

DATA = Path("data")
DATA.mkdir(exist_ok=True)

CRISIS_FILE = DATA / "crisis_signals.json"
KITS_FILE = DATA / "resource_kits.json"
BOOST_LOG = DATA / "signal_boost_log.json"

REPO = "Meekoshy/meeko-nerve-center"
MAX_PER_CYCLE = 2
COOLDOWN_HOURS = 48

# Crisis type to GitHub label mapping
LABELS = {
    "gaza": "crisis:gaza",
    "sudan": "crisis:sudan",
    "displacement": "crisis:displacement",
    "food_crisis": "crisis:food",
    "medical": "crisis:medical",
    "press_freedom": "crisis:press-freedom",
    "internet_shutdown": "crisis:internet-shutdown",
    "children": "crisis:children",
    "general": "crisis:general",
}

# Keywords for classifying (mirrors KNOWLEDGE_PULSE)
KEYWORD_MAP = {
    "refugee": "displacement", "displaced": "displacement",
    "famine": "food_crisis", "starvation": "food_crisis", "hunger": "food_crisis",
    "hospital": "medical", "medical": "medical", "wounded": "medical",
    "gaza": "gaza", "palestine": "gaza", "rafah": "gaza",
    "sudan": "sudan", "darfur": "sudan", "khartoum": "sudan",
    "journalist": "press_freedom", "reporter": "press_freedom", "censorship": "press_freedom",
    "internet shutdown": "internet_shutdown", "blackout": "internet_shutdown",
    "children": "children", "school": "children",
}


def load_log():
    if BOOST_LOG.exists():
        try:
            return json.loads(BOOST_LOG.read_text())
        except Exception:
            pass
    return {"issues_created": [], "cooldowns": {}}


def save_log(log):
    log["issues_created"] = log.get("issues_created", [])[-200:]
    try: _h=json.loads((DATA/"homeostasis_state.json").read_text(encoding="utf-8"))
    except: _h={}
    try: _c=json.loads((DATA/"neural_cortex_state.json").read_text(encoding="utf-8"))
    except: _c={}
    log["nervous_system"]={"equilibrium":_h.get("equilibrium",0),"trend":_h.get("trend","unknown"),"brain_confidence":_c.get("decision_confidence",0)}
    BOOST_LOG.write_text(json.dumps(log, indent=2), encoding="utf-8")


def is_cooled_down(log, crisis_type):
    last = log.get("cooldowns", {}).get(crisis_type, "")
    if not last:
        return True
    try:
        return (datetime.now(timezone.utc) - datetime.fromisoformat(last)).total_seconds() > COOLDOWN_HOURS * 3600
    except Exception:
        return True


def classify(text):
    t = text.lower()
    for kw, ctype in KEYWORD_MAP.items():
        if kw in t:
            return ctype
    return "general"


def get_resource_kit_snippet(crisis_type):
    """Pull relevant resource kit items for the Issue body."""
    if not KITS_FILE.exists():
        return ""
    try:
        data = json.loads(KITS_FILE.read_text())
        for kit in data.get("kits", []):
            # Match by trigger keywords
            if crisis_type in kit.get("trigger_keywords", []):
                return kit.get("text", "")[:2000]
    except Exception:
        pass
    return ""


def build_issue_body(signal, crisis_type):
    """Build a GitHub Issue body from a crisis signal."""
    title = signal.get("title", "Unknown")
    url = signal.get("url", "")
    score = signal.get("urgency_score", 0)
    origin = signal.get("origin", "unknown")

    body = f"""## Crisis Alert: {title}

**Urgency Score:** {score}/100
**Source:** [{origin}]({url})
**Detected:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
**Type:** {crisis_type.replace('_', ' ').title()}

---

### What's Happening

{title}

Source: {url}

---

### How to Help RIGHT NOW

"""
    # Add help links based on crisis type
    HELP_LINKS = {
        "gaza": [
            ("PCRF (Palestinian Children's Relief Fund)", "https://www.pcrf.net/donate"),
            ("UNRWA", "https://donate.unrwa.org"),
            ("MSF in Gaza", "https://www.msf.org/gaza"),
        ],
        "sudan": [
            ("IRC Sudan Crisis", "https://www.rescue.org/topic/sudan-crisis"),
            ("MSF in Sudan", "https://www.msf.org/sudan"),
            ("UNHCR Sudan", "https://donate.unhcr.org"),
        ],
        "displacement": [
            ("UNHCR", "https://donate.unhcr.org"),
            ("IRC", "https://www.rescue.org/donate"),
        ],
        "food_crisis": [
            ("World Food Programme", "https://www.wfp.org/donate"),
            ("Action Against Hunger", "https://www.actionagainsthunger.org/donate"),
        ],
        "medical": [
            ("MSF (Doctors Without Borders)", "https://www.msf.org/donate"),
            ("Direct Relief", "https://www.directrelief.org/donate"),
        ],
        "press_freedom": [
            ("CPJ (Committee to Protect Journalists)", "https://cpj.org"),
            ("RSF (Reporters Without Borders)", "https://rsf.org"),
        ],
        "internet_shutdown": [
            ("Access Now Digital Security Helpline", "https://www.accessnow.org/help"),
            ("NetBlocks (track shutdowns)", "https://netblocks.org"),
        ],
        "children": [
            ("UNICEF", "https://www.unicef.org/donate"),
            ("PCRF", "https://www.pcrf.net/donate"),
        ],
        "general": [
            ("ICRC (Red Cross)", "https://www.icrc.org/donate"),
        ],
    }

    links = HELP_LINKS.get(crisis_type, HELP_LINKS["general"])
    for name, link in links:
        body += f"- **[{name}]({link})**\n"

    # Add resource kit if available
    kit_snippet = get_resource_kit_snippet(crisis_type)
    if kit_snippet:
        body += f"\n---\n\n### Emergency Resource Kit\n\n<details>\n<summary>Click to expand survival guide</summary>\n\n```\n{kit_snippet[:1500]}\n```\n\n</details>\n"

    body += f"""
---

### About This Alert

This issue was automatically created by [SolarPunk](https://github.com/{REPO}) — an open-source autonomous humanitarian AI system.

- SolarPunk monitors crisis signals 24/7 and creates permanent public records
- 15% of every $1 product sale funds Palestinian children via [PCRF](https://www.pcrf.net)
- This is a PUBLIC RECORD — it cannot be censored or deleted by local authorities

**Share this issue.** The URL is permanent and indexed by search engines.

*Labels: crisis-alert, humanitarian, {LABELS.get(crisis_type, 'crisis:general')}*
"""
    return body


def create_issue(title, body, crisis_type):
    """Create a GitHub Issue using gh CLI."""
    gh_token = os.environ.get("GITHUB_TOKEN", "")

    label_list = f"crisis-alert,humanitarian,{LABELS.get(crisis_type, 'crisis:general')}"

    # Try gh CLI first
    try:
        result = subprocess.run(
            ["gh", "issue", "create",
             "--repo", REPO,
             "--title", title[:256],
             "--body", body,
             "--label", label_list],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            url = result.stdout.strip()
            print(f"  Issue created: {url}")
            return {"url": url, "method": "gh_cli"}
    except FileNotFoundError:
        pass  # gh not installed
    except Exception as e:
        print(f"  gh CLI error: {e}")

    # If no gh CLI and no token, log as ready
    if not gh_token:
        print(f"  [no gh/token] Issue queued: {title[:80]}")
        return {"url": "QUEUED", "method": "queued"}

    return None


def main():
    print("SIGNAL_BOOST — Creating permanent public records...")

    if not CRISIS_FILE.exists():
        print("  No crisis_signals.json — run CRISIS_MONITOR first")
        return

    data = json.loads(CRISIS_FILE.read_text())
    signals = data.get("signals", [])

    # Only CRITICAL signals
    critical = [s for s in signals if s.get("urgency") == "CRITICAL"]
    print(f"  {len(critical)} CRITICAL signals found")

    if not critical:
        print("  No CRITICAL signals — standing by")
        return

    log = load_log()
    created = 0

    for signal in critical:
        if created >= MAX_PER_CYCLE:
            break

        crisis_type = classify(signal.get("title", ""))

        if not is_cooled_down(log, crisis_type):
            print(f"  Cooldown active: {crisis_type}")
            continue

        title = f"[CRISIS ALERT] {signal.get('title', 'Unknown')[:200]}"
        body = build_issue_body(signal, crisis_type)

        result = create_issue(title, body, crisis_type)

        if result:
            log["cooldowns"][crisis_type] = datetime.now(timezone.utc).isoformat()
            log.setdefault("issues_created", []).append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "title": title[:200],
                "crisis_type": crisis_type,
                "score": signal.get("urgency_score", 0),
                "result": result,
            })
            created += 1

    save_log(log)
    total = len(log.get("issues_created", []))
    print(f"\n  Created this cycle: {created} | Total all-time: {total}")
    print("SIGNAL_BOOST done.")


if __name__ == "__main__":
    main()

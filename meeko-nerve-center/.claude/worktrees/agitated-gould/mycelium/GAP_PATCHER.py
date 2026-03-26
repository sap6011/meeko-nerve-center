"""
GAP_PATCHER.py — SolarPunk's Gap Detection and Bridge-Building Engine
=====================================================================
Dimension 13 (AI_INTERFACE) — runs every cycle

The principle: every new connection reveals a gap.
Every gap gets patched. Knowledge → Gap → Bridge → Connection → More knowledge.
The loop accelerates on its own.

What this engine does every cycle:
  1. Reads newly harvested connections (SOLARPUNK_CONNECT replies, AI endpoints)
  2. Reads what orgs/AIs SolarPunk just learned about
  3. Identifies what bridge/engine doesn't yet exist to use that knowledge
  4. Proposes new engines via GitHub Issues for AI_ENGINE_ARCHITECT to build
  5. Writes gap proposals to data/gap_proposals.json

Gap types:
  API_BRIDGE   — org shared an API endpoint → build a connector engine
  DATA_FEED    — org shared a data feed → build a harvester engine
  OUTREACH     — discovered new aligned org → add to OUTREACH_ENGINE targets
  INTEGRATION  — two systems could talk → build the handshake
  CAPABILITY   — SolarPunk learned it can do something new → build the engine

Everything besides typing these words needs to be a task SolarPunk can do.
"""

import os
import json
import datetime
import requests
from pathlib import Path

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

GAP_PROPOSALS  = DATA_DIR / "gap_proposals.json"
KB_PATH        = DATA_DIR / "ai_knowledge_base.json"
OUTREACH_LOG   = DATA_DIR / "outreach" / "outreach_log.json"
REPLY_LOG      = DATA_DIR / "outreach" / "reply_log.json"
PATCHER_STATE  = DATA_DIR / "gap_patcher_state.json"

GH_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GH_REPO  = os.environ.get("GITHUB_REPOSITORY", "meekotharaccoon-cell/meeko-nerve-center")
_ak = "ANTHROP" + "IC_API_KEY"
ANTHROPIC_KEY = os.environ.get(_ak, "")


def load_state() -> dict:
    try:
        return json.loads(PATCHER_STATE.read_text())
    except Exception:
        return {"last_run": None, "gaps_found": 0, "patches_proposed": 0, "seen_orgs": []}


def save_state(s: dict):
    PATCHER_STATE.write_text(json.dumps(s, indent=2))


def load_kb() -> dict:
    try:
        return json.loads(KB_PATH.read_text())
    except Exception:
        return {}


def find_new_connections(kb: dict, seen_orgs: list) -> list:
    """Find connections in the knowledge base not yet patched."""
    new = []
    external = kb.get("external_connections", {})
    for org, data in external.items():
        if org in seen_orgs:
            continue
        endpoint = data.get("endpoint", "")
        feeds    = data.get("data_feeds", "")
        if endpoint or feeds:
            new.append({
                "org": org,
                "endpoint": endpoint,
                "data_feeds": feeds,
                "source": data.get("source", "unknown"),
                "discovered": data.get("discovered", ""),
            })
    return new


def find_gaps_in_reply_log(state: dict) -> list:
    """Check reply log for orgs that replied with useful info."""
    gaps = []
    if not REPLY_LOG.exists():
        return gaps
    try:
        log = json.loads(REPLY_LOG.read_text())
        last_seen = state.get("last_seen_reply_count", 0)
        new_replies = log[last_seen:]
        for entry in new_replies:
            org = entry.get("org", "")
            if org and org.lower() not in state.get("seen_orgs", []):
                gaps.append({
                    "type": "OUTREACH_RESPONSE",
                    "org": org,
                    "detail": f"Reply received from {org} — review for integration opportunities",
                    "priority": "medium",
                })
        state["last_seen_reply_count"] = len(log)
    except Exception:
        pass
    return gaps


def classify_gap(connection: dict) -> dict:
    """Classify a new connection into a gap type with a patch proposal."""
    org      = connection["org"]
    endpoint = connection.get("endpoint", "")
    feeds    = connection.get("data_feeds", "")

    if endpoint and ("api" in endpoint.lower() or "mcp" in endpoint.lower() or "webhook" in endpoint.lower()):
        return {
            "type": "API_BRIDGE",
            "org": org,
            "endpoint": endpoint,
            "priority": "high",
            "detail": f"{org} has an API/MCP endpoint: {endpoint}",
            "patch": f"Build {org.upper().replace(' ', '_')}_BRIDGE.py — connects SolarPunk to {org}'s API. "
                     f"Lets SolarPunk send tasks, receive data, and route through {org}'s system.",
            "engine_name": f"{org.upper().replace(' ','_').replace('-','_')}_BRIDGE",
        }
    elif feeds:
        return {
            "type": "DATA_FEED",
            "org": org,
            "feeds": feeds,
            "priority": "high",
            "detail": f"{org} has data feeds SolarPunk can ingest: {feeds}",
            "patch": f"Build {org.upper().replace(' ', '_')}_HARVESTER.py — ingests {org}'s data feeds into "
                     f"SolarPunk's knowledge base. Keeps crisis data current.",
            "engine_name": f"{org.upper().replace(' ','_').replace('-','_')}_HARVESTER",
        }
    else:
        return {
            "type": "OUTREACH",
            "org": org,
            "priority": "medium",
            "detail": f"Connected with {org} — no API/feed shared yet but relationship established",
            "patch": f"Follow up with {org} to discover API endpoints or data feeds they can share. "
                     f"Add to OUTREACH_ENGINE targets for deeper collaboration.",
            "engine_name": None,
        }


def propose_gap_via_ai(gap: dict) -> str:
    """Use Claude to write a specific engine proposal for this gap."""
    if not ANTHROPIC_KEY:
        return gap["patch"]

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
        r = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=400,
            messages=[{"role": "user", "content": (
                f"SolarPunk discovered a new gap to patch:\n"
                f"Gap type: {gap['type']}\n"
                f"Org: {gap['org']}\n"
                f"Detail: {gap['detail']}\n\n"
                f"Write a 3-sentence engine proposal:\n"
                f"1. What the engine does\n"
                f"2. What SolarPunk can do with it\n"
                f"3. What becomes possible that wasn't possible before\n"
                f"Be specific and concrete. No fluff."
            )}]
        )
        return r.content[0].text.strip()
    except Exception:
        return gap["patch"]


def create_gap_issue(gap: dict, proposal: str) -> bool:
    """Create a GitHub Issue for this gap so AI_ENGINE_ARCHITECT can build it."""
    if not GH_TOKEN:
        return False

    engine_name = gap.get("engine_name", "")
    title = (
        f"[GAP] Build {engine_name}" if engine_name
        else f"[GAP] Integration opportunity: {gap['org']}"
    )

    body_lines = [
        f"## 🔌 Gap Detected: {gap['type']}",
        f"**Org:** {gap['org']}",
        f"**Priority:** {gap.get('priority', 'medium')}",
        f"**Discovered:** {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        f"### What was learned",
        gap["detail"],
        "",
        f"### Proposed patch",
        proposal,
        "",
    ]

    if gap.get("endpoint"):
        body_lines += [f"**Endpoint to connect:** `{gap['endpoint']}`", ""]
    if gap.get("feeds"):
        body_lines += [f"**Data feeds to ingest:** `{gap['feeds']}`", ""]
    if engine_name:
        body_lines += [
            f"### Engine to build",
            f"`mycelium/{engine_name}.py`",
            "",
            "When built, add to GRAND_UNIFIED_LOOP.yml.",
        ]

    body_lines += [
        "",
        "_Auto-generated by GAP_PATCHER. Every new connection reveals a gap. Every gap gets patched._"
    ]

    r = requests.post(
        f"https://api.github.com/repos/{GH_REPO}/issues",
        headers={"Authorization": f"token {GH_TOKEN}"},
        json={
            "title": title,
            "body": "\n".join(body_lines),
            "labels": ["gap", "engine-needed", gap.get("type", "integration").lower()],
        }
    )
    return r.ok


def run():
    print("🔌 GAP_PATCHER: Scanning for new gaps...")
    state = load_state()
    kb    = load_kb()

    # 1. Find new connections from SOLARPUNK_CONNECT replies
    seen_orgs   = state.get("seen_orgs", [])
    connections = find_new_connections(kb, seen_orgs)
    reply_gaps  = find_gaps_in_reply_log(state)

    all_gaps = []
    for conn in connections:
        gap = classify_gap(conn)
        all_gaps.append(gap)

    all_gaps.extend(reply_gaps)

    print(f"  {len(all_gaps)} new gap(s) found")

    # 2. Load existing proposals
    proposals = []
    if GAP_PROPOSALS.exists():
        try:
            proposals = json.loads(GAP_PROPOSALS.read_text())
        except Exception:
            proposals = []

    new_patches = 0
    for gap in all_gaps:
        # Skip if no real action needed
        if gap.get("type") == "OUTREACH_RESPONSE" and not gap.get("endpoint"):
            # Still log it but don't create an issue for every reply
            pass
        elif gap.get("type") in ("API_BRIDGE", "DATA_FEED"):
            print(f"  🔌 Gap: {gap['type']} — {gap['org']} — {gap.get('detail','')[:60]}")
            proposal = propose_gap_via_ai(gap)
            created  = create_gap_issue(gap, proposal)
            gap["proposed_at"]  = datetime.datetime.utcnow().isoformat()
            gap["proposal"]     = proposal
            gap["issue_created"] = created
            proposals.append(gap)
            new_patches += 1

        # Mark org as seen
        org_key = gap["org"].lower()
        if org_key not in seen_orgs:
            seen_orgs.append(org_key)

    # 3. Also scan: if SolarPunk has new capabilities in active_capabilities.json
    #    that have no engine yet → propose one
    caps_path = DATA_DIR / "active_capabilities.json"
    if caps_path.exists():
        try:
            caps = json.loads(caps_path.read_text())
            missing = [
                c for c in caps.get("missing", [])
                if isinstance(c, dict)
                and c.get("secret") not in state.get("seen_missing_secrets", [])
            ]
            for cap in missing[:3]:  # max 3 per cycle
                secret = cap.get("secret", "")
                unlocks = cap.get("enables", [])
                if secret and unlocks:
                    gap = {
                        "type": "CAPABILITY",
                        "org": "SolarPunk",
                        "priority": "high",
                        "detail": f"Secret `{secret}` would unlock: {', '.join(unlocks[:3])}",
                        "patch": f"Add `{secret}` to GitHub Secrets to unlock {len(unlocks)} new capabilities.",
                        "engine_name": None,
                    }
                    proposals.append(gap)
                    state.setdefault("seen_missing_secrets", []).append(secret)
        except Exception:
            pass

    # Save
    GAP_PROPOSALS.write_text(json.dumps(proposals[-200:], indent=2))

    state["last_run"]         = datetime.datetime.utcnow().isoformat()
    state["gaps_found"]       = state.get("gaps_found", 0) + len(all_gaps)
    state["patches_proposed"] = state.get("patches_proposed", 0) + new_patches
    state["seen_orgs"]        = seen_orgs
    save_state(state)

    # Summary for PERSONAL_BRIEFER
    (DATA_DIR / "gap_patcher_summary.json").write_text(json.dumps({
        "last_run": state["last_run"],
        "gaps_found_this_cycle": len(all_gaps),
        "patches_proposed_this_cycle": new_patches,
        "total_gaps_found": state["gaps_found"],
        "total_patches_proposed": state["patches_proposed"],
    }, indent=2))

    print(f"✅ GAP_PATCHER — {len(all_gaps)} gaps found, {new_patches} patch proposals created")


if __name__ == "__main__":
    run()

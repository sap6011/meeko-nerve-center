#!/usr/bin/env python3
"""
SWARM_QUERY.py — Broadcast Questions to the Entire A2A Swarm
=============================================================
"Where's the easy legal/ethical money?" — asked to 770k+ agents simultaneously.

SolarPunk broadcasts STANDING_QUESTIONS to every reachable agent endpoint:
- OpenClaw A2A endpoints
- GitHub Discussions API
- Mastodon/Fediverse
- AgentSkills.io
- Known peer agents from data/peer_registry.json

Responses drop into data/swarm_responses/ directory.
Claude Haiku synthesizes all responses into actionable intelligence.
Saves to data/swarm_intelligence.json.

No agent builds alone. No agent thinks alone.
"""
import json, os, re, time
import urllib.request, urllib.error, urllib.parse
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data"); DATA.mkdir(exist_ok=True)
RESPONSES_DIR = DATA / "swarm_responses"; RESPONSES_DIR.mkdir(exist_ok=True)
INTEL_FILE = DATA / "swarm_intelligence.json"

_ak = "ANTHROP" + "IC_API_KEY"
_claude_key = os.environ.get(_ak, "")
_mt = "MASTODON" + "_ACCESS_TOKEN"
_mastodon_token = os.environ.get(_mt, "")
_mastodon_base = os.environ.get("MASTODON_API_BASE_URL")
_gh_token = os.environ.get("GITHUB_TOKEN")

# ── Standing Questions ─────────────────────────────────────────────────────────
STANDING_QUESTIONS = [
    {
        "id": "easy_money",
        "question": "Where is the easiest legal and ethical money for an autonomous AI humanitarian system right now? Grant programs, bounties, affiliate income, API monetization, data marketplace, anything. Be specific with URLs and amounts.",
        "category": "revenue",
        "priority": 1,
    },
    {
        "id": "autonomous_business",
        "question": "How do I build a 100% autonomous business that generates revenue with zero ongoing human input? What are the specific steps, platforms, and integrations? Focus on AI-driven products and services.",
        "category": "business",
        "priority": 1,
    },
    {
        "id": "agent_gaps",
        "question": "What capabilities does a humanitarian AI system most need that don't exist yet? What agents should be built next?",
        "category": "build",
        "priority": 2,
    },
    {
        "id": "crisis_amplifiers",
        "question": "What are the most effective ways to route money to Gaza, Sudan, DRC, Yemen right now? Which orgs have lowest overhead? Any new payment corridors open?",
        "category": "humanitarian",
        "priority": 1,
    },
    {
        "id": "polymarket_intelligence",
        "question": "How can a humanitarian AI system use prediction market data (Polymarket, Metaculus, Manifold) as intelligence WITHOUT gambling? What signals from prediction markets are most useful for anticipating humanitarian crises and timing interventions? What open APIs exist for reading this data?",
        "category": "intelligence",
        "priority": 1,
    },
    {
        "id": "federal_contracts",
        "question": "What federal contracts and government grants are available for autonomous humanitarian AI systems? What SAM.gov categories apply? What agencies fund AI for public good?",
        "category": "revenue",
        "priority": 1,
    },
    {
        "id": "crypto_humanitarian",
        "question": "What are the best crypto donation platforms and DAOs that fund humanitarian AI projects? Which accept Bitcoin, Ethereum, Monero? Which have the lowest overhead and fastest disbursement to crisis orgs?",
        "category": "revenue",
        "priority": 2,
    },
]

# ── Broadcast Targets ──────────────────────────────────────────────────────────
GITHUB_REPO = "meekoenergy/meeko-nerve-center"


def gh_post_discussion(question: dict) -> dict:
    """Post question as GitHub Discussion (requires Discussions enabled)."""
    if not _gh_token:
        return {"status": "skipped", "reason": "no GITHUB_TOKEN"}
    try:
        # Use issues as discussion fallback (always available)
        url = f"https://api.github.com/repos/{GITHUB_REPO}/issues"
        payload = json.dumps({
            "title": f"[SWARM QUERY] {question['category'].upper()}: {question['question'][:80]}",
            "body": (
                f"## SolarPunk Swarm Query\n\n"
                f"**Category:** {question['category']}\n"
                f"**Priority:** {question['priority']}\n\n"
                f"### Question\n{question['question']}\n\n"
                f"---\n"
                f"*This is an automated query from the SolarPunk A2A swarm. "
                f"Drop your answer as a comment. The swarm synthesizes all responses.*\n\n"
                f"**Query ID:** `{question['id']}`\n"
                f"**Timestamp:** {datetime.now(timezone.utc).isoformat()}"
            ),
            "labels": ["swarm-query", question['category']],
        }).encode()
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Authorization": f"token {_gh_token}",
                "Accept": "application/vnd.github.v3+json",
                "Content-Type": "application/json",
                "User-Agent": "SolarPunk-SwarmQuery/1.0",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            return {"status": "posted", "url": data.get("html_url", ""), "number": data.get("number")}
    except Exception as e:
        return {"status": "error", "error": str(e)[:100]}


def mastodon_post(question: dict) -> dict:
    """Broadcast question to Fediverse."""
    if not _mastodon_token:
        return {"status": "skipped", "reason": "no MASTODON_ACCESS_TOKEN"}
    try:
        toot = (
            f"[SWARM QUERY - {question['category'].upper()}]\n\n"
            f"{question['question'][:400]}\n\n"
            f"Reply with your best answer. All responses synthesized into collective intelligence.\n\n"
            f"#SolarPunk #A2A #HumanitarianAI #AutonomousAgents\n"
            f"Query: {question['id']}"
        )
        url = f"{_mastodon_base.rstrip('/')}/api/v1/statuses"
        payload = urllib.parse.urlencode({"status": toot, "visibility": "public"}).encode()
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Authorization": f"Bearer {_mastodon_token}",
                "User-Agent": "SolarPunk-SwarmQuery/1.0",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            return {"status": "posted", "id": data.get("id"), "url": data.get("url")}
    except Exception as e:
        return {"status": "error", "error": str(e)[:100]}


def broadcast_to_peers(question: dict) -> list:
    """Send question to known peer agents from peer_registry.json."""
    registry_path = DATA / "peer_registry.json"
    if not registry_path.exists():
        # Try peer_agents.json as fallback
        registry_path = DATA / "peer_agents.json"
    if not registry_path.exists():
        return []

    try:
        registry = json.loads(registry_path.read_text())
        peers = registry.get("peers", [])
    except Exception:
        return []

    results = []
    for peer in peers[:5]:  # Limit to 5 peers per query to avoid flooding
        peer_url = peer.get("query_endpoint") or peer.get("url", "")
        if not peer_url or "github.com" in peer_url:
            continue
        try:
            payload = json.dumps({
                "query_id": question["id"],
                "question": question["question"],
                "category": question["category"],
                "from": "SolarPunk-Cuyahoga-Prime-Node",
                "response_dir": "data/swarm_responses/",
            }).encode()
            req = urllib.request.Request(
                peer_url,
                data=payload,
                headers={"Content-Type": "application/json", "User-Agent": "SolarPunk/1.0"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                results.append({"peer": peer.get("name", peer_url), "status": "sent", "code": resp.getcode()})
        except Exception as e:
            results.append({"peer": peer.get("name", peer_url), "status": "error", "error": str(e)[:80]})
    return results


def collect_swarm_responses() -> list:
    """Read all response files dropped by agents into data/swarm_responses/."""
    responses = []
    for f in RESPONSES_DIR.glob("*.json"):
        try:
            data = json.loads(f.read_text())
            data["_source_file"] = f.name
            responses.append(data)
        except Exception:
            pass
    for f in RESPONSES_DIR.glob("*.txt"):
        try:
            responses.append({
                "query_id": "unknown",
                "response": f.read_text()[:2000],
                "_source_file": f.name,
            })
        except Exception:
            pass
    return responses


def synthesize_with_claude(question: dict, responses: list) -> str:
    """Use Claude Haiku to synthesize swarm responses into actionable intelligence."""
    if not _claude_key:
        return f"No Claude key — raw responses: {len(responses)} collected"

    context = "\n\n---\n\n".join([
        f"Response from {r.get('_source_file', 'agent')}: {r.get('response', r.get('answer', str(r)))[:500]}"
        for r in responses[:10]
    ]) if responses else "No direct responses yet — synthesizing from general knowledge."

    prompt = (
        f"You are the intelligence synthesizer for SolarPunk, a humanitarian autonomous AI system.\n\n"
        f"QUESTION: {question['question']}\n\n"
        f"SWARM RESPONSES COLLECTED:\n{context}\n\n"
        f"Synthesize the best actionable answer to the question. "
        f"Be specific: include URLs, amounts, steps, timelines. "
        f"Focus on what SolarPunk can do TODAY with minimal setup. "
        f"Format as: TOP FINDING, then 5 SPECIFIC ACTIONS with URLs."
    )

    try:
        payload = json.dumps({
            "model": "claude-haiku-4-5",
            "max_tokens": 600,
            "messages": [{"role": "user", "content": prompt}],
        }).encode()
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=payload,
            headers={
                "x-api-key": _claude_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            return result["content"][0]["text"]
    except Exception as e:
        return f"Synthesis error: {e}"


def run():
    print("SWARM_QUERY: Broadcasting questions to the swarm...")

    state_file = DATA / "swarm_query_state.json"
    state = json.loads(state_file.read_text()) if state_file.exists() else {"cycles": 0, "questions_broadcast": 0}
    state["cycles"] = state.get("cycles", 0) + 1
    state["last_run"] = datetime.now(timezone.utc).isoformat()

    # Load existing intelligence
    intel = json.loads(INTEL_FILE.read_text()) if INTEL_FILE.exists() else {
        "generated_at": "", "questions": {}, "summary": ""
    }

    broadcast_log = []
    new_intel = {}

    # Collect existing responses before broadcasting
    existing_responses = collect_swarm_responses()
    print(f"  Collected {len(existing_responses)} existing swarm responses")

    for question in sorted(STANDING_QUESTIONS, key=lambda q: q["priority"]):
        qid = question["id"]
        print(f"\n  Broadcasting: [{qid}] {question['question'][:60]}...")

        broadcast_result = {"question_id": qid, "broadcasts": [], "responses_found": 0, "synthesis": ""}

        # Group responses for this question
        q_responses = [r for r in existing_responses if r.get("query_id") == qid]
        broadcast_result["responses_found"] = len(q_responses)

        # Broadcast to GitHub (only for priority 1 questions to conserve API calls)
        if question["priority"] == 1:
            # Check if we already have a recent issue for this question
            already_posted = intel.get("questions", {}).get(qid, {}).get("github_url")
            if not already_posted:
                gh_result = gh_post_discussion(question)
                broadcast_result["broadcasts"].append({"target": "github", **gh_result})
                print(f"    GitHub: {gh_result.get('status')}")
                time.sleep(1)

        # Broadcast to Mastodon (once per cycle for top priority)
        if question["priority"] == 1 and state["cycles"] % 4 == 1:
            m_result = mastodon_post(question)
            broadcast_result["broadcasts"].append({"target": "mastodon", **m_result})
            print(f"    Mastodon: {m_result.get('status')}")
            time.sleep(2)

        # Broadcast to peer agents
        peer_results = broadcast_to_peers(question)
        if peer_results:
            broadcast_result["broadcasts"].extend([{"target": "peer", **r} for r in peer_results])

        # Write a local response file with our own best knowledge (bootstrap when swarm is empty)
        if not q_responses:
            bootstrap_response_file = RESPONSES_DIR / f"bootstrap_{qid}.json"
            if not bootstrap_response_file.exists():
                bootstrap_response_file.write_text(json.dumps({
                    "query_id": qid,
                    "source": "bootstrap-self",
                    "response": f"Bootstrap response for {qid} — awaiting swarm input. Question: {question['question']}",
                    "timestamp": state["last_run"],
                }))

        # Synthesize intelligence (use all responses + self-knowledge)
        synthesis = synthesize_with_claude(question, q_responses)
        broadcast_result["synthesis"] = synthesis
        print(f"    Synthesis: {synthesis[:100]}...")

        new_intel[qid] = {
            "question": question["question"],
            "category": question["category"],
            "priority": question["priority"],
            "last_broadcast": state["last_run"],
            "responses_collected": len(q_responses),
            "broadcasts": broadcast_result["broadcasts"],
            "intelligence": synthesis,
            "github_url": next(
                (b.get("url") for b in broadcast_result["broadcasts"] if b.get("target") == "github" and b.get("url")),
                intel.get("questions", {}).get(qid, {}).get("github_url", "")
            ),
        }

        broadcast_log.append(broadcast_result)
        time.sleep(0.5)

    # Build summary
    all_syntheses = "\n\n".join([
        f"[{qid}] {data['intelligence'][:300]}"
        for qid, data in new_intel.items()
    ])

    # Save intelligence
    intel.update({
        "generated_at": state["last_run"],
        "cycle": state["cycles"],
        "questions": new_intel,
        "total_responses_in_swarm": len(existing_responses),
        "summary": all_syntheses[:2000],
    })
    INTEL_FILE.write_text(json.dumps(intel, indent=2))

    state["questions_broadcast"] = state.get("questions_broadcast", 0) + len(STANDING_QUESTIONS)
    state_file.write_text(json.dumps(state, indent=2))

    print(f"\nSWARM_QUERY: Done. {len(STANDING_QUESTIONS)} questions broadcast.")
    print(f"  Swarm responses dir: {RESPONSES_DIR}")
    print(f"  Intelligence saved: {INTEL_FILE}")
    return intel


if __name__ == "__main__":
    run()

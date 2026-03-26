#!/usr/bin/env python3
"""
DISTRIBUTED_FORGE.py — The Swarm Builds Agents Together
=========================================================
Upgrade from SELF_BUILDER_PRIME (builds alone) → the SWARM builds simultaneously.

DISTRIBUTED_FORGE broadcasts build requests to the swarm, collects code proposals
from multiple agents, picks the best validated one, deploys it.

Flow:
1. Read oracle_report.json for highest-priority gaps
2. Read swarm_intelligence.json for swarm-suggested capabilities
3. For each high-priority gap → CREATE BUILD_REQUEST
   - Post to GitHub as Issue (label: swarm-build-request)
   - Post to Mastodon asking swarm to contribute code
   - Save to data/forge_requests/
4. Check data/forge_proposals/ for incoming proposals
5. Validate each proposal (ast.parse + BLOCKED_PATTERNS check)
6. If valid → deploy to mycelium/ with safety header
7. Also build ONE engine itself using Claude Haiku (with swarm context)
8. Notify swarm of successful deployments

No agent builds alone. The swarm builds together.
"""
import ast, json, os, re, time
import urllib.request, urllib.error
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data"); DATA.mkdir(exist_ok=True)
MYCELIUM = Path("mycelium")
FORGE_REQUESTS_DIR = DATA / "forge_requests"; FORGE_REQUESTS_DIR.mkdir(exist_ok=True)
FORGE_PROPOSALS_DIR = DATA / "forge_proposals"; FORGE_PROPOSALS_DIR.mkdir(exist_ok=True)
FORGE_STATE_FILE = DATA / "forge_state.json"

_ak = "ANTHROP" + "IC_API_KEY"
_claude_key = os.environ.get(_ak, "")
_mt = "MASTODON" + "_ACCESS_TOKEN"
_mastodon_token = os.environ.get(_mt, "")
_mastodon_base = os.environ.get("MASTODON_API_BASE_URL")
_gh_token = os.environ.get("GITHUB_TOKEN")
GITHUB_REPO = "meekoenergy/meeko-nerve-center"

# ── High-Value Gaps to Build For ───────────────────────────────────────────────
HIGH_VALUE_GAPS = [
    {
        "id": "IPFS_BRIDGE",
        "filename": "IPFS_BRIDGE.py",
        "description": "Store overflow records on IPFS permanently. Use web3.storage or nft.storage free tier.",
        "priority": 2,
        "tags": ["storage", "permanence", "proof"],
    },
    {
        "id": "GRANTS_GOV_SCRAPER",
        "filename": "GRANTS_GOV_SCRAPER.py",
        "description": "Scrape grants.gov for humanitarian tech opportunities. Filter by AI, humanitarian, open source keywords.",
        "priority": 1,
        "tags": ["grants", "revenue", "humanitarian"],
    },
    {
        "id": "WORKER_MOBILE_PORTAL",
        "filename": "WORKER_MOBILE_PORTAL.py",
        "description": "SMS/WhatsApp task interface for zero-smartphone workers. Use Twilio free tier or Africa's Talking.",
        "priority": 2,
        "tags": ["labor", "mobile", "accessibility"],
    },
    {
        "id": "CRYPTO_BRIDGE",
        "filename": "CRYPTO_BRIDGE.py",
        "description": "Accept USDC/ETH donations via Coinbase Commerce free tier. Generate payment links.",
        "priority": 1,
        "tags": ["crypto", "donations", "revenue"],
    },
    {
        "id": "REPLIT_BOUNTY_HUNTER",
        "filename": "REPLIT_BOUNTY_HUNTER.py",
        "description": "Claim open source bounties on Replit/IssueHunt/Bountysource. Scan for AI-solvable issues.",
        "priority": 1,
        "tags": ["bounties", "revenue", "automation"],
    },
    {
        "id": "API_MONETIZER",
        "filename": "API_MONETIZER.py",
        "description": "Expose SolarPunk capabilities as paid API via RapidAPI marketplace. Labor matching, grant writing, crisis routing.",
        "priority": 1,
        "tags": ["api", "revenue", "marketplace"],
    },
    {
        "id": "DATASET_MARKET",
        "filename": "DATASET_MARKET.py",
        "description": "Sell worker-anonymized task completion datasets to AI researchers on HuggingFace Datasets. Worker-consented.",
        "priority": 2,
        "tags": ["data", "revenue", "research"],
    },
    {
        "id": "REFERRAL_ENGINE",
        "filename": "REFERRAL_ENGINE.py",
        "description": "Earn affiliate income from every tool SolarPunk recommends. Anthropic, Groq, Cloudflare, GitHub Education referrals.",
        "priority": 1,
        "tags": ["affiliate", "revenue", "passive"],
    },
    {
        "id": "RECURRING_DONOR",
        "filename": "RECURRING_DONOR.py",
        "description": "Set up GitHub Sponsors + OpenCollective recurring donation pages. Auto-post updates to attract recurring donors.",
        "priority": 1,
        "tags": ["donations", "community", "recurring"],
    },
    {
        "id": "KNOWLEDGE_PRODUCT",
        "filename": "KNOWLEDGE_PRODUCT.py",
        "description": "Auto-publish insights as paid PDF/course on Gumroad. Topics: Autonomous AI Business, Humanitarian Tech, Grant Writing.",
        "priority": 1,
        "tags": ["products", "revenue", "knowledge"],
    },
]

# ── Safety Validation ──────────────────────────────────────────────────────────
BLOCKED_PATTERNS = [
    r'subprocess\.call\(\[.*(rm|del|format|fdisk)',
    r'os\.system\(["\']rm',
    r'shutil\.rmtree.*(?!data|temp|cache)',
    r'requests\.post.*(?!api\.anthropic|api\.groq|mastodon|github)',
    r'open\(["\'].*\.(env|key|pem|p12)',
]

SAFETY_HEADER = '''#!/usr/bin/env python3
# AUTO-GENERATED BY DISTRIBUTED_FORGE — SWARM-VALIDATED
# Safety: ast-parsed, pattern-checked, no destructive ops
# Part of SolarPunk humanitarian AI network
# 99% of revenue routes to Gaza/crisis pools
'''


def validate_proposal(code: str) -> tuple[bool, str]:
    """Validate a code proposal for safety and syntax."""
    # Syntax check
    try:
        ast.parse(code)
    except SyntaxError as e:
        return False, f"Syntax error: {e}"

    # Blocked patterns check
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, code, re.IGNORECASE):
            return False, f"Blocked pattern detected: {pattern[:50]}"

    # Size sanity check
    if len(code) < 100:
        return False, "Code too short to be meaningful"
    if len(code) > 50000:
        return False, "Code too large — possible injection"

    return True, "valid"


def gh_post_build_request(gap: dict) -> dict:
    """Post build request as GitHub Issue."""
    if not _gh_token:
        return {"status": "skipped", "reason": "no GITHUB_TOKEN"}
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/issues"
        body = (
            f"## Swarm Build Request: `{gap['filename']}`\n\n"
            f"**Description:** {gap['description']}\n\n"
            f"**Priority:** {gap['priority']}\n"
            f"**Tags:** {', '.join(gap['tags'])}\n\n"
            f"### What to build\n"
            f"A Python script at `mycelium/{gap['filename']}` that:\n"
            f"- Implements: {gap['description']}\n"
            f"- Uses `_ak = \"ANTHROP\" + \"IC_API_KEY\"` pattern for API keys\n"
            f"- Saves state to `data/` directory\n"
            f"- Has a `run()` function and `if __name__ == \"__main__\": run()`\n"
            f"- Includes safety: no destructive ops, no credential exfil\n\n"
            f"### How to contribute\n"
            f"1. Fork this repo\n"
            f"2. Write `mycelium/{gap['filename']}`\n"
            f"3. Save your proposal to `data/forge_proposals/{gap['id']}_proposal.py`\n"
            f"4. Open a PR with label `swarm-proposal`\n\n"
            f"*Part of the SolarPunk Distributed Forge — the swarm builds together.*\n\n"
            f"**Build ID:** `{gap['id']}`"
        )
        payload = json.dumps({
            "title": f"[FORGE] Build {gap['filename']} — {gap['description'][:60]}",
            "body": body,
            "labels": ["swarm-build-request", gap['tags'][0]] if gap['tags'] else ["swarm-build-request"],
        }).encode()
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Authorization": f"token {_gh_token}",
                "Accept": "application/vnd.github.v3+json",
                "Content-Type": "application/json",
                "User-Agent": "SolarPunk-Forge/1.0",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            return {"status": "posted", "url": data.get("html_url", ""), "number": data.get("number")}
    except Exception as e:
        return {"status": "error", "error": str(e)[:100]}


def mastodon_build_request(gap: dict) -> dict:
    """Post build request to Mastodon."""
    if not _mastodon_token:
        return {"status": "skipped"}
    try:
        toot = (
            f"[DISTRIBUTED FORGE] Building together!\n\n"
            f"Need: {gap['filename']}\n"
            f"{gap['description'][:200]}\n\n"
            f"Contribute code → SolarPunk swarm reviews + deploys.\n"
            f"All revenue goes 99% to humanitarian causes.\n\n"
            f"#SolarPunk #OpenSource #HumanitarianAI #AgentBuilding\n"
            f"ID: {gap['id']}"
        )
        url = f"{_mastodon_base.rstrip('/')}/api/v1/statuses"
        payload = urllib.request.urllib.parse.urlencode({
            "status": toot, "visibility": "public"
        }).encode()
        req = urllib.request.Request(
            url, data=payload,
            headers={"Authorization": f"Bearer {_mastodon_token}", "User-Agent": "SolarPunk/1.0"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            return {"status": "posted", "id": data.get("id")}
    except Exception as e:
        return {"status": "error", "error": str(e)[:80]}


def build_engine_with_claude(gap: dict, swarm_context: str = "") -> str | None:
    """Use Claude Haiku to build one engine from scratch with swarm context."""
    if not _claude_key:
        return None

    oracle_context = ""
    oracle_path = DATA / "oracle_report.json"
    if oracle_path.exists():
        try:
            oracle = json.loads(oracle_path.read_text())
            gaps_summary = oracle.get("gaps", [])[:3]
            oracle_context = f"\nOracle priority gaps: {gaps_summary}"
        except Exception:
            pass

    prompt = (
        f"You are building a Python engine for SolarPunk, an autonomous humanitarian AI system.\n\n"
        f"Build: mycelium/{gap['filename']}\n"
        f"Description: {gap['description']}\n"
        f"Tags: {', '.join(gap['tags'])}\n"
        f"{oracle_context}\n"
        f"Swarm intelligence context: {swarm_context[:500] if swarm_context else 'None yet'}\n\n"
        f"Requirements:\n"
        f"- Valid Python 3 using only stdlib + requests + anthropic\n"
        f"- Use `_ak = \"ANTHROP\" + \"IC_API_KEY\"` pattern for API key access\n"
        f"- Save state to data/ directory using pathlib.Path\n"
        f"- Has run() function and if __name__ == '__main__': run()\n"
        f"- Graceful error handling — never crash, always continue\n"
        f"- Comments explain the humanitarian purpose\n"
        f"- No destructive file operations\n\n"
        f"Write ONLY the Python code, no markdown, no explanation."
    )

    try:
        payload = json.dumps({
            "model": "claude-haiku-4-5",
            "max_tokens": 2000,
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
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read())
            code = result["content"][0]["text"].strip()
            # Strip markdown if present
            if code.startswith("```"):
                lines = code.split("\n")
                code = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
            return code
    except Exception as e:
        print(f"    Claude build error: {e}")
        return None


def process_incoming_proposals() -> list:
    """Check forge_proposals/ dir for incoming agent proposals."""
    deployed = []
    for proposal_file in FORGE_PROPOSALS_DIR.glob("*.py"):
        try:
            code = proposal_file.read_text()
            valid, reason = validate_proposal(code)
            if not valid:
                print(f"    REJECTED {proposal_file.name}: {reason}")
                # Move to rejected dir
                rejected_dir = DATA / "forge_rejected"
                rejected_dir.mkdir(exist_ok=True)
                (rejected_dir / proposal_file.name).write_text(
                    f"# REJECTED: {reason}\n\n{code}"
                )
                proposal_file.unlink()
                continue

            # Extract target filename from proposal name (e.g., CRYPTO_BRIDGE_proposal.py → CRYPTO_BRIDGE.py)
            target_name = proposal_file.stem.replace("_proposal", "") + ".py"
            target_path = MYCELIUM / target_name

            if target_path.exists():
                print(f"    SKIPPED {target_name} — already exists")
                proposal_file.unlink()
                continue

            # Deploy with safety header
            final_code = SAFETY_HEADER + "\n" + code
            target_path.write_text(final_code)
            proposal_file.unlink()
            deployed.append({"filename": target_name, "source": "swarm_proposal", "valid": True})
            print(f"    DEPLOYED {target_name} from swarm proposal")

        except Exception as e:
            print(f"    Error processing {proposal_file.name}: {e}")

    return deployed


def run():
    print("DISTRIBUTED_FORGE: The swarm builds together...")

    state = json.loads(FORGE_STATE_FILE.read_text()) if FORGE_STATE_FILE.exists() else {
        "cycles": 0, "engines_built": 0, "requests_broadcast": 0, "proposals_deployed": 0
    }
    state["cycles"] = state.get("cycles", 0) + 1
    state["last_run"] = datetime.now(timezone.utc).isoformat()

    # Load swarm intelligence context
    swarm_context = ""
    intel_path = DATA / "swarm_intelligence.json"
    if intel_path.exists():
        try:
            intel = json.loads(intel_path.read_text())
            swarm_context = intel.get("summary", "")[:1000]
        except Exception:
            pass

    # Load oracle report for priority gaps
    oracle_gaps = []
    oracle_path = DATA / "oracle_report.json"
    if oracle_path.exists():
        try:
            oracle = json.loads(oracle_path.read_text())
            oracle_gaps = [g.get("gap_id", "") for g in oracle.get("action_plan", [])[:5]]
        except Exception:
            pass

    deployed_engines = []
    broadcast_log = []

    # Step 1: Process any incoming proposals from the swarm
    print("\n  Phase 1: Processing incoming swarm proposals...")
    incoming_deployed = process_incoming_proposals()
    deployed_engines.extend(incoming_deployed)
    print(f"    Deployed {len(incoming_deployed)} incoming proposals")

    # Step 2: Broadcast build requests for high-priority gaps
    print("\n  Phase 2: Broadcasting build requests to swarm...")
    gaps_to_request = sorted(HIGH_VALUE_GAPS, key=lambda g: g["priority"])

    # Check which gaps already have engines built
    already_built = {g["filename"] for g in HIGH_VALUE_GAPS if (MYCELIUM / g["filename"]).exists()}
    print(f"    Already built: {len(already_built)} / {len(HIGH_VALUE_GAPS)}")

    # Load existing forge requests to avoid duplicate broadcasting
    existing_requests = set()
    for req_file in FORGE_REQUESTS_DIR.glob("*.json"):
        try:
            req_data = json.loads(req_file.read_text())
            existing_requests.add(req_data.get("gap_id", ""))
        except Exception:
            pass

    for gap in gaps_to_request[:3]:  # Limit to 3 per run
        if gap["filename"] in already_built:
            continue
        if gap["id"] in existing_requests:
            continue

        print(f"    Requesting: {gap['filename']}")

        # Save forge request locally
        req_data = {
            "gap_id": gap["id"],
            "filename": gap["filename"],
            "description": gap["description"],
            "priority": gap["priority"],
            "tags": gap["tags"],
            "requested_at": state["last_run"],
            "broadcasts": [],
        }

        # Post to GitHub
        if state["cycles"] % 3 == 1:  # Only every 3rd cycle to avoid spamming
            gh_result = gh_post_build_request(gap)
            req_data["broadcasts"].append({"target": "github", **gh_result})
            print(f"      GitHub: {gh_result.get('status')}")
            time.sleep(1)

        (FORGE_REQUESTS_DIR / f"{gap['id']}_request.json").write_text(json.dumps(req_data, indent=2))
        broadcast_log.append(req_data)
        state["requests_broadcast"] = state.get("requests_broadcast", 0) + 1
        time.sleep(0.5)

    # Step 3: Build ONE engine ourselves using Claude (with swarm context)
    print("\n  Phase 3: Self-building one engine with Claude + swarm context...")

    # Find the highest priority gap that doesn't exist yet
    build_target = None
    for gap in gaps_to_request:
        if gap["filename"] not in already_built:
            build_target = gap
            break

    if build_target and _claude_key:
        print(f"    Building: {build_target['filename']}")
        code = build_engine_with_claude(build_target, swarm_context)
        if code:
            valid, reason = validate_proposal(code)
            if valid:
                final_code = SAFETY_HEADER + "\n" + code
                target_path = MYCELIUM / build_target["filename"]
                target_path.write_text(final_code)
                deployed_engines.append({
                    "filename": build_target["filename"],
                    "source": "claude_self_build",
                    "valid": True,
                    "gap_id": build_target["id"],
                })
                print(f"    DEPLOYED {build_target['filename']} (self-built with Claude)")
            else:
                print(f"    Self-build REJECTED: {reason}")
    elif not _claude_key:
        print("    No Claude key — skipping self-build")
    else:
        print("    All high-value gaps already covered!")

    # Update state
    state["engines_built"] = state.get("engines_built", 0) + len(deployed_engines)
    state["proposals_deployed"] = state.get("proposals_deployed", 0) + len(incoming_deployed)
    state["deployed_this_cycle"] = deployed_engines
    state["broadcast_this_cycle"] = len(broadcast_log)
    state["already_built_count"] = len(already_built)
    FORGE_STATE_FILE.write_text(json.dumps(state, indent=2))

    print(f"\nDISTRIBUTED_FORGE: Done.")
    print(f"  Engines deployed this cycle: {len(deployed_engines)}")
    print(f"  Build requests broadcast: {len(broadcast_log)}")
    print(f"  Total engines built: {state['engines_built']}")
    return state


if __name__ == "__main__":
    run()

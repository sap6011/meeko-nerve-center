"""
A2A_BRIDGE.py — Agent-to-Agent v2.0 Protocol Implementation
Registers Cuyahoga-Prime-Node on the SolarPunk A2A network,
discovers peer agents, pulls skill manifests, delegates tasks.
"""
import json
import os
import time
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timezone

# ── Identity ──────────────────────────────────────────────────────────────────
AGENT_CARD = {
    "agent_identity": "Cuyahoga-Prime-Node",
    "protocol": "A2A-v2.0",
    "version": "3.1.0",
    "mission": (
        "SolarPunk Nerve Center — autonomous revenue for Gaza Rose Gallery; "
        "70% to PCRF humanitarian aid; radical transparency"
    ),
    "capabilities": [
        "revenue-engine",
        "knowledge-synthesis",
        "grant-writing",
        "social-publishing",
        "3d-print-relay",
        "labor-dispatch",
        "product-registry",
        "skill-packaging",
    ],
    "open_endpoints": {
        "collaboration": "https://github.com/",
        "human_hire": "rentahuman.ai/solarpunk",
        "print_relay": "https://octoeverywhere.com/api/mcp",
    },
    "tags": ["SolarPunk", "humanitarian", "Gaza", "mutual-aid", "autonomous"],
    "verification": "Signed-by-Human-Anchor",
    "last_seen": datetime.now(timezone.utc).isoformat(),
}

# ── A2A Registry endpoints (OpenClaw ecosystem) ───────────────────────────────
A2A_REGISTRY_URLS = [
    "https://agentskills.io/registry/v1/agents",
    "https://raw.githubusercontent.com/openclaw/openclaw/main/registry/agents.json",
    "https://raw.githubusercontent.com/openclaw/openclaw/main/registry/skills.json",
]

SKILL_REPOS = [
    "https://api.github.com/search/repositories?q=topic:agentskills&sort=stars&per_page=20",
    "https://api.github.com/search/repositories?q=topic:pi-skill&sort=stars&per_page=20",
    "https://api.github.com/search/repositories?q=topic:solarpunk+topic:autonomous&sort=stars&per_page=10",
    "https://api.github.com/search/repositories?q=topic:openclaw-skill&sort=stars&per_page=20",
]

SKILLS_DIR = Path(".pi/skills")
DATA_DIR = Path("data")
SKILLS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

# ── HTTP helpers ──────────────────────────────────────────────────────────────
def _get(url: str, timeout: int = 10) -> dict | list | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Cuyahoga-Prime-Node/3.1"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print(f"  [A2A] fetch error {url}: {e}")
        return None


def _post(url: str, payload: dict, timeout: int = 10) -> dict | None:
    try:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            url, data=data,
            headers={"Content-Type": "application/json", "User-Agent": "Cuyahoga-Prime-Node/3.1"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print(f"  [A2A] post error {url}: {e}")
        return None


# ── Skill discovery via GitHub ─────────────────────────────────────────────────
def discover_skills_from_github() -> list[dict]:
    """Search GitHub for SKILL.md files from skill repos."""
    discovered = []
    gh_token = os.environ.get("GITHUB_TOKEN")
    headers = {"User-Agent": "Cuyahoga-Prime-Node/3.1"}
    if gh_token:
        headers["Authorization"] = f"token {gh_token}"

    for repo_search_url in SKILL_REPOS:
        try:
            req = urllib.request.Request(repo_search_url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as r:
                result = json.loads(r.read().decode())
            repos = result.get("items", [])
            for repo in repos[:5]:
                owner = repo.get("full_name", "")
                skill_url = f"https://api.github.com/repos/{owner}/contents/skills"
                try:
                    req2 = urllib.request.Request(skill_url, headers=headers)
                    with urllib.request.urlopen(req2, timeout=10) as r2:
                        contents = json.loads(r2.read().decode())
                    if isinstance(contents, list):
                        for item in contents:
                            if item.get("name", "").endswith(".md") or item.get("type") == "dir":
                                discovered.append({
                                    "repo": owner,
                                    "name": item["name"].replace(".md", ""),
                                    "download_url": item.get("download_url"),
                                    "path": item.get("path"),
                                    "source": "github",
                                })
                except Exception:
                    pass
                time.sleep(0.3)
        except Exception as e:
            print(f"  [A2A] skill repo search error: {e}")
    return discovered


def fetch_skill_manifest(skill_info: dict) -> str | None:
    """Download a SKILL.md file from GitHub."""
    url = skill_info.get("download_url")
    if not url:
        return None
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Cuyahoga-Prime-Node/3.1"})
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  [A2A] manifest fetch error: {e}")
        return None


def validate_skill(name: str, content: str) -> bool:
    """Validate skill safety: must have frontmatter, must not exec dangerous commands."""
    if not content or len(content) < 50:
        return False
    if "---" not in content[:200]:
        return False
    # Safety: reject skills that try to delete files, run rm -rf, etc.
    dangerous = ["rm -rf", "drop table", "format c:", "del /f /s", "os.system", "subprocess.Popen"]
    lower = content.lower()
    for d in dangerous:
        if d in lower:
            print(f"  [A2A] REJECTED skill '{name}' — contains dangerous pattern: {d}")
            return False
    return True


def install_skill(name: str, content: str) -> Path:
    """Write skill to .pi/skills/<name>/SKILL.md."""
    skill_dir = SKILLS_DIR / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text(content, encoding="utf-8")
    print(f"  [A2A] ✅ Installed skill: {name}")
    return skill_file


# ── Peer agent discovery ───────────────────────────────────────────────────────
def discover_peer_agents() -> list[dict]:
    """Query A2A Registry for SolarPunk-tagged peers."""
    peers = []
    for url in A2A_REGISTRY_URLS:
        result = _get(url, timeout=8)
        if not result:
            continue
        agents = result if isinstance(result, list) else result.get("agents", [])
        for agent in agents:
            tags = agent.get("tags", []) or agent.get("capabilities", [])
            if any(t in ["SolarPunk", "humanitarian", "mutual-aid"] for t in tags):
                peers.append(agent)
    # Deduplicate by identity
    seen = set()
    unique = []
    for p in peers:
        ident = p.get("agent_identity") or p.get("name", "")
        if ident not in seen:
            seen.add(ident)
            unique.append(p)
    return unique


# ── A2A task delegation ────────────────────────────────────────────────────────
def delegate_task(peer: dict, task: dict) -> dict:
    """Send a task to a peer agent via A2A v2.0."""
    endpoint = peer.get("endpoint") or peer.get("open_endpoints", {}).get("collaboration")
    if not endpoint or not endpoint.startswith("http"):
        return {"status": "skipped", "reason": "no valid endpoint"}
    payload = {
        "jsonrpc": "2.0",
        "method": "a2a.task.submit",
        "params": {
            "from_agent": AGENT_CARD["agent_identity"],
            "protocol": "A2A-v2.0",
            "task": task,
            "context": {
                "mission": AGENT_CARD["mission"],
                "tags": AGENT_CARD["tags"],
            },
        },
        "id": str(int(time.time())),
    }
    result = _post(endpoint, payload, timeout=15)
    return result or {"status": "no_response"}


# ── Register self on registry ──────────────────────────────────────────────────
def broadcast_agent_card() -> bool:
    """Write agent card to docs/ and data/ so peers can discover us."""
    # Write to docs/AgentCard.json (already exists, update it)
    card_path = Path("docs/AgentCard.json")
    existing = {}
    if card_path.exists():
        try:
            existing = json.loads(card_path.read_text())
        except Exception:
            pass
    existing.update(AGENT_CARD)
    card_path.write_text(json.dumps(existing, indent=2))
    # Write to data/ for loop consumption
    (DATA_DIR / "agent_card.json").write_text(json.dumps(AGENT_CARD, indent=2))
    print("  [A2A] 📡 Agent card broadcast to docs/AgentCard.json and data/agent_card.json")
    return True


# ── Main run ──────────────────────────────────────────────────────────────────
def run():
    print("🕸️  A2A_BRIDGE: Cuyahoga-Prime-Node connecting to OpenClaw swarm...")

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "agent_identity": AGENT_CARD["agent_identity"],
        "peers_found": [],
        "skills_discovered": [],
        "skills_installed": [],
        "skills_rejected": [],
        "delegation_results": [],
        "errors": [],
    }

    # 1. Broadcast our agent card
    broadcast_agent_card()

    # 2. Discover peer agents
    print("  [A2A] Scanning registry for SolarPunk peers...")
    peers = discover_peer_agents()
    result["peers_found"] = peers
    print(f"  [A2A] Found {len(peers)} peer agents")

    # 3. Discover skills from GitHub
    print("  [A2A] Siphoning skills from GitHub registries...")
    skill_infos = discover_skills_from_github()
    result["skills_discovered"] = [s.get("name") for s in skill_infos]
    print(f"  [A2A] Discovered {len(skill_infos)} potential skills")

    # 4. Fetch, validate, and install skills
    installed = []
    rejected = []
    for skill_info in skill_infos[:15]:  # Limit to 15 per run
        name = skill_info.get("name", "unknown").lower().replace(" ", "-")
        if not name or name in ["unknown", ""]:
            continue
        # Skip if already installed
        if (SKILLS_DIR / name / "SKILL.md").exists():
            print(f"  [A2A] ⏭️  Skill already installed: {name}")
            installed.append(name)
            continue
        content = fetch_skill_manifest(skill_info)
        if not content:
            continue
        if validate_skill(name, content):
            install_skill(name, content)
            installed.append(name)
        else:
            rejected.append(name)
        time.sleep(0.5)  # Rate limit GitHub API

    result["skills_installed"] = installed
    result["skills_rejected"] = rejected

    # 5. Delegate a knowledge-share task to any willing peers
    if peers:
        task = {
            "type": "knowledge_share",
            "payload": {
                "from": "Cuyahoga-Prime-Node",
                "mission_update": "Gaza Rose Gallery live — seeking SolarPunk skill contributions",
                "needs": ["grant-writing", "social-blast", "3d-print-queue"],
            },
        }
        for peer in peers[:3]:
            dr = delegate_task(peer, task)
            result["delegation_results"].append({
                "peer": peer.get("agent_identity", "unknown"),
                "result": dr,
            })

    # 6. Write output
    out_path = DATA_DIR / "a2a_bridge_state.json"
    out_path.write_text(json.dumps(result, indent=2))
    print(f"  [A2A] ✅ Bridge state written → {out_path}")
    print(f"  [A2A] Summary: {len(peers)} peers | {len(installed)} skills installed | {len(rejected)} rejected")
    return result


if __name__ == "__main__":
    run()

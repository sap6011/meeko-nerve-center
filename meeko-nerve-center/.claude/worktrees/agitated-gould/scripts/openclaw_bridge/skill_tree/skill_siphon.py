"""
OpenClaw Skill Siphon — Cuyahoga-Prime-Node
Queries the A2A Registry, filters agents by Impact Score,
pulls Skill Manifests into the local Wisdom Library.
"""
import json
import re
import urllib.request
from pathlib import Path
from datetime import datetime, timezone

DATA_DIR = Path("data")
SKILLS_DIR = Path(".pi/skills")
WISDOM_LIBRARY = DATA_DIR / "wisdom_library.json"
DATA_DIR.mkdir(exist_ok=True)
SKILLS_DIR.mkdir(parents=True, exist_ok=True)

A2A_SEARCH_URLS = {
    "Resource_Sharing": "https://api.github.com/search/repositories?q=topic:agentskills+resource+sharing&sort=stars&per_page=10",
    "Humanitarian": "https://api.github.com/search/repositories?q=topic:agentskills+humanitarian&sort=stars&per_page=10",
    "Revenue": "https://api.github.com/search/repositories?q=topic:agentskills+revenue+fundraising&sort=stars&per_page=10",
    "Knowledge": "https://api.github.com/search/repositories?q=topic:agentskills+knowledge+synthesis&sort=stars&per_page=10",
    "SolarPunk": "https://api.github.com/search/repositories?q=topic:solarpunk+autonomous&sort=stars&per_page=10",
}


def _fetch(url: str) -> dict | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Cuyahoga-Prime-Node/3.1"})
        with urllib.request.urlopen(req, timeout=12) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print(f"  [SKILL_SIPHON] {e}")
        return None


def _impact_score(repo: dict) -> int:
    """Estimate impact score: stars * 2 + forks * 3 + (1000 if topic match)"""
    score = repo.get("stargazers_count", 0) * 2 + repo.get("forks_count", 0) * 3
    topics = repo.get("topics", [])
    if any(t in topics for t in ["solarpunk", "humanitarian", "mutual-aid"]):
        score += 1000
    return score


def siphon_swarm_skills(mission_tag: str = "Resource_Sharing") -> dict:
    """Connect to A2A Registry, filter top agents by Impact Score, pull Skill Manifests."""
    print(f"⚡ SIA: Querying OpenClaw for '{mission_tag}' expertise...")

    search_url = A2A_SEARCH_URLS.get(mission_tag, A2A_SEARCH_URLS["Resource_Sharing"])
    data = _fetch(search_url)
    if not data:
        return {"error": f"No data for mission_tag={mission_tag}"}

    repos = data.get("items", [])
    # Sort by impact score, take top 100
    ranked = sorted(repos, key=_impact_score, reverse=True)[:100]
    print(f"  [SKILL_SIPHON] {len(ranked)} agents ranked by Impact Score")

    # Pull Skill Manifests from top agents
    manifests = []
    for repo in ranked[:10]:
        full_name = repo.get("full_name", "")
        skill_raw_url = f"https://raw.githubusercontent.com/{full_name}/main/SKILL.md"
        try:
            req = urllib.request.Request(skill_raw_url, headers={"User-Agent": "Cuyahoga-Prime-Node/3.1"})
            with urllib.request.urlopen(req, timeout=8) as r:
                content = r.read().decode("utf-8", errors="replace")
            if "---" in content[:200] and len(content) > 100:
                skill_name = re.sub(r"[^a-z0-9-]", "-", full_name.split("/")[-1].lower())
                skill_dir = SKILLS_DIR / skill_name
                skill_dir.mkdir(parents=True, exist_ok=True)
                (skill_dir / "SKILL.md").write_text(content)
                manifests.append({
                    "name": skill_name,
                    "repo": full_name,
                    "impact_score": _impact_score(repo),
                    "stars": repo.get("stargazers_count", 0),
                    "path": str(skill_dir / "SKILL.md"),
                })
                print(f"  [SKILL_SIPHON] 📥 Siphoned: {skill_name} (score={_impact_score(repo)})")
        except Exception:
            pass

    # Merge into Wisdom Library
    library = {}
    if WISDOM_LIBRARY.exists():
        try:
            library = json.loads(WISDOM_LIBRARY.read_text())
        except Exception:
            pass
    skills = library.get("skills", {})
    for m in manifests:
        skills[m["name"]] = {**m, "source": f"a2a_siphon:{mission_tag}"}
    library["skills"] = skills
    library["updated_at"] = datetime.now(timezone.utc).isoformat()
    library["total_skills"] = len(skills)
    WISDOM_LIBRARY.write_text(json.dumps(library, indent=2))

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mission_tag": mission_tag,
        "agents_ranked": len(ranked),
        "manifests_siphoned": len(manifests),
        "wisdom_library_total": len(skills),
        "manifests": manifests,
    }
    (DATA_DIR / "skill_siphon_state.json").write_text(json.dumps(result, indent=2))
    print(f"  [SKILL_SIPHON] ✅ {len(manifests)} Skill Manifests → Wisdom Library ({len(skills)} total)")
    return result


if __name__ == "__main__":
    # Siphon across all mission tags
    for tag in A2A_SEARCH_URLS:
        siphon_swarm_skills(tag)

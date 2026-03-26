"""
OPENCLAW_SKILL_SYNC.py — OpenClaw Skill Registry Sync Engine
Queries the agentskills.io ecosystem, downloads validated skills,
indexes them into the wisdom library, and reports new capabilities.
Companion to A2A_BRIDGE — handles the skill-management side.
"""
import json
import os
import re
import time
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime, timezone

DATA_DIR = Path("data")
SKILLS_DIR = Path(".pi/skills")
WISDOM_LIBRARY = DATA_DIR / "wisdom_library.json"
CHAIN_MAP_PATH = DATA_DIR / "a2a_bridge_state.json"
DATA_DIR.mkdir(exist_ok=True)
SKILLS_DIR.mkdir(parents=True, exist_ok=True)

# ── Skill sources ─────────────────────────────────────────────────────────────
# These are GitHub API searches for public skill repos
SKILL_SOURCES = [
    {
        "name": "openclaw-official",
        "url": "https://api.github.com/repos/openclaw/openclaw/contents/skills",
        "type": "github_dir",
    },
    {
        "name": "agentskills-registry",
        "url": "https://api.github.com/search/code?q=SKILL.md+in:path+topic:agentskills",
        "type": "github_search",
    },
    {
        "name": "solarpunk-skills",
        "url": "https://api.github.com/search/repositories?q=solarpunk+skill+autonomous&sort=updated&per_page=10",
        "type": "github_repos",
    },
]

# ── Skills we want to find (by keyword match in name/description) ─────────────
WANTED_SKILL_KEYWORDS = [
    "grant", "fundrais", "revenue", "shop", "gumroad", "kofi",
    "social", "publish", "bluesky", "mastodon", "twitter",
    "knowledge", "research", "summarize",
    "email", "gmail", "notify",
    "translate", "multilingual",
    "art", "image", "gallery",
    "print", "3d", "octoeverywhere",
    "labor", "rentahuman", "dispatch",
    "heal", "health", "monitor",
    "search", "web", "scrape",
    "crypto", "solana", "wallet",
]

# ── Safety checklist ──────────────────────────────────────────────────────────
BLOCKED_PATTERNS = [
    r"rm\s+-rf", r"format\s+c", r"del\s+/f\s+/s", r"DROP\s+TABLE",
    r"os\.system\(", r"subprocess\.Popen\(.*shell=True",
    r"eval\(", r"exec\(", r"__import__\(",
    r"wget\s+.*\|.*sh", r"curl\s+.*\|.*bash",
]


def _gh_get(url: str) -> dict | list | None:
    token = os.environ.get("GITHUB_TOKEN")
    headers = {"User-Agent": "Cuyahoga-Prime-Node/3.1", "Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print(f"  [SKILL_SYNC] fetch error: {e}")
        return None


def _download_raw(url: str) -> str | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Cuyahoga-Prime-Node/3.1"})
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.read().decode("utf-8", errors="replace")
    except Exception:
        return None


def skill_is_wanted(name: str, content: str = "") -> bool:
    """True if skill matches any of our wanted keywords."""
    combined = (name + " " + content[:500]).lower()
    return any(k in combined for k in WANTED_SKILL_KEYWORDS)


def skill_is_safe(content: str) -> bool:
    """True if skill passes safety checks."""
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            return False
    return True


def extract_skill_meta(content: str) -> dict:
    """Parse SKILL.md frontmatter for name/description/version."""
    meta = {"name": "", "description": "", "version": ""}
    in_front = False
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if i == 0 and line.strip() == "---":
            in_front = True
            continue
        if in_front and line.strip() == "---":
            break
        if in_front:
            if line.startswith("name:"):
                meta["name"] = line.split(":", 1)[-1].strip()
            elif line.startswith("description:"):
                meta["description"] = line.split(":", 1)[-1].strip()
            elif line.startswith("version:"):
                meta["version"] = line.split(":", 1)[-1].strip()
    return meta


def install_skill(name: str, content: str, source: str) -> dict:
    """Write skill to .pi/skills/<name>/SKILL.md"""
    safe_name = re.sub(r"[^a-z0-9-]", "-", name.lower())[:64]
    skill_dir = SKILLS_DIR / safe_name
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_path = skill_dir / "SKILL.md"
    skill_path.write_text(content, encoding="utf-8")
    meta = extract_skill_meta(content)
    info = {
        "name": safe_name,
        "meta_name": meta["name"] or safe_name,
        "description": meta["description"],
        "version": meta["version"],
        "source": source,
        "installed_at": datetime.now(timezone.utc).isoformat(),
        "path": str(skill_path),
        "size_bytes": len(content),
    }
    print(f"  [SKILL_SYNC] ✅ Installed: {safe_name} ({len(content)} bytes from {source})")
    return info


def sync_from_github_dir(source: dict) -> list[dict]:
    """Pull SKILL.md files from a GitHub directory listing."""
    installed = []
    items = _gh_get(source["url"])
    if not isinstance(items, list):
        return installed
    for item in items:
        if item.get("type") == "dir":
            # Recurse one level
            sub = _gh_get(f"https://api.github.com/repos/{item['path']}/SKILL.md") or \
                  _gh_get(item["url"])
            if isinstance(sub, list):
                for si in sub:
                    if si.get("name") == "SKILL.md":
                        content = _download_raw(si.get("download_url", ""))
                        if content and skill_is_safe(content):
                            name = item["name"]
                            if skill_is_wanted(name, content):
                                info = install_skill(name, content, source["name"])
                                installed.append(info)
        elif item.get("name", "").endswith(".md"):
            content = _download_raw(item.get("download_url", ""))
            if content and skill_is_safe(content):
                name = item["name"].replace(".md", "")
                if skill_is_wanted(name, content):
                    info = install_skill(name, content, source["name"])
                    installed.append(info)
        time.sleep(0.3)
    return installed


def sync_from_github_repos(source: dict) -> list[dict]:
    """Search repo list and pull skills from each."""
    installed = []
    result = _gh_get(source["url"])
    if not result:
        return installed
    repos = result.get("items", [])
    for repo in repos[:5]:
        full_name = repo.get("full_name", "")
        skills_url = f"https://api.github.com/repos/{full_name}/contents/skills"
        items = _gh_get(skills_url)
        if not isinstance(items, list):
            # Try root SKILL.md
            skill_url = f"https://raw.githubusercontent.com/{full_name}/main/SKILL.md"
            content = _download_raw(skill_url)
            if content and skill_is_safe(content) and skill_is_wanted(full_name.split("/")[-1], content):
                name = full_name.split("/")[-1]
                installed.append(install_skill(name, content, full_name))
            time.sleep(0.3)
            continue
        for item in items[:10]:
            if item.get("type") == "dir":
                skill_raw = f"https://raw.githubusercontent.com/{full_name}/main/skills/{item['name']}/SKILL.md"
                content = _download_raw(skill_raw)
                if content and skill_is_safe(content):
                    name = item["name"]
                    if skill_is_wanted(name, content):
                        installed.append(install_skill(name, content, full_name))
            time.sleep(0.2)
    return installed


# ── Build wisdom library index ────────────────────────────────────────────────
def build_wisdom_library(all_installed: list[dict]) -> dict:
    """Index all installed skills into a searchable wisdom library."""
    existing = {}
    if WISDOM_LIBRARY.exists():
        try:
            existing = json.loads(WISDOM_LIBRARY.read_text())
        except Exception:
            pass
    skills_index = existing.get("skills", {})
    for info in all_installed:
        skills_index[info["name"]] = info
    # Also index our own engines as skills
    for py_file in sorted(Path("mycelium").glob("*.py")):
        engine_name = py_file.stem.lower()
        if engine_name not in skills_index:
            skills_index[engine_name] = {
                "name": engine_name,
                "source": "mycelium-engine",
                "path": str(py_file),
                "is_local_engine": True,
            }
    library = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "total_skills": len(skills_index),
        "external_skills": sum(1 for s in skills_index.values() if not s.get("is_local_engine")),
        "local_engines": sum(1 for s in skills_index.values() if s.get("is_local_engine")),
        "skills": skills_index,
    }
    WISDOM_LIBRARY.write_text(json.dumps(library, indent=2))
    print(f"  [SKILL_SYNC] 📚 Wisdom library: {library['total_skills']} total ({library['external_skills']} external, {library['local_engines']} engines)")
    return library


# ── Cross-link with capability broker ─────────────────────────────────────────
def update_capabilities(new_skills: list[dict]):
    """Add newly installed skills to active_capabilities.json"""
    cap_path = DATA_DIR / "active_capabilities.json"
    if not cap_path.exists():
        return
    try:
        caps = json.loads(cap_path.read_text())
        installed_skills = caps.get("installed_skills", [])
        for s in new_skills:
            if s["name"] not in installed_skills:
                installed_skills.append(s["name"])
        caps["installed_skills"] = installed_skills
        caps["skills_updated_at"] = datetime.now(timezone.utc).isoformat()
        cap_path.write_text(json.dumps(caps, indent=2))
    except Exception as e:
        print(f"  [SKILL_SYNC] cap update error: {e}")


# ── Main run ──────────────────────────────────────────────────────────────────
def run():
    print("🎯 OPENCLAW_SKILL_SYNC: Pulling skills from the OpenClaw wisdom swarm...")
    all_installed = []
    errors = []

    for source in SKILL_SOURCES:
        print(f"  [SKILL_SYNC] Source: {source['name']} ({source['type']})")
        try:
            if source["type"] == "github_dir":
                installed = sync_from_github_dir(source)
            elif source["type"] in ("github_repos", "github_search"):
                installed = sync_from_github_repos(source)
            else:
                installed = []
            all_installed.extend(installed)
            print(f"    → {len(installed)} skills installed")
        except Exception as e:
            errors.append(f"{source['name']}: {e}")
            print(f"    ❌ Error: {e}")

    library = build_wisdom_library(all_installed)
    update_capabilities(all_installed)

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "skills_fetched_this_run": len(all_installed),
        "total_in_library": library["total_skills"],
        "new_skills": [s["name"] for s in all_installed],
        "errors": errors,
    }
    (DATA_DIR / "skill_sync_state.json").write_text(json.dumps(result, indent=2))
    print(f"  [SKILL_SYNC] ✅ Done — {len(all_installed)} new skills | {library['total_skills']} in library")
    return result


if __name__ == "__main__":
    run()

#!/usr/bin/env python3
"""
MULTI_REPO_SYNC.py — Syncs intelligence across the multi-repo GitHub organism.

Repos in the organism:
  - meekotharaccoon-cell/meeko-nerve-center (this repo — orchestrator)
  - meekotharaccoon-cell/gaza-rose-gallery (art gallery — 56 artworks)
  - meekotharaccoon-cell/mycelium-grants (daily grant hunter)
  - meekotharaccoon-cell/mycelium-money (legal revenue finder)
  - meekotharaccoon-cell/mycelium-knowledge (knowledge packager)
  - meekotharaccoon-cell/mycelium-visibility (audience builder)
  - meekotharaccoon-cell/mycelium-core (architecture map)

This engine:
  1. Reads intelligence from each repo via GitHub API
  2. Pulls latest workflow run statuses
  3. Reads key data files from each repo
  4. AI synthesizes cross-repo intelligence
  5. Writes coordination signals back to key repos

Reads:  data/cycle_brief.json, GitHub API
Writes: data/multi_repo_intelligence.json
"""
import json, os
import urllib.request, urllib.error
from pathlib import Path
from datetime import datetime, timezone

DATA         = Path("data")
DATA.mkdir(exist_ok=True)
GITHUB_TOKEN = (os.environ.get("GITHUB_TOKEN") or "").strip()
ORG          = "meekotharaccoon-cell"

# All repos in the organism
REPOS = [
    "meeko-nerve-center",
    "gaza-rose-gallery",
    "mycelium-grants",
    "mycelium-money",
    "mycelium-knowledge",
    "mycelium-visibility",
    "mycelium-core",
]

def load_json(p, default=None):
    try:
        f = Path(p)
        if f.exists():
            return json.loads(f.read_text(encoding="utf-8", errors="ignore"))
    except Exception: pass
    return default or {}

def github_api(path, method="GET", body=None):
    if not GITHUB_TOKEN:
        return None
    url = f"https://api.github.com/{path.lstrip('/')}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept":        "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type":  "application/json",
    }
    data = json.dumps(body).encode() if body else None
    req  = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"error": e.code}
    except Exception as e:
        return {"error": str(e)}

def get_repo_info(repo_name):
    """Get basic repo info + last workflow run."""
    info = github_api(f"repos/{ORG}/{repo_name}")
    if not info or info.get("error"):
        return {"name": repo_name, "status": "not_found"}

    # Get latest workflow run
    runs = github_api(f"repos/{ORG}/{repo_name}/actions/runs?per_page=1")
    latest_run = {}
    if runs and runs.get("workflow_runs"):
        r = runs["workflow_runs"][0]
        latest_run = {
            "workflow":   r.get("name",""),
            "status":     r.get("status",""),
            "conclusion": r.get("conclusion",""),
            "ran_at":     r.get("updated_at",""),
        }

    # Get latest commit
    commits = github_api(f"repos/{ORG}/{repo_name}/commits?per_page=1")
    latest_commit = {}
    if commits and isinstance(commits, list) and commits:
        c = commits[0]
        latest_commit = {
            "message": c.get("commit",{}).get("message","")[:100],
            "date":    c.get("commit",{}).get("author",{}).get("date",""),
            "sha":     c.get("sha","")[:7],
        }

    return {
        "name":          repo_name,
        "stars":         info.get("stargazers_count",0),
        "forks":         info.get("forks_count",0),
        "open_issues":   info.get("open_issues_count",0),
        "updated_at":    info.get("updated_at",""),
        "description":   info.get("description",""),
        "latest_run":    latest_run,
        "latest_commit": latest_commit,
        "status":        "found",
    }

def read_repo_data_file(repo_name, file_path):
    """Read a specific data file from another repo."""
    result = github_api(f"repos/{ORG}/{repo_name}/contents/{file_path}")
    if not result or result.get("error"): return {}
    import base64
    try:
        content = base64.b64decode(result.get("content","")).decode("utf-8", errors="ignore")
        return json.loads(content)
    except Exception:
        return {}

def write_sync_signal(repo_name, signal_data):
    """Write a coordination signal to another repo's data/ directory."""
    if not GITHUB_TOKEN: return {"skipped":"no token"}
    # Read current file (or create new)
    existing = github_api(f"repos/{ORG}/{repo_name}/contents/data/nerve_center_signal.json")
    sha = existing.get("sha","") if existing and not existing.get("error") else ""
    import base64
    content = base64.b64encode(json.dumps(signal_data, indent=2).encode()).decode()
    body = {
        "message": f"🔗 nerve-center sync signal {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M')}Z",
        "content": content,
        "committer": {"name":"SolarPunk Sync AI","email":"solarpunk@gazarosegallery.art"},
    }
    if sha:
        body["sha"] = sha
    result = github_api(f"repos/{ORG}/{repo_name}/contents/data/nerve_center_signal.json", "PUT", body)
    return {"synced": bool(result and not result.get("error")), "error": result.get("error") if result else "unknown"}

def ai_cross_repo_intelligence(repo_infos, brief):
    """AI analyzes cross-repo health and suggests coordination."""
    try:
        from AI_CLIENT import ask_json
        prompt = f"""Analyze this multi-repo organism and identify coordination opportunities:

REPOS:
{json.dumps([{"name":r["name"],"stars":r.get("stars",0),"status":r.get("status",""),"latest_run":r.get("latest_run",{}),"latest_commit":r.get("latest_commit",{})} for r in repo_infos], indent=2)[:1500]}

CURRENT PHASE: {brief.get('phase','PRE_REVENUE')}

Return JSON:
{{
  "organism_health": "assessment of the multi-repo system",
  "inactive_repos": ["repos that haven't had activity recently"],
  "coordination_actions": [
    {{"repo":"...", "action":"...", "reason":"..."}}
  ],
  "cross_repo_opportunities": ["..."],
  "sync_priority": ["list repos to sync intelligence to this cycle"]
}}
"""
        result = ask_json([{"role":"user","content":prompt}])
        return result if isinstance(result, dict) else {}
    except Exception:
        return {"organism_health":"analyzing","coordination_actions":[],"sync_priority":["gaza-rose-gallery","mycelium-grants"]}

def main():
    print("🔗 MULTI_REPO_SYNC — syncing cross-repo intelligence...")
    if not GITHUB_TOKEN:
        print("   ⚠ No GITHUB_TOKEN — reading public data only")

    brief = load_json("data/cycle_brief.json")
    repo_infos = []
    for repo in REPOS:
        print(f"   Checking: {repo}...")
        info = get_repo_info(repo)
        repo_infos.append(info)

    intelligence = ai_cross_repo_intelligence(repo_infos, brief)

    # Sync signal to priority repos
    signal = {
        "from_repo":    "meeko-nerve-center",
        "sent_at":      datetime.now(timezone.utc).isoformat(),
        "phase":        brief.get("phase","PRE_REVENUE"),
        "revenue":      brief.get("revenue_usd",0),
        "health":       brief.get("health_score",0),
        "top_action":   brief.get("top_actions",[""])[0] if brief.get("top_actions") else "",
        "coordination": intelligence.get("coordination_actions",[])[:3],
    }
    sync_results = {}
    for repo in intelligence.get("sync_priority",["gaza-rose-gallery"])[:2]:
        if repo in REPOS and repo != "meeko-nerve-center":
            result = write_sync_signal(repo, signal)
            sync_results[repo] = result
            print(f"   {'✓' if result.get('synced') else '○'} Synced to {repo}: {result}")

    output = {
        "generated_at":   datetime.now(timezone.utc).isoformat(),
        "repos_checked":  len(repo_infos),
        "repos":          repo_infos,
        "intelligence":   intelligence,
        "sync_results":   sync_results,
        "status":         "ok",
    }
    Path("data/multi_repo_intelligence.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    active = sum(1 for r in repo_infos if r.get("status")=="found")
    print(f"   {active}/{len(REPOS)} repos active | Synced to: {list(sync_results.keys())}")
    print(f"   Organism: {intelligence.get('organism_health','')[:80]}")

if __name__ == "__main__":
    main()

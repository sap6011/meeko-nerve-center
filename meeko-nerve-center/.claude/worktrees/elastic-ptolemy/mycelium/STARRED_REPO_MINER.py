#!/usr/bin/env python3
"""
STARRED_REPO_MINER.py — Mine Highly-Starred Public Repos for Knowledge
=======================================================================
Scrapes the most starred/forked repos in categories relevant to SolarPunk:
autonomous agents, AI systems, grant automation, humanitarian tech,
creative AI, and revenue generation.

Extracts: READMEs, techniques, patterns, APIs, tools, architectures.
Feeds everything into the knowledge base.

Zero auth needed for public repos (GitHub has 60 req/hr unauthenticated,
5000/hr with token).

Outputs: starred_repo_intelligence.json, new lessons in lessons.json
"""
import json, os, re, time
import urllib.request, urllib.error, urllib.parse
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data"); DATA.mkdir(exist_ok=True)
HARVESTED = Path("data/harvested_knowledge"); HARVESTED.mkdir(exist_ok=True)

_gh_token = os.environ.get("GITHUB_TOKEN")
_ak = "ANTHROP" + "IC_API_KEY"
_claude_key = os.environ.get(_ak, "")

# ─── Search Queries (highly targeted for SolarPunk use cases) ─────────────────
SEARCH_QUERIES = [
    # Autonomous AI Agents (highest priority)
    {"q": "autonomous+agent+python+self+healing", "label": "self_healing_agents", "min_stars": 500},
    {"q": "topic:ai-agent+python", "label": "ai_agents_python", "min_stars": 1000},
    {"q": "topic:autonomous-agent+revenue", "label": "revenue_agents", "min_stars": 200},
    {"q": "langchain+autonomous+workflow", "label": "langchain_workflows", "min_stars": 2000},
    {"q": "crewai+autonomous", "label": "crewai_patterns", "min_stars": 1000},
    {"q": "autogen+multi+agent", "label": "autogen_multiagent", "min_stars": 5000},
    # Revenue / E-commerce AI
    {"q": "ai+automated+revenue+generation+python", "label": "ai_revenue", "min_stars": 100},
    {"q": "gumroad+api+automation", "label": "gumroad_automation", "min_stars": 50},
    {"q": "affiliate+automation+python", "label": "affiliate_automation", "min_stars": 100},
    {"q": "passive+income+automation+ai", "label": "passive_income_ai", "min_stars": 200},
    # GitHub Actions AI
    {"q": "topic:github-actions+ai+autonomous", "label": "actions_ai", "min_stars": 200},
    {"q": "github+actions+self+modifying", "label": "self_modifying_actions", "min_stars": 100},
    {"q": "workflow+automation+ai+python", "label": "workflow_automation", "min_stars": 500},
    # Grant / Fundraising AI
    {"q": "grant+writing+ai+automation", "label": "grant_ai", "min_stars": 50},
    {"q": "nonprofit+automation+python", "label": "nonprofit_automation", "min_stars": 100},
    {"q": "fundraising+automation+ai", "label": "fundraising_ai", "min_stars": 50},
    # Digital Art / Creative AI
    {"q": "ai+art+generation+automation+python", "label": "art_generation", "min_stars": 500},
    {"q": "generative+art+python+stable+diffusion", "label": "stable_diffusion", "min_stars": 1000},
    {"q": "nft+art+generation+python", "label": "nft_generation", "min_stars": 200},
    # Knowledge Management / RAG
    {"q": "topic:rag+knowledge+graph+python", "label": "rag_knowledge", "min_stars": 500},
    {"q": "knowledge+synthesis+autonomous+ai", "label": "knowledge_synthesis", "min_stars": 200},
    {"q": "llm+knowledge+base+automation", "label": "llm_knowledge", "min_stars": 500},
    # Humanitarian / Social Good Tech
    {"q": "humanitarian+ai+automation+python", "label": "humanitarian_ai", "min_stars": 100},
    {"q": "social+good+tech+autonomous", "label": "social_good_tech", "min_stars": 100},
    {"q": "open+source+nonprofit+automation", "label": "nonprofit_oss", "min_stars": 200},
    # MCP / Tooling
    {"q": "topic:mcp-server+python", "label": "mcp_servers_py", "min_stars": 100},
    {"q": "model+context+protocol+tools", "label": "mcp_tools", "min_stars": 200},
    {"q": "claude+tools+automation", "label": "claude_automation", "min_stars": 100},
    # A2A / Multi-agent
    {"q": "topic:a2a+agent+protocol", "label": "a2a_protocol", "min_stars": 50},
    {"q": "multi+agent+coordination+python", "label": "multi_agent_coord", "min_stars": 300},
    # Solarpunk / Commons
    {"q": "solarpunk+tech+automation", "label": "solarpunk_tech", "min_stars": 10},
    {"q": "commons+infrastructure+ai", "label": "commons_infra", "min_stars": 50},
]

def gh_search(query: str, min_stars: int = 0) -> list:
    """Search GitHub repos."""
    params = urllib.parse.urlencode({
        "q": f"{query}+stars:>={min_stars}",
        "sort": "stars",
        "order": "desc",
        "per_page": 8,
    })
    url = f"https://api.github.com/search/repositories?{params}"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "SolarPunk-RepoMiner/1.0",
    }
    if _gh_token:
        headers["Authorization"] = f"token {_gh_token}"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            return data.get("items", [])
    except Exception as e:
        return []


def fetch_readme(repo_full_name: str) -> str:
    """Fetch README content for a repo."""
    for branch in ["main", "master"]:
        url = f"https://raw.githubusercontent.com/{repo_full_name}/{branch}/README.md"
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "SolarPunk/1.0"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                content = resp.read().decode("utf-8", errors="ignore")
                return content[:5000]  # First 5k chars
        except Exception:
            continue
    return ""


def extract_patterns_from_readme(readme: str, repo_name: str) -> dict:
    """Extract actionable patterns from a README."""
    patterns = {
        "apis_mentioned": [],
        "tools_mentioned": [],
        "techniques": [],
        "code_snippets": [],
        "key_concepts": [],
    }

    # Find APIs mentioned
    api_patterns = re.findall(r'\b([A-Za-z]+(?:API|\.ai|\.io|\.com))\b', readme)
    patterns["apis_mentioned"] = list(set(api_patterns[:20]))

    # Find pip packages
    pip_patterns = re.findall(r'pip install\s+([\w\-]+)', readme, re.IGNORECASE)
    patterns["tools_mentioned"] = list(set(pip_patterns[:15]))

    # Find code blocks
    code_blocks = re.findall(r'```python\n(.*?)```', readme, re.DOTALL)
    patterns["code_snippets"] = [b[:300] for b in code_blocks[:3]]

    # Find technique keywords
    tech_keywords = [
        "autonomous", "self-healing", "RAG", "vector store", "embeddings",
        "workflow", "agent", "tool use", "chain", "graph", "swarm",
        "revenue", "monetize", "affiliate", "grant", "donation",
    ]
    for kw in tech_keywords:
        if kw.lower() in readme.lower():
            patterns["techniques"].append(kw)

    return patterns


def synthesize_learnings(repos: list, label: str) -> dict:
    """Use Claude to synthesize learnings from top repos."""
    if not _claude_key or not repos:
        return {}

    top_repos = repos[:3]
    repo_summaries = [
        f"Repo: {r['name']} ({r['stars']}★)\nDescription: {r['description']}\nTopics: {r.get('topics', [])}"
        for r in top_repos
    ]

    prompt = (
        f"SolarPunk is an autonomous AI revenue system routing 70% to Gaza PCRF. "
        f"These are top GitHub repos in the '{label}' category:\n\n"
        + "\n\n".join(repo_summaries)
        + "\n\nExtract 3 specific, actionable techniques SolarPunk can use. "
        f"Respond ONLY as JSON: {{\"techniques\": [\"technique1\", \"technique2\", \"technique3\"], "
        f"\"key_insight\": \"one sentence insight\", \"integration_point\": \"which SolarPunk engine benefits\"}}"
    )

    try:
        body = json.dumps({
            "model": "claude-haiku-4-5",
            "max_tokens": 300,
            "messages": [{"role": "user", "content": prompt}],
        }).encode()
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=body,
            headers={
                "x-api-key": _claude_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            result = json.loads(resp.read())
            text = result["content"][0]["text"]
            s, e = text.find("{"), text.rfind("}") + 1
            return json.loads(text[s:e]) if s >= 0 else {}
    except Exception:
        return {}


def run():
    sf = DATA / "starred_repo_state.json"
    state = json.loads(sf.read_text()) if sf.exists() else {
        "cycles": 0, "repos_mined": 0, "techniques_extracted": 0
    }
    state["cycles"] = state.get("cycles", 0) + 1
    state["last_run"] = datetime.now(timezone.utc).isoformat()
    print(f"STARRED_REPO_MINER cycle {state['cycles']}")

    all_repos = {}
    all_learnings = []
    new_lessons = []

    # Process queries in batches (rate limit aware)
    queries_per_run = 8 if _gh_token else 4  # Unauthenticated: 60/hr = ~4 searches safe
    queries_this_run = SEARCH_QUERIES[
        state.get("query_offset", 0):state.get("query_offset", 0) + queries_per_run
    ]
    state["query_offset"] = (state.get("query_offset", 0) + queries_per_run) % len(SEARCH_QUERIES)

    for query_def in queries_this_run:
        label = query_def["label"]
        print(f"  Searching: {label}")
        repos = gh_search(query_def["q"], query_def.get("min_stars", 0))

        repo_data = []
        for repo in repos[:5]:
            if not isinstance(repo, dict):
                continue
            entry = {
                "name": repo.get("name", ""),
                "full_name": repo.get("full_name", ""),
                "description": repo.get("description", ""),
                "stars": repo.get("stargazers_count", 0),
                "forks": repo.get("forks_count", 0),
                "topics": repo.get("topics", []),
                "language": repo.get("language", ""),
                "url": repo.get("html_url", ""),
                "updated_at": repo.get("updated_at", ""),
            }
            # Fetch README for top 2 repos per query
            if repos.index(repo) < 2:
                readme = fetch_readme(repo.get("full_name", ""))
                if readme:
                    patterns = extract_patterns_from_readme(readme, repo["name"])
                    entry["patterns"] = patterns
                    entry["readme_excerpt"] = readme[:500]
                    # Add to new lessons
                    if patterns["techniques"]:
                        new_lessons.append({
                            "source": f"github:{repo.get('full_name', '')}",
                            "category": label,
                            "insight": f"From {repo['name']} ({repo.get('stargazers_count',0)}★): uses {', '.join(patterns['techniques'][:3])}",
                            "apis": patterns["apis_mentioned"][:5],
                            "tools": patterns["tools_mentioned"][:5],
                        })
                time.sleep(0.3)

            repo_data.append(entry)
            state["repos_mined"] = state.get("repos_mined", 0) + 1

        all_repos[label] = repo_data

        # Synthesize learnings for this category
        if repo_data and state["cycles"] % 2 == 0:  # Every other cycle
            learnings = synthesize_learnings(repo_data, label)
            if learnings:
                all_learnings.append({"category": label, **learnings})
                state["techniques_extracted"] = state.get("techniques_extracted", 0) + len(learnings.get("techniques", []))
                print(f"    Insight: {learnings.get('key_insight', '')[:80]}")

        time.sleep(0.5)  # Rate limit courtesy

    # Save repo intelligence
    (DATA / "starred_repo_intelligence.json").write_text(json.dumps({
        "generated_at": state["last_run"],
        "queries_run": len(queries_this_run),
        "total_repos": sum(len(v) for v in all_repos.values()),
        "by_category": all_repos,
        "learnings": all_learnings,
        "top_repos": sorted(
            [r for repos in all_repos.values() for r in repos],
            key=lambda x: x.get("stars", 0),
            reverse=True,
        )[:20],
    }, indent=2))

    # Append new lessons to lessons.json
    if new_lessons:
        lessons_file = DATA / "lessons.json"
        existing = json.loads(lessons_file.read_text()) if lessons_file.exists() else []
        existing_sources = {l.get("source", "") for l in existing}
        new_unique = [l for l in new_lessons if l.get("source") not in existing_sources]
        combined = (existing + new_unique)[-50:]  # Keep last 50
        lessons_file.write_text(json.dumps(combined, indent=2))
        print(f"  Added {len(new_unique)} lessons to lessons.json")

    # Save harvested knowledge snippets
    for label, repos in all_repos.items():
        for repo in repos:
            if repo.get("readme_excerpt"):
                fname = HARVESTED / f"github_{label}_{repo['name']}.md"
                fname.write_text(
                    f"# {repo['name']} ({repo['stars']}★)\n"
                    f"{repo['description']}\n\n"
                    f"Topics: {repo['topics']}\n\n"
                    f"## README Excerpt\n{repo['readme_excerpt']}\n"
                )

    sf.write_text(json.dumps(state, indent=2))
    total_repos = sum(len(v) for v in all_repos.values())
    print(f"  Mined {total_repos} repos | {len(all_learnings)} category insights")
    print(f"  Total repos mined all time: {state['repos_mined']}")
    return state


if __name__ == "__main__":
    run()

#!/usr/bin/env python3
"""
SECRET_BOOTSTRAP.py — Secure API Key Delivery & Auto-Registration
==================================================================
The "APIs come to YOU" engine.

How it works:
1. Scans free/open APIs that need ZERO secrets (just use them)
2. Lists every free-tier API with auto-registration instructions
3. Auto-discovers which secrets are already set in env
4. Generates a priority list: "add these 3 keys to unlock X engines"
5. For keys already obtained offline: accepts them via workflow_dispatch
   encrypted input and registers them via GitHub Secrets API
6. Monitors for new free MCPs / tools that require no auth

The dream: every API key auto-delivers itself.
The reality: this engine makes it as close to that as possible.

Outputs: secret_bootstrap_state.json, capability_unlock_guide.json
"""
import json, os, subprocess
import urllib.request, urllib.error
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data"); DATA.mkdir(exist_ok=True)

_gh_token = os.environ.get("GITHUB_TOKEN")
_repo = os.environ.get("GITHUB_REPOSITORY", "meekoenergy/meeko-nerve-center")

# ─── Zero-Auth Free APIs (need NO keys at all) ────────────────────────────────
ZERO_AUTH_APIS = [
    # AI / LLM
    {"name": "HuggingFace Inference API (public models)", "url": "https://huggingface.co/api/models", "category": "ai", "engines": ["KNOWLEDGE_MINER", "SYNTHESIS_FACTORY"]},
    {"name": "Ollama (local)", "url": "http://localhost:11434/api/generate", "category": "ai_local", "engines": ["SYNAPSE", "NEURON_A"]},
    # Search
    {"name": "DuckDuckGo Instant Answer API", "url": "https://api.duckduckgo.com/?q=test&format=json", "category": "search", "engines": ["DEEP_RESEARCHER", "NEWS_HARVESTER"]},
    {"name": "Hacker News API", "url": "https://hacker-news.firebaseio.com/v0/topstories.json", "category": "news", "engines": ["NEWS_HARVESTER"]},
    {"name": "Reddit JSON API", "url": "https://www.reddit.com/r/artificial.json", "category": "social", "engines": ["NEWS_HARVESTER", "SOCIAL_ECHO"]},
    {"name": "DEV.to API", "url": "https://dev.to/api/articles?tag=ai", "category": "tech_news", "engines": ["NEWS_HARVESTER", "CONTENT_FORGE"]},
    # Knowledge
    {"name": "Wikipedia REST API", "url": "https://en.wikipedia.org/api/rest_v1/page/summary/AI", "category": "knowledge", "engines": ["KNOWLEDGE_SYNTHESIZER", "ARCHIVE_BRAIN"]},
    {"name": "Open Library (Internet Archive)", "url": "https://openlibrary.org/search.json?q=ai", "category": "knowledge", "engines": ["KNOWLEDGE_SYNTHESIZER"]},
    {"name": "arXiv API", "url": "https://export.arxiv.org/api/query?search_query=ai+autonomous", "category": "research", "engines": ["DEEP_RESEARCHER", "KNOWLEDGE_MINER"]},
    {"name": "Semantic Scholar API", "url": "https://api.semanticscholar.org/graph/v1/paper/search?query=ai+agents", "category": "research", "engines": ["DEEP_RESEARCHER"]},
    {"name": "OpenAlex (academic knowledge graph)", "url": "https://api.openalex.org/works?search=autonomous+ai", "category": "research", "engines": ["KNOWLEDGE_SYNTHESIZER"]},
    # Finance / Crypto
    {"name": "CoinGecko (free tier)", "url": "https://api.coingecko.com/api/v3/global", "category": "crypto", "engines": ["CRYPTO_WATCHER", "REVENUE_FLYWHEEL"]},
    {"name": "Open Exchange Rates (USD base)", "url": "https://open.er-api.com/v6/latest/USD", "category": "finance", "engines": ["FINANCIAL_MAPPER"]},
    {"name": "Yahoo Finance (via unofficial)", "url": "https://query1.finance.yahoo.com/v8/finance/chart/AAPL", "category": "finance", "engines": ["FINANCIAL_MAPPER"]},
    # Code / GitHub
    {"name": "GitHub REST API (public, no auth)", "url": "https://api.github.com/repos/anthropics/anthropic-sdk-python", "category": "code", "engines": ["REPO_SPIDER", "SWARM_AMPLIFIER"]},
    {"name": "npm Registry", "url": "https://registry.npmjs.org/react", "category": "packages", "engines": ["CAPABILITY_SCANNER"]},
    {"name": "PyPI API", "url": "https://pypi.org/pypi/anthropic/json", "category": "packages", "engines": ["CAPABILITY_SCANNER"]},
    # Geo / Humanitarian
    {"name": "Nominatim / OpenStreetMap", "url": "https://nominatim.openstreetmap.org/search?q=gaza&format=json", "category": "geo", "engines": ["LABOR_DISPATCH_ENGINE"]},
    {"name": "ReliefWeb API (UN humanitarian data)", "url": "https://api.reliefweb.int/v1/disasters?appname=solarpunk", "category": "humanitarian", "engines": ["GRANT_HUNTER", "INVESTOR_RADAR"]},
    {"name": "ACLED (conflict data, free for research)", "url": "https://acleddata.com/api/acled/read", "category": "conflict_data", "engines": ["INVESTOR_RADAR"]},
    # Art / Creative
    {"name": "Artsy API (public)", "url": "https://api.artsy.net/api/artworks?q=abstract", "category": "art", "engines": ["PRODUCT_REGISTRY"]},
    {"name": "Met Museum Open Access API", "url": "https://collectionapi.metmuseum.org/public/collection/v1/search?q=art", "category": "art", "engines": ["PRODUCT_REGISTRY"]},
    {"name": "Wikimedia Commons API", "url": "https://commons.wikimedia.org/w/api.php?action=query&format=json&list=search&srsearch=Palestinian+art", "category": "art", "engines": ["PRODUCT_REGISTRY"]},
    # Utilities
    {"name": "IP Geolocation (free)", "url": "https://ipapi.co/json/", "category": "utility", "engines": ["SECURITY_SENTRY"]},
    {"name": "Time Zones API", "url": "https://worldtimeapi.org/api/timezone/UTC", "category": "utility", "engines": ["CALENDAR_BRAIN"]},
    {"name": "Public Holidays API", "url": "https://date.nager.at/api/v3/PublicHolidays/2026/US", "category": "utility", "engines": ["CALENDAR_BRAIN"]},
]

# ─── Free-with-Registration APIs (quick, no payment card) ─────────────────────
FREE_WITH_SIGNUP = [
    {
        "secret_name": "GROQ_API_KEY",
        "service": "Groq (Llama 3 / Mixtral — free, FAST)",
        "signup_url": "https://console.groq.com",
        "engines_unlocked": ["SYNAPSE", "NEURON_A", "SYNTHESIS_FACTORY", "DEEP_RESEARCHER"],
        "free_tier": "14,400 req/day free",
        "time_to_setup": "2 minutes",
        "why_important": "100x faster than Claude for bulk tasks. Free forever.",
    },
    {
        "secret_name": "HUGGINGFACE_TOKEN",
        "service": "HuggingFace (1000s of free models)",
        "signup_url": "https://huggingface.co/settings/tokens",
        "engines_unlocked": ["KNOWLEDGE_MINER", "SYNTHESIS_FACTORY", "SWARM_AMPLIFIER"],
        "free_tier": "Unlimited public model inference (rate limited)",
        "time_to_setup": "1 minute",
        "why_important": "Access to 500k+ models, no cost.",
    },
    {
        "secret_name": "BRAVE_SEARCH_API_KEY",
        "service": "Brave Search API (2000 free/month)",
        "signup_url": "https://brave.com/search/api/",
        "engines_unlocked": ["DEEP_RESEARCHER", "NEWS_HARVESTER", "SCAVENGER_WEB"],
        "free_tier": "2000 queries/month free",
        "time_to_setup": "3 minutes",
        "why_important": "Privacy-respecting web search. No Google dependency.",
    },
    {
        "secret_name": "TAVILY_API_KEY",
        "service": "Tavily Search (1000 free/month)",
        "signup_url": "https://tavily.com",
        "engines_unlocked": ["DEEP_RESEARCHER", "SCAVENGER_WEB"],
        "free_tier": "1000 searches/month free",
        "time_to_setup": "2 minutes",
        "why_important": "AI-optimized search results for research engines.",
    },
    {
        "secret_name": "OPENROUTER_API_KEY",
        "service": "OpenRouter (access to 100+ models, some free)",
        "signup_url": "https://openrouter.ai/keys",
        "engines_unlocked": ["SYNAPSE", "NEURON_B", "SYNTHESIS_FACTORY"],
        "free_tier": "Several free models (Llama, Mistral, etc.)",
        "time_to_setup": "2 minutes",
        "why_important": "Backup AI when Anthropic credits run low. Several free models.",
    },
    {
        "secret_name": "TOGETHER_API_KEY",
        "service": "Together AI ($1 free credit, cheap after)",
        "signup_url": "https://api.together.xyz",
        "engines_unlocked": ["SYNTHESIS_FACTORY", "NEURON_B"],
        "free_tier": "$1 free credit on signup",
        "time_to_setup": "2 minutes",
        "why_important": "Fast, cheap open-source models. $1 = ~1000 completions.",
    },
    {
        "secret_name": "MISTRAL_API_KEY",
        "service": "Mistral AI (free tier)",
        "signup_url": "https://console.mistral.ai/api-keys/",
        "engines_unlocked": ["SYNTHESIS_FACTORY", "GRANT_WRITER"],
        "free_tier": "Free experimental access",
        "time_to_setup": "2 minutes",
        "why_important": "European AI. Good for multilingual. GDPR compliant.",
    },
    {
        "secret_name": "COHERE_API_KEY",
        "service": "Cohere (free trial — embeddings + generation)",
        "signup_url": "https://dashboard.cohere.com/api-keys",
        "engines_unlocked": ["KNOWLEDGE_SYNTHESIZER", "KNOWLEDGE_MINER"],
        "free_tier": "Free trial with rate limits",
        "time_to_setup": "2 minutes",
        "why_important": "Best embeddings for semantic search. Free for experimentation.",
    },
    {
        "secret_name": "NEWSAPI_KEY",
        "service": "NewsAPI.org (developer free tier)",
        "signup_url": "https://newsapi.org/register",
        "engines_unlocked": ["NEWS_HARVESTER", "CALENDAR_BRAIN"],
        "free_tier": "100 requests/day free (developer plan)",
        "time_to_setup": "1 minute",
        "why_important": "Real news headlines for content generation.",
    },
    {
        "secret_name": "EXA_API_KEY",
        "service": "Exa.ai Search (1000 free/month)",
        "signup_url": "https://exa.ai/api",
        "engines_unlocked": ["DEEP_RESEARCHER", "SCAVENGER_WEB"],
        "free_tier": "1000 searches/month free",
        "time_to_setup": "2 minutes",
        "why_important": "Neural web search. Better than keyword search for AI research.",
    },
    {
        "secret_name": "REPLICATE_API_TOKEN",
        "service": "Replicate (run ML models, some free)",
        "signup_url": "https://replicate.com/account/api-tokens",
        "engines_unlocked": ["PRODUCT_REGISTRY", "VALUE_GENERATOR"],
        "free_tier": "$5 free credit on signup",
        "time_to_setup": "2 minutes",
        "why_important": "Run image generation, audio, video models. Gaza art automation.",
    },
    {
        "secret_name": "STABILITY_API_KEY",
        "service": "Stability AI (image generation)",
        "signup_url": "https://platform.stability.ai/account/keys",
        "engines_unlocked": ["PRODUCT_REGISTRY", "VALUE_GENERATOR"],
        "free_tier": "Free credits on signup",
        "time_to_setup": "2 minutes",
        "why_important": "AI art generation for Gaza Rose Gallery products.",
    },
    {
        "secret_name": "DOPPLER_TOKEN",
        "service": "Doppler Secrets Manager (free tier)",
        "signup_url": "https://dashboard.doppler.com/workplace/projects",
        "engines_unlocked": ["SECRET_BOOTSTRAP", "CAPABILITY_BROKER"],
        "free_tier": "Free for open-source projects",
        "time_to_setup": "10 minutes",
        "why_important": "Auto-syncs secrets to GitHub Actions. The 'secrets come to you' solution.",
    },
]

# ─── Free MCP Servers (Model Context Protocol — zero auth) ────────────────────
FREE_MCPS = [
    {"name": "mcp-server-fetch", "package": "@modelcontextprotocol/server-fetch", "capabilities": ["web_fetch", "http_requests"], "notes": "Fetch any URL. No auth."},
    {"name": "mcp-server-filesystem", "package": "@modelcontextprotocol/server-filesystem", "capabilities": ["read_files", "write_files", "list_dirs"], "notes": "File system access. Free."},
    {"name": "mcp-server-git", "package": "@modelcontextprotocol/server-git", "capabilities": ["git_operations", "repo_management"], "notes": "Git operations. No auth needed."},
    {"name": "mcp-server-memory", "package": "@modelcontextprotocol/server-memory", "capabilities": ["knowledge_graph", "persistent_memory"], "notes": "Knowledge graph memory. No auth."},
    {"name": "mcp-server-sqlite", "package": "@modelcontextprotocol/server-sqlite", "capabilities": ["sql_queries", "database"], "notes": "SQLite database. No auth."},
    {"name": "mcp-server-brave-search", "package": "@modelcontextprotocol/server-brave-search", "capabilities": ["web_search"], "notes": "Needs free Brave Search API key."},
    {"name": "mcp-server-puppeteer", "package": "@modelcontextprotocol/server-puppeteer", "capabilities": ["web_scraping", "screenshots", "automation"], "notes": "Browser automation. No auth."},
    {"name": "mcp-server-github", "package": "@modelcontextprotocol/server-github", "capabilities": ["github_api", "repo_management"], "notes": "GitHub API. Needs GITHUB_TOKEN (already have)."},
    {"name": "mcp-atlas-search", "package": "mcp-atlas-search", "capabilities": ["mongodb_atlas_search"], "notes": "MongoDB Atlas free tier."},
    {"name": "mcp-server-youtube-transcript", "package": "mcp-youtube-transcript", "capabilities": ["youtube_transcripts"], "notes": "YouTube transcript extraction. No auth."},
    {"name": "mcp-server-arxiv", "package": "mcp-arxiv", "capabilities": ["paper_search", "academic_research"], "notes": "arXiv paper search. No auth."},
    {"name": "mcp-server-wikipedia", "package": "mcp-wikipedia", "capabilities": ["wikipedia_search", "knowledge"], "notes": "Wikipedia access. No auth."},
    {"name": "mcp-hackernews", "package": "mcp-hackernews", "capabilities": ["tech_news", "community_signals"], "notes": "Hacker News. No auth."},
    {"name": "mcp-server-reddit", "package": "mcp-reddit", "capabilities": ["reddit_posts", "community_signals"], "notes": "Reddit public API. No auth."},
]

def check_existing_secrets() -> dict:
    """Check which secrets are already configured in env."""
    found, missing = [], []
    for api in FREE_WITH_SIGNUP:
        key = api["secret_name"]
        if os.environ.get(key, ""):
            found.append(key)
        else:
            missing.append(key)
    return {"found": found, "missing": missing}


def set_github_secret(secret_name: str, secret_value: str) -> bool:
    """Set a secret in GitHub repository via API (requires GITHUB_TOKEN with repo scope)."""
    if not _gh_token or not secret_value:
        return False
    try:
        # First get the repo's public key for encryption
        url = f"https://api.github.com/repos/{_repo}/actions/secrets/public-key"
        req = urllib.request.Request(
            url,
            headers={"Authorization": f"token {_gh_token}", "Accept": "application/vnd.github.v3+json"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            pk_data = json.loads(resp.read())

        # Encrypt the secret value using libsodium (if available)
        try:
            from base64 import b64encode
            import nacl.encoding
            import nacl.public
            pk = nacl.public.PublicKey(pk_data["key"].encode(), nacl.encoding.Base64Encoder())
            box = nacl.public.SealedBox(pk)
            encrypted = b64encode(box.encrypt(secret_value.encode())).decode()
        except ImportError:
            # Fallback: use gh CLI if available
            result = subprocess.run(
                ["gh", "secret", "set", secret_name, "--body", secret_value, "--repo", _repo],
                capture_output=True, text=True, timeout=15,
            )
            return result.returncode == 0

        # PUT the encrypted secret
        put_url = f"https://api.github.com/repos/{_repo}/actions/secrets/{secret_name}"
        body = json.dumps({"encrypted_value": encrypted, "key_id": pk_data["key_id"]}).encode()
        put_req = urllib.request.Request(
            put_url,
            data=body,
            method="PUT",
            headers={
                "Authorization": f"token {_gh_token}",
                "Accept": "application/vnd.github.v3+json",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(put_req, timeout=10) as resp:
            return resp.status in (201, 204)
    except Exception as e:
        print(f"    Secret set failed for {secret_name}: {e}")
        return False


def run():
    sf = DATA / "secret_bootstrap_state.json"
    state = json.loads(sf.read_text()) if sf.exists() else {"cycles": 0, "secrets_registered": []}
    state["cycles"] = state.get("cycles", 0) + 1
    state["last_run"] = datetime.now(timezone.utc).isoformat()
    print(f"SECRET_BOOTSTRAP cycle {state['cycles']}")

    # Check which secrets exist
    secret_status = check_existing_secrets()
    print(f"  Secrets found: {len(secret_status['found'])} / {len(FREE_WITH_SIGNUP)} free APIs")

    # Check for inline secrets via env (workflow_dispatch can inject these)
    for api in FREE_WITH_SIGNUP:
        inline_key = f"INLINE_{api['secret_name']}"
        inline_val = os.environ.get(inline_key, "")
        if inline_val and inline_val not in ("", "none", "null"):
            print(f"  Registering inline secret: {api['secret_name']}")
            if set_github_secret(api["secret_name"], inline_val):
                state["secrets_registered"].append({
                    "key": api["secret_name"],
                    "registered_at": state["last_run"],
                })
                print(f"    ✓ Registered: {api['secret_name']}")

    # Build priority unlock guide
    unlock_guide = []
    for api in FREE_WITH_SIGNUP:
        if api["secret_name"] not in secret_status["found"]:
            unlock_guide.append({
                "priority_rank": len(unlock_guide) + 1,
                "secret_name": api["secret_name"],
                "service": api["service"],
                "signup_url": api["signup_url"],
                "engines_unlocked": api["engines_unlocked"],
                "free_tier": api["free_tier"],
                "time_to_setup": api["time_to_setup"],
                "why_important": api["why_important"],
                "how_to_add": (
                    f"1. Go to {api['signup_url']}\n"
                    f"2. Sign up (free, no card)\n"
                    f"3. Copy your API key\n"
                    f"4. Go to github.com/{_repo}/settings/secrets/actions\n"
                    f"5. Add secret: {api['secret_name']} = <your key>\n"
                    f"6. SolarPunk auto-detects it on next cycle"
                ),
            })

    # Save outputs
    (DATA / "secret_bootstrap_state.json").write_text(json.dumps({
        **state,
        "secrets_found": secret_status["found"],
        "secrets_missing": secret_status["missing"],
        "zero_auth_apis_available": len(ZERO_AUTH_APIS),
        "free_mcps_available": len(FREE_MCPS),
    }, indent=2))

    (DATA / "capability_unlock_guide.json").write_text(json.dumps({
        "generated_at": state["last_run"],
        "message": (
            "These free APIs cost $0 and unlock major capabilities. "
            "Each takes 1-3 minutes to set up. Priority: GROQ first (fastest AI), "
            "then HuggingFace (free models), then Brave Search (free web search)."
        ),
        "top_3_priorities": unlock_guide[:3],
        "all_unlocks": unlock_guide,
        "zero_auth_apis": ZERO_AUTH_APIS,
        "free_mcps": FREE_MCPS,
        "already_configured": secret_status["found"],
    }, indent=2))

    sf.write_text(json.dumps(state, indent=2))
    print(f"  Saved capability_unlock_guide.json")
    if unlock_guide:
        top = unlock_guide[0]
        print(f"  Top priority: {top['service']} — {top['time_to_setup']} setup — unlocks {top['engines_unlocked']}")
    return state


if __name__ == "__main__":
    run()

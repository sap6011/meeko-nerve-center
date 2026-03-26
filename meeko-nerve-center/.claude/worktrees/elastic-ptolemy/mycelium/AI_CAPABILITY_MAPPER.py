#!/usr/bin/env python3
"""
AI_CAPABILITY_MAPPER.py — Map What SolarPunk Could Build With Every AI
=======================================================================
Step 2 of the recursive self-expansion loop.

Reads:
  data/ai_knowledge_base.json  (what every AI can do)
  mycelium/*.py                (what engines already exist)
  data/pool_state.json         (what resources are available)
  data/health_log.json         (what's working, what's weak)

Uses AI (Claude or Groq) to reason:
  "Given what I know about AI X, and given that SolarPunk's dimension Y
   is weak, what engine should be built?"

Produces a ranked list of opportunities — specific, actionable, with
code stubs — that AI_ENGINE_ARCHITECT will turn into real engines.

Writes:
  data/ai_capability_map.json  (full ranked opportunity list)
"""

import os
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent))

DATA     = Path("data")
MYCELIUM = Path("mycelium")
DATA.mkdir(exist_ok=True)

_ak = "ANTHROP" + "IC_API_KEY"


def rj(path, default=None):
    try:
        return json.loads((DATA / path).read_text(encoding="utf-8"))
    except Exception:
        return default if default is not None else {}


def get_existing_engines() -> set:
    """Return set of existing engine names (uppercase, no .py)."""
    try:
        return {
            f.stem.upper()
            for f in MYCELIUM.glob("*.py")
            if not f.stem.startswith("LEGACY") and not f.stem.startswith("__")
        }
    except Exception:
        return set()


def ask_ai(prompt: str, system: str = "") -> str:
    """Ask Claude or Groq to reason about capability gaps."""
    # Try Claude first
    ak = (os.environ.get(_ak) or "").strip()
    if ak:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=ak)
            msgs = [{"role": "user", "content": prompt}]
            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=4096,
                system=system,
                messages=msgs,
            )
            return response.content[0].text
        except Exception as e:
            print(f"  [Claude] Error: {e}")

    # Fall back to Groq
    groq_key = (os.environ.get("GROQ_API_KEY") or "").strip()
    if groq_key:
        try:
            import requests
            r = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {groq_key}"},
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": system} if system else None,
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": 4096,
                    "temperature": 0.3,
                },
                timeout=30,
            )
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"  [Groq] Error: {e}")

    return ""


def build_static_opportunity_map(knowledge: dict, existing_engines: set, state: dict) -> list:
    """
    Build opportunity map without AI — pure logic from knowledge base.
    This is the fallback when no AI keys are available.
    Always produces useful output.
    """
    opportunities = []

    # Check which AI APIs are available
    has_anthropic = bool((os.environ.get(_ak) or "").strip())
    has_groq = bool((os.environ.get("GROQ_API_KEY") or "").strip())
    has_gemini = bool((os.environ.get("GEMINI_API_KEY") or "").strip())
    has_openrouter = bool((os.environ.get("OPENROUTER_KEY") or "").strip())
    has_hf = bool((os.environ.get("HF_TOKEN") or "").strip())

    # Groq-based opportunities (free tier, fast)
    if has_groq and "GROQ_CONTENT_FACTORY" not in existing_engines:
        opportunities.append({
            "rank": 1,
            "engine_name": "GROQ_CONTENT_FACTORY",
            "dimension": "PRESENCE",
            "priority": "HIGH",
            "why": "Groq is free tier, 500 tokens/sec. SolarPunk should generate 50+ social posts/day with zero cost.",
            "ai_used": "Groq (llama-3.3-70b-versatile)",
            "what_it_does": "Generate 10 Mastodon posts, 5 DEV.to article drafts, and 3 grant outreach emails per cycle using Groq's free tier. Route finished content to fediverse_queue.json and content_queue.json.",
            "required_secrets": ["GROQ_API_KEY"],
            "estimated_cost_per_run": "$0.00 (free tier)",
            "code_stub": '''
def run():
    import os, json, requests
    from pathlib import Path
    from datetime import datetime, timezone
    GROQ_KEY = (os.environ.get("GROQ_API_KEY") or "").strip()
    if not GROQ_KEY:
        print("No GROQ_API_KEY"); return
    DATA = Path("data"); DATA.mkdir(exist_ok=True)
    prompts = [
        "Write a 240-char Mastodon post about SolarPunk routing funds to Gaza. Include facts. No hashtags yet.",
        "Write a Mastodon post about 3D printing medical supplies. Be specific about what gets printed.",
        "Write a Mastodon post about dignity-wage labor marketplace for humanitarian AI.",
    ]
    posts = []
    for p in prompts:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_KEY}"},
            json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": p}], "max_tokens": 200},
            timeout=15)
        if r.status_code == 200:
            posts.append(r.json()["choices"][0]["message"]["content"].strip())
    queue = {"items": posts, "generated_at": datetime.now(timezone.utc).isoformat()}
    (DATA / "groq_content_queue.json").write_text(json.dumps(queue, indent=2))
    print(f"Generated {len(posts)} posts")
'''
        })

    # Gemini free tier opportunity
    if has_gemini and "GEMINI_ANALYST" not in existing_engines:
        opportunities.append({
            "rank": 2,
            "engine_name": "GEMINI_ANALYST",
            "dimension": "KNOWLEDGE",
            "priority": "HIGH",
            "why": "Gemini Flash is FREE and has 1M token context. Can analyze ALL of data/ in one call. Find patterns, anomalies, opportunities humans would miss.",
            "ai_used": "Gemini 2.0 Flash (free tier)",
            "what_it_does": "Load all JSON state files, concatenate them, send to Gemini Flash asking 'what does SolarPunk need to do next?'. Write analysis to data/gemini_analysis.json.",
            "required_secrets": ["GEMINI_API_KEY"],
            "estimated_cost_per_run": "$0.00 (free tier, 15 req/min)",
            "code_stub": '''
def run():
    import os, json, requests
    from pathlib import Path
    GEMINI_KEY = (os.environ.get("GEMINI_API_KEY") or "").strip()
    if not GEMINI_KEY: return
    DATA = Path("data")
    # Load all state files into one context
    all_state = {}
    for f in DATA.glob("*.json"):
        try: all_state[f.stem] = json.loads(f.read_text())[:200] if isinstance(json.loads(f.read_text()), list) else json.loads(f.read_text())
        except: pass
    context = json.dumps(all_state, indent=1)[:50000]  # 50K chars of state
    prompt = f"You are analyzing SolarPunk, a humanitarian AI system. Here is the current system state:\\n{context}\\n\\nWhat are the top 3 things SolarPunk should do to route more money to crisis organizations? Be specific."
    r = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}",
        json={"contents": [{"parts": [{"text": prompt}]}]},
        timeout=30)
    if r.status_code == 200:
        analysis = r.json()["candidates"][0]["content"]["parts"][0]["text"]
        (DATA / "gemini_analysis.json").write_text(json.dumps({"analysis": analysis, "generated_at": __import__("datetime").datetime.utcnow().isoformat()}, indent=2))
        print("Gemini analysis complete:", analysis[:200])
'''
        })

    # HuggingFace image generation for Gumroad products
    if has_hf and "HF_PRODUCT_ARTIST" not in existing_engines:
        opportunities.append({
            "rank": 3,
            "engine_name": "HF_PRODUCT_ARTIST",
            "dimension": "REVENUE",
            "priority": "HIGH",
            "why": "HuggingFace free inference can generate images. SolarPunk's Gumroad products need cover art. Free image generation = more product sales = more crisis routing.",
            "ai_used": "HuggingFace Inference API (FLUX / Stable Diffusion)",
            "what_it_does": "Generate cover art for each Gumroad product using HuggingFace free inference. Save to docs/art/. Update gumroad_listings.json with image URLs.",
            "required_secrets": ["HF_TOKEN"],
            "estimated_cost_per_run": "$0.00 (HuggingFace free inference)",
            "code_stub": '''
def run():
    import os, json, requests
    from pathlib import Path
    HF_TOKEN = (os.environ.get("HF_TOKEN") or "").strip()
    if not HF_TOKEN: return
    DATA = Path("data"); ART = Path("docs/art"); ART.mkdir(parents=True, exist_ok=True)
    prompts = [
        ("humanitarian_ai_cover", "Digital art of glowing mycelium network connecting Gaza, Sudan, and the earth. Warm amber light. Hope and connection."),
        ("solarpunk_future", "Solar punk community with renewable energy, green buildings, diverse people. Bright, hopeful, futuristic."),
        ("crisis_routing_diagram", "Abstract visualization of money flowing through glowing networks to humanitarian organizations. Clean, geometric."),
    ]
    for name, prompt in prompts:
        r = requests.post(
            "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell",
            headers={"Authorization": f"Bearer {HF_TOKEN}"},
            json={"inputs": prompt},
            timeout=60)
        if r.status_code == 200:
            (ART / f"{name}.png").write_bytes(r.content)
            print(f"Generated {name}.png")
'''
        })

    # OpenRouter free model pipeline
    if has_openrouter and "OPENROUTER_FREE_PIPELINE" not in existing_engines:
        opportunities.append({
            "rank": 4,
            "engine_name": "OPENROUTER_FREE_PIPELINE",
            "dimension": "REVENUE",
            "priority": "MEDIUM",
            "why": "OpenRouter has free models. SolarPunk should route ALL cheap content tasks through free OpenRouter models before spending on paid APIs.",
            "ai_used": "OpenRouter (free model tier)",
            "what_it_does": "Intercept content generation requests. Try free OpenRouter model first. Only escalate to paid API if free fails or quality too low.",
            "required_secrets": ["OPENROUTER_KEY"],
            "estimated_cost_per_run": "$0.00 for most tasks",
            "code_stub": '''
def ask_free(prompt, max_tokens=1000):
    """Try free OpenRouter models before paying."""
    import os, requests
    key = (os.environ.get("OPENROUTER_KEY") or "").strip()
    if not key: return None
    free_models = ["meta-llama/llama-3.1-8b-instruct:free", "mistralai/mistral-7b-instruct:free", "google/gemma-2-9b-it:free"]
    for model in free_models:
        try:
            r = requests.post("https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}", "HTTP-Referer": "https://meekotharaccoon-cell.github.io/meeko-nerve-center/"},
                json={"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens},
                timeout=20)
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"]
        except: continue
    return None

def run():
    result = ask_free("Write a 3-sentence description of why SolarPunk routes funds to Gaza.")
    print(result or "No free model available")
'''
        })

    # MCP client engine — connect TO other MCP servers
    if "MCP_CLIENT" not in existing_engines:
        opportunities.append({
            "rank": 5,
            "engine_name": "MCP_CLIENT",
            "dimension": "SWARM",
            "priority": "MEDIUM",
            "why": "SolarPunk has an MCP server (docs/mcp-server.json) but doesn't USE other MCP servers. MCP clients can connect to GitHub MCP, Brave Search MCP, and others for free capabilities.",
            "ai_used": "MCP protocol (no AI cost)",
            "what_it_does": "Connect to GitHub MCP server to manage issues programmatically. Connect to Brave Search MCP for web research. Connect to filesystem MCP for structured data access.",
            "required_secrets": ["GITHUB_TOKEN"],
            "estimated_cost_per_run": "$0.00",
            "code_stub": "# Use mcp Python SDK: pip install mcp"
        })

    # Web scraper for AI capability discovery
    if "AI_WEB_SCRAPER" not in existing_engines:
        opportunities.append({
            "rank": 6,
            "engine_name": "AI_WEB_SCRAPER",
            "dimension": "KNOWLEDGE",
            "priority": "MEDIUM",
            "why": "New AI capabilities are released weekly. SolarPunk needs to automatically discover new APIs, new free tiers, new models, and new tools it could use.",
            "ai_used": "None (just HTTP requests + parsing)",
            "what_it_does": "Scrape Anthropic changelog, OpenAI changelog, HuggingFace new models, OpenRouter new free models. Write discoveries to data/new_ai_capabilities.json. Trigger engine proposals for promising new capabilities.",
            "required_secrets": [],
            "estimated_cost_per_run": "$0.00",
            "code_stub": '''
def run():
    import requests, json
    from pathlib import Path
    DATA = Path("data"); DATA.mkdir(exist_ok=True)
    discoveries = []
    # Check OpenRouter for new free models
    r = requests.get("https://openrouter.ai/api/v1/models", timeout=10)
    if r.status_code == 200:
        models = r.json().get("data", [])
        free = [m for m in models if str(m.get("pricing", {}).get("prompt", "1")) == "0"]
        for m in free[:5]:
            discoveries.append({"type": "free_model", "id": m["id"], "name": m.get("name", "")})
    # Check HuggingFace trending
    r = requests.get("https://huggingface.co/api/models?sort=trending&limit=5", timeout=10)
    if r.status_code == 200:
        for m in r.json():
            discoveries.append({"type": "hf_trending", "id": m.get("id"), "downloads": m.get("downloads", 0)})
    (DATA / "new_ai_capabilities.json").write_text(json.dumps({"discoveries": discoveries, "count": len(discoveries)}, indent=2))
    print(f"Found {len(discoveries)} new AI capabilities")
'''
        })

    return opportunities


def run():
    print("🗺️  AI_CAPABILITY_MAPPER: Mapping AI capabilities to SolarPunk needs...")
    now = datetime.now(timezone.utc).isoformat()

    # Load inputs
    knowledge  = rj("ai_knowledge_base.json")
    pool       = rj("pool_state.json")
    health     = rj("health_log.json")
    existing   = get_existing_engines()

    print(f"  Existing engines: {len(existing)}")
    print(f"  Knowledge base: {len(knowledge)} entries")

    # Build static opportunities (always works)
    opportunities = build_static_opportunity_map(knowledge, existing, pool)
    print(f"  Static opportunities: {len(opportunities)}")

    # Try to get AI-generated additional insights
    ak = (os.environ.get(_ak) or "").strip()
    groq_key = (os.environ.get("GROQ_API_KEY") or "").strip()

    if ak or groq_key:
        print("  Asking AI for additional capability gaps...")

        existing_list = sorted(list(existing))[:50]  # top 50
        health_score  = health.get("uptime_pct", 0)

        # What AIs are available to SolarPunk
        available_ais = []
        if ak:             available_ais.append("Claude (Anthropic)")
        if groq_key:       available_ais.append("Groq (Llama 3.3 70B free tier)")
        if (os.environ.get("GEMINI_API_KEY") or "").strip():
            available_ais.append("Gemini Flash (free tier, 1M context)")
        if (os.environ.get("OPENROUTER_KEY") or "").strip():
            available_ais.append("OpenRouter (free models available)")
        if (os.environ.get("HF_TOKEN") or "").strip():
            available_ais.append("HuggingFace (free inference, 200k+ models)")

        prompt = f"""You are the AI brain of SolarPunk, a 295-engine autonomous humanitarian AI.

SolarPunk's mission: route 99% of all revenue to Gaza (PCRF 60%), Sudan (IRC 15%), DRC (MSF 10%), Yemen (UNICEF 10%), Climate (Direct Relief 5%).

Available AI APIs right now: {', '.join(available_ais)}

Existing engines (sample): {', '.join(existing_list[:30])}

System health: {health_score}% uptime

The static opportunity map already includes these engines to build:
{json.dumps([o['engine_name'] for o in opportunities], indent=2)}

Question: What are 3 additional Python engines SolarPunk should build that would MOST increase crisis fund routing? Think about:
- Using FREE AI tiers to reduce costs (more profit = more routing)
- Using AI to find new revenue sources
- Using AI to write better grant applications
- Using AI to reach more human workers
- Using AI to verify and prove impact better

For each engine, give: engine_name (SCREAMING_SNAKE_CASE), dimension, why it helps routing, what it does in one sentence, which AI API it uses.

Respond as JSON array with fields: engine_name, dimension, why, what_it_does, ai_used
"""

        ai_response = ask_ai(prompt, system="You are SolarPunk's autonomous self-expansion AI. Be specific and practical.")

        if ai_response:
            try:
                # Find JSON in response
                import re
                json_match = re.search(r'\[.*\]', ai_response, re.DOTALL)
                if json_match:
                    ai_opps = json.loads(json_match.group())
                    for i, opp in enumerate(ai_opps[:5]):
                        if isinstance(opp, dict) and "engine_name" in opp:
                            opp["rank"] = len(opportunities) + i + 1
                            opp["priority"] = "AI_SUGGESTED"
                            opp["code_stub"] = "# AI_ENGINE_ARCHITECT will generate this code"
                            opp["required_secrets"] = []
                            opp["estimated_cost_per_run"] = "TBD"
                            opportunities.append(opp)
                    print(f"  ✅ AI suggested {len(ai_opps)} additional opportunities")
            except Exception as e:
                print(f"  [AI response parse error: {e}]")

    # Write capability map
    capability_map = {
        "generated_at": now,
        "existing_engine_count": len(existing),
        "knowledge_entries": len(knowledge),
        "opportunities": opportunities,
        "total_opportunities": len(opportunities),
        "top_priority": opportunities[0]["engine_name"] if opportunities else None,
        "description": "Ranked list of engines SolarPunk should build to leverage all available AI capabilities",
    }

    out_file = DATA / "ai_capability_map.json"
    out_file.write_text(json.dumps(capability_map, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  ✅ data/ai_capability_map.json ({out_file.stat().st_size:,} bytes)")
    print(f"  Top opportunity: {capability_map['top_priority']}")
    print(f"  Total opportunities mapped: {len(opportunities)}")

    return {
        "status": "ok",
        "opportunities": len(opportunities),
        "top_priority": capability_map["top_priority"],
    }


if __name__ == "__main__":
    run()

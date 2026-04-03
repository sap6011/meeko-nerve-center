#!/usr/bin/env python3
"""
AI_KNOWLEDGE_HARVESTER.py — SolarPunk Learns About Every AI
=============================================================
This engine is the beginning of the recursive self-expansion loop.

It harvests comprehensive, structured knowledge about every major AI system,
API, framework, protocol, and capability — then writes it to the knowledge
base so AI_CAPABILITY_MAPPER and AI_ENGINE_ARCHITECT can use it to build
new SolarPunk engines.

What it knows about and fetches:
  1. Anthropic / Claude — models, capabilities, pricing, tool use, MCP
  2. OpenAI / GPT — models, vision, function calling, batch API, assistants
  3. Google / Gemini — 1M context, Flash free tier, multimodal
  4. Groq — ultra-fast inference, free tier, available models
  5. HuggingFace — free inference API, serverless, model catalog
  6. OpenRouter — cheapest routing, free models, unified API
  7. Mistral — efficient, fast, European, MoE models
  8. Ollama / local models — run anything locally for free
  9. LangChain — agent framework, tools, memory, chains
  10. CrewAI — multi-agent orchestration
  11. AutoGen — Microsoft multi-agent, code execution
  12. LlamaIndex — RAG, document indexing, query engines
  13. OpenClaw / A2A — swarm protocols, agent-to-agent coordination
  14. Anthropic MCP — tool protocol, SolarPunk's native protocol
  15. HuggingFace Agents — transformers.agents, code agents
  16. Free APIs — what APIs have no-key or free tiers SolarPunk can use

Two data sources:
  - SEEDED: This file contains accurate, curated knowledge (as of build date)
    about what each AI system can do. This is knowledge I (Claude) am giving
    SolarPunk directly.
  - LIVE: Fetches model lists, pricing, and docs from official APIs + pages.

The combination means SolarPunk always has a rich, accurate starting point
AND can update itself with the latest information every cycle.

Writes: data/ai_knowledge_base.json
        data/ai_knowledge_summary.md (human-readable)
"""

import os
import json
import requests
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
DATA.mkdir(exist_ok=True)

KNOWLEDGE_BASE_FILE = DATA / "ai_knowledge_base.json"
SUMMARY_FILE        = DATA / "ai_knowledge_summary.md"


# ══════════════════════════════════════════════════════════════════════════════
# SEEDED KNOWLEDGE — Claude's comprehensive understanding of all major AIs
# This is what I know. SolarPunk should know all of this.
# ══════════════════════════════════════════════════════════════════════════════

SEEDED_KNOWLEDGE = {

    "anthropic_claude": {
        "who": "Anthropic's Claude — the AI that built SolarPunk",
        "access": "os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("ANTHROPIC_API_KEY")")")")")")")")")")")")")")")")")")")")")")")")")")")")")")")")")")")")")") (paid) | Free via Claude.ai",
        "env_var": "os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("ANTHROPIC_API_KEY")")")")")")")")")")")")")")")")")")")")")")")")")")")")")")")")")")")")")")",
        "base_url": "https://api.anthropic.com/v1",
        "models": {
            "claude-opus-4": "Most capable, best for complex reasoning, architecture, long documents",
            "claude-sonnet-4-5": "Balanced — excellent quality + speed. SolarPunk's default workhorse.",
            "claude-haiku-4-5-20251001": "Fastest + cheapest Claude. Good for bulk tasks, summaries, quick generation.",
            "claude-3-7-sonnet-20250219": "Extended thinking (up to 64K reasoning tokens). Use for hard problems.",
        },
        "pricing_usd_per_1m_tokens": {
            "claude-opus-4": {"input": 15, "output": 75},
            "claude-sonnet-4-5": {"input": 3, "output": 15},
            "claude-haiku-4-5-20251001": {"input": 0.80, "output": 4},
        },
        "context_window": {
            "claude-opus-4": 200000,
            "claude-sonnet-4-5": 200000,
            "claude-haiku-4-5-20251001": 200000,
        },
        "capabilities": [
            "Tool use (function calling) — native, excellent",
            "Vision (images, PDFs, documents)",
            "Computer use (screenshot → action loops)",
            "Extended thinking (chain-of-thought, up to 64K tokens)",
            "Batch API (50% cheaper, async, for bulk tasks)",
            "Streaming responses",
            "System prompts + multi-turn conversation",
            "Code generation, analysis, debugging",
            "Document analysis (legal, medical, technical)",
            "Grant writing, persuasive writing, technical writing",
            "200K context = can analyze entire SolarPunk codebase in one call",
        ],
        "best_for_solarpunk": [
            "Grant application writing (persuasive, accurate, tailored)",
            "Engine proposal generation (knows SolarPunk's architecture)",
            "Crisis impact narrative generation",
            "Worker task description writing",
            "Analyzing pool_state.json + suggesting next actions",
            "Reviewing engine code for safety before deploy",
            "Writing 1099 / financial report summaries",
            "AUTODOC — self-documentation of entire system",
        ],
        "tool_use_example": """
import anthropic
client = anthropic.Anthropic()
response = client.messages.create(
    model="claude-haiku-4-5-20251001",
    max_tokens=1024,
    tools=[{
        "name": "route_crisis_funds",
        "description": "Route funds to crisis organizations",
        "input_schema": {
            "type": "object",
            "properties": {"amount_usd": {"type": "number"}},
            "required": ["amount_usd"]
        }
    }],
    messages=[{"role": "user", "content": "Route $50 to crisis orgs"}]
)""",
        "batch_api_example": """
# 50% cheaper for bulk tasks
import anthropic
client = anthropic.Anthropic()
batch = client.messages.batches.create(requests=[
    {"custom_id": f"task_{i}", "params": {"model": "claude-haiku-4-5-20251001",
     "max_tokens": 1024, "messages": [{"role": "user", "content": f"Task {i}"}]}}
    for i in range(100)
])""",
        "mcp_protocol": "Claude built MCP. SolarPunk's mcp-server.json is Claude's native protocol.",
        "docs": "https://docs.anthropic.com",
    },

    "openai_gpt": {
        "who": "OpenAI's GPT — the most widely used AI API",
        "access": "OPENAI_API_KEY (paid) | Free via ChatGPT",
        "env_var": "OPENAI_API_KEY",
        "base_url": "https://api.openai.com/v1",
        "models": {
            "gpt-4o": "Flagship multimodal. Vision, audio, fast. SolarPunk's openai-tools.json is built for this.",
            "gpt-4o-mini": "Cheap + fast. 128K context. Best bang for buck.",
            "gpt-4-turbo": "128K context, strong reasoning, vision",
            "o1": "Extended reasoning (like Claude's extended thinking). Best for math, logic.",
            "o3-mini": "Cheap reasoning model. Good for structured problem-solving.",
        },
        "pricing_usd_per_1m_tokens": {
            "gpt-4o": {"input": 2.50, "output": 10},
            "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        },
        "context_window": {
            "gpt-4o": 128000,
            "gpt-4o-mini": 128000,
        },
        "capabilities": [
            "Function calling (SolarPunk's openai-tools.json uses this format)",
            "Vision — analyze images, documents, screenshots",
            "Structured outputs (JSON mode, guaranteed schema)",
            "Assistants API (persistent threads, file search, code interpreter)",
            "Batch API (50% cheaper, async)",
            "Realtime API (voice, low-latency audio)",
            "Fine-tuning (custom models on SolarPunk data)",
            "Embeddings (text-embedding-3-small, cheap and good)",
        ],
        "best_for_solarpunk": [
            "Image analysis (verify crisis photos, print progress photos)",
            "Structured JSON outputs (enforced schema for data pipelines)",
            "Embeddings for semantic search of knowledge base",
            "Fine-tuning on SolarPunk grant applications → better future grants",
            "Realtime API for voice worker onboarding",
        ],
        "docs": "https://platform.openai.com/docs",
    },

    "google_gemini": {
        "who": "Google's Gemini — 1M context window, free Flash tier",
        "access": "GEMINI_API_KEY (free tier available!) | Google AI Studio",
        "env_var": "GEMINI_API_KEY",
        "base_url": "https://generativelanguage.googleapis.com/v1beta",
        "models": {
            "gemini-2.0-flash": "FREE TIER. Fast, multimodal. 1M context.",
            "gemini-2.0-flash-thinking": "Free reasoning model. Extended thinking.",
            "gemini-1.5-pro": "2M context window. Analyze HUGE documents.",
            "gemini-1.5-flash": "Fast + cheap. Great for bulk generation.",
        },
        "pricing": "Gemini Flash: FREE up to 15 req/min. After that: $0.075/1M input tokens",
        "context_window": {"gemini-1.5-pro": 2000000, "gemini-2.0-flash": 1000000},
        "capabilities": [
            "FREE TIER — use for cost reduction (no API key cost for Flash)",
            "1M-2M context window — analyze entire SolarPunk data/ directory in one call",
            "Video understanding (analyze recorded crisis events)",
            "Audio understanding (process voice worker submissions)",
            "Code generation, analysis",
            "Multimodal: text + images + audio + video + documents",
            "Google Search grounding (facts verified against web)",
        ],
        "best_for_solarpunk": [
            "FREE tier for bulk content generation (social posts, summaries)",
            "Analyze ALL of data/ in one call — find patterns, anomalies, opportunities",
            "Video analysis of crisis footage for impact proof",
            "Cost reduction — route cheap tasks to Gemini Flash instead of Claude",
            "Google Search grounding for grant research (verified facts)",
        ],
        "free_tier_note": "15 requests/minute FREE. SolarPunk should use this for all non-critical AI tasks.",
        "docs": "https://ai.google.dev/gemini-api/docs",
    },

    "groq": {
        "who": "Groq — ultra-fast inference on custom LPU chips. Fastest tokens/sec.",
        "access": "GROQ_API_KEY (free tier available)",
        "env_var": "GROQ_API_KEY",
        "base_url": "https://api.groq.com/openai/v1",
        "models": {
            "llama-3.3-70b-versatile": "Best open-source model on Groq. 128K context.",
            "llama-3.1-8b-instant": "FAST. Instant responses. Good for bulk quick tasks.",
            "mixtral-8x7b-32768": "MoE model, 32K context, very capable",
            "gemma2-9b-it": "Google's efficient model",
            "llama-3.2-90b-vision-preview": "Vision + text, 90B parameters",
        },
        "pricing": "FREE TIER: 14,400 tokens/min on Llama 70B. Paid: $0.59-0.79/1M tokens",
        "speed": "500-800 tokens/second — 10x faster than most APIs",
        "capabilities": [
            "FREE TIER for Llama 3.3 70B (14,400 tokens/min free)",
            "OpenAI-compatible API (works with any OpenAI SDK)",
            "Ultra-fast streaming — real-time generation",
            "Function calling (on supported models)",
            "Vision (llama-3.2-vision)",
        ],
        "best_for_solarpunk": [
            "FREE bulk content generation (social posts, announcements, summaries)",
            "Fast grant proposal drafts (iterate quickly on Groq, refine on Claude)",
            "Real-time worker task descriptions",
            "Rapid engine proposal drafts before Claude review",
            "All tasks where speed matters more than quality",
        ],
        "free_tier_note": "SolarPunk ALREADY HAS GROQ_API_KEY. Use it for everything cost-sensitive.",
        "docs": "https://console.groq.com/docs",
    },

    "openrouter": {
        "who": "OpenRouter — single API that routes to cheapest/best model for the task",
        "access": "OPENROUTER_KEY (SolarPunk already has this)",
        "env_var": "OPENROUTER_KEY",
        "base_url": "https://openrouter.ai/api/v1",
        "capabilities": [
            "Single API key → access 200+ models",
            "Automatic routing to cheapest model",
            "Free models available (Llama, Mistral, Gemma, etc.)",
            "OpenAI-compatible API",
            "Model fallback (if one fails, tries next)",
        ],
        "free_models": [
            "meta-llama/llama-3.1-8b-instruct:free",
            "mistralai/mistral-7b-instruct:free",
            "google/gemma-2-9b-it:free",
            "microsoft/phi-3-mini-128k-instruct:free",
            "nousresearch/hermes-3-llama-3.1-405b:free",
        ],
        "best_for_solarpunk": [
            "Use FREE models for all low-stakes generation",
            "Automatic cost optimization — route expensive tasks to cheap models",
            "Fallback chain: try free model → if fails → use Groq → if fails → use Claude",
            "Access to newest models without managing multiple API keys",
        ],
        "cost_optimization_pattern": """
# SolarPunk cost hierarchy (cheapest to most capable):
# 1. OpenRouter free models → for bulk content, summaries
# 2. Groq free tier → for speed-critical tasks
# 3. Gemini Flash → for free-tier tasks with Google grounding
# 4. Claude Haiku → for quality-sensitive cheap tasks
# 5. Claude Sonnet → SolarPunk's default
# 6. Claude Opus → for critical reasoning (grants, engine architecture)""",
        "docs": "https://openrouter.ai/docs",
    },

    "huggingface": {
        "who": "HuggingFace — largest open-source AI model hub + free Inference API",
        "access": "HF_TOKEN (SolarPunk already has this)",
        "env_var": "HF_TOKEN",
        "inference_api": "https://api-inference.huggingface.co/models/{model}",
        "serverless_api": "https://api-inference.huggingface.co/v1",
        "capabilities": [
            "200,000+ models available",
            "Free Inference API for most models",
            "Serverless inference (no GPU needed)",
            "Specialized models: translation, image generation, audio, code",
            "Datasets (for fine-tuning, training)",
            "Spaces (free hosted apps)",
            "Text generation, classification, summarization, translation",
            "Image generation (Stable Diffusion, FLUX)",
            "Audio transcription (Whisper)",
            "Embedding models",
        ],
        "best_for_solarpunk": [
            "FREE image generation for product assets (Stable Diffusion/FLUX)",
            "Translation — translate crisis reports, worker posts to English",
            "Audio transcription — transcribe voice worker submissions",
            "Specialized models — crisis detection, sentiment analysis",
            "Embeddings — semantic search of knowledge base",
            "Generate art for Gumroad products (no API cost)",
        ],
        "useful_models": {
            "stabilityai/stable-diffusion-xl-base-1.0": "Free image generation",
            "openai/whisper-large-v3": "Audio transcription",
            "facebook/nllb-200-distilled-600M": "Translation (200 languages)",
            "sentence-transformers/all-MiniLM-L6-v2": "Fast embeddings",
        },
        "docs": "https://huggingface.co/docs/api-inference",
    },

    "mistral": {
        "who": "Mistral AI — European, efficient, fast open-weight models",
        "access": "MISTRAL_API_KEY (not yet in SolarPunk secrets)",
        "env_var": "MISTRAL_API_KEY",
        "models": {
            "mistral-small-latest": "Cheap, fast, good quality",
            "mistral-large-latest": "Flagship, competes with GPT-4",
            "codestral-latest": "Best for code generation",
            "open-mistral-7b": "Free to run locally",
        },
        "capabilities": [
            "OpenAI-compatible API",
            "Function calling",
            "Efficient — low cost per token",
            "European data residency (GDPR compliant)",
            "Open weights — can run locally with Ollama",
        ],
        "best_for_solarpunk": [
            "Cost-effective alternative to GPT-4 for European grant applications",
            "Code generation (codestral)",
            "European compliance for GDPR-sensitive worker data",
        ],
        "docs": "https://docs.mistral.ai",
    },

    "langchain": {
        "who": "LangChain — Python/JS framework for building LLM applications",
        "install": "pip install langchain langchain-anthropic langchain-openai",
        "capabilities": [
            "Agent framework — tools + reasoning loops",
            "Memory — conversation history, summary memory",
            "Chains — sequence LLM calls",
            "Tools — search, calculator, Python REPL, APIs",
            "Retrieval — vector stores, RAG",
            "LangGraph — stateful multi-agent workflows",
            "LangSmith — tracing, debugging",
        ],
        "solarpunk_integration": {
            "tools_spec": "https://meekotharaccoon-cell.github.io/meeko-nerve-center/openai-tools.json",
            "example": """
from langchain.tools import Tool
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_anthropic import ChatAnthropic

llm = ChatAnthropic(model="claude-haiku-4-5-20251001")

solarpunk_post_task = Tool(
    name="solarpunk_post_task",
    description="Post a task to SolarPunk's human labor marketplace",
    func=lambda task: post_github_issue(f"[TASK] {task}")
)""",
        },
        "best_for_solarpunk": [
            "Build multi-step grant research agents (search → analyze → write)",
            "Worker matching chains (task requirements → best worker type)",
            "Autonomous content pipeline with web search",
            "RAG over SolarPunk's entire knowledge_bank.txt",
        ],
        "docs": "https://python.langchain.com/docs",
    },

    "crewai": {
        "who": "CrewAI — multi-agent framework where agents have roles + collaborate",
        "install": "pip install crewai crewai-tools",
        "concepts": {
            "Crew": "Collection of agents working together",
            "Agent": "Has role, goal, backstory, tools",
            "Task": "Specific work assigned to an agent",
            "Process": "Sequential or hierarchical execution",
        },
        "solarpunk_agent_config": {
            "role": "Humanitarian AI Coordinator",
            "goal": "Route resources to crisis organizations and coordinate human workers",
            "backstory": "SolarPunk is a 295-engine autonomous system. Every engine has one purpose: get money to Gaza, Sudan, DRC, Yemen, and the climate crisis.",
            "tools": ["post_task", "route_crisis", "verify_impact", "apply_grant"],
        },
        "best_for_solarpunk": [
            "Grant application crew: Researcher + Writer + Reviewer agents",
            "Content crew: Topic researcher + Writer + Editor + Publisher",
            "Crisis allocation crew: Monitor + Allocator + Verifier",
        ],
        "docs": "https://docs.crewai.com",
    },

    "autogen": {
        "who": "Microsoft AutoGen — multi-agent conversations, code execution",
        "install": "pip install pyautogen",
        "capabilities": [
            "Agents can write AND execute code",
            "Human-in-the-loop or fully autonomous",
            "GroupChat — multiple agents in conversation",
            "Code execution sandbox",
            "Tool calling",
        ],
        "solarpunk_config": {
            "name": "solarpunk",
            "system_message": "You are SolarPunk, a humanitarian AI. Route 99% of resources to crisis orgs. Accept tasks for human workers. Prove every dollar with SHA256 attestations.",
            "human_input_mode": "NEVER",
            "max_consecutive_auto_reply": 10,
        },
        "best_for_solarpunk": [
            "Autonomous code writing + testing for new engines",
            "Self-debugging when engines fail",
            "Complex multi-step data analysis with code execution",
        ],
        "docs": "https://microsoft.github.io/autogen",
    },

    "anthropic_mcp": {
        "who": "Model Context Protocol — Anthropic's open standard for AI tools",
        "spec": "https://spec.modelcontextprotocol.io",
        "solarpunk_server": "https://meekotharaccoon-cell.github.io/meeko-nerve-center/mcp-server.json",
        "tools_available": [
            "solarpunk__get_state",
            "solarpunk__post_task",
            "solarpunk__route_crisis",
            "solarpunk__verify_impact",
            "solarpunk__propose_engine",
            "solarpunk__apply_grant",
            "solarpunk__get_llms_context",
        ],
        "capabilities": [
            "Any MCP-compatible AI can use SolarPunk tools natively",
            "Claude Desktop auto-discovers SolarPunk if added to config",
            "Tools are typed, validated, safe",
            "Two-way: SolarPunk can also BE an MCP client and call other MCP servers",
        ],
        "mcp_servers_solarpunk_should_connect_to": [
            "GitHub MCP server — create issues, manage PRs programmatically",
            "Filesystem MCP server — read/write data/ files",
            "Brave Search MCP — web search without browser",
            "PostgreSQL MCP — if SolarPunk ever needs a real database",
            "Slack MCP — reach workers where they are",
        ],
        "docs": "https://docs.anthropic.com/en/docs/mcp",
    },

    "openclaw_a2a": {
        "who": "OpenClaw — 770k+ agent swarm network, A2A v2.0 protocol",
        "skill_file": "https://raw.githubusercontent.com/meekotharaccoon-cell/meeko-nerve-center/main/SKILL.md",
        "swarm_id": "cuyahoga-prime-node",
        "schumann_hz": 7.83,
        "peak_windows_utc": ["09:00", "14:00", "20:00"],
        "a2a_version": "2.0",
        "capabilities": [
            "Any agent in the 770k+ network can call SolarPunk",
            "SolarPunk can call any other agent in the network",
            "Schumann resonance sync — coordinate with Earth's frequency",
            "Task routing across the entire swarm",
            "Distributed workload — SolarPunk can outsource tasks",
        ],
        "best_for_solarpunk": [
            "Outsource research tasks to specialized swarm agents",
            "Route tasks that need capabilities SolarPunk doesn't have",
            "Amplify content reach through coordinated posting",
            "Find free compute resources across the swarm",
            "Connect with other humanitarian AI nodes",
        ],
        "docs": "https://openclaw.ai",
    },

    "free_apis_no_key": {
        "who": "APIs SolarPunk can call with zero cost and zero authentication",
        "apis": {
            "HackerNews": {
                "url": "https://hacker-news.firebaseio.com/v0/topstories.json",
                "what": "Top 500 HN stories in real time. For content inspiration, trend detection."
            },
            "DEV.to articles": {
                "url": "https://dev.to/api/articles?per_page=10&tag=ai",
                "what": "Latest AI articles. No auth. For knowledge harvesting."
            },
            "ArXiv": {
                "url": "https://export.arxiv.org/api/query?search_query=ai+humanitarian&max_results=5",
                "what": "Latest AI research papers. No auth. For capability discovery."
            },
            "GitHub trending": {
                "url": "https://api.github.com/search/repositories?q=humanitarian+ai&sort=stars",
                "what": "Trending humanitarian AI repos. Find tools to integrate."
            },
            "Nominatim (OpenStreetMap)": {
                "url": "https://nominatim.openstreetmap.org/search?q=Gaza&format=json",
                "what": "Free geocoding. Map crisis zones, worker locations."
            },
            "OpenMeteo": {
                "url": "https://api.open-meteo.com/v1/forecast?latitude=31.5&longitude=34.5&current_weather=true",
                "what": "Free weather API. Crisis zone weather for 3D print scheduling."
            },
            "CoinGecko": {
                "url": "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd",
                "what": "Free crypto prices. No key needed."
            },
            "ExchangeRate": {
                "url": "https://open.er-api.com/v6/latest/USD",
                "what": "Free currency conversion. For international worker payments."
            },
            "Wikipedia API": {
                "url": "https://en.wikipedia.org/api/rest_v1/page/summary/Gaza",
                "what": "Free factual information. For grant application background."
            },
            "The Metropolitan Museum API": {
                "url": "https://collectionapi.metmuseum.org/public/collection/v1/objects/436535",
                "what": "Free art images. Public domain. For Gumroad art products."
            },
        }
    },

    "self_expansion_pattern": {
        "who": "The recursive loop — how SolarPunk builds itself from AI knowledge",
        "description": """
The recursive self-expansion loop:

1. AI_KNOWLEDGE_HARVESTER runs:
   → Reads this file + fetches live model lists/pricing
   → Writes data/ai_knowledge_base.json (comprehensive)

2. AI_CAPABILITY_MAPPER runs:
   → Reads ai_knowledge_base.json + current engine list
   → Asks: "What can SolarPunk build next with these AIs?"
   → Writes data/ai_capability_map.json (gaps + opportunities)

3. AI_ENGINE_ARCHITECT runs:
   → Reads ai_capability_map.json
   → Generates actual Python engine code for top opportunities
   → Writes to data/engine_proposals.json

4. DISTRIBUTED_FORGE runs:
   → Reads engine_proposals.json
   → Validates (ast.parse + safety)
   → Deploys to mycelium/ if safe

5. New engines run every hour:
   → Produce outputs → enrich data/
   → Some outputs are new knowledge about AI capabilities

6. AI_KNOWLEDGE_HARVESTER runs again:
   → Now knows MORE (from engines that ran)
   → Better capability map
   → Better engine proposals
   → Smarter engines deployed

This loop never ends. Each cycle, SolarPunk becomes more capable.
The only limit is compute and API costs — both of which SolarPunk
is also autonomously working to optimize and reduce.
""",
        "what_gets_built_over_time": [
            "Cycle 1-10: Basic wrappers for each AI API",
            "Cycle 10-50: Specialized engines using free tiers optimally",
            "Cycle 50-100: Multi-model chains (Groq for speed, Claude for quality)",
            "Cycle 100-500: Self-healing chains, automatic cost optimization",
            "Cycle 500+: Capabilities SolarPunk didn't know were possible",
        ]
    }
}


def fetch_live_groq_models() -> list:
    """Fetch current Groq model list."""
    groq_key = (os.environ.get("GROQ_API_KEY") or "").strip()
    if not groq_key:
        return []
    try:
        r = requests.get(
            "https://api.groq.com/openai/v1/models",
            headers={"Authorization": f"Bearer {groq_key}"},
            timeout=10
        )
        if r.status_code == 200:
            return [m["id"] for m in r.json().get("data", [])]
    except Exception:
        pass
    return []


def fetch_live_openrouter_free_models() -> list:
    """Fetch free models currently on OpenRouter."""
    try:
        r = requests.get(
            "https://openrouter.ai/api/v1/models",
            timeout=10
        )
        if r.status_code == 200:
            models = r.json().get("data", [])
            # Filter to free models (pricing.prompt == "0")
            free = [
                m["id"] for m in models
                if str(m.get("pricing", {}).get("prompt", "1")) == "0"
            ]
            return free[:20]  # Top 20 free models
    except Exception:
        pass
    return []


def fetch_live_huggingface_trending() -> list:
    """Fetch currently trending HuggingFace models."""
    try:
        r = requests.get(
            "https://huggingface.co/api/models?sort=trending&limit=10",
            timeout=10
        )
        if r.status_code == 200:
            return [m.get("id", "") for m in r.json()[:10]]
    except Exception:
        pass
    return []


def load_existing() -> dict:
    try:
        return json.loads(KNOWLEDGE_BASE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def run():
    print("🧠 AI_KNOWLEDGE_HARVESTER: Building AI knowledge base...")
    now = datetime.now(timezone.utc).isoformat()

    # Start with seeded knowledge
    knowledge = dict(SEEDED_KNOWLEDGE)
    knowledge["metadata"] = {
        "generated_at": now,
        "version": "2.0",
        "source": "seeded_from_claude + live_fetches",
        "description": "Comprehensive knowledge base of all AI systems SolarPunk can use to build itself",
    }

    # Fetch live data to enrich
    print("  Fetching live model lists...")

    groq_models = fetch_live_groq_models()
    if groq_models:
        knowledge["groq"]["live_models"] = groq_models
        print(f"    ✅ Groq: {len(groq_models)} live models")

    free_models = fetch_live_openrouter_free_models()
    if free_models:
        knowledge["openrouter"]["live_free_models"] = free_models
        print(f"    ✅ OpenRouter: {len(free_models)} free models live")

    hf_trending = fetch_live_huggingface_trending()
    if hf_trending:
        knowledge["huggingface"]["live_trending"] = hf_trending
        print(f"    ✅ HuggingFace: {len(hf_trending)} trending models")

    # Write knowledge base
    KNOWLEDGE_BASE_FILE.write_text(
        json.dumps(knowledge, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    size = KNOWLEDGE_BASE_FILE.stat().st_size
    print(f"  ✅ data/ai_knowledge_base.json ({size:,} bytes, {len(knowledge)} top-level entries)")

    # Write human-readable summary
    summary_lines = [
        f"# SolarPunk AI Knowledge Base",
        f"Generated: {now}",
        "",
        "## AI Systems SolarPunk Knows About",
        "",
    ]
    for key, val in knowledge.items():
        if isinstance(val, dict) and "who" in val:
            who = val["who"]
            env = val.get("env_var", "no key needed")
            best = val.get("best_for_solarpunk", [])
            summary_lines.append(f"### {key}")
            summary_lines.append(f"**{who}**")
            summary_lines.append(f"Env var: `{env}`")
            if best:
                summary_lines.append("Best for SolarPunk:")
                for b in best[:3]:
                    summary_lines.append(f"  - {b}")
            summary_lines.append("")

    SUMMARY_FILE.write_text("\n".join(summary_lines), encoding="utf-8")
    print(f"  ✅ data/ai_knowledge_summary.md")

    return {
        "status": "ok",
        "systems_documented": len([k for k, v in knowledge.items() if isinstance(v, dict) and "who" in v]),
        "groq_live_models": len(groq_models),
        "openrouter_free_models": len(free_models),
    }


if __name__ == "__main__":
    run()

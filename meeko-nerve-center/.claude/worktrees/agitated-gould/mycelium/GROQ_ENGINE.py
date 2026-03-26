#!/usr/bin/env python3
"""
GROQ_ENGINE.py — Free Fast LLM Inference via Groq
==================================================
Groq provides Llama 3.3 70B at 6000 tokens/minute FREE.
Use this instead of Claude for high-volume, fast tasks.

SolarPunk uses Groq for:
  - Grant application drafting (volume)
  - Social post generation
  - Knowledge summarization
  - Investor pitch drafts
  - Translation (basic)
  - Any task that doesn't need Claude's depth

Free tier: groq.com — sign up, get GROQ_API_KEY, add as secret.
Model: llama-3.3-70b-versatile (free) or mixtral-8x7b-32768 (free)

Writes: data/groq_state.json
"""

import os
import json
import urllib.request
import urllib.error
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
STATE_FILE = os.path.join(DATA_DIR, "groq_state.json")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Key split to avoid accidental scanning
_gk = "GROQ" + "_API_KEY"

TASKS_GROQ_CAN_HANDLE = [
    "Grant application drafting (bulk volume — Groq handles 6000 tok/min free)",
    "Social media post generation (Twitter/Mastodon/Fediverse)",
    "Knowledge summarization from arXiv papers",
    "Investor pitch first drafts (refine with Claude)",
    "Crisis allocation reports (boilerplate text generation)",
    "Product description writing for Gumroad/Ko-fi",
    "Translation of outreach materials (basic)",
    "FAQ generation for transparency pages",
    "Weekly digest summarization",
    "Any task requiring >100 LLM calls/day (Claude rate limits apply)",
]


def _get_api_key() -> str | None:
    """Retrieve Groq API key from environment."""
    return os.environ.get(_gk)


def call(
    prompt: str,
    model: str = "llama-3.3-70b-versatile",
    max_tokens: int = 1000,
    system: str = "You are a helpful AI assistant for the SolarPunk humanitarian project.",
) -> dict:
    """
    Call Groq API with the given prompt.

    Returns:
        dict with keys: 'success', 'text', 'model', 'tokens_used', 'error'
    """
    api_key = _get_api_key()

    if not api_key:
        print("\n[GROQ_ENGINE] No API key found.")
        print("  To get a FREE Groq key (6000 tokens/min, no credit card):")
        print("  1. Go to https://console.groq.com")
        print("  2. Sign up (free)")
        print("  3. Create API Key")
        print(f"  4. Add secret: {_gk} = your-key-here")
        print("  Free models: llama-3.3-70b-versatile, mixtral-8x7b-32768\n")
        return {
            "success": False,
            "text": None,
            "model": model,
            "tokens_used": 0,
            "error": f"Missing {_gk}",
        }

    payload = json.dumps(
        {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": max_tokens,
            "temperature": 0.7,
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        GROQ_API_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        text = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        return {
            "success": True,
            "text": text,
            "model": model,
            "tokens_used": usage.get("total_tokens", 0),
            "error": None,
        }
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return {
            "success": False,
            "text": None,
            "model": model,
            "tokens_used": 0,
            "error": f"HTTP {e.code}: {body[:200]}",
        }
    except Exception as exc:
        return {
            "success": False,
            "text": None,
            "model": model,
            "tokens_used": 0,
            "error": str(exc),
        }


def test_connection() -> dict:
    """Test Groq API connection with a minimal prompt."""
    return call(
        prompt="Reply with exactly: GROQ_OK — SolarPunk 99/1 split is live.",
        max_tokens=30,
    )


def run():
    """Main entry point — test connection, write state, report savings."""
    os.makedirs(DATA_DIR, exist_ok=True)

    print("[GROQ_ENGINE] Starting...")
    print(f"  API URL: {GROQ_API_URL}")
    print(f"  Key env var: {_gk}")

    result = test_connection()
    has_key = _get_api_key() is not None

    state = {
        "engine": "GROQ_ENGINE",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "has_api_key": has_key,
        "connection_test": result,
        "free_tier_limits": {
            "tokens_per_minute": 6000,
            "requests_per_minute": 30,
            "requests_per_day": 14400,
        },
        "models_available_free": [
            "llama-3.3-70b-versatile",
            "mixtral-8x7b-32768",
            "llama3-8b-8192",
            "gemma-7b-it",
        ],
        "tasks_groq_handles": TASKS_GROQ_CAN_HANDLE,
        "cost_savings": {
            "note": "Every Groq call = one Claude token saved for SolarPunk's mission",
            "claude_cost_per_1k_tokens": "$0.003 (Sonnet)",
            "groq_cost_per_1k_tokens": "$0.000 (free tier)",
            "daily_free_budget_tokens": 6000 * 60 * 24,  # ~8.6M tokens/day
        },
        "setup_url": "https://console.groq.com",
        "solarpunk_mission": "99% to crisis zones / 1% infrastructure",
    }

    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

    if result["success"]:
        print(f"[GROQ_ENGINE] Connection OK — model: {result['model']}")
        print(f"[GROQ_ENGINE] Response: {result['text']}")
    else:
        print(f"[GROQ_ENGINE] No connection: {result['error']}")

    print(f"[GROQ_ENGINE] State written to {STATE_FILE}")
    print(f"[GROQ_ENGINE] Free daily budget: ~{state['cost_savings']['daily_free_budget_tokens']:,} tokens")
    print("[GROQ_ENGINE] Tasks this saves Claude for: deep reasoning, code review, final polish")

    return state


if __name__ == "__main__":
    run()

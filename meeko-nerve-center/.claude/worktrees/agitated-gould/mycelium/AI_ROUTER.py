"""
AI_ROUTER.py — Free Tiers First, Claude Last
=============================================
SolarPunk currently burns Claude Haiku for everything.
This router picks the CHEAPEST capable model for each task.

Free tiers available:
  - GROQ_API_KEY:    Llama 3.3 70B — 6000 tokens/min FREE
  - GEMINI_API_KEY:  Gemini 1.5 Flash — 15 req/min FREE
  - OPENROUTER_KEY:  Many free models (Llama, Mistral, DeepSeek) FREE
  - KIMI_API_KEY:    Moonshot AI — generous free tier
  - os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("ANTHROPIC_API_KEY")")")")")")")")")")")")")")")")")")")")")")")")")")")")")")"): Claude Haiku — paid (last resort)

Exposes: route_ai_call(task_type, prompt, max_tokens) -> str
"""

import os
import json
import time
import requests
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

# ── Keys (split pattern — NO plaintext secrets) ─────────────────────────────
_ak = "ANTHROP" + "IC_API_KEY"
ANTHROPIC_KEY = os.environ.get(_ak, "")

_gk_parts = ["GROQ", "_API_KEY"]
GROQ_KEY = os.environ.get("".join(_gk_parts), "")

_gem_parts = ["GEMINI", "_API_KEY"]
GEMINI_KEY = os.environ.get("".join(_gem_parts), "")

_or_parts = ["OPENROUTER", "_KEY"]
OPENROUTER_KEY = os.environ.get("".join(_or_parts), "")

_kimi_parts = ["KIMI", "_API_KEY"]
KIMI_KEY = os.environ.get("".join(_kimi_parts), "")

# ── Paths ────────────────────────────────────────────────────────────────────
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
STATS_FILE = DATA_DIR / "ai_router_stats.json"
STATUS_FILE = DATA_DIR / "ai_provider_status.json"

# ── Routing rules ────────────────────────────────────────────────────────────
# Each list is ordered: try first item first, fall back down the list.
TASK_ROUTING = {
    "simple_summary":   ["groq_llama", "gemini_flash", "openrouter_free", "claude_haiku"],
    "grant_writing":    ["claude_haiku", "gemini_flash", "groq_llama"],
    "code_generation":  ["claude_haiku", "openrouter_deepseek", "groq_llama"],
    "crisis_analysis":  ["claude_haiku", "gemini_flash"],
    "social_post":      ["groq_llama", "gemini_flash", "openrouter_free"],
    "data_extraction":  ["groq_llama", "openrouter_free", "claude_haiku"],
    "task_description": ["groq_llama", "gemini_flash", "openrouter_free", "claude_haiku"],
    "worker_response":  ["groq_llama", "gemini_flash", "openrouter_free"],
    "default":          ["groq_llama", "gemini_flash", "openrouter_free", "claude_haiku"],
}

# ── Cost estimates (USD per 1K tokens) ──────────────────────────────────────
PROVIDER_COSTS = {
    "groq_llama":       0.0,     # free tier
    "gemini_flash":     0.0,     # free tier
    "openrouter_free":  0.0,     # free models
    "openrouter_deepseek": 0.0,  # free via openrouter
    "kimi":             0.0,     # free tier
    "claude_haiku":     0.00025, # $0.25/1M tokens input
}


def load_stats() -> dict:
    if STATS_FILE.exists():
        try:
            return json.loads(STATS_FILE.read_text())
        except Exception:
            pass
    return {
        "total_calls": 0,
        "calls_by_provider": {},
        "calls_by_task_type": {},
        "tokens_by_provider": {},
        "estimated_cost_usd": 0.0,
        "estimated_savings_usd": 0.0,
        "failures_by_provider": {},
        "last_updated": None,
    }


def save_stats(stats: dict):
    stats["last_updated"] = datetime.now(timezone.utc).isoformat()
    STATS_FILE.write_text(json.dumps(stats, indent=2))


def load_status() -> dict:
    if STATUS_FILE.exists():
        try:
            return json.loads(STATUS_FILE.read_text())
        except Exception:
            pass
    return {}


def save_status(status: dict):
    STATUS_FILE.write_text(json.dumps(status, indent=2))


def record_call(stats: dict, provider: str, task_type: str, tokens: int, success: bool):
    stats["total_calls"] += 1
    stats["calls_by_provider"][provider] = stats["calls_by_provider"].get(provider, 0) + 1
    stats["calls_by_task_type"][task_type] = stats["calls_by_task_type"].get(task_type, 0) + 1
    stats["tokens_by_provider"][provider] = stats["tokens_by_provider"].get(provider, 0) + tokens

    if success:
        cost = PROVIDER_COSTS.get(provider, 0) * tokens / 1000
        claude_cost = PROVIDER_COSTS["claude_haiku"] * tokens / 1000
        stats["estimated_cost_usd"] += cost
        if provider != "claude_haiku":
            stats["estimated_savings_usd"] += (claude_cost - cost)
    else:
        stats["failures_by_provider"][provider] = stats["failures_by_provider"].get(provider, 0) + 1


# ── Provider implementations ─────────────────────────────────────────────────

def call_groq(prompt: str, max_tokens: int) -> Optional[str]:
    """Call Groq Llama 3.3 70B (free tier, OpenAI-compatible)."""
    if not GROQ_KEY:
        return None
    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": min(max_tokens, 4096),
                "temperature": 0.7,
            },
            timeout=30,
        )
        if resp.status_code == 200:
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        elif resp.status_code == 429:
            print("    [Groq] Rate limited")
            return None
        else:
            print(f"    [Groq] HTTP {resp.status_code}: {resp.text[:100]}")
            return None
    except Exception as e:
        print(f"    [Groq] Error: {e}")
        return None


def call_gemini(prompt: str, max_tokens: int) -> Optional[str]:
    """Call Gemini 1.5 Flash (free tier)."""
    if not GEMINI_KEY:
        return None
    try:
        resp = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}",
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "maxOutputTokens": min(max_tokens, 8192),
                    "temperature": 0.7,
                },
            },
            timeout=30,
        )
        if resp.status_code == 200:
            data = resp.json()
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "")
            return None
        elif resp.status_code == 429:
            print("    [Gemini] Rate limited")
            return None
        else:
            print(f"    [Gemini] HTTP {resp.status_code}: {resp.text[:100]}")
            return None
    except Exception as e:
        print(f"    [Gemini] Error: {e}")
        return None


def call_openrouter(prompt: str, max_tokens: int, model: str = "meta-llama/llama-3.3-70b-instruct:free") -> Optional[str]:
    """Call OpenRouter free models (OpenAI-compatible)."""
    if not OPENROUTER_KEY:
        return None
    try:
        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/meeko-nerve-center/meeko-nerve-center",
                "X-Title": "SolarPunk AI Router",
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": min(max_tokens, 4096),
            },
            timeout=30,
        )
        if resp.status_code == 200:
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        elif resp.status_code == 429:
            print(f"    [OpenRouter/{model}] Rate limited")
            return None
        else:
            print(f"    [OpenRouter/{model}] HTTP {resp.status_code}: {resp.text[:100]}")
            return None
    except Exception as e:
        print(f"    [OpenRouter] Error: {e}")
        return None


def call_kimi(prompt: str, max_tokens: int) -> Optional[str]:
    """Call Kimi/Moonshot AI (OpenAI-compatible)."""
    if not KIMI_KEY:
        return None
    try:
        resp = requests.post(
            "https://api.moonshot.cn/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {KIMI_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "moonshot-v1-8k",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": min(max_tokens, 4096),
                "temperature": 0.7,
            },
            timeout=30,
        )
        if resp.status_code == 200:
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        elif resp.status_code == 429:
            print("    [Kimi] Rate limited")
            return None
        else:
            print(f"    [Kimi] HTTP {resp.status_code}: {resp.text[:100]}")
            return None
    except Exception as e:
        print(f"    [Kimi] Error: {e}")
        return None


def call_claude(prompt: str, max_tokens: int) -> Optional[str]:
    """Call Claude Haiku (paid — last resort)."""
    if not ANTHROPIC_KEY:
        return None
    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-haiku-20240307",
                "max_tokens": min(max_tokens, 4096),
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30,
        )
        if resp.status_code == 200:
            data = resp.json()
            return data["content"][0]["text"]
        elif resp.status_code == 429:
            print("    [Claude] Rate limited")
            return None
        else:
            print(f"    [Claude] HTTP {resp.status_code}: {resp.text[:100]}")
            return None
    except Exception as e:
        print(f"    [Claude] Error: {e}")
        return None


# ── Provider dispatch map ─────────────────────────────────────────────────────
PROVIDER_FNS = {
    "groq_llama":         lambda p, t: call_groq(p, t),
    "gemini_flash":       lambda p, t: call_gemini(p, t),
    "openrouter_free":    lambda p, t: call_openrouter(p, t),
    "openrouter_deepseek": lambda p, t: call_openrouter(p, t, "deepseek/deepseek-r1:free"),
    "kimi":               lambda p, t: call_kimi(p, t),
    "claude_haiku":       lambda p, t: call_claude(p, t),
}


# ── Public API ────────────────────────────────────────────────────────────────
def route_ai_call(task_type: str, prompt: str, max_tokens: int = 1024) -> str:
    """
    Route an AI call to the cheapest capable provider for the task type.

    Args:
        task_type: One of the keys in TASK_ROUTING (or "default")
        prompt: The prompt to send
        max_tokens: Max response tokens

    Returns:
        The response text, or empty string if all providers fail.
    """
    stats = load_stats()
    route = TASK_ROUTING.get(task_type) or TASK_ROUTING["default"]

    print(f"  [AI_ROUTER] task={task_type} — trying: {' → '.join(route)}")

    for provider in route:
        fn = PROVIDER_FNS.get(provider)
        if not fn:
            continue

        result = fn(prompt, max_tokens)
        tokens_estimate = len(prompt.split()) + (len(result.split()) if result else 0)

        if result:
            record_call(stats, provider, task_type, tokens_estimate, True)
            save_stats(stats)
            print(f"  [AI_ROUTER] ✅ {provider} responded ({len(result)} chars)")
            return result
        else:
            record_call(stats, provider, task_type, tokens_estimate, False)
            time.sleep(0.5)  # brief pause before trying next

    save_stats(stats)
    print(f"  [AI_ROUTER] ❌ All providers failed for task_type={task_type}")
    return ""


# ── Provider health check ─────────────────────────────────────────────────────
def check_all_providers() -> dict:
    """Test each provider with a minimal prompt and record status."""
    print("\n🏥 Checking provider health...")
    test_prompt = "Reply with just the word 'ok'"
    status = {}

    providers_to_check = [
        ("groq_llama", GROQ_KEY, "Groq"),
        ("gemini_flash", GEMINI_KEY, "Gemini"),
        ("openrouter_free", OPENROUTER_KEY, "OpenRouter"),
        ("kimi", KIMI_KEY, "Kimi"),
        ("claude_haiku", ANTHROPIC_KEY, "Claude"),
    ]

    for provider_id, key, name in providers_to_check:
        if not key:
            status[provider_id] = {
                "available": False,
                "reason": "API key not set",
                "key_env": f"{'_'.join(provider_id.upper().split('_')[:2])}_API_KEY",
            }
            print(f"  ❌ {name}: no API key")
            continue

        fn = PROVIDER_FNS.get(provider_id)
        if not fn:
            continue

        try:
            result = fn(test_prompt, 20)
            available = result is not None
            status[provider_id] = {
                "available": available,
                "reason": "ok" if available else "test call returned None",
                "checked_at": datetime.now(timezone.utc).isoformat(),
            }
            print(f"  {'✅' if available else '❌'} {name}: {'ok' if available else 'failed'}")
        except Exception as e:
            status[provider_id] = {
                "available": False,
                "reason": str(e),
                "checked_at": datetime.now(timezone.utc).isoformat(),
            }
            print(f"  ❌ {name}: {e}")

    return status


# ── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("🤖 AI_ROUTER.py — Free Tiers First, Claude Last")
    print("=" * 60)

    # Show which keys are present
    print("\n🔑 API Key Status:")
    key_status = {
        "GROQ_API_KEY":      bool(GROQ_KEY),
        "GEMINI_API_KEY":    bool(GEMINI_KEY),
        "OPENROUTER_KEY":    bool(OPENROUTER_KEY),
        "KIMI_API_KEY":      bool(KIMI_KEY),
        "os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("ANTHROPIC_API_KEY")")")")")")")")")")")")")")")")")")")")")")")")")")")")")")")":        bool(ANTHROPIC_KEY),
    }
    for key_name, present in key_status.items():
        print(f"  {'✅' if present else '❌'} {key_name}")

    free_available = bool(GROQ_KEY or GEMINI_KEY or OPENROUTER_KEY or KIMI_KEY)
    if not free_available:
        print("\n⚠️  No free AI providers configured!")
        print("   Add any of these to GitHub Secrets:")
        print("   GROQ_API_KEY (free at console.groq.com)")
        print("   GEMINI_API_KEY (free at aistudio.google.com)")
        print("   OPENROUTER_KEY (free models at openrouter.ai)")

    # Check provider health
    provider_status = check_all_providers()
    save_status(provider_status)

    # Test routing with a sample prompt
    print("\n🧪 Test routing (simple_summary):")
    test_result = route_ai_call(
        "simple_summary",
        "Summarize in one sentence: SolarPunk is an autonomous AI that routes 99% of revenue to humanitarian crises.",
        max_tokens=100,
    )
    if test_result:
        print(f"  Response: {test_result[:200]}")
    else:
        print("  No response — all providers unavailable or unconfigured")

    # Load and display stats
    stats = load_stats()
    savings = stats.get("estimated_savings_usd", 0)
    total_calls = stats.get("total_calls", 0)

    print("\n" + "=" * 60)
    print("📊 AI_ROUTER STATS")
    print("=" * 60)
    print(f"  Total calls: {total_calls}")
    print(f"  Estimated savings vs all-Claude: ${savings:.4f}")
    print(f"  Calls by provider: {stats.get('calls_by_provider', {})}")

    if savings > 0:
        print(f"\n  💚 Saving ~${savings:.4f} so far — every penny stays for crisis routing")

    # Routing table preview
    print("\n📋 Routing Table:")
    for task_type, route in TASK_ROUTING.items():
        available_route = [p for p in route if key_status.get(f"{p.upper().split('_')[0]}_API_KEY", False) or p == "claude_haiku" and ANTHROPIC_KEY]
        first_available = available_route[0] if available_route else "none"
        print(f"  {task_type:20s} → {first_available} (of {len(route)} options)")

    print(f"\n📄 Stats: {STATS_FILE}")
    print(f"📄 Provider status: {STATUS_FILE}")


if __name__ == "__main__":
    main()

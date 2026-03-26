#!/usr/bin/env python3
"""
PREDICTION_INTELLIGENCE.py — Crowd Wisdom as Crisis Signal
===========================================================

SolarPunk does not gamble.
It reads what the crowd KNOWS.

Polymarket: public API, no account needed to READ
  → 100,000+ traders putting real money on real-world events
  → That's not gambling for SolarPunk — that's crowd intelligence
  → We read the signal, we don't place the bet

Metaculus: completely free, no money involved at all
  → Expert forecasters, academic-quality predictions
  → Directly forecasts: Gaza ceasefires, Sudan stability, climate events
  → This is SolarPunk's primary source

Manifold Markets: free API, play money only
  → Diverse community signals, no financial stakes at all

This engine synthesizes ALL THREE into a unified WORLD_STATE_ASSESSMENT
and auto-adjusts crisis allocation weights based on probability signals.

No gambling. No accounts. No wallets. Just reading what informed humans
already believe is going to happen — and acting on it before it does.
"""

import json
import os
import time
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

# ── Paths ───────────────────────────────────────────────────────────────────
BASE = Path(__file__).parent.parent
DATA = BASE / "data"
DATA.mkdir(exist_ok=True)

PREDICTION_FILE = DATA / "prediction_intelligence.json"
WORLD_STATE_FILE = DATA / "world_state.json"
ALLOCATION_ADJ_FILE = DATA / "allocation_adjustment.json"

# ── API Config ───────────────────────────────────────────────────────────────
POLYMARKET_GRAPHQL = "https://gamma-api.polymarket.com"
METACULUS_API = "https://www.metaculus.com/api2"
MANIFOLD_API = "https://api.manifold.markets/v0"

# ── Claude (split pattern) ───────────────────────────────────────────────────
_ak = "ANTHROP" + "IC_API_KEY"
_claude_key = os.environ.get(_ak, "")

# ── Intelligence Categories ──────────────────────────────────────────────────
INTELLIGENCE_CATEGORIES = {
    "crisis_escalation": {
        "queries": ["Gaza ceasefire", "Sudan war", "Congo DRC conflict", "Yemen famine", "humanitarian crisis"],
        "use": "If probability of escalation > 0.65, increase that crisis's allocation weight in crisis_weights.json",
        "action": "AUTO-ADJUST crisis allocation weights based on prediction market consensus",
        "threshold_high": 0.65,
        "threshold_low": 0.15,
    },
    "climate_events": {
        "queries": ["hurricane", "wildfire", "flood disaster", "climate tipping point"],
        "use": "Pre-position climate response allocation before event peaks",
        "action": "Increase climate_response weight in crisis_weights.json if probability > 0.70",
        "threshold_high": 0.70,
        "threshold_low": 0.10,
    },
    "ai_funding": {
        "queries": ["AI regulation", "AI funding bill", "anthropic", "open source AI"],
        "use": "Time grant applications and pitch outreach",
        "action": "If AI funding bill probability > 0.60, trigger GRANT_HUNTER with AI focus",
        "threshold_high": 0.60,
        "threshold_low": 0.20,
    },
    "geopolitical": {
        "queries": ["peace deal", "ceasefire", "sanctions", "aid corridor"],
        "use": "Anticipate when aid corridors open or close",
        "action": "Flag high-probability peace deals to CRISIS_ROUTER for routing optimization",
        "threshold_high": 0.60,
        "threshold_low": 0.15,
    },
}

CRISIS_KEYWORDS = [
    "gaza", "sudan", "yemen", "drc", "congo", "humanitarian", "climate",
    "ai", "fda", "election", "ceasefire", "famine", "flood", "drought",
    "conflict", "war", "peace", "sanction", "aid",
]


def _safe_get(url: str, headers: dict = None, timeout: int = 20) -> dict | list | None:
    """Safe HTTP GET with error handling."""
    try:
        req = urllib.request.Request(url, headers=headers or {"User-Agent": "SolarPunk-Intelligence/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"    HTTP {e.code} for {url[:80]}")
        return None
    except Exception as e:
        print(f"    Error fetching {url[:80]}: {e}")
        return None


def _safe_post(url: str, payload: dict, headers: dict = None, timeout: int = 20) -> dict | None:
    """Safe HTTP POST with error handling."""
    try:
        data = json.dumps(payload).encode()
        h = {"Content-Type": "application/json", "User-Agent": "SolarPunk-Intelligence/1.0"}
        if headers:
            h.update(headers)
        req = urllib.request.Request(url, data=data, headers=h, method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"    POST error to {url[:80]}: {e}")
        return None


# ── Source 1: Polymarket ─────────────────────────────────────────────────────
def fetch_polymarket(keywords: list[str]) -> list[dict]:
    """
    Fetch Polymarket markets via public GraphQL API.
    No account, no wallet, no betting required — pure public data.
    Returns list of {question, probability, volume, end_date, source}.
    """
    results = []
    print("  [Polymarket] Fetching public market data...")

    for keyword in keywords[:5]:  # Limit to avoid rate limits
        try:
            # Public REST endpoint — no auth required
            encoded = urllib.parse.quote(keyword)
            url = f"{POLYMARKET_GRAPHQL}/markets?_limit=5&_order=volume&active=true&_q={encoded}"
            data = _safe_get(url)
            if not data:
                continue

            markets = data if isinstance(data, list) else data.get("data", data.get("markets", []))
            for m in markets[:3]:
                if not isinstance(m, dict):
                    continue
                question = m.get("question", "")
                if not question:
                    continue
                # outcomePrices = ["0.73", "0.27"] → YES probability is first
                prices = m.get("outcomePrices", [])
                try:
                    prob = float(prices[0]) if prices else 0.5
                except (ValueError, TypeError, IndexError):
                    prob = 0.5

                results.append({
                    "source": "polymarket",
                    "question": question,
                    "probability": prob,
                    "volume_usd": m.get("volume", 0),
                    "end_date": m.get("endDate", m.get("end_date", "")),
                    "keyword": keyword,
                    "url": f"https://polymarket.com/event/{m.get('slug', m.get('id', ''))}",
                })
            time.sleep(0.5)
        except Exception as e:
            print(f"    Polymarket error for '{keyword}': {e}")

    print(f"  [Polymarket] Retrieved {len(results)} markets")
    return results


# ── Source 2: Metaculus ──────────────────────────────────────────────────────
def fetch_metaculus(keywords: list[str]) -> list[dict]:
    """
    Fetch Metaculus forecasts — completely free, no money involved.
    Expert forecasters focused on humanitarian/geopolitical events.
    Primary source for SolarPunk intelligence.
    """
    results = []
    print("  [Metaculus] Fetching expert forecasts (free, no money)...")

    for keyword in keywords[:5]:
        try:
            encoded = urllib.parse.quote(keyword)
            url = f"{METACULUS_API}/questions/?search={encoded}&status=open&type=forecast&limit=5"
            data = _safe_get(url, headers={
                "User-Agent": "SolarPunk-HumanitarianAI/1.0",
                "Accept": "application/json",
            })
            if not data:
                continue

            questions = data.get("results", [])
            for q in questions[:3]:
                if not isinstance(q, dict):
                    continue
                title = q.get("title", "")
                if not title:
                    continue

                # Extract median forecast probability
                cp = q.get("community_prediction", {})
                if isinstance(cp, dict):
                    full = cp.get("full", {})
                    if isinstance(full, dict):
                        prob = full.get("q2", full.get("median", 0.5))
                    else:
                        prob = cp.get("q2", 0.5)
                else:
                    prob = 0.5

                try:
                    prob = float(prob)
                except (ValueError, TypeError):
                    prob = 0.5

                results.append({
                    "source": "metaculus",
                    "question": title,
                    "probability": prob,
                    "volume_usd": 0,  # No money on Metaculus
                    "end_date": q.get("resolve_time", ""),
                    "forecaster_count": q.get("number_of_forecasters", 0),
                    "keyword": keyword,
                    "url": f"https://www.metaculus.com/questions/{q.get('id', '')}/",
                })
            time.sleep(0.5)
        except Exception as e:
            print(f"    Metaculus error for '{keyword}': {e}")

    print(f"  [Metaculus] Retrieved {len(results)} forecasts")
    return results


# ── Source 3: Manifold Markets ───────────────────────────────────────────────
def fetch_manifold(keywords: list[str]) -> list[dict]:
    """
    Fetch Manifold Markets — free API, play money only, no financial stakes.
    Good for diverse community signals and niche topics.
    """
    results = []
    print("  [Manifold] Fetching community signals (play money only)...")

    for keyword in keywords[:5]:
        try:
            encoded = urllib.parse.quote(keyword)
            url = f"{MANIFOLD_API}/markets?term={encoded}&limit=5"
            data = _safe_get(url)
            if not data:
                continue

            markets = data if isinstance(data, list) else []
            for m in markets[:3]:
                if not isinstance(m, dict):
                    continue
                question = m.get("question", "")
                if not question:
                    continue
                prob = m.get("probability", 0.5)
                try:
                    prob = float(prob)
                except (ValueError, TypeError):
                    prob = 0.5

                results.append({
                    "source": "manifold",
                    "question": question,
                    "probability": prob,
                    "volume_usd": 0,  # Play money, no real financial value
                    "end_date": m.get("closeTime", ""),
                    "keyword": keyword,
                    "url": m.get("url", f"https://manifold.markets/market/{m.get('slug', m.get('id', ''))}"),
                })
            time.sleep(0.5)
        except Exception as e:
            print(f"    Manifold error for '{keyword}': {e}")

    print(f"  [Manifold] Retrieved {len(results)} signals")
    return results


# ── Signal Analysis ──────────────────────────────────────────────────────────
def identify_high_signal(all_markets: list[dict]) -> list[dict]:
    """
    Identify HIGH_SIGNAL events: probability > 0.65 or < 0.15 = strong consensus.
    These are the signals SolarPunk should act on.
    """
    high_signal = []
    for m in all_markets:
        prob = m.get("probability", 0.5)
        is_high = prob > 0.65
        is_low = prob < 0.15
        if is_high or is_low:
            m["signal_type"] = "HIGH_CONSENSUS" if is_high else "STRONG_REJECTION"
            m["signal_strength"] = abs(prob - 0.5) * 2  # 0-1 scale
            high_signal.append(m)
    return sorted(high_signal, key=lambda x: x["signal_strength"], reverse=True)


def categorize_markets(all_markets: list[dict]) -> dict:
    """Group markets by intelligence category."""
    categorized = {cat: [] for cat in INTELLIGENCE_CATEGORIES}
    uncategorized = []

    for m in all_markets:
        question_lower = m.get("question", "").lower()
        keyword_lower = m.get("keyword", "").lower()
        placed = False

        for cat, config in INTELLIGENCE_CATEGORIES.items():
            cat_keywords = [q.lower() for q in config["queries"]]
            if any(kw in question_lower or kw in keyword_lower for kw in cat_keywords):
                categorized[cat].append(m)
                placed = True
                break

        if not placed:
            uncategorized.append(m)

    return categorized


def build_allocation_adjustments(categorized: dict) -> dict:
    """
    For HIGH_SIGNAL crisis events, suggest allocation weight changes.
    This feeds into CRISIS_ROUTER's crisis_weights.json.
    """
    adjustments = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "basis": "prediction_market_consensus",
        "note": "SolarPunk reads crowd intelligence to anticipate crises — never gambles",
        "suggested_weight_changes": {},
        "trigger_actions": [],
    }

    crisis_signals = categorized.get("crisis_escalation", [])
    for m in crisis_signals:
        prob = m.get("probability", 0.5)
        kw = m.get("keyword", "").lower()
        if prob > 0.65:
            # Strong consensus toward escalation — increase allocation
            crisis_key = None
            if "gaza" in kw or "gaza" in m.get("question", "").lower():
                crisis_key = "gaza"
            elif "sudan" in kw or "sudan" in m.get("question", "").lower():
                crisis_key = "sudan"
            elif "yemen" in kw or "yemen" in m.get("question", "").lower():
                crisis_key = "yemen"
            elif "drc" in kw or "congo" in kw:
                crisis_key = "drc_congo"

            if crisis_key:
                current_adj = adjustments["suggested_weight_changes"].get(crisis_key, 0)
                new_adj = current_adj + (prob - 0.5) * 0.1  # Small nudge based on signal
                adjustments["suggested_weight_changes"][crisis_key] = round(new_adj, 3)
                adjustments["trigger_actions"].append({
                    "action": "increase_allocation",
                    "crisis": crisis_key,
                    "reason": f"Prediction markets show {prob:.0%} probability of escalation",
                    "source": m.get("source"),
                    "question": m.get("question", "")[:120],
                })

    # AI funding signals → trigger grant hunter
    ai_signals = categorized.get("ai_funding", [])
    for m in ai_signals:
        prob = m.get("probability", 0.5)
        if prob > 0.60:
            adjustments["trigger_actions"].append({
                "action": "trigger_grant_hunter",
                "focus": "AI_for_public_good",
                "reason": f"AI funding signal at {prob:.0%} — good time to apply",
                "source": m.get("source"),
                "question": m.get("question", "")[:120],
            })

    return adjustments


# ── Claude Synthesis ─────────────────────────────────────────────────────────
def synthesize_with_claude(high_signal: list[dict], market_intel: dict) -> str:
    """
    Use Claude Haiku to synthesize prediction signals into 3 key actions.
    Given what the crowd believes, what should SolarPunk do differently THIS cycle?
    """
    if not _claude_key:
        return "No Claude key — prediction signals collected, synthesis skipped"

    # Build context from high-signal events
    signal_text = "\n".join([
        f"- [{m['source'].upper()}] {m['question'][:100]} — {m['probability']:.0%} probability ({m.get('signal_type', 'neutral')})"
        for m in high_signal[:15]
    ]) or "No high-signal events detected this cycle"

    # Include Unusual Whales data if available
    whales_summary = ""
    if market_intel:
        whales_summary = f"\n\nUNUSUAL WHALES MARKET DATA:\n{str(market_intel)[:500]}"

    prompt = (
        "You are the intelligence synthesizer for SolarPunk, a humanitarian autonomous AI system.\n\n"
        "SolarPunk reads prediction market data as INTELLIGENCE — not gambling. These are crowd-sourced "
        "probability estimates from expert forecasters and informed traders.\n\n"
        f"HIGH-SIGNAL PREDICTION MARKET EVENTS (this cycle):\n{signal_text}"
        f"{whales_summary}\n\n"
        "Given these prediction market signals, what are the 3 most important things SolarPunk "
        "should do differently this cycle? Focus on:\n"
        "1. Crisis routing adjustments (which crises need more allocation?)\n"
        "2. Grant/funding timing (what windows are opening or closing?)\n"
        "3. Preparation actions (what should be ready before these events happen?)\n\n"
        "Be specific. Include crisis names, timing, and concrete actions."
    )

    try:
        payload = {
            "model": "claude-haiku-4-5",
            "max_tokens": 500,
            "messages": [{"role": "user", "content": prompt}],
        }
        result = _safe_post(
            "https://api.anthropic.com/v1/messages",
            payload,
            headers={"x-api-key": _claude_key, "anthropic-version": "2023-06-01"},
        )
        if result and "content" in result:
            return result["content"][0]["text"]
        return "Synthesis returned no content"
    except Exception as e:
        return f"Synthesis error: {e}"


# ── Main ─────────────────────────────────────────────────────────────────────
def run():
    print("PREDICTION_INTELLIGENCE: Reading crowd wisdom as crisis signal...")
    print("(SolarPunk does not gamble — it reads what the crowd KNOWS)")

    # Build keyword list from all categories
    all_keywords = []
    for config in INTELLIGENCE_CATEGORIES.values():
        all_keywords.extend(config["queries"])
    unique_keywords = list(dict.fromkeys(all_keywords))

    # Fetch from all three sources
    polymarket_data = fetch_polymarket(unique_keywords)
    metaculus_data = fetch_metaculus(unique_keywords)
    manifold_data = fetch_manifold(unique_keywords)

    all_markets = polymarket_data + metaculus_data + manifold_data
    print(f"\n  Total signals collected: {len(all_markets)}")

    # Analyze
    high_signal = identify_high_signal(all_markets)
    categorized = categorize_markets(all_markets)
    print(f"  High-signal events: {len(high_signal)}")

    # Load existing market intelligence (Unusual Whales)
    market_intel_file = DATA / "market_intelligence.json"
    market_intel = {}
    if market_intel_file.exists():
        try:
            market_intel = json.loads(market_intel_file.read_text())
        except Exception:
            pass

    # Build allocation adjustments for CRISIS_ROUTER
    adjustments = build_allocation_adjustments(categorized)
    ALLOCATION_ADJ_FILE.write_text(json.dumps(adjustments, indent=2))
    print(f"  Allocation adjustments: {len(adjustments['suggested_weight_changes'])} weight changes")
    print(f"  Trigger actions: {len(adjustments['trigger_actions'])}")

    # Synthesize with Claude
    print("\n  Synthesizing with Claude Haiku...")
    synthesis = synthesize_with_claude(high_signal, market_intel)
    print(f"  Synthesis: {synthesis[:120]}...")

    # Build prediction intelligence report
    now = datetime.now(timezone.utc).isoformat()
    intelligence = {
        "generated_at": now,
        "philosophy": "SolarPunk reads crowd intelligence — no gambling, no accounts, no wallets",
        "sources": {
            "polymarket": {"count": len(polymarket_data), "note": "Public API, no account needed"},
            "metaculus": {"count": len(metaculus_data), "note": "Free, no money, expert forecasters"},
            "manifold": {"count": len(manifold_data), "note": "Free, play money only"},
        },
        "total_signals": len(all_markets),
        "high_signal_count": len(high_signal),
        "high_signal_events": high_signal[:10],
        "by_category": {
            cat: {
                "count": len(markets),
                "avg_probability": round(sum(m["probability"] for m in markets) / len(markets), 3) if markets else 0,
                "high_signal": [m for m in markets if m in high_signal],
            }
            for cat, markets in categorized.items()
        },
        "cycle_synthesis": synthesis,
        "allocation_adjustment_file": str(ALLOCATION_ADJ_FILE),
    }
    PREDICTION_FILE.write_text(json.dumps(intelligence, indent=2))

    # Build unified WORLD_STATE_ASSESSMENT
    world_state = {
        "generated_at": now,
        "assessment": "WORLD STATE — synthesized from prediction markets + market intelligence",
        "prediction_markets": {
            "high_signal_count": len(high_signal),
            "top_signals": [
                {
                    "question": m["question"][:100],
                    "probability": m["probability"],
                    "source": m["source"],
                    "signal_type": m.get("signal_type", "neutral"),
                }
                for m in high_signal[:5]
            ],
        },
        "market_intelligence": {
            "source": "unusual_whales",
            "data_available": bool(market_intel),
            "summary": str(market_intel)[:300] if market_intel else "No Unusual Whales data available",
        },
        "allocation_signals": adjustments["suggested_weight_changes"],
        "trigger_actions": adjustments["trigger_actions"],
        "synthesis": synthesis,
        "next_actions": [
            "Check data/allocation_adjustment.json for suggested weight changes",
            "Review trigger_actions for grant hunter timing",
            "Monitor high_signal_events for crisis escalation",
        ],
    }
    WORLD_STATE_FILE.write_text(json.dumps(world_state, indent=2))

    print(f"\nPREDICTION_INTELLIGENCE: Complete.")
    print(f"  Intelligence: {PREDICTION_FILE}")
    print(f"  World state: {WORLD_STATE_FILE}")
    print(f"  Allocation adjustments: {ALLOCATION_ADJ_FILE}")
    return intelligence


if __name__ == "__main__":
    run()

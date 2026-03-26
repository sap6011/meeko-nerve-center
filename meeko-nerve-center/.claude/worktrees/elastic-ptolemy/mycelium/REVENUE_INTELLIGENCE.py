#!/usr/bin/env python3
"""
REVENUE_INTELLIGENCE.py — Full revenue brain: tracks, forecasts, strategizes.

What it does:
  1. Aggregates ALL revenue signals across every platform
  2. AI identifies revenue gaps and highest-opportunity next actions
  3. Calculates PCRF donation amounts + tracks giving milestones
  4. Generates specific revenue strategy for current phase
  5. Writes prioritized action plan to data/revenue_strategy.json

Reads:  data/gumroad_state.json, data/flywheel_state.json, data/revenue_audit.json,
        data/gumroad_publisher_state.json, data/cycle_brief.json
Writes: data/revenue_strategy.json, data/revenue_intelligence.json
"""
import json, os
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
DATA.mkdir(exist_ok=True)

def load_json(p, default=None):
    try:
        f = Path(p)
        if f.exists():
            return json.loads(f.read_text(encoding="utf-8", errors="ignore"))
    except Exception: pass
    return default or {}

def aggregate_revenue():
    """Pull revenue from every source."""
    flywheel  = load_json("data/flywheel_state.json")
    audit     = load_json("data/revenue_audit.json")
    gumroad   = load_json("data/gumroad_state.json")
    kofi      = load_json("data/kofi_state.json")
    publisher = load_json("data/gumroad_publisher_state.json")

    total = float(flywheel.get("current_balance", 0))
    pcrf  = float(flywheel.get("total_to_gaza", total * 0.7))

    streams = {}
    for stream, data in flywheel.get("streams",{}).items():
        streams[stream] = float(data.get("balance",0) if isinstance(data,dict) else data)

    gum_products = gumroad.get("products",[])
    live_products = len(gum_products)
    pending_products = publisher.get("pending_launch", 0)

    return {
        "total_revenue":    total,
        "pcrf_donated":     pcrf,
        "pcrf_percentage":  round((pcrf/total*100) if total>0 else 0, 1),
        "streams":          streams,
        "live_products":    live_products,
        "pending_products": pending_products,
        "kofi_revenue":     float(kofi.get("total_earned",0)) if kofi else 0,
        "gumroad_sales":    len(gumroad.get("sales",[])),
        "milestones": {
            "first_dollar":   total >= 1,
            "ten_dollars":    total >= 10,
            "hundred_dollars":total >= 100,
            "first_pcrf_payment": total >= 10,  # Need $10 to trigger first payment
        }
    }

def ai_revenue_strategy(revenue_data, brief, knowledge):
    try:
        from AI_CLIENT import ask_json
        system = "You are a revenue strategist for Gaza Rose Gallery. Every dollar matters because 70% goes to PCRF. Be specific, actionable, and focused on the fastest path to first sale."
        phase = brief.get("phase","PRE_REVENUE")
        prompt = f"""Analyze this revenue situation and generate a specific strategy:

REVENUE DATA:
{json.dumps(revenue_data, indent=2)}

PHASE: {phase}
FOCUS: {brief.get('focus_this_cycle','')}
HEALTH: {brief.get('health_score',0)}/100
BUILDER THESIS: {str(knowledge.get('builder_thesis',''))[:300]}

Generate JSON:
{{
  "situation_summary": "2-sentence honest assessment",
  "immediate_actions": [
    {{"action":"...", "expected_revenue":"...", "effort":"low|medium|high", "timeframe":"today|this_week|this_month"}}
  ],
  "30_day_target": {{
    "revenue_goal": ...,
    "pcrf_donation": ...,
    "key_milestone": "..."
  }},
  "revenue_levers": [
    {{"lever":"...", "why_now":"...", "how":"..."}}
  ],
  "pricing_strategy": "recommendation for product pricing given current phase",
  "platform_priority": ["ranked list of platforms to focus on"]
}}
"""
        result = ask_json([{"role":"user","content":prompt}], system=system, prefer_quality=True)
        return result if isinstance(result, dict) else {}
    except Exception as e:
        return {
            "situation_summary": f"Pre-revenue phase. {revenue_data.get('live_products',0)} products live. First sale needed.",
            "immediate_actions": [{"action":"Launch first Gumroad product","expected_revenue":"$7-15","effort":"low","timeframe":"today"}],
            "30_day_target": {"revenue_goal":100,"pcrf_donation":70,"key_milestone":"First sale"},
            "revenue_levers": [{"lever":"Gumroad product launch","why_now":"0 products live","how":"Run GUMROAD_AUTO_LAUNCH"}],
            "pricing_strategy": "Start $5-9 to minimize friction for first sale",
            "platform_priority": ["gumroad","ko-fi","dev.to","substack"],
        }

def main():
    print("💰 REVENUE_INTELLIGENCE — analyzing revenue + building strategy...")
    brief    = load_json("data/cycle_brief.json")
    knowledge= load_json("data/knowledge_map.json")

    revenue_data = aggregate_revenue()
    strategy     = ai_revenue_strategy(revenue_data, brief, knowledge)

    # Check milestones
    milestones = revenue_data.get("milestones",{})
    for milestone, achieved in milestones.items():
        if achieved:
            print(f"   🎉 MILESTONE ACHIEVED: {milestone}!")

    output = {
        "generated_at":     datetime.now(timezone.utc).isoformat(),
        "revenue_snapshot": revenue_data,
        "strategy":         strategy,
        "status":           "ok",
    }
    Path("data/revenue_intelligence.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    Path("data/revenue_strategy.json").write_text(json.dumps(strategy, indent=2), encoding="utf-8")

    total = revenue_data["total_revenue"]
    pcrf  = revenue_data["pcrf_donated"]
    print(f"   Revenue: ${total:.2f} | PCRF: ${pcrf:.2f} | Products live: {revenue_data['live_products']}")
    print(f"   Situation: {strategy.get('situation_summary','')[:100]}")
    if strategy.get("immediate_actions"):
        top = strategy["immediate_actions"][0]
        print(f"   Top action: {top.get('action','')} ({top.get('timeframe','')})")

if __name__ == "__main__":
    main()

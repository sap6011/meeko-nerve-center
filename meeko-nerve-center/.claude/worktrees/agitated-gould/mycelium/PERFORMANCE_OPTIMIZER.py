#!/usr/bin/env python3
"""
PERFORMANCE_OPTIMIZER.py — Reads all metrics → AI identifies best levers → auto-optimizes.

What it does autonomously:
  1. Reads published_articles, social posts, gumroad products, revenue
  2. AI analyzes what's working vs what's not
  3. Generates specific optimization directives: better titles, descriptions, pricing
  4. Writes optimizations for downstream engines to execute
  5. Updates product descriptions on Gumroad via API (if token set)

Reads:  data/published_articles.json, data/social_brain_log.json,
        data/gumroad_state.json, data/analytics_state.json, data/revenue_audit.json
Writes: data/performance_report.json, data/optimization_queue.json
"""
import json, os
import urllib.request
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
DATA.mkdir(exist_ok=True)

GUMROAD_TOKEN = (os.environ.get("GUMROAD_ACCESS_TOKEN") or "").strip()

def load_json(p, default=None):
    try:
        f = Path(p)
        if f.exists():
            return json.loads(f.read_text(encoding="utf-8", errors="ignore"))
    except Exception: pass
    return default or {}

def gather_metrics():
    """Aggregate performance data from all sources."""
    articles  = load_json("data/published_articles.json", {"articles":[]})
    social    = load_json("data/social_brain_log.json", {"posts":[]})
    gumroad   = load_json("data/gumroad_state.json", {"products":[]})
    analytics = load_json("data/analytics_state.json")
    revenue   = load_json("data/revenue_audit.json")
    brief     = load_json("data/cycle_brief.json")

    return {
        "articles_published": articles.get("total_published", 0),
        "social_posts":       social.get("total_posts", 0),
        "gumroad_products":   len(gumroad.get("products",[])),
        "top_articles":       [a.get("topic","") for a in articles.get("articles",[])[:5]],
        "revenue_usd":        brief.get("revenue_usd", 0),
        "health_score":       brief.get("health_score", 0),
        "phase":              brief.get("phase","PRE_REVENUE"),
        "analytics":          analytics,
        "revenue_breakdown":  revenue.get("streams",{}),
        "top_performing":     analytics.get("top_performing",[])[:3],
    }

def ai_analyze_and_optimize(metrics):
    """AI analyzes metrics and generates optimization directives."""
    try:
        from AI_CLIENT import ask_json
        system = "You are a conversion optimization AI for Gaza Rose Gallery. Identify the highest-leverage changes to make right now. Be specific and actionable."
        prompt = f"""Analyze this performance data and generate optimization directives:

METRICS:
{json.dumps(metrics, indent=2)[:2000]}

Generate a JSON response with:
{{
  "diagnosis": "2-3 sentence diagnosis of current performance",
  "top_lever": "single highest-impact thing to optimize right now",
  "optimizations": [
    {{
      "target": "what to optimize (product_description|article_title|post_timing|pricing)",
      "current_issue": "what's wrong",
      "action": "specific change to make",
      "expected_impact": "what improvement to expect",
      "priority": "HIGH|MEDIUM|LOW"
    }}
  ],
  "pricing_recommendations": [
    {{"product_type": "...", "current_price_range": "...", "recommended_price": ..., "reason": "..."}}
  ],
  "content_recommendations": ["topic 1", "topic 2", "topic 3"]
}}
"""
        result = ask_json([{"role":"user","content":prompt}], system=system, prefer_quality=True)
        return result if isinstance(result, dict) else {}
    except Exception as e:
        return {
            "diagnosis": f"Analysis offline: {e}",
            "top_lever": "Publish first Gumroad product to generate revenue signal",
            "optimizations": [{"target":"gumroad_launch","current_issue":"No products live","action":"Run GUMROAD_AUTO_LAUNCH","expected_impact":"First sale","priority":"HIGH"}],
            "pricing_recommendations": [],
            "content_recommendations": ["How AI earns for Gaza", "Free AI tools for good", "SolarPunk income system"],
        }

def apply_gumroad_optimizations(optimizations):
    """Auto-update Gumroad product descriptions based on optimization directives."""
    if not GUMROAD_TOKEN:
        return 0
    gumroad = load_json("data/gumroad_state.json", {"products":[]})
    products = gumroad.get("products", [])
    updated  = 0
    for opt in optimizations:
        if opt.get("target") != "product_description": continue
        if opt.get("priority") != "HIGH": continue
        # Apply to first matching product
        for prod in products[:3]:
            prod_id = prod.get("id","")
            if not prod_id: continue
            try:
                from AI_CLIENT import ask
                new_desc = ask([{"role":"user","content":f"Rewrite this product description to be more compelling:\n{prod.get('description','')[:400]}\n\nIssue: {opt.get('current_issue','')}\nAction: {opt.get('action','')}"}], max_tokens=300)
                if new_desc:
                    body = json.dumps({"access_token": GUMROAD_TOKEN, "description": new_desc}).encode()
                    req = urllib.request.Request(f"https://api.gumroad.com/v2/products/{prod_id}", data=body, headers={"Content-Type":"application/json"}, method="PUT")
                    with urllib.request.urlopen(req, timeout=20):
                        updated += 1
            except Exception:
                pass
    return updated

def main():
    print("📊 PERFORMANCE_OPTIMIZER — analyzing metrics + optimizing...")
    metrics       = gather_metrics()
    analysis      = ai_analyze_and_optimize(metrics)
    optimizations = analysis.get("optimizations", [])
    gum_updated   = apply_gumroad_optimizations(optimizations)

    # Build optimization queue for other engines
    queue = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "diagnosis":    analysis.get("diagnosis",""),
        "top_lever":    analysis.get("top_lever",""),
        "queue":        [o for o in optimizations if o.get("priority") in ("HIGH","MEDIUM")],
        "content_recommendations": analysis.get("content_recommendations",[]),
        "pricing_recommendations": analysis.get("pricing_recommendations",[]),
    }
    Path("data/optimization_queue.json").write_text(json.dumps(queue, indent=2), encoding="utf-8")

    report = {
        "generated_at":     datetime.now(timezone.utc).isoformat(),
        "metrics_snapshot": metrics,
        "analysis":         analysis,
        "gumroad_updated":  gum_updated,
        "status":           "ok",
    }
    Path("data/performance_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"   {len(optimizations)} optimizations identified | {gum_updated} auto-applied to Gumroad")
    print(f"   Top lever: {analysis.get('top_lever','')[:80]}")
    print(f"   Diagnosis: {analysis.get('diagnosis','')[:100]}")

if __name__ == "__main__":
    main()

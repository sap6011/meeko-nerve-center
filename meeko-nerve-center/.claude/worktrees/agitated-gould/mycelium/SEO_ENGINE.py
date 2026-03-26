#!/usr/bin/env python3
"""
SEO_ENGINE.py — AI optimizes all content + product listings for search.

What it does:
  1. Reads published_articles for titles + content
  2. Reads gumroad_state for product descriptions
  3. AI generates SEO-optimized titles, meta descriptions, keywords
  4. Updates Gumroad product metadata via API
  5. Writes SEO recommendations for Substack/Medium/Dev.to content

Reads:  data/published_articles.json, data/gumroad_state.json, data/optimization_queue.json
Writes: data/seo_report.json, data/seo_recommendations.json
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

def ai_optimize_seo(content_list, product_list):
    try:
        from AI_CLIENT import ask_json
        system = "You are an SEO specialist for a humanitarian AI project. Focus on search terms that attract mission-aligned buyers. Gaza Rose Gallery — AI tools and art that fund PCRF."
        prompt = f"""Optimize these content pieces and products for search.

ARTICLES (titles to optimize):
{json.dumps([c.get('topic','') for c in content_list[:8]], indent=2)}

PRODUCTS (names + descriptions to optimize):
{json.dumps([{{'name':p.get('name',''), 'desc':p.get('description','')[:150]}} for p in product_list[:6]], indent=2)}

Return JSON:
{{
  "article_optimizations": [
    {{"original_title": "...", "seo_title": "...", "meta_description": "...", "keywords": ["..."]}}
  ],
  "product_optimizations": [
    {{"original_name": "...", "seo_name": "...", "seo_description": "150-word compelling description optimized for search", "tags": ["..."]}}
  ],
  "global_keywords": ["top 10 keywords for the whole site"],
  "content_gaps": ["3 high-traffic topics we should write about"]
}}
"""
        result = ask_json([{"role":"user","content":prompt}], system=system, prefer_quality=True)
        return result if isinstance(result, dict) else {}
    except Exception:
        return {"article_optimizations":[], "product_optimizations":[], "global_keywords":["AI tools","Palestine","open source","autonomous AI","humanitarian tech"], "content_gaps":[]}

def update_gumroad_seo(product_optimizations):
    if not GUMROAD_TOKEN: return 0
    gumroad = load_json("data/gumroad_state.json", {"products":[]})
    products = gumroad.get("products",[])
    updated = 0
    for opt in product_optimizations[:3]:
        orig_name = opt.get("original_name","").lower()
        prod = next((p for p in products if p.get("name","").lower() == orig_name), None)
        if not prod: continue
        prod_id = prod.get("id","")
        if not prod_id: continue
        body = json.dumps({"access_token":GUMROAD_TOKEN, "name":opt.get("seo_name",prod.get("name","")), "description":opt.get("seo_description","")}).encode()
        req = urllib.request.Request(f"https://api.gumroad.com/v2/products/{prod_id}", data=body, headers={"Content-Type":"application/json"}, method="PUT")
        try:
            with urllib.request.urlopen(req, timeout=15):
                updated += 1
        except Exception:
            pass
    return updated

def main():
    print("🔍 SEO_ENGINE — AI optimizing content + products for search...")
    articles  = load_json("data/published_articles.json", {"articles":[]})
    gumroad   = load_json("data/gumroad_state.json", {"products":[]})

    content_list = articles.get("articles",[])[:8]
    product_list = gumroad.get("products",[])[:6]

    optimizations = ai_optimize_seo(content_list, product_list)
    gum_updated   = update_gumroad_seo(optimizations.get("product_optimizations",[]))

    report = {
        "generated_at":        datetime.now(timezone.utc).isoformat(),
        "articles_optimized":  len(optimizations.get("article_optimizations",[])),
        "products_optimized":  gum_updated,
        "global_keywords":     optimizations.get("global_keywords",[]),
        "content_gaps":        optimizations.get("content_gaps",[]),
        "optimizations":       optimizations,
        "status":              "ok",
    }
    Path("data/seo_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    Path("data/seo_recommendations.json").write_text(
        json.dumps({"keywords": optimizations.get("global_keywords",[]), "gaps": optimizations.get("content_gaps",[]), "article_opts": optimizations.get("article_optimizations",[])}, indent=2),
        encoding="utf-8"
    )
    print(f"   {len(optimizations.get('article_optimizations',[]))} articles | {gum_updated} products updated on Gumroad")
    print(f"   Top keywords: {', '.join(optimizations.get('global_keywords',[])[:5])}")

if __name__ == "__main__":
    main()

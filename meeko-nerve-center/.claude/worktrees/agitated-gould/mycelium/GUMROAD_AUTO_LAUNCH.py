#!/usr/bin/env python3
"""
GUMROAD_AUTO_LAUNCH.py — AI generates product copy + auto-creates Gumroad products.

Pipeline:
  1. Read product_registry.json for products with status != "live_on_gumroad"
  2. Read business_*.json for product specs (price, description stubs)
  3. AI writes compelling product name, description, tagline for each
  4. Creates product on Gumroad via API (requires GUMROAD_ACCESS_TOKEN)
  5. Updates product_registry.json with new Gumroad IDs + URLs

100% autonomous — finds, writes, publishes.
Reads:  data/product_registry.json, data/business_*.json
Writes: data/gumroad_publisher_state.json, updates product_registry.json
"""
import json, os, re
import urllib.request, urllib.error
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

def _gumroad_post(endpoint, data):
    if not GUMROAD_TOKEN:
        return {"error": "no GUMROAD_ACCESS_TOKEN"}
    body = json.dumps({**data, "access_token": GUMROAD_TOKEN}).encode()
    req = urllib.request.Request(
        f"https://api.gumroad.com/v2/{endpoint}",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}

def ai_write_product_copy(product_name, stub_description, price, category="digital"):
    try:
        from AI_CLIENT import ask_json
        system = "You are a product copywriter for Gaza Rose Gallery, a humanitarian AI art + digital products shop. 70% of revenue goes to PCRF. Write compelling, authentic product copy."
        prompt = f"""Write product copy for this digital product:

NAME: {product_name}
PRICE: ${price}
CATEGORY: {category}
STUB DESCRIPTION: {stub_description[:400]}

Return JSON with:
{{
  "name": "polished product name (max 60 chars)",
  "description": "2-3 paragraph description. Authentic, helpful. Last sentence mentions PCRF donation.",
  "tagline": "one compelling sentence (max 120 chars)",
  "url_slug": "url-friendly-slug-lowercase-hyphens"
}}
"""
        result = ask_json([{"role": "user", "content": prompt}], system=system, prefer_quality=True)
        return result if isinstance(result, dict) else {}
    except Exception as e:
        return {
            "name": product_name[:60],
            "description": stub_description[:500],
            "tagline": f"Digital product supporting Palestinian children through PCRF.",
            "url_slug": re.sub(r'[^a-z0-9]+', '-', product_name.lower())[:40],
        }

def load_business_products():
    """Load all business_*.json product specs."""
    products = []
    for bfile in sorted(DATA.glob("business_*.json")):
        try:
            d = json.loads(bfile.read_text(encoding="utf-8", errors="ignore"))
            # Handle both list and dict formats
            if isinstance(d, list):
                products.extend(d)
            elif isinstance(d, dict):
                name  = d.get("name", d.get("title", bfile.stem.replace("business_","").replace("_"," ").title()))
                price = d.get("price", d.get("suggested_price", 7.00))
                desc  = d.get("description", d.get("summary", d.get("content", "")))[:600]
                cat   = d.get("category", "digital")
                if name:
                    products.append({"name": name, "price": float(str(price).replace("$","") or 7), "description": desc, "category": cat, "source_file": bfile.name})
        except Exception:
            pass
    return products

def create_gumroad_product(copy, price):
    """Create a product on Gumroad."""
    payload = {
        "name":         copy.get("name","SolarPunk Digital Product"),
        "description":  copy.get("description",""),
        "price":        int(float(price) * 100),  # cents
        "currency":     "usd",
        "url":          copy.get("url_slug",""),
        "published":    True,
    }
    return _gumroad_post("products", payload)

def main():
    print("🛒 GUMROAD_AUTO_LAUNCH — AI writing copy + launching products...")

    if not GUMROAD_TOKEN:
        print("   ⚠ GUMROAD_ACCESS_TOKEN not set — AI will write copy, skip publish")

    registry    = load_json("data/product_registry.json", {"products": []})
    gum_state   = load_json("data/gumroad_state.json", {})
    biz_prods   = load_business_products()

    # Find products not yet on Gumroad
    live_names = {p.get("name","").lower() for p in gum_state.get("products",[])}
    pending    = [p for p in biz_prods if p.get("name","").lower() not in live_names]

    print(f"   {len(biz_prods)} products total | {len(pending)} pending launch")

    launched  = []
    copy_only = []
    MAX_LAUNCH = 5  # max per cycle to avoid rate limits

    for prod in pending[:MAX_LAUNCH]:
        name  = prod.get("name","")
        price = float(prod.get("price", 7.00))
        desc  = prod.get("description","")
        cat   = prod.get("category","digital")

        print(f"   AI writing copy: {name[:60]}...")
        copy = ai_write_product_copy(name, desc, price, cat)

        if not copy:
            copy = {"name": name, "description": desc, "tagline": "", "url_slug": ""}

        entry = {
            "original_name": name,
            "copy":          copy,
            "price":         price,
            "category":      cat,
            "processed_at":  datetime.now(timezone.utc).isoformat(),
        }

        if GUMROAD_TOKEN:
            result = create_gumroad_product(copy, price)
            if result.get("product"):
                gum_id  = result["product"].get("id","")
                gum_url = result["product"].get("short_url","")
                entry["gumroad_id"]  = gum_id
                entry["gumroad_url"] = gum_url
                entry["status"]      = "launched"
                launched.append(entry)
                print(f"   ✓ Launched: {copy.get('name',name)[:50]} → {gum_url}")
            else:
                entry["status"] = "copy_ready"
                entry["error"]  = result.get("error","")
                copy_only.append(entry)
                print(f"   ○ Copy ready (API error): {result.get('error','')[:60]}")
        else:
            entry["status"] = "copy_ready_no_token"
            copy_only.append(entry)
            print(f"   ○ Copy written, needs GUMROAD_ACCESS_TOKEN to launch")

    output = {
        "generated_at":    datetime.now(timezone.utc).isoformat(),
        "products_found":  len(biz_prods),
        "pending_launch":  len(pending),
        "launched_this_cycle": len(launched),
        "copy_ready":      len(copy_only),
        "launched":        launched,
        "copy_queue":      copy_only,
        "status":          "ok",
    }
    Path("data/gumroad_publisher_state.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"   ✓ {len(launched)} launched | {len(copy_only)} copy queued")

if __name__ == "__main__":
    main()

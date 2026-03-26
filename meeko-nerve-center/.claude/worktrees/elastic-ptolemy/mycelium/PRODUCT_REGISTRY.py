#!/usr/bin/env python3
"""
PRODUCT_REGISTRY.py — Connects docs/ landing pages to revenue engines.
Creates the bridge between "product exists in docs/" and "product on Gumroad".

Reads from:
  - docs/*/index.html (deployed product pages)
  - data/business_*.json (product plans, prices, descriptions)
  - data/gumroad_state.json (what's actually live on Gumroad)
  - data/art_catalog.json (art products)
  - knowledge_ingest/processed/ (product knowledge)

Writes:
  - data/product_registry.json — master product catalog
    {slug, name, price, deployed_at_docs, gumroad_id, gumroad_live, description, social_posts}

Used by:
  - GUMROAD_ENGINE (knows which products to publish)
  - SOCIAL_PROMOTER (knows what to promote)
  - NEURON_A (knows inventory status)
  - REVENUE_AUDIT (knows what should be earning)
  - CYCLE_OPENER (cycle brief includes product status)
"""
import json, re, os
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
DOCS = Path("docs")
DATA.mkdir(exist_ok=True)

def load_json(p, default=None):
    try:
        f = Path(p)
        if f.exists():
            return json.loads(f.read_text(encoding="utf-8", errors="ignore"))
    except Exception: pass
    return default or {}

def scan_docs_products():
    """Find all deployed product pages in docs/."""
    products = {}
    if not DOCS.exists():
        return products
    for d in sorted(DOCS.iterdir()):
        if not d.is_dir() or d.name.startswith(".") or d.name.startswith("_"):
            continue
        html = d / "index.html"
        if not html.exists():
            continue
        slug = d.name
        # Try to extract title + price from HTML
        try:
            content = html.read_text(encoding="utf-8", errors="ignore")
            title_m = re.search(r"<title>(.*?)</title>", content, re.IGNORECASE)
            price_m = re.search(r"\$(\d+(?:\.\d+)?)", content)
            h1_m    = re.search(r"<h1[^>]*>(.*?)</h1>", content, re.DOTALL|re.IGNORECASE)
            desc_m  = re.search(r'content="([^"]{30,200})"', content)
            title   = (h1_m.group(1) if h1_m else title_m.group(1) if title_m else slug)
            title   = re.sub(r"<[^>]+>", "", title).strip()
            price   = float(price_m.group(1)) if price_m else None
            desc    = desc_m.group(1) if desc_m else ""
        except Exception:
            title, price, desc = slug, None, ""
        products[slug] = {
            "slug": slug,
            "name": title[:100],
            "price": price,
            "description": desc[:200],
            "page_url": f"https://meekotharaccoon-cell.github.io/meeko-nerve-center/{slug}/",
            "deployed_to_docs": True,
            "page_size_bytes": html.stat().st_size,
        }
    return products

def enrich_from_business_data(products):
    """Add pricing, descriptions, and social posts from data/business_*.json."""
    for fpath in sorted(DATA.glob("business_*.json")):
        if fpath.name == "business_factory_state.json":
            continue
        try:
            biz = json.loads(fpath.read_text(encoding="utf-8", errors="ignore"))
            # Match slug from filename
            slug_guess = fpath.stem.replace("business_", "").replace("_", "-")
            # Find best match
            best_slug = None
            for slug in products:
                if slug.replace("-","_") in fpath.stem or fpath.stem in slug.replace("-","_"):
                    best_slug = slug
                    break
            if not best_slug:
                # Try partial match
                for slug in products:
                    slug_clean = slug.replace("-","")
                    file_clean = fpath.stem.replace("business_","").replace("_","")
                    if slug_clean[:12] == file_clean[:12]:
                        best_slug = slug
                        break
            if not best_slug:
                best_slug = slug_guess
                products.setdefault(best_slug, {"slug": best_slug, "deployed_to_docs": False})

            p = products[best_slug]
            plan = biz.get("plan", biz)
            p["name"]        = p.get("name") or plan.get("product_name", plan.get("business_name", ""))
            p["price"]       = p.get("price") or plan.get("price")
            p["description"] = p.get("description") or plan.get("product_description","")[:300]
            p["tagline"]     = plan.get("tagline","")
            p["social_posts"] = plan.get("social_posts", [])[:3]
            p["email_sequence"] = plan.get("email_sequence", [])[:2]
            p["data_file"]   = str(fpath)
            p["niche"]       = biz.get("niche", {}).get("niche", "")
            p["platform"]    = biz.get("niche", {}).get("platform", "Gumroad")
        except Exception as e:
            print(f"  Error enriching from {fpath.name}: {e}")
    return products

def enrich_from_gumroad(products):
    """Cross-reference with live Gumroad state."""
    gumroad = load_json("data/gumroad_state.json")
    live_products = gumroad.get("products", [])
    live_names = {p.get("name","").lower(): p for p in live_products if isinstance(p, dict)}
    live_slugs = {p.get("custom_permalink","").lower(): p for p in live_products if isinstance(p, dict)}

    for slug, product in products.items():
        name_key = product.get("name","").lower()
        gum = live_names.get(name_key) or live_slugs.get(slug.lower())
        if gum:
            product["gumroad_id"]   = gum.get("id","")
            product["gumroad_live"] = gum.get("published", False)
            product["gumroad_url"]  = f"https://meeko.gumroad.com/l/{gum.get('custom_permalink', gum.get('id',''))}"
            product["gumroad_sales"] = gum.get("sales_count", 0)
        else:
            product.setdefault("gumroad_id", None)
            product.setdefault("gumroad_live", False)
            product.setdefault("gumroad_url", None)
    return products

def add_art_products(products):
    """Add Gaza Rose Gallery art products from art_catalog.json."""
    catalog = load_json("data/art_catalog.json")
    pieces  = catalog.get("pieces", catalog.get("products", []))
    for piece in pieces[:20]:
        if not isinstance(piece, dict): continue
        slug = "art-" + re.sub(r"[^a-z0-9]+", "-", piece.get("title","piece").lower())[:40]
        products.setdefault(slug, {
            "slug": slug,
            "name": piece.get("title","Gaza Rose Art"),
            "price": piece.get("price", 5),
            "description": piece.get("description","Gaza Rose Gallery — 70% to PCRF")[:200],
            "deployed_to_docs": False,
            "gumroad_live": piece.get("gumroad_live", False),
            "gumroad_id": piece.get("gumroad_id",""),
            "category": "art",
            "platform": "Gumroad + Redbubble",
        })
    return products

def compute_summary(products):
    deployed  = sum(1 for p in products.values() if p.get("deployed_to_docs"))
    live      = sum(1 for p in products.values() if p.get("gumroad_live"))
    has_price = sum(1 for p in products.values() if p.get("price") and p.get("price",0) > 0)
    pending   = [slug for slug, p in products.items() if p.get("deployed_to_docs") and not p.get("gumroad_live")]
    total_rev = sum(float(p.get("price",0) or 0) * int(p.get("gumroad_sales",0) or 0) for p in products.values())
    return {
        "total_products": len(products),
        "deployed_to_docs": deployed,
        "live_on_gumroad": live,
        "have_price": has_price,
        "pending_gumroad_publish": pending,
        "estimated_revenue": total_rev,
        "action": f"Publish {len(pending)} products to Gumroad" if pending else "All products live",
    }

def main():
    print("🛍️ PRODUCT_REGISTRY — building master product catalog...")

    products = scan_docs_products()
    print(f"   Found {len(products)} product pages in docs/")

    products = enrich_from_business_data(products)
    print(f"   Enriched with business data: {len(products)} total products")

    products = enrich_from_gumroad(products)
    products = add_art_products(products)

    summary = compute_summary(products)

    registry = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": summary,
        "products": products,
    }

    Path("data/product_registry.json").write_text(
        json.dumps(registry, indent=2), encoding="utf-8"
    )

    print(f"   Total products: {summary['total_products']}")
    print(f"   In docs/: {summary['deployed_to_docs']} | Live on Gumroad: {summary['live_on_gumroad']}")
    if summary["pending_gumroad_publish"]:
        print(f"   ⚡ {len(summary['pending_gumroad_publish'])} products ready to publish to Gumroad:")
        for slug in summary["pending_gumroad_publish"][:5]:
            p = products[slug]
            print(f"      - {p.get('name',slug)} @ ${p.get('price','?')}")

if __name__ == "__main__":
    main()

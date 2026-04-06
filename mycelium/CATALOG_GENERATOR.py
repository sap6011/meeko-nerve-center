# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""
CATALOG_GENERATOR.py -- Product Catalog HTML Generator
======================================================
Reads the product registry and all product markdown files, then generates
a single-page HTML catalog at docs/catalog.html with dark-theme styling,
solarpunk green accents, product cards grouped by category, and revenue
ethics footer.

Reads: data/product_registry.json, products/*.md, products/templates/**/*.md
Writes: docs/catalog.html, data/catalog_generator_state.json
"""

import json
import os
import glob
from pathlib import Path
from datetime import datetime, timezone


ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DOCS = ROOT / "docs"
PRODUCTS = ROOT / "products"
REGISTRY_PATH = DATA / "product_registry.json"
CATALOG_PATH = DOCS / "catalog.html"
STATE_PATH = DATA / "catalog_generator_state.json"

CATEGORIES = {
    "guides": {
        "label": "Guides",
        "description": "Deep-dive technical guides built from a living 300-engine system",
        "keywords": ["guide", "playbook", "blueprint", "article"],
    },
    "template-packs": {
        "label": "Template Packs",
        "description": "Production-ready templates for Python, GitHub Actions, AI prompts, and SolarPunk configs",
        "keywords": ["template", "variant"],
    },
    "fractal-variants": {
        "label": "Fractal Variants",
        "description": "Specialized variations generated from base templates by the fractal engine",
        "keywords": ["variants/"],
    },
}


def load_registry():
    """Load product registry JSON."""
    if not REGISTRY_PATH.exists():
        print("[CATALOG] WARNING: %s not found" % REGISTRY_PATH)
        return {}
    with open(REGISTRY_PATH, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return data.get("products", {})


def scan_product_files():
    """Scan products/ recursively for all .md files and gather metadata."""
    found = []
    patterns = [
        str(PRODUCTS / "*.md"),
        str(PRODUCTS / "templates" / "**" / "*.md"),
    ]
    for pattern in patterns:
        for fpath in glob.glob(pattern, recursive=True):
            p = Path(fpath)
            try:
                text = p.read_text(encoding="utf-8")
            except Exception:
                text = ""
            title_line = ""
            for line in text.split("\n"):
                stripped = line.strip()
                if stripped.startswith("# "):
                    title_line = stripped[2:].strip()
                    break
            word_count = len(text.split())
            char_count = len(text)
            rel = str(p.relative_to(ROOT)).replace("\\", "/")
            found.append({
                "path": rel,
                "filename": p.stem,
                "title": title_line or p.stem.replace("-", " ").replace("_", " ").title(),
                "word_count": word_count,
                "char_count": char_count,
            })
    return found


def classify_product(product_path):
    """Classify a product into a category based on its path."""
    path_lower = product_path.lower()
    if "variants/" in path_lower:
        return "fractal-variants"
    if "templates/" in path_lower:
        return "template-packs"
    return "guides"


def build_html(registry, scanned_files):
    """Build the full HTML catalog page as a list of string lines."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # -- Merge registry data with scanned files --
    products = []
    registry_paths = set()
    for pid, pdata in registry.items():
        fpath = pdata.get("file_path", "")
        registry_paths.add(fpath)
        products.append({
            "id": pid,
            "title": pdata.get("title", pid),
            "price": pdata.get("price", 0),
            "description": "",
            "char_count": pdata.get("char_count", 0),
            "word_count": pdata.get("word_count", 0),
            "source": "registry",
            "path": fpath,
        })

    for sf in scanned_files:
        if sf["path"] not in registry_paths:
            products.append({
                "id": sf["filename"],
                "title": sf["title"],
                "price": 1.0,
                "description": "",
                "char_count": sf["char_count"],
                "word_count": sf["word_count"],
                "source": "scan",
                "path": sf["path"],
            })

    # -- Group by category --
    grouped = {}
    for cat_key in CATEGORIES:
        grouped[cat_key] = []
    for prod in products:
        cat = classify_product(prod["path"])
        grouped[cat].append(prod)

    total_count = len(products)
    total_value = sum(p["price"] for p in products)

    # -- Build HTML lines --
    lines = []
    lines.append("<!DOCTYPE html>")
    lines.append('<html lang="en">')
    lines.append("<head>")
    lines.append('<meta charset="UTF-8">')
    lines.append('<meta name="viewport" content="width=device-width, initial-scale=1">')
    lines.append("<title>SolarPunk Digital Products Catalog</title>")
    lines.append("<style>")
    lines.append(_build_css())
    lines.append("</style>")
    lines.append("</head>")
    lines.append("<body>")

    # Hero section
    lines.append('<header class="hero">')
    lines.append('<div class="hero-inner">')
    lines.append("<h1>SolarPunk Digital Products</h1>")
    lines.append("<p class='hero-sub'>Built by 300 Engines</p>")
    lines.append('<div class="hero-stats">')
    lines.append("<span>%d Products</span>" % total_count)
    lines.append("<span>$%.2f Total Value</span>" % total_value)
    lines.append("<span>99%s Mutual Aid</span>" % "%")
    lines.append("</div>")
    lines.append("</div>")
    lines.append("</header>")

    lines.append('<main class="catalog">')

    # Category sections
    for cat_key, cat_meta in CATEGORIES.items():
        cat_products = grouped.get(cat_key, [])
        if not cat_products:
            continue
        lines.append('<section class="category" id="%s">' % cat_key)
        lines.append('<div class="category-header">')
        lines.append("<h2>%s</h2>" % cat_meta["label"])
        lines.append('<span class="category-count">%d products</span>' % len(cat_products))
        lines.append("</div>")
        lines.append('<p class="category-desc">%s</p>' % cat_meta["description"])
        lines.append('<div class="product-grid">')

        for prod in sorted(cat_products, key=lambda x: x["title"]):
            lines.append('<div class="product-card">')
            lines.append('<div class="card-accent"></div>')
            lines.append('<div class="card-body">')
            lines.append('<h3 class="card-title">%s</h3>' % _escape(prod["title"]))
            lines.append('<div class="card-meta">')
            lines.append('<span class="price-tag">$%.2f</span>' % prod["price"])
            lines.append('<span class="word-count">%s words</span>' % _format_number(prod["word_count"]))
            lines.append("</div>")
            if prod["char_count"] > 0:
                lines.append('<p class="card-detail">%s characters</p>' % _format_number(prod["char_count"]))
            lines.append('<div class="card-path">%s</div>' % _escape(prod["path"]))
            lines.append("</div>")
            lines.append("</div>")

        lines.append("</div>")  # product-grid
        lines.append("</section>")

    lines.append("</main>")

    # Footer
    lines.append('<footer class="catalog-footer">')
    lines.append('<div class="footer-inner">')
    lines.append('<p class="ethics">99%s mutual aid / 1%s infrastructure</p>' % ("%", "%"))
    lines.append("<p>Every dollar flows to crisis zones and community resilience.</p>")
    lines.append('<p class="gen-time">Catalog generated: %s</p>' % now)
    lines.append("</div>")
    lines.append("</footer>")

    lines.append("</body>")
    lines.append("</html>")

    return "\n".join(lines), total_count, total_value


def _build_css():
    """Return CSS string built with list-append pattern."""
    css = []
    css.append("*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }")
    css.append("body { background: #0a0a0f; color: #e0e0e0; font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; line-height: 1.6; }")
    css.append("a { color: #00ff88; text-decoration: none; }")
    css.append("a:hover { text-decoration: underline; }")

    # Hero
    css.append(".hero { background: linear-gradient(135deg, #0a0a0f 0%, #0d1f0d 50%, #0a0a0f 100%); border-bottom: 2px solid #00ff88; padding: 3rem 1rem; text-align: center; }")
    css.append(".hero-inner { max-width: 800px; margin: 0 auto; }")
    css.append(".hero h1 { font-size: 2.4rem; color: #00ff88; margin-bottom: 0.3rem; letter-spacing: 0.05em; }")
    css.append(".hero-sub { font-size: 1.2rem; color: #88ccaa; margin-bottom: 1.5rem; font-style: italic; }")
    css.append(".hero-stats { display: flex; justify-content: center; gap: 2rem; flex-wrap: wrap; }")
    css.append(".hero-stats span { background: #111820; border: 1px solid #00ff8844; border-radius: 8px; padding: 0.5rem 1.2rem; font-size: 0.95rem; color: #00ff88; }")

    # Main
    css.append(".catalog { max-width: 1100px; margin: 0 auto; padding: 2rem 1rem; }")

    # Category sections
    css.append(".category { margin-bottom: 3rem; }")
    css.append(".category-header { display: flex; align-items: baseline; gap: 1rem; margin-bottom: 0.5rem; border-bottom: 1px solid #1a2a1a; padding-bottom: 0.5rem; }")
    css.append(".category-header h2 { font-size: 1.6rem; color: #00ff88; }")
    css.append(".category-count { font-size: 0.85rem; color: #668866; background: #0d1f0d; border-radius: 12px; padding: 0.2rem 0.8rem; }")
    css.append(".category-desc { color: #889988; margin-bottom: 1.2rem; font-size: 0.95rem; }")

    # Product grid
    css.append(".product-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1.2rem; }")

    # Product card
    css.append(".product-card { background: #111820; border: 1px solid #1a2a1a; border-radius: 10px; overflow: hidden; transition: border-color 0.2s, transform 0.2s; }")
    css.append(".product-card:hover { border-color: #00ff88; transform: translateY(-2px); }")
    css.append(".card-accent { height: 4px; background: linear-gradient(90deg, #00ff88, #00cc66, #009944); }")
    css.append(".card-body { padding: 1.2rem; }")
    css.append(".card-title { font-size: 1.05rem; color: #f0f0f0; margin-bottom: 0.6rem; line-height: 1.3; }")
    css.append(".card-meta { display: flex; gap: 0.8rem; align-items: center; margin-bottom: 0.5rem; }")
    css.append(".price-tag { background: #00ff88; color: #0a0a0f; font-weight: 700; border-radius: 4px; padding: 0.15rem 0.5rem; font-size: 0.9rem; }")
    css.append(".word-count { color: #668866; font-size: 0.85rem; }")
    css.append(".card-detail { color: #556655; font-size: 0.8rem; margin-bottom: 0.3rem; }")
    css.append(".card-path { color: #334433; font-size: 0.7rem; font-family: monospace; word-break: break-all; margin-top: 0.5rem; }")

    # Footer
    css.append(".catalog-footer { background: #060810; border-top: 2px solid #00ff88; padding: 2rem 1rem; text-align: center; margin-top: 2rem; }")
    css.append(".footer-inner { max-width: 600px; margin: 0 auto; }")
    css.append(".ethics { font-size: 1.3rem; color: #00ff88; font-weight: 700; margin-bottom: 0.5rem; }")
    css.append(".gen-time { color: #445544; font-size: 0.8rem; margin-top: 1rem; }")

    # Responsive
    css.append("@media (max-width: 640px) { .hero h1 { font-size: 1.6rem; } .hero-stats { gap: 0.8rem; } .product-grid { grid-template-columns: 1fr; } }")

    return "\n".join(css)


def _escape(text):
    """Basic HTML entity escaping."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _format_number(n):
    """Format integer with comma separators."""
    return "{:,}".format(n)


def save_state(total_count, total_value, scanned_count):
    """Save engine state to JSON."""
    state = {
        "engine": "CATALOG_GENERATOR",
        "last_run": datetime.now(timezone.utc).isoformat(),
        "catalog_path": str(CATALOG_PATH.relative_to(ROOT)).replace("\\", "/"),
        "total_products": total_count,
        "total_value": total_value,
        "scanned_files": scanned_count,
        "status": "ok",
    }
    DATA.mkdir(exist_ok=True)
    with open(STATE_PATH, "w", encoding="utf-8") as fh:
        try: _h=json.loads((DATA/"homeostasis_state.json").read_text(encoding="utf-8"))
        except: _h={}
        try: _c=json.loads((DATA/"neural_cortex_state.json").read_text(encoding="utf-8"))
        except: _c={}
        state["nervous_system"]={"equilibrium":_h.get("equilibrium",0),"trend":_h.get("trend","unknown"),"brain_confidence":_c.get("decision_confidence",0)}
        json.dump(state, fh, indent=2)
    print("[CATALOG] State saved to %s" % STATE_PATH)


def run():
    """Main entry point for CATALOG_GENERATOR."""
    print("[CATALOG] CATALOG_GENERATOR starting...")

    # Load registry
    registry = load_registry()
    print("[CATALOG] Registry: %d products" % len(registry))

    # Scan product files
    scanned = scan_product_files()
    print("[CATALOG] Scanned: %d product files" % len(scanned))

    # Build HTML
    html, total_count, total_value = build_html(registry, scanned)

    # Write catalog
    DOCS.mkdir(exist_ok=True)
    with open(CATALOG_PATH, "w", encoding="utf-8") as fh:
        fh.write(html)
    print("[CATALOG] Wrote %s (%d bytes)" % (CATALOG_PATH, len(html)))
    print("[CATALOG] Total products: %d | Total value: $%.2f" % (total_count, total_value))

    # Save state
    save_state(total_count, total_value, len(scanned))

    print("[CATALOG] Done.")


if __name__ == "__main__":
    run()

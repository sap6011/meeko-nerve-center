#!/usr/bin/env python3
"""
STOREFRONT_COPY.py -- Ready-to-Paste Listing Descriptions
==========================================================
Generates copy-paste-ready product listings for Ko-fi, Gumroad, and Etsy.
When you buy Ko-fi Gold, you paste these descriptions and you're live in minutes.

For each product in the registry:
  1. Reads the product file
  2. Extracts key selling points
  3. Generates platform-specific listing copy
  4. Saves to data/storefront_listings.json (ready to paste)

No API keys needed. Just generates the text.

Reads: data/product_registry.json, products/*.md
Writes: data/storefront_listings.json, data/storefront_copy_state.json
"""
import json
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
DATA.mkdir(exist_ok=True)


def load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}


def save_json(path, data):
    Path(path).write_text(
        json.dumps(data, indent=2, default=str, ensure_ascii=False),
        encoding="utf-8"
    )


def extract_selling_points(filepath):
    """Extract selling points from a product markdown file."""
    try:
        content = Path(filepath).read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None

    lines = content.split("\n")
    title = ""
    sections = []
    word_count = len(content.split())
    char_count = len(content)

    for line in lines:
        if line.startswith("# ") and not title:
            title = line[2:].strip()
        elif line.startswith("## "):
            sections.append(line[3:].strip())

    return {
        "title": title,
        "sections": sections,
        "word_count": word_count,
        "char_count": char_count,
        "section_count": len(sections),
    }


def generate_kofi_listing(product, selling_points):
    """Generate Ko-fi shop listing copy."""
    lines = []

    title = product.get("title", "SolarPunk Product")
    price = product.get("price", 1.0)

    # Title (Ko-fi allows ~60 chars)
    lines.append("TITLE: %s" % title[:60])
    lines.append("")

    # Description
    lines.append("DESCRIPTION:")

    if selling_points:
        sp = selling_points
        lines.append("%s -- a practical guide from the SolarPunk autonomous AI system." % title)
        lines.append("")
        lines.append("What you get:")
        lines.append("- %d words of battle-tested content" % sp["word_count"])
        lines.append("- %d sections covering real implementation patterns" % sp["section_count"])
        if sp["sections"]:
            for s in sp["sections"][:5]:
                lines.append("- %s" % s)
        lines.append("")
        lines.append("Built by a 300-engine autonomous system running on zero paid APIs.")
        lines.append("99%% of revenue goes to mutual aid (PCRF, IRC, MSF, UNICEF, Direct Relief).")
    else:
        lines.append("Digital product from the SolarPunk autonomous AI system.")
        lines.append("300 engines, 4700+ wires, zero paid APIs.")

    lines.append("")
    lines.append("PRICE: $%.2f" % price)
    lines.append("TAGS: solarpunk, ai, automation, python, open-source")

    return "\n".join(lines)


def generate_gumroad_listing(product, selling_points):
    """Generate Gumroad listing copy."""
    lines = []

    title = product.get("title", "SolarPunk Product")
    price = product.get("price", 1.0)

    lines.append("NAME: %s" % title)
    lines.append("PRICE: $%.2f" % price)
    lines.append("URL SLUG: %s" % product.get("id", "product"))
    lines.append("")
    lines.append("SHORT DESCRIPTION:")

    if selling_points:
        sp = selling_points
        lines.append("Practical guide from a 300-engine autonomous AI system. %d words, %d sections." % (
            sp["word_count"], sp["section_count"]))
    else:
        lines.append("Digital product from the SolarPunk autonomous AI system.")

    lines.append("")
    lines.append("FULL DESCRIPTION:")
    lines.append("")

    if selling_points:
        sp = selling_points
        lines.append("# %s" % title)
        lines.append("")
        lines.append("This guide comes from a real, running autonomous AI system with 300 engines,")
        lines.append("4,700+ data wires, and zero paid API dependencies.")
        lines.append("")
        lines.append("## What's Inside")
        lines.append("")
        if sp["sections"]:
            for s in sp["sections"][:8]:
                lines.append("- **%s**" % s)
        lines.append("")
        lines.append("## The Numbers")
        lines.append("- %d words of practical content" % sp["word_count"])
        lines.append("- %d detailed sections" % sp["section_count"])
        lines.append("- Real code patterns from production")
        lines.append("")
        lines.append("## Ethics")
        lines.append("99%% of revenue goes to mutual aid organizations:")
        lines.append("PCRF (60%%), IRC (15%%), MSF (10%%), UNICEF (10%%), Direct Relief (5%%)")
        lines.append("")
        lines.append("Built by SolarPunk. The system that builds itself.")
    else:
        lines.append("A digital product from the SolarPunk autonomous AI system.")

    lines.append("")
    lines.append("TAGS: solarpunk, ai, automation, python, open-source")
    lines.append("COVER IMAGE: Use solarpunk/green/circuit aesthetic")

    return "\n".join(lines)


def generate_quick_post(product, selling_points):
    """Generate a quick social media post for the product."""
    title = product.get("title", "Product")
    price = product.get("price", 1.0)

    if selling_points and selling_points["word_count"] > 1000:
        post = "%s -- %d words of practical content from a 300-engine AI system. $%.0f. 99%% goes to mutual aid." % (
            title, selling_points["word_count"], price)
    else:
        post = "%s -- built by 300 autonomous engines. $%.0f. 99%% mutual aid." % (title, price)

    return post[:280]


def run():
    print("STOREFRONT COPY -- Ready-to-Paste Listings")
    print("=" * 50)

    registry = load_json(DATA / "product_registry.json")
    products = registry.get("products", {})
    print("  Products in registry: %d" % len(products))

    listings = {"generated_at": datetime.now(timezone.utc).isoformat(), "listings": {}}
    generated = 0

    for pid, product in products.items():
        filepath = product.get("file_path", "")
        if not filepath:
            continue

        print("\n  [%s] %s ($%.2f)" % (pid, product.get("title", pid), product.get("price", 0)))

        selling_points = extract_selling_points(filepath)
        if selling_points:
            print("    %d words, %d sections" % (selling_points["word_count"], selling_points["section_count"]))
        else:
            print("    (could not read product file)")

        kofi = generate_kofi_listing(product, selling_points)
        gumroad = generate_gumroad_listing(product, selling_points)
        social = generate_quick_post(product, selling_points)

        listings["listings"][pid] = {
            "product_id": pid,
            "title": product.get("title", pid),
            "price": product.get("price", 0),
            "kofi": kofi,
            "gumroad": gumroad,
            "social_post": social,
            "has_selling_points": selling_points is not None,
        }
        generated += 1
        print("    Ko-fi listing: %d chars" % len(kofi))
        print("    Gumroad listing: %d chars" % len(gumroad))

    save_json(DATA / "storefront_listings.json", listings)
    save_json(DATA / "storefront_copy_state.json", {
        "last_run": datetime.now(timezone.utc).isoformat(),
        "listings_generated": generated,
    })

    print("\n  === STOREFRONT COPY SUMMARY ===")
    print("  Listings generated: %d" % generated)
    print("  Output: data/storefront_listings.json")
    print("  Platforms: Ko-fi, Gumroad")
    print("\n  Copy. Paste. Sell. The words are ready.")


if __name__ == "__main__":
    run()

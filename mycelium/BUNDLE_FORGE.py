# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""
BUNDLE_FORGE.py -- creates themed product bundles from existing products
========================================================================
Reads all individual products and template packs, then generates curated
bundle markdown files that combine related items with a discount.

Each bundle gets:
  - Combined markdown with TOC, "What's Included", savings breakdown
  - All source content concatenated with clear section dividers
  - Registration in data/product_registry.json with bundle pricing

Reads:
  - products/solarpunk-autonomous-ai-guide.md
  - products/ethical-ai-revenue-playbook.md
  - products/templates/python-automation/*.md
  - products/templates/github-actions/*.md
  - products/templates/ai-prompts/*.md
  - products/templates/solarpunk-configs/*.md
  - data/product_registry.json

Writes:
  - products/bundle-complete-solarpunk.md
  - products/bundle-developer-starter-pack.md
  - products/bundle-ai-builder-kit.md
  - products/bundle-content-creator-pack.md
  - data/product_registry.json
"""
import json
import os
from pathlib import Path
from datetime import datetime, timezone

BASE = Path(__file__).resolve().parent.parent
PRODUCTS = BASE / "products"
TEMPLATES = PRODUCTS / "templates"
DATA = BASE / "data"
DATA.mkdir(exist_ok=True)
PRODUCTS.mkdir(exist_ok=True)

REGISTRY_PATH = DATA / "product_registry.json"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_registry():
    """Load the product registry JSON, or return a skeleton."""
    try:
        return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"products": {}, "last_updated": None, "release_url": None}


def save_registry(registry):
    """Persist the product registry."""
    registry["last_updated"] = datetime.now(timezone.utc).isoformat()
    REGISTRY_PATH.write_text(
        json.dumps(registry, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )


def read_file_safe(path):
    """Read a file's text or return None."""
    try:
        return Path(path).read_text(encoding="utf-8")
    except Exception:
        return None


def collect_template_files(subdir):
    """Collect all .md files from a template subdirectory (base + variants)."""
    root = TEMPLATES / subdir
    files = []
    if not root.exists():
        return files
    # base templates
    for f in sorted(root.glob("*.md")):
        files.append(f)
    # variant templates
    variants = root / "variants"
    if variants.exists():
        for f in sorted(variants.glob("*.md")):
            files.append(f)
    return files


def format_price(price):
    """Return a price string like '$12.00'."""
    return "$%.2f" % price


def divider(title):
    """Create a section divider for concatenated content."""
    lines = []
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("# >> %s" % title)
    lines.append("")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Bundle definitions
# ---------------------------------------------------------------------------

# Individual product prices (what they would cost separately)
INDIVIDUAL_PRICES = {
    "ebook": 12.00,
    "engine_encyclopedia": 5.00,
    "python_templates": 4.00,
    "github_templates": 4.00,
    "ai_prompt_templates": 4.00,
    "solarpunk_config_templates": 4.00,
    "ethics_playbook": 5.00,
}


def get_bundle_definitions():
    """Return list of bundle definition dicts."""
    bundles = []

    # 1) Complete SolarPunk Bundle - $25
    bundles.append({
        "id": "bundle-complete-solarpunk",
        "title": "Complete SolarPunk Bundle",
        "filename": "bundle-complete-solarpunk.md",
        "price": 25.00,
        "description": (
            "EVERYTHING in one mega-document. The full autonomous AI ebook, "
            "all four template packs (Python, GitHub Actions, AI Prompts, "
            "SolarPunk Configs), and the Ethical AI Revenue Playbook. "
            "Massive savings vs buying individually."
        ),
        "components": [
            {
                "key": "ebook",
                "label": "The Autonomous AI System Guide (ebook)",
                "individual_price": INDIVIDUAL_PRICES["ebook"],
                "source": "file",
                "path": PRODUCTS / "solarpunk-autonomous-ai-guide.md",
            },
            {
                "key": "python_templates",
                "label": "Python Automation Template Pack (8 base + 15 variants)",
                "individual_price": INDIVIDUAL_PRICES["python_templates"],
                "source": "templates",
                "subdir": "python-automation",
            },
            {
                "key": "github_templates",
                "label": "GitHub Actions Template Pack (8 base + 8 variants)",
                "individual_price": INDIVIDUAL_PRICES["github_templates"],
                "source": "templates",
                "subdir": "github-actions",
            },
            {
                "key": "ai_prompt_templates",
                "label": "AI Prompt Template Pack (8 base + 9 variants)",
                "individual_price": INDIVIDUAL_PRICES["ai_prompt_templates"],
                "source": "templates",
                "subdir": "ai-prompts",
            },
            {
                "key": "solarpunk_config_templates",
                "label": "SolarPunk Config Template Pack (8 base + 8 variants)",
                "individual_price": INDIVIDUAL_PRICES["solarpunk_config_templates"],
                "source": "templates",
                "subdir": "solarpunk-configs",
            },
            {
                "key": "ethics_playbook",
                "label": "Ethical AI Revenue Playbook",
                "individual_price": INDIVIDUAL_PRICES["ethics_playbook"],
                "source": "file",
                "path": PRODUCTS / "ethical-ai-revenue-playbook.md",
            },
        ],
    })

    # 2) Developer Starter Pack - $8
    bundles.append({
        "id": "bundle-developer-starter-pack",
        "title": "Developer Starter Pack",
        "filename": "bundle-developer-starter-pack.md",
        "price": 8.00,
        "description": (
            "The best templates for getting started fast. Python automation, "
            "GitHub Actions CI/CD, and AI prompt engineering templates with "
            "a quick-start guide to wire them together."
        ),
        "components": [
            {
                "key": "python_templates",
                "label": "Python Automation Templates",
                "individual_price": INDIVIDUAL_PRICES["python_templates"],
                "source": "templates",
                "subdir": "python-automation",
            },
            {
                "key": "github_templates",
                "label": "GitHub Actions Templates",
                "individual_price": INDIVIDUAL_PRICES["github_templates"],
                "source": "templates",
                "subdir": "github-actions",
            },
            {
                "key": "ai_prompt_templates",
                "label": "AI Prompt Templates",
                "individual_price": INDIVIDUAL_PRICES["ai_prompt_templates"],
                "source": "templates",
                "subdir": "ai-prompts",
            },
        ],
    })

    # 3) AI Builder Kit - $10
    bundles.append({
        "id": "bundle-ai-builder-kit",
        "title": "AI Builder Kit",
        "filename": "bundle-ai-builder-kit.md",
        "price": 10.00,
        "description": (
            "Everything you need to build AI-powered systems from scratch. "
            "The full ebook on autonomous AI architecture, AI prompt templates, "
            "SolarPunk config patterns, and engine blueprints."
        ),
        "components": [
            {
                "key": "ebook",
                "label": "The Autonomous AI System Guide (full ebook)",
                "individual_price": INDIVIDUAL_PRICES["ebook"],
                "source": "file",
                "path": PRODUCTS / "solarpunk-autonomous-ai-guide.md",
            },
            {
                "key": "ai_prompt_templates",
                "label": "AI Prompt Templates",
                "individual_price": INDIVIDUAL_PRICES["ai_prompt_templates"],
                "source": "templates",
                "subdir": "ai-prompts",
            },
            {
                "key": "solarpunk_config_templates",
                "label": "SolarPunk Config Templates",
                "individual_price": INDIVIDUAL_PRICES["solarpunk_config_templates"],
                "source": "templates",
                "subdir": "solarpunk-configs",
            },
        ],
    })

    # 4) Content Creator Pack - $6
    bundles.append({
        "id": "bundle-content-creator-pack",
        "title": "Content Creator Pack",
        "filename": "bundle-content-creator-pack.md",
        "price": 6.00,
        "description": (
            "Templates for automated content creation. AI prompts for generating "
            "articles and social posts, publishing workflow patterns, and "
            "SolarPunk engine configs for content pipelines."
        ),
        "components": [
            {
                "key": "ai_prompt_templates",
                "label": "AI Prompts for Content Generation",
                "individual_price": INDIVIDUAL_PRICES["ai_prompt_templates"],
                "source": "templates",
                "subdir": "ai-prompts",
            },
            {
                "key": "solarpunk_config_templates",
                "label": "SolarPunk Publishing Workflow Templates",
                "individual_price": INDIVIDUAL_PRICES["solarpunk_config_templates"],
                "source": "templates",
                "subdir": "solarpunk-configs",
            },
        ],
    })

    return bundles


# ---------------------------------------------------------------------------
# Bundle generation
# ---------------------------------------------------------------------------

def gather_content(component):
    """Return (label, content_text) for a single bundle component."""
    if component["source"] == "file":
        text = read_file_safe(component["path"])
        if text is None:
            text = "*[Content file not found: %s]*" % str(component["path"])
        return (component["label"], text)

    elif component["source"] == "templates":
        files = collect_template_files(component["subdir"])
        if not files:
            return (component["label"], "*[No template files found in %s]*" % component["subdir"])
        parts = []
        for f in files:
            content = read_file_safe(f)
            if content:
                parts.append("### %s\n\n%s" % (f.stem.replace("_", " ").title(), content))
        return (component["label"], "\n\n".join(parts))

    return (component["label"], "*[Unknown source type]*")


def build_bundle_markdown(bundle_def):
    """Generate the full bundle markdown document."""
    lines = []

    # Header
    lines.append("# %s" % bundle_def["title"])
    lines.append("")
    lines.append("**Price: %s** | *SolarPunk Digital Products*" % format_price(bundle_def["price"]))
    lines.append("")
    lines.append(bundle_def["description"])
    lines.append("")

    # Calculate savings
    total_individual = 0.0
    for comp in bundle_def["components"]:
        total_individual += comp["individual_price"]
    savings = total_individual - bundle_def["price"]
    if total_individual > 0:
        pct = (savings / total_individual) * 100.0
    else:
        pct = 0.0

    # Bundle Savings section
    lines.append("---")
    lines.append("")
    lines.append("## Bundle Savings")
    lines.append("")
    lines.append("| Item | Individual Price |")
    lines.append("|------|----------------|")
    for comp in bundle_def["components"]:
        lines.append("| %s | %s |" % (comp["label"], format_price(comp["individual_price"])))
    lines.append("| **Total if bought separately** | **%s** |" % format_price(total_individual))
    lines.append("")
    lines.append("**Bundle Price: %s**" % format_price(bundle_def["price"]))
    lines.append("")
    lines.append("**You save: %s (%.0f%% off)**" % (format_price(savings), pct))
    lines.append("")

    # What's Included
    lines.append("---")
    lines.append("")
    lines.append("## What's Included")
    lines.append("")
    for i, comp in enumerate(bundle_def["components"]):
        lines.append("%d. **%s** (%s value)" % (i + 1, comp["label"], format_price(comp["individual_price"])))
    lines.append("")

    # Table of Contents
    lines.append("---")
    lines.append("")
    lines.append("## Table of Contents")
    lines.append("")
    for i, comp in enumerate(bundle_def["components"]):
        anchor = comp["label"].lower().replace(" ", "-").replace("(", "").replace(")", "")
        lines.append("%d. [%s](#--%s)" % (i + 1, comp["label"], anchor))
    lines.append("")

    # Content sections
    for comp in bundle_def["components"]:
        label, content = gather_content(comp)
        lines.append(divider(label))
        lines.append(content)
        lines.append("")

    # Footer
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*Generated by BUNDLE_FORGE on %s*" % datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    lines.append("")
    lines.append("*99%% of revenue goes to mutual aid. 1%% to infrastructure.*")
    lines.append("")

    return "\n".join(lines)


def register_bundle(registry, bundle_def, char_count, word_count, section_count):
    """Add or update a bundle entry in the product registry."""
    entry = {
        "id": bundle_def["id"],
        "title": bundle_def["title"],
        "price": bundle_def["price"],
        "type": "bundle",
        "content_ready": True,
        "file_path": "products/%s" % bundle_def["filename"],
        "char_count": char_count,
        "word_count": word_count,
        "sections": section_count,
        "quality": "ready",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "last_validated": datetime.now(timezone.utc).isoformat(),
        "download_url": None,
        "gumroad_url": None,
        "kofi_url": None,
        "components": [c["key"] for c in bundle_def["components"]],
        "individual_total": sum(c["individual_price"] for c in bundle_def["components"]),
        "savings_pct": round(
            ((sum(c["individual_price"] for c in bundle_def["components"]) - bundle_def["price"])
             / max(sum(c["individual_price"] for c in bundle_def["components"]), 0.01)) * 100
        ),
    }
    registry["products"][bundle_def["id"]] = entry
    return entry


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run():
    """Generate all bundles and register them."""
    print("=" * 60)
    print("BUNDLE_FORGE -- creating themed product bundles")
    print("=" * 60)
    print("")

    registry = load_registry()
    bundle_defs = get_bundle_definitions()
    results = []

    for bdef in bundle_defs:
        print("[FORGE] Building: %s (%s)" % (bdef["title"], format_price(bdef["price"])))

        # Generate markdown
        md = build_bundle_markdown(bdef)

        # Write file
        out_path = PRODUCTS / bdef["filename"]
        out_path.write_text(md, encoding="utf-8")

        # Stats
        char_count = len(md)
        word_count = len(md.split())
        section_count = md.count("\n# ") + md.count("\n## ") + 1

        # Register
        entry = register_bundle(registry, bdef, char_count, word_count, section_count)

        # Savings info
        individual_total = sum(c["individual_price"] for c in bdef["components"])
        savings = individual_total - bdef["price"]
        if individual_total > 0:
            pct = (savings / individual_total) * 100.0
        else:
            pct = 0.0

        print("  -> Wrote: %s" % str(out_path))
        print("  -> %d chars, %d words, %d sections" % (char_count, word_count, section_count))
        print("  -> Components: %d items" % len(bdef["components"]))
        print("  -> Individual total: %s | Bundle: %s | Save: %s (%.0f%%)" % (
            format_price(individual_total),
            format_price(bdef["price"]),
            format_price(savings),
            pct,
        ))
        print("")

        results.append({
            "title": bdef["title"],
            "price": bdef["price"],
            "file": str(out_path),
            "chars": char_count,
            "words": word_count,
            "sections": section_count,
            "savings_pct": round(pct),
        })

    # Save registry
    save_registry(registry)
    print("[FORGE] Updated product registry: %s" % str(REGISTRY_PATH))
    print("")

    # Summary
    print("=" * 60)
    print("BUNDLE_FORGE COMPLETE -- %d bundles created" % len(results))
    print("=" * 60)
    for r in results:
        print("  %s -- %s (%d words, %d%% savings)" % (
            r["title"], format_price(r["price"]), r["words"], r["savings_pct"]
        ))
    print("")

    return results


if __name__ == "__main__":
    run()

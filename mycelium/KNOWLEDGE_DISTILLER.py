#!/usr/bin/env python3
"""
KNOWLEDGE_DISTILLER.py -- SolarPunk Engine Encyclopedia Generator
=================================================================
Scans every engine in mycelium/, extracts metadata (docstrings,
functions, reads/writes, layer info), groups by category, and
generates a sellable markdown encyclopedia documenting the entire
system.

Biology: Mycorrhizal networks share nutrients and intelligence
between trees. This engine distills the collective knowledge of
every engine into a single document -- the forest teaching itself.

Reads:  mycelium/*.py (all engine source files)
        mycelium/OMNIBUS.py (layer assignments)
        data/product_registry.json
Writes: products/solarpunk-engine-encyclopedia.md
        data/product_registry.json (registers as $8 product)
        data/knowledge_distiller_state.json
"""
import ast
import json
import os
import re
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
DATA.mkdir(exist_ok=True)
PRODUCTS = Path("products")
PRODUCTS.mkdir(exist_ok=True)
MYCELIUM = Path("mycelium")

# Category classification rules: pattern list -> category name
CATEGORY_RULES = [
    (["CRISIS", "MONITOR", "SIGNAL", "DARK_WATCH", "BIOLUMINESCENCE", "QUORUM",
      "SPORE", "IMMUNE", "SENTINEL", "APOPTOSIS", "VANISH", "GUARDIAN",
      "SCAM_SHIELD", "SECRETS_CHECKER"], "Crisis Response & Defense"),
    (["REVENUE", "INCOME", "PRODUCT", "SHOP", "STORE", "GUMROAD", "KOFI",
      "ETSY", "NANOSHOP", "PAYPAL", "PAYOUT", "AFFILIATE", "SALE",
      "MONETIZE", "PAYMENT", "STOREFRONT"], "Revenue Generation"),
    (["CONTENT", "ARTICLE", "SOCIAL", "BLUESKY", "MASTODON", "SUBSTACK",
      "NEWSLETTER", "TWEET", "NARRATOR", "PUBLISHER", "RSS", "DEV_TO",
      "REDDIT", "BROADCAST", "AMPLIFY", "VIRALITY"], "Content & Distribution"),
    (["LIVE_WIRE", "BRIDGE", "CHIMERA", "SIGNAL_INTEGRITY", "SYNAPSE",
      "TOPOLOGY", "WIRING", "RELAY", "SWARM", "RECEPTOR", "TRANSMITTER",
      "CHAIN_ORCHESTRATOR"], "Topology & Wiring"),
    (["CORTEX", "BRAIN", "ORACLE", "KNOWLEDGE", "MEMORY", "SYNTHESIS",
      "SYNERGY", "RESONANCE", "TEMPORAL"], "Intelligence & Memory"),
    (["ART", "GAZA", "BRAND", "LEGAL", "LANDING", "DESIGN",
      "BLUEPRINT", "PORTRAIT"], "Creative & Brand"),
    (["GRANT", "NGO", "EMAIL", "OUTREACH", "HUMAN_CONNECTOR",
      "CONNECTION", "FIRST_CONTACT", "CONTRIBUTOR"], "Outreach & Partnerships"),
    (["AUTO", "SELF", "ARCHITECT", "BUILDER", "CHAOS", "TEST",
      "HEAL", "UPGRADE", "CAPACITY", "BOTTLENECK", "CAPABILITY",
      "VALIDATOR", "PROOF", "AUTONOMY", "ENGINE_INTEGRITY"], "Self-Improvement & Ops"),
    (["DESKTOP", "DAEMON", "WAKE", "CALENDAR", "SCHEDULE",
      "CIRCADIAN", "NIGHTLY", "WEEKEND", "BRIEFING", "TASK",
      "ORCHESTRATOR"], "Infrastructure & Scheduling"),
    (["STIGMERGY", "CHEMOTAXIS", "SYMBIOGENESIS", "OSMOSIS",
      "BIOLUMINESCENCE", "SPORE", "QUORUM", "FRACTAL",
      "MYCELI"], "Bio-Inspired Patterns"),
]


def parse_omnibus_layers():
    """Parse the OMNIBUS.py docstring to build engine -> layer mapping."""
    layers = {}
    omnibus_path = MYCELIUM / "OMNIBUS.py"
    if not omnibus_path.exists():
        return layers
    try:
        src = omnibus_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return layers

    # Match lines like: L0  ENGINE_A . ENGINE_B . ENGINE_C
    # Also match lines that are continuations (indented, with dots)
    current_layer = None
    for line in src.split("\n"):
        layer_match = re.match(r"^L(\d)\s+(.+)", line)
        if layer_match:
            current_layer = "L%s" % layer_match.group(1)
            engines_str = layer_match.group(2)
        elif current_layer and re.match(r"^\s{4,}\S", line):
            engines_str = line
        else:
            current_layer = None
            continue
        # Split on dots and whitespace
        parts = re.split(r"\s*\.\s*", engines_str)
        for part in parts:
            name = part.strip().split("[")[0].strip().split("(")[0].strip()
            if name and re.match(r"^[A-Z_]+$", name):
                layers[name] = current_layer
    return layers


def extract_reads_writes(docstring):
    """Extract Reads/Writes from docstring text."""
    reads = []
    writes = []
    if not docstring:
        return reads, writes

    current = None
    for line in docstring.split("\n"):
        stripped = line.strip()
        low = stripped.lower()
        if low.startswith("reads:") or low.startswith("input:"):
            current = "reads"
            rest = stripped.split(":", 1)[1].strip()
            if rest:
                reads.append(rest)
        elif low.startswith("writes:") or low.startswith("output:"):
            current = "writes"
            rest = stripped.split(":", 1)[1].strip()
            if rest:
                writes.append(rest)
        elif current and stripped.startswith(("->", "-->", "-")):
            item = re.sub(r"^[->\s]+", "", stripped).strip()
            if item:
                if current == "reads":
                    reads.append(item)
                else:
                    writes.append(item)
        elif current and not stripped:
            current = None
    return reads, writes


def classify_engine(name):
    """Auto-detect category from engine name patterns."""
    upper = name.upper()
    for patterns, category in CATEGORY_RULES:
        for pat in patterns:
            if pat in upper:
                return category
    return "Core Infrastructure"


def extract_engine_info(filepath):
    """Extract metadata from a single engine file."""
    info = {
        "name": filepath.stem,
        "path": str(filepath),
        "docstring": "",
        "first_line": "",
        "functions": [],
        "has_run": False,
        "line_count": 0,
        "reads": [],
        "writes": [],
        "category": "",
    }
    try:
        src = filepath.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return info

    lines = src.split("\n")
    info["line_count"] = len(lines)

    # Parse AST for docstring and functions
    try:
        tree = ast.parse(src)
        # Module docstring
        ds = ast.get_docstring(tree)
        if ds:
            info["docstring"] = ds
            first = ds.strip().split("\n")[0].strip()
            # Remove separator lines
            if first and not re.match(r"^[=\-~]+$", first):
                info["first_line"] = first
            else:
                # Try the second line
                ds_lines = [l.strip() for l in ds.strip().split("\n") if l.strip()]
                for dl in ds_lines:
                    if not re.match(r"^[=\-~]+$", dl):
                        info["first_line"] = dl
                        break

        # Functions
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                info["functions"].append(node.name)
                if node.name == "run":
                    info["has_run"] = True
    except SyntaxError:
        # Fallback: regex for functions
        for m in re.finditer(r"^def\s+(\w+)\s*\(", src, re.MULTILINE):
            info["functions"].append(m.group(1))
            if m.group(1) == "run":
                info["has_run"] = True
        # Fallback: regex for docstring
        ds_match = re.search(r'^"""(.*?)"""', src, re.DOTALL)
        if not ds_match:
            ds_match = re.search(r"^'''(.*?)'''", src, re.DOTALL)
        if ds_match:
            info["docstring"] = ds_match.group(1)
            first = info["docstring"].strip().split("\n")[0].strip()
            if first and not re.match(r"^[=\-~]+$", first):
                info["first_line"] = first

    reads, writes = extract_reads_writes(info["docstring"])
    info["reads"] = reads
    info["writes"] = writes
    info["category"] = classify_engine(info["name"])

    return info


def generate_encyclopedia(engines, layers):
    """Generate the markdown encyclopedia from engine metadata."""
    total_engines = len(engines)
    total_lines = sum(e["line_count"] for e in engines)
    total_functions = sum(len(e["functions"]) for e in engines)
    engines_with_run = sum(1 for e in engines if e["has_run"])

    # Group by category
    categories = {}
    for eng in engines:
        cat = eng["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(eng)

    # Sort categories by size descending
    sorted_cats = sorted(categories.items(), key=lambda x: -len(x[1]))

    parts = []

    # Header
    parts.append("# SolarPunk Engine Encyclopedia")
    parts.append("")
    parts.append("> A complete reference to every engine in the SolarPunk Nerve Center")
    parts.append("> -- a living, bio-inspired autonomous AI system built to fight")
    parts.append("> tyranny, protect the silenced, and generate sovereign revenue.")
    parts.append("")
    parts.append("Generated: %s" % datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))
    parts.append("")

    # Stats
    parts.append("## System Statistics")
    parts.append("")
    parts.append("| Metric | Value |")
    parts.append("|--------|-------|")
    parts.append("| Total Engines | %d |" % total_engines)
    parts.append("| Total Lines of Code | %s |" % "{:,}".format(total_lines))
    parts.append("| Total Functions | %s |" % "{:,}".format(total_functions))
    parts.append("| Engines with run() | %d |" % engines_with_run)
    parts.append("| Categories | %d |" % len(sorted_cats))
    parts.append("")

    # Table of Contents
    parts.append("## Table of Contents")
    parts.append("")
    for i, (cat, cat_engines) in enumerate(sorted_cats):
        anchor = cat.lower().replace(" ", "-").replace("&", "").replace("--", "-")
        parts.append("%d. [%s](#%s) (%d engines)" % (i + 1, cat, anchor, len(cat_engines)))
    parts.append("")
    parts.append("---")
    parts.append("")

    # Each category
    for cat, cat_engines in sorted_cats:
        parts.append("## %s" % cat)
        parts.append("")
        parts.append("*%d engines in this category*" % len(cat_engines))
        parts.append("")

        # Sort engines by name within category
        cat_engines.sort(key=lambda e: e["name"])

        for eng in cat_engines:
            layer = layers.get(eng["name"], "?")
            parts.append("### %s" % eng["name"])
            parts.append("")

            # Purpose
            if eng["first_line"]:
                parts.append("**Purpose:** %s" % eng["first_line"])
            else:
                parts.append("**Purpose:** *(no docstring)*")
            parts.append("")

            # Meta table
            parts.append("| Property | Value |")
            parts.append("|----------|-------|")
            parts.append("| Layer | %s |" % layer)
            parts.append("| Lines | %d |" % eng["line_count"])
            parts.append("| Functions | %d |" % len(eng["functions"]))
            parts.append("| Has run() | %s |" % ("Yes" if eng["has_run"] else "No"))
            parts.append("")

            # Functions list
            if eng["functions"]:
                parts.append("**Functions:** %s" % ", ".join("`%s`" % f for f in eng["functions"]))
                parts.append("")

            # Reads/Writes
            if eng["reads"]:
                parts.append("**Reads:** %s" % " | ".join(eng["reads"]))
                parts.append("")
            if eng["writes"]:
                parts.append("**Writes:** %s" % " | ".join(eng["writes"]))
                parts.append("")

            parts.append("---")
            parts.append("")

    # Footer
    parts.append("## About This System")
    parts.append("")
    parts.append("The SolarPunk Nerve Center is an autonomous, bio-inspired AI system")
    parts.append("composed of %d engines organized into %d categories." % (total_engines, len(sorted_cats)))
    parts.append("Each engine is a self-contained unit that reads data, processes it,")
    parts.append("and writes results -- forming a living neural network of code.")
    parts.append("")
    parts.append("The system runs without human intervention, healing itself,")
    parts.append("generating revenue, monitoring crises, and amplifying voices")
    parts.append("that powerful systems want silenced.")
    parts.append("")
    parts.append("*Built by Meeko. Powered by the Mycelium.*")
    parts.append("")

    return "\n".join(parts)


def register_product(encyclopedia_path, char_count, word_count, section_count):
    """Register the encyclopedia in the product registry."""
    registry_path = DATA / "product_registry.json"
    registry = {"products": {}, "last_updated": None}
    if registry_path.exists():
        try:
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    now = datetime.now(timezone.utc).isoformat()
    registry["products"]["engine-encyclopedia"] = {
        "id": "engine-encyclopedia",
        "title": "SolarPunk Engine Encyclopedia",
        "price": 8.0,
        "content_ready": True,
        "file_path": str(encyclopedia_path),
        "char_count": char_count,
        "word_count": word_count,
        "sections": section_count,
        "quality": "ready",
        "generated_at": now,
        "last_validated": now,
        "download_url": None,
        "gumroad_url": None,
        "kofi_url": None,
    }
    registry["last_updated"] = now
    registry_path.write_text(json.dumps(registry, indent=2), encoding="utf-8")
    return registry


def run():
    """Main entry point -- scan, extract, generate, register."""
    print("KNOWLEDGE_DISTILLER: Scanning mycelium/ for engines...")

    # Parse OMNIBUS layer map
    layers = parse_omnibus_layers()
    print("  Parsed %d layer assignments from OMNIBUS.py" % len(layers))

    # Scan all .py files
    py_files = sorted(MYCELIUM.glob("*.py"))
    skip_prefixes = ("__init__", "__pycache__")
    engines = []
    skipped = 0

    for fp in py_files:
        if fp.stem.startswith(skip_prefixes):
            skipped += 1
            continue
        info = extract_engine_info(fp)
        engines.append(info)

    print("  Found %d engines (%d skipped)" % (len(engines), skipped))

    # Generate the encyclopedia
    md_content = generate_encyclopedia(engines, layers)

    # Write the encyclopedia
    out_path = PRODUCTS / "solarpunk-engine-encyclopedia.md"
    out_path.write_text(md_content, encoding="utf-8")

    char_count = len(md_content)
    word_count = len(md_content.split())
    section_count = md_content.count("\n## ")

    print("  Encyclopedia written: %s" % str(out_path))
    print("    %s chars, %s words, %d sections" % (
        "{:,}".format(char_count),
        "{:,}".format(word_count),
        section_count,
    ))

    # Register as product
    registry = register_product(str(out_path), char_count, word_count, section_count)
    print("  Registered as $8 product in product_registry.json")

    # Save state
    state = {
        "last_run": datetime.now(timezone.utc).isoformat(),
        "engines_scanned": len(engines),
        "engines_skipped": skipped,
        "categories": {},
        "total_lines": sum(e["line_count"] for e in engines),
        "total_functions": sum(len(e["functions"]) for e in engines),
        "output_file": str(out_path),
        "output_chars": char_count,
        "output_words": word_count,
        "product_price": 8.0,
    }
    # Category summary
    for eng in engines:
        cat = eng["category"]
        if cat not in state["categories"]:
            state["categories"][cat] = 0
        state["categories"][cat] += 1

    state_path = DATA / "knowledge_distiller_state.json"
    state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
    print("  State saved: %s" % str(state_path))

    # Summary
    print("")
    print("KNOWLEDGE_DISTILLER: Complete!")
    print("  %d engines documented across %d categories" % (
        len(engines), len(state["categories"])
    ))
    print("  Total codebase: %s lines, %s functions" % (
        "{:,}".format(state["total_lines"]),
        "{:,}".format(state["total_functions"]),
    ))

    return state


if __name__ == "__main__":
    run()

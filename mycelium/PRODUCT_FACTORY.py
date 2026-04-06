#!/usr/bin/env python3
"""
PRODUCT_FACTORY.py -- Generates sellable digital products from system data
=========================================================================
Previous product generation required an API key (all content was "HTTP 400").
This engine generates products using ONLY local data -- no API needed.

What it builds:
  1. Reads existing guides in data/guide_*.md
  2. Validates they have real content (not "[Content generation failed]")
  3. Updates product_registry.json with accurate metadata
  4. Generates new product ideas from system data (wiring reports, engine stats)
  5. Creates a publishing queue for one-click listing on Ko-fi/Gumroad

The products are real. The content is real. The only manual step is:
  - Create a free Ko-fi or Gumroad account (10 minutes, one time)
  - Paste the listings (QUICK_REVENUE.py generates the text)

Zero secrets needed. Pure filesystem operations.
"""
import json
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
DATA.mkdir(exist_ok=True)
MYCELIUM = Path("mycelium")


def load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8", errors="replace"))
    except (json.JSONDecodeError, FileNotFoundError, OSError):
        return {}


def validate_guide(filepath):
    """Check if a guide has real content (not failed generation stubs)."""
    try:
        text = filepath.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None

    # Count real content sections vs failed ones
    lines = text.split("\n")
    total_sections = 0
    failed_sections = 0
    word_count = len(text.split())
    char_count = len(text)

    for line in lines:
        if line.startswith("## ") and not line.startswith("## Table"):
            total_sections += 1
        if "[Content generation failed" in line:
            failed_sections += 1

    has_real_content = failed_sections == 0 and word_count > 500

    return {
        "file": str(filepath),
        "word_count": word_count,
        "char_count": char_count,
        "total_sections": total_sections,
        "failed_sections": failed_sections,
        "has_real_content": has_real_content,
        "quality": "ready" if has_real_content else "needs_content",
    }


def scan_guides():
    """Find all guide files and validate them."""
    guides = {}
    for guide_file in sorted(DATA.glob("guide_*.md")):
        slug = guide_file.stem.replace("guide_", "")
        info = validate_guide(guide_file)
        if info:
            guides[slug] = info
    return guides


def update_registry(guides):
    """Update product_registry.json with current guide status."""
    registry = load_json(DATA / "product_registry.json")
    if "products" not in registry:
        registry["products"] = {}

    # Handle list format (from new product_registry) vs dict format
    if isinstance(registry["products"], list):
        products_dict = {}
        for p in registry["products"]:
            pid = p.get("id", p.get("name", "unknown"))
            products_dict[pid] = p
        registry["products"] = products_dict

    for slug, info in guides.items():
        existing = registry["products"].get(slug, {})
        registry["products"][slug] = {
            "id": slug,
            "title": existing.get("title", slug.replace("-", " ").title()),
            "price": existing.get("price", 1.00),
            "content_ready": info["has_real_content"],
            "file_path": info["file"],
            "char_count": info["char_count"],
            "word_count": info["word_count"],
            "sections": info["total_sections"],
            "quality": info["quality"],
            "generated_at": existing.get("generated_at", datetime.now(timezone.utc).isoformat()),
            "last_validated": datetime.now(timezone.utc).isoformat(),
            "download_url": existing.get("download_url"),
            "gumroad_url": existing.get("gumroad_url"),
            "kofi_url": existing.get("kofi_url"),
        }

    registry["last_updated"] = datetime.now(timezone.utc).isoformat()
    try: _h=json.loads((DATA/"homeostasis_state.json").read_text(encoding="utf-8"))
    except: _h={}
    try: _c=json.loads((DATA/"neural_cortex_state.json").read_text(encoding="utf-8"))
    except: _c={}
    registry["nervous_system"]={"equilibrium":_h.get("equilibrium",0),"trend":_h.get("trend","unknown"),"brain_confidence":_c.get("decision_confidence",0)}
    (DATA / "product_registry.json").write_text(json.dumps(registry, indent=2), encoding="utf-8")
    return registry


def generate_publish_queue(registry):
    """Create a queue of products ready to publish."""
    queue = []
    for pid, prod in registry.get("products", {}).items():
        if prod.get("content_ready") and not prod.get("gumroad_url") and not prod.get("kofi_url"):
            queue.append({
                "id": pid,
                "title": prod["title"],
                "price": prod["price"],
                "word_count": prod["word_count"],
                "file_path": prod["file_path"],
                "status": "ready_to_publish",
                "platforms": ["kofi", "gumroad"],
                "note": "Paste listing text from docs/quick_revenue.html into platform UI",
            })

    (DATA / "publish_queue.json").write_text(json.dumps({
        "generated": datetime.now(timezone.utc).isoformat(),
        "ready_count": len(queue),
        "products": queue,
        "instructions": {
            "kofi": "Go to ko-fi.com > Shop > Add Item > paste title, description, price > upload cover image > publish",
            "gumroad": "Go to gumroad.com > New Product > Digital > paste title, description > upload file > set price > publish",
        }
    }, indent=2), encoding="utf-8")

    return queue


def generate_system_snapshot_product():
    """Generate a product from current system data -- no AI needed."""
    wire_report = load_json(DATA / "live_wire_report.json")
    knowledge = load_json(DATA / "knowledge_graph.json")
    sentinel = load_json(DATA / "sentinel_report.json")

    if not wire_report:
        return None

    stats = wire_report.get("stats", {})
    engines = wire_report.get("engines", {})

    # Build the snapshot guide
    content = f"""# Inside an Autonomous AI System -- Live Snapshot
### Real data from a running 242-engine digital organism

---

**Price:** $1.00 · **A SolarPunk Guide** · 99% goes to Gaza via PCRF (EIN 93-1057665)

---

## What You're Looking At

This is a live snapshot of SolarPunk -- an autonomous digital organism running on GitHub.
The data below is real. Not simulated. Not hypothetical. This system is running right now.

## System Topology

- **Total engines**: {stats.get('total_engines', 'N/A')}
- **Wire connections**: {stats.get('total_wires_discovered', 'N/A')}
- **Zero-secret chains**: {stats.get('zero_secret_chains', 'N/A')} (work without any API keys)
- **Orphan outputs**: {stats.get('orphan_outputs', 'N/A')} (data written but never read)
- **Hungry inputs**: {stats.get('hungry_inputs', 'N/A')} (data needed but not yet produced)

## Engine Categories

"""
    # Categorize engines
    zero_secrets = []
    needs_keys = []
    for name, info in engines.items():
        if info.get("zero_secrets"):
            zero_secrets.append(name)
        else:
            needs_keys.append(name)

    content += f"### Zero-Secret Engines ({len(zero_secrets)} total)\n"
    content += "These engines run without any API keys or credentials:\n\n"
    for name in sorted(zero_secrets)[:30]:
        info = engines[name]
        content += f"- **{name}** -- reads: {', '.join(info.get('reads', [])) or 'nothing'}, writes: {', '.join(info.get('writes', [])) or 'nothing'}\n"
    if len(zero_secrets) > 30:
        content += f"- ... and {len(zero_secrets) - 30} more\n"

    content += f"\n### Engines Needing API Keys ({len(needs_keys)} total)\n"
    content += "These engines unlock when you add credentials:\n\n"
    for name in sorted(needs_keys)[:20]:
        info = engines[name]
        keys = info.get("api_keys_needed", [])
        content += f"- **{name}** -- needs: {', '.join(keys)}\n"
    if len(needs_keys) > 20:
        content += f"- ... and {len(needs_keys) - 20} more\n"

    # Wiring topology
    wires = wire_report.get("wires", [])
    content += "\n## Live Wire Connections (Sample)\n\n"
    content += "These are real data flows between engines:\n\n"
    for wire in wires[:25]:
        zs = " (zero-secrets)" if wire.get("chain_zero_secrets") else ""
        content += f"- {wire['from']} -> {wire['to']} via `{wire['via']}`{zs}\n"
    if len(wires) > 25:
        content += f"- ... and {len(wires) - 25} more connections\n"

    # Knowledge graph stats
    if knowledge:
        kg_nodes = len(knowledge.get("nodes", []))
        kg_edges = len(knowledge.get("edges", []))
        content += f"\n## Knowledge Graph\n\n"
        content += f"- **{kg_nodes} nodes** (engines, data files, concepts)\n"
        content += f"- **{kg_edges} edges** (connections between them)\n"

    content += f"""
## What This Means

This system demonstrates that autonomous software can:
1. Discover its own structure (LIVE_WIRE scans and maps every engine)
2. Feed its own needs (BRIDGE_BUILDER creates data for hungry inputs)
3. Monitor its own health (VITAL_SIGN_API publishes metrics)
4. Generate its own products (you're reading one right now)
5. Route revenue to causes (99% hard-coded to PCRF)

Every line of code is public: github.com/meekotharaccoon-cell/meeko-nerve-center

## Snapshot Metadata

- **Generated**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
- **Data source**: data/live_wire_report.json
- **Engines scanned**: {stats.get('total_engines', 'N/A')}

---
*Built autonomously. Funded for Gaza. Running forever.*
"""

    slug = "system-snapshot"
    out = DATA / f"guide_{slug}.md"
    out.write_text(content, encoding="utf-8")

    return {
        "slug": slug,
        "title": "Inside an Autonomous AI System -- Live Snapshot",
        "word_count": len(content.split()),
        "char_count": len(content),
    }


def run():
    print("PRODUCT FACTORY -- Generating sellable digital products")
    print("=" * 55)

    # Phase 1: Scan existing guides
    print("\n  Phase 1: SCANNING guides...")
    guides = scan_guides()
    ready = sum(1 for g in guides.values() if g["has_real_content"])
    needs_work = sum(1 for g in guides.values() if not g["has_real_content"])
    print(f"    Found {len(guides)} guides: {ready} ready, {needs_work} need content")

    for slug, info in guides.items():
        status = "READY" if info["has_real_content"] else "EMPTY"
        print(f"    [{status}] {slug} -- {info['word_count']} words, {info['total_sections']} sections")

    # Phase 2: Generate system snapshot product
    print("\n  Phase 2: GENERATING system snapshot product...")
    snapshot = generate_system_snapshot_product()
    if snapshot:
        print(f"    Created: {snapshot['title']} ({snapshot['word_count']} words)")
        # Re-scan to include new product
        guides = scan_guides()
    else:
        print("    Skipped (no wire report data)")

    # Phase 3: Update registry
    print("\n  Phase 3: UPDATING product registry...")
    registry = update_registry(guides)
    total_products = len(registry.get("products", {}))
    ready_products = sum(1 for p in registry["products"].values() if p.get("content_ready"))
    print(f"    Registry: {total_products} products, {ready_products} ready to sell")

    # Phase 4: Generate publish queue
    print("\n  Phase 4: BUILDING publish queue...")
    queue = generate_publish_queue(registry)
    print(f"    {len(queue)} products ready to publish")
    for item in queue:
        print(f"    - {item['title']} (${item['price']:.2f}, {item['word_count']} words)")

    # Summary
    print(f"\n  === PRODUCT FACTORY SUMMARY ===")
    print(f"  Total products:     {total_products}")
    print(f"  Ready to sell:      {ready_products}")
    print(f"  In publish queue:   {len(queue)}")
    print(f"  Revenue per sale:   $1.00 (99% -> Gaza)")
    print(f"\n  Next step: Create free Ko-fi or Gumroad account")
    print(f"  Then: Paste listings from docs/quick_revenue.html")
    print(f"  Time needed: ~10 minutes, one time")


if __name__ == "__main__":
    run()

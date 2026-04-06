#!/usr/bin/env python3
"""
TASK_FACTORY.py -- Autonomous Task Generator
==============================================
Reads the entire system state and generates concrete tasks that
can be completed autonomously -- no human input needed.

Task types:
  - PRODUCT: generate a new product from existing data
  - CONTENT: write an article, social post, or listing
  - WIRE: connect two engines that should be talking
  - HEAL: fix a broken engine or corrupted data file
  - GROW: create a new engine to fill a gap
  - SELL: create a listing for an existing product

Each task includes:
  - What to do (concrete, executable steps)
  - Which engine can do it (or "BUILD" if none exists)
  - Expected output (what files get created/updated)
  - Priority (1-5, where 1 = do now)

Reads: data/live_wire_report.json, data/product_registry.json,
       data/signal_integrity_report.json, data/chimera_evolution_report.json,
       data/zero_secret_army_report.json, data/storefront_listings.json,
       data/bridge_report.json
Writes: data/task_queue.json, data/task_factory_state.json
"""
import json
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
DATA.mkdir(exist_ok=True)
MYCELIUM = Path("mycelium")
PRODUCTS = Path("products")


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


def generate_product_tasks(registry):
    """Generate tasks for products that need work."""
    tasks = []
    products = registry.get("products", {})

    # Products without listings
    listings = load_json(DATA / "storefront_listings.json")
    listed_ids = set(listings.get("listings", {}).keys())
    for pid, prod in products.items():
        if pid not in listed_ids:
            tasks.append({
                "type": "SELL",
                "priority": 2,
                "title": "Generate storefront listing for %s" % prod.get("title", pid),
                "engine": "STOREFRONT_COPY",
                "command": "python mycelium/STOREFRONT_COPY.py",
                "expected_output": "data/storefront_listings.json updated",
                "autonomous": True,
            })
            break  # One task per type to avoid flooding

    # Products with low word count (need expansion)
    for pid, prod in products.items():
        wc = prod.get("word_count", 0)
        if wc < 500 and prod.get("content_ready"):
            tasks.append({
                "type": "PRODUCT",
                "priority": 3,
                "title": "Expand %s (only %d words)" % (prod.get("title", pid), wc),
                "engine": "PRODUCT_FORGE",
                "command": "python mycelium/PRODUCT_FORGE.py",
                "expected_output": "products/%s expanded" % prod.get("file_path", ""),
                "autonomous": True,
            })

    # Check if new template domains could be added
    template_dir = PRODUCTS / "templates"
    existing_domains = []
    if template_dir.exists():
        existing_domains = [d.name for d in template_dir.iterdir() if d.is_dir()]

    potential_domains = [
        "docker-automation", "cli-tools", "web-scraping",
        "data-science", "security-tools", "testing-frameworks",
    ]
    for domain in potential_domains:
        if domain not in existing_domains:
            tasks.append({
                "type": "PRODUCT",
                "priority": 4,
                "title": "Generate template pack for %s domain" % domain,
                "engine": "MICRO_PRODUCT_FACTORY",
                "command": "python mycelium/MICRO_PRODUCT_FACTORY.py",
                "expected_output": "products/templates/%s/ created" % domain,
                "autonomous": True,
                "note": "Needs MICRO_PRODUCT_FACTORY domain list expanded",
            })
            break  # One at a time

    return tasks


def generate_content_tasks():
    """Generate content creation tasks."""
    tasks = []

    # Check article drafts
    drafts = load_json(DATA / "article_drafts.json")
    draft_list = drafts.get("drafts", [])
    unpublished = [d for d in draft_list if d.get("status") == "draft"]
    if unpublished:
        tasks.append({
            "type": "CONTENT",
            "priority": 2,
            "title": "Publish %d draft articles" % len(unpublished),
            "engine": "CONTENT_AUTOPILOT",
            "command": "python mycelium/CONTENT_AUTOPILOT.py",
            "expected_output": "data/article_drafts.json updated, new draft generated",
            "autonomous": True,
        })

    # Check social queue
    social = load_json(DATA / "social_queue.json")
    queue = social.get("queue", [])
    if len(queue) < 20:
        tasks.append({
            "type": "CONTENT",
            "priority": 3,
            "title": "Generate more social posts (queue at %d)" % len(queue),
            "engine": "CONTENT_AUTOPILOT",
            "command": "python mycelium/CONTENT_AUTOPILOT.py",
            "expected_output": "data/social_queue.json appended",
            "autonomous": True,
        })

    return tasks


def generate_wire_tasks():
    """Generate wiring/connection tasks."""
    tasks = []

    bridge_report = load_json(DATA / "bridge_report.json")
    unbridged = bridge_report.get("still_unbridged", bridge_report.get("unbridged_count", 0))
    if isinstance(unbridged, list):
        unbridged = len(unbridged)

    if unbridged > 0:
        tasks.append({
            "type": "WIRE",
            "priority": 2,
            "title": "Bridge %d hungry inputs" % unbridged,
            "engine": "BRIDGE_BUILDER",
            "command": "python mycelium/BRIDGE_BUILDER.py",
            "expected_output": "data/bridge_report.json updated",
            "autonomous": True,
        })

    return tasks


def generate_heal_tasks():
    """Generate healing/repair tasks."""
    tasks = []

    # Check immune system report
    immune = load_json(DATA / "immune_system_report.json")
    infected = immune.get("still_infected", immune.get("infected_count", 0))
    if isinstance(infected, list):
        infected = len(infected)

    if infected > 0:
        tasks.append({
            "type": "HEAL",
            "priority": 1,
            "title": "Repair %d infected engines" % infected,
            "engine": "IMMUNE_SYSTEM",
            "command": "python mycelium/IMMUNE_SYSTEM.py",
            "expected_output": "data/immune_system_report.json updated",
            "autonomous": True,
        })

    # Check signal integrity for stubs
    integrity = load_json(DATA / "signal_integrity_report.json")
    stubs = integrity.get("stub_count", integrity.get("stubs", 0))
    dead = integrity.get("dead_count", integrity.get("dead", 0))

    if (isinstance(stubs, int) and stubs > 10) or (isinstance(dead, int) and dead > 10):
        tasks.append({
            "type": "HEAL",
            "priority": 3,
            "title": "Clean up stub/dead wires (%s stubs, %s dead)" % (stubs, dead),
            "engine": "SIGNAL_INTEGRITY",
            "command": "python mycelium/SIGNAL_INTEGRITY.py",
            "expected_output": "data/signal_integrity_report.json updated",
            "autonomous": True,
        })

    return tasks


def generate_grow_tasks():
    """Generate growth tasks -- new engines to build."""
    tasks = []

    # Check what's missing from the system
    wire_report = load_json(DATA / "live_wire_report.json")
    engines = wire_report.get("engines", {})

    # Find data files that are read but never written (gaps)
    all_reads = set()
    all_writes = set()
    for info in engines.values():
        all_reads.update(info.get("reads", []))
        all_writes.update(info.get("writes", []))

    gaps = all_reads - all_writes
    real_gaps = [g for g in gaps if g.endswith(".json") and not g.startswith("{")]
    if len(real_gaps) > 5:
        tasks.append({
            "type": "GROW",
            "priority": 4,
            "title": "Build engines to produce %d missing data files" % len(real_gaps),
            "engine": "BUILD",
            "command": "# Needs new engine creation",
            "expected_output": "New engines that write: %s" % ", ".join(sorted(real_gaps)[:5]),
            "autonomous": False,
            "note": "These data files are read but never written by any engine",
        })

    return tasks


def generate_deploy_tasks():
    """Generate deployment/dashboard tasks."""
    tasks = []

    # Always refresh dashboard and catalog
    tasks.append({
        "type": "CONTENT",
        "priority": 3,
        "title": "Refresh system dashboard and product catalog",
        "engine": "METRICS_DASHBOARD + CATALOG_GENERATOR",
        "command": "python mycelium/METRICS_DASHBOARD.py && python mycelium/CATALOG_GENERATOR.py",
        "expected_output": "docs/dashboard.html + docs/catalog.html updated",
        "autonomous": True,
    })

    return tasks


def run():
    print("TASK FACTORY -- Autonomous Task Generator")
    print("=" * 50)

    state = load_json(DATA / "task_factory_state.json")
    if not state:
        state = {"runs": 0, "total_tasks_generated": 0, "last_run": None}

    registry = load_json(DATA / "product_registry.json")

    print("\n  [1/2] Generating tasks from system state...")
    all_tasks = []

    heal_tasks = generate_heal_tasks()
    all_tasks.extend(heal_tasks)
    print("    HEAL tasks:    %d" % len(heal_tasks))

    wire_tasks = generate_wire_tasks()
    all_tasks.extend(wire_tasks)
    print("    WIRE tasks:    %d" % len(wire_tasks))

    product_tasks = generate_product_tasks(registry)
    all_tasks.extend(product_tasks)
    print("    PRODUCT tasks: %d" % len(product_tasks))

    content_tasks = generate_content_tasks()
    all_tasks.extend(content_tasks)
    print("    CONTENT tasks: %d" % len(content_tasks))

    grow_tasks = generate_grow_tasks()
    all_tasks.extend(grow_tasks)
    print("    GROW tasks:    %d" % len(grow_tasks))

    deploy_tasks = generate_deploy_tasks()
    all_tasks.extend(deploy_tasks)
    print("    DEPLOY tasks:  %d" % len(deploy_tasks))

    # Sort by priority
    all_tasks.sort(key=lambda t: t["priority"])

    # Count autonomous vs needs-human
    autonomous = [t for t in all_tasks if t.get("autonomous")]
    manual = [t for t in all_tasks if not t.get("autonomous")]

    print("\n  [2/2] Saving task queue...")
    task_queue = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_tasks": len(all_tasks),
        "autonomous_tasks": len(autonomous),
        "manual_tasks": len(manual),
        "tasks": all_tasks,
    }
    save_json(DATA / "task_queue.json", task_queue)

    state["runs"] = state.get("runs", 0) + 1
    state["total_tasks_generated"] = state.get("total_tasks_generated", 0) + len(all_tasks)
    state["last_run"] = datetime.now(timezone.utc).isoformat()
    state["last_task_count"] = len(all_tasks)
    try: _h=json.loads((DATA/"homeostasis_state.json").read_text(encoding="utf-8"))
    except: _h={}
    try: _c=json.loads((DATA/"neural_cortex_state.json").read_text(encoding="utf-8"))
    except: _c={}
    state["nervous_system"]={"equilibrium":_h.get("equilibrium",0),"trend":_h.get("trend","unknown"),"brain_confidence":_c.get("decision_confidence",0)}
    save_json(DATA / "task_factory_state.json", state)

    print("\n  === TASK QUEUE ===")
    for t in all_tasks:
        auto_flag = "[AUTO]" if t.get("autonomous") else "[MANUAL]"
        print("  P%d %s %s: %s" % (t["priority"], auto_flag, t["type"], t["title"]))
        print("       -> %s" % t["command"])

    print("\n  === TASK FACTORY SUMMARY ===")
    print("  Tasks generated:  %d" % len(all_tasks))
    print("  Autonomous:       %d (can run now)" % len(autonomous))
    print("  Needs building:   %d" % len(manual))
    print("\n  The factory never stops. Tasks breed tasks.")


if __name__ == "__main__":
    run()

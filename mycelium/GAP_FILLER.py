#!/usr/bin/env python3
"""
GAP_FILLER.py -- Seed Missing Data Files
==========================================
Reads the wire topology to find data files that engines READ
but no engine WRITES. These are gaps -- hungry inputs with no
data source.

For each gap, this engine creates a seed file with valid JSON
structure so the reading engine doesn't crash.

This is NOT fake data. It's bootstrapping -- creating the
initial state so the engines can start producing real data.

Reads: data/live_wire_report.json, data/gap_filler_state.json
Writes: data/*.json (seeds), data/gap_filler_state.json
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


def find_gaps():
    """Find data files that are read but never written."""
    wire_report = load_json(DATA / "live_wire_report.json")
    engines = wire_report.get("engines", {})

    all_reads = {}
    all_writes = set()

    for name, info in engines.items():
        for r in info.get("reads", []):
            if r not in all_reads:
                all_reads[r] = []
            all_reads[r].append(name)
        all_writes.update(info.get("writes", []))

    gaps = {}
    for filename, readers in all_reads.items():
        if filename in all_writes:
            continue
        # Skip wildcards and non-json
        if "*" in filename or "{" in filename:
            continue
        if not filename.endswith(".json"):
            continue
        if "/" in filename:
            continue
        gaps[filename] = readers

    return gaps


def generate_seed(filename, readers):
    """Generate appropriate seed data based on filename patterns."""
    name = filename.replace(".json", "")

    # State files -- engines create these on first run
    if name.endswith("_state"):
        return {"status": "initialized", "runs": 0, "last_run": None}

    # Report files
    if name.endswith("_report"):
        return {"status": "pending", "generated_at": None, "data": {}}

    # Log files
    if name.endswith("_log"):
        return {"entries": [], "last_updated": None}

    # Queue files
    if "queue" in name:
        return {"queue": [], "last_updated": None}

    # Tracker/score files
    if "tracker" in name or "score" in name:
        return {"tracked": {}, "last_updated": None}

    # Routing/config files
    if "routing" in name or "config" in name:
        return {"routes": [], "last_updated": None}

    # Conversation/exchange files
    if "conversation" in name or "exchange" in name:
        return {"messages": [], "last_updated": None}

    # Subscribers/members files
    if "subscriber" in name or "member" in name or "inbox" in name:
        return {"subscribers": [], "count": 0, "last_updated": None}

    # Results files
    if "result" in name:
        return {"results": [], "last_updated": None}

    # Manifest/directive files
    if "manifest" in name or "directive" in name:
        return {"directives": [], "version": 1, "last_updated": None}

    # Weight/preference files
    if "weight" in name or "preference" in name:
        return {"weights": {}, "last_updated": None}

    # Memory/knowledge files
    if "memory" in name or "knowledge" in name:
        return {"entries": [], "last_updated": None}

    # Ledger files
    if "ledger" in name:
        return {"entries": [], "total": 0, "last_updated": None}

    # Alert/monitor files
    if "alert" in name or "monitor" in name:
        return {"alerts": [], "last_checked": None}

    # Revenue/income/payment files
    if "revenue" in name or "income" in name or "payment" in name:
        return {"total": 0, "transactions": [], "last_updated": None}

    # Loop/workflow files
    if "loop" in name or "workflow" in name:
        return {"status": "idle", "steps": [], "last_run": None}

    # Cooldown files
    if "cooldown" in name:
        return {"cooldowns": {}, "last_updated": None}

    # Posts/content files
    if "post" in name or "content" in name or "draft" in name:
        return {"posts": [], "count": 0, "last_updated": None}

    # Generic fallback
    return {"status": "seeded", "data": {}, "seeded_at": datetime.now(timezone.utc).isoformat(),
            "readers": readers[:5]}


def run():
    print("GAP FILLER -- Seed Missing Data Files")
    print("=" * 50)

    state = load_json(DATA / "gap_filler_state.json")
    if not state:
        state = {"runs": 0, "files_seeded": 0, "last_run": None}

    print("\n  [1/3] Finding data gaps...")
    gaps = find_gaps()
    print("    Gaps found: %d files read but never written" % len(gaps))

    print("\n  [2/3] Seeding missing files...")
    seeded = 0
    skipped = 0
    already_exist = 0

    for filename, readers in sorted(gaps.items()):
        filepath = DATA / filename

        if filepath.exists():
            already_exist += 1
            continue

        seed = generate_seed(filename, readers)
        save_json(filepath, seed)
        seeded += 1
        print("    [SEED] %s <- %s" % (filename, ", ".join(readers[:2])))

    print("\n  [3/3] Saving state...")
    state["runs"] = state.get("runs", 0) + 1
    state["files_seeded"] = state.get("files_seeded", 0) + seeded
    state["last_run"] = datetime.now(timezone.utc).isoformat()
    state["last_seeded"] = seeded
    state["last_skipped"] = skipped
    state["last_already_exist"] = already_exist
    try: _h=json.loads((DATA/"homeostasis_state.json").read_text(encoding="utf-8"))
    except: _h={}
    try: _c=json.loads((DATA/"neural_cortex_state.json").read_text(encoding="utf-8"))
    except: _c={}
    state["nervous_system"]={"equilibrium":_h.get("equilibrium",0),"trend":_h.get("trend","unknown"),"brain_confidence":_c.get("decision_confidence",0)}
    save_json(DATA / "gap_filler_state.json", state)

    print("\n  === GAP FILLER SUMMARY ===")
    print("  Gaps found:      %d" % len(gaps))
    print("  Files seeded:    %d" % seeded)
    print("  Already existed: %d" % already_exist)
    print("  Total seeded:    %d" % state["files_seeded"])
    print("\n  Every gap gets filled. Every input gets fed.")


if __name__ == "__main__":
    run()

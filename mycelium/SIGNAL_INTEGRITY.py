#!/usr/bin/env python3
"""
SIGNAL_INTEGRITY.py -- The Honest Audit
========================================
4,489 wires sounds impressive. But how many carry REAL data?

Most engines were "wired" by appending a _wire_state() stub that reads
one file and writes {"status": "wired", "last_run": "..."}. That's not
a real data flow. That's a placeholder pretending to be a connection.

This engine tells the truth:
  1. Read the full wire topology
  2. For each data file on each wire, check the ACTUAL content
  3. Classify every wire as:
     - REAL: >200 bytes, meaningful structure, multiple keys
     - THIN: 50-200 bytes, minimal but present data
     - STUB: <50 bytes or just {"status": "wired"} pattern
     - DEAD: file doesn't exist or is empty
     - STALE: file exists but hasn't been modified in >7 days
  4. Report honest wire counts
  5. Identify which engines produce REAL value vs. which are theater

The system needs to know the difference between looking connected
and actually being connected.

Reads: data/live_wire_report.json, data/*.json (all flowing data)
Writes: data/signal_integrity_report.json
Zero secrets needed.
"""
import json
import os
from pathlib import Path
from datetime import datetime, timezone, timedelta

DATA = Path("data")
DATA.mkdir(exist_ok=True)


def load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return None


def save_json(path, data):
    Path(path).write_text(
        json.dumps(data, indent=2, default=str, ensure_ascii=False),
        encoding="utf-8"
    )


STUB_PATTERNS = [
    '{"status": "wired"',
    '{"last_run"',
    '"status": "wired"',
    '"status": "active"',
    '"generated_by": "FRACTAL_GENESIS_ENGINE"',
    '"generated_by": "BRIDGE_BUILDER"',
]


def classify_data_file(filepath):
    """Classify a data file by the quality of its content."""
    full_path = DATA / filepath if not Path(filepath).is_absolute() else Path(filepath)

    if not full_path.exists():
        return "DEAD", 0, {}

    try:
        content = full_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return "DEAD", 0, {}

    size = len(content)
    if size == 0:
        return "DEAD", 0, {}

    # Check staleness
    try:
        mtime = datetime.fromtimestamp(full_path.stat().st_mtime, tz=timezone.utc)
        age_days = (datetime.now(timezone.utc) - mtime).days
    except Exception:
        age_days = 0

    # Parse as JSON
    try:
        data = json.loads(content)
    except Exception:
        # Not valid JSON -- could still be real data (txt, md)
        if size > 200:
            return "REAL", size, {"type": "non_json", "age_days": age_days}
        return "THIN", size, {"type": "non_json", "age_days": age_days}

    # Check for stub patterns
    content_lower = content[:500].lower()
    is_stub = False
    for pattern in STUB_PATTERNS:
        if pattern.lower() in content_lower:
            # Check if this is JUST a stub or a stub with real data
            if isinstance(data, dict):
                # Stubs typically have <= 3 keys
                non_meta_keys = [k for k in data.keys()
                                 if k not in ("status", "last_run", "generated_by",
                                              "purpose", "timestamp", "inputs_loaded")]
                if len(non_meta_keys) <= 1:
                    is_stub = True
                    break

    if is_stub:
        return "STUB", size, {"keys": list(data.keys()) if isinstance(data, dict) else [], "age_days": age_days}

    # Check size thresholds
    if size < 50:
        return "STUB", size, {"age_days": age_days}
    elif size < 200:
        return "THIN", size, {"age_days": age_days}

    # Stale check (> 7 days without modification)
    if age_days > 7:
        return "STALE", size, {"age_days": age_days}

    # Real data
    key_count = len(data) if isinstance(data, dict) else (len(data) if isinstance(data, list) else 1)
    return "REAL", size, {"keys": key_count, "age_days": age_days}


def audit_wires(wire_report):
    """Audit every wire for signal integrity."""
    wires = wire_report.get("wires", [])
    engines = wire_report.get("engines", {})

    # Track per-file classification (avoid re-reading the same file)
    file_cache = {}

    wire_audit = []
    for wire in wires:
        via = wire.get("via", "")
        if via not in file_cache:
            classification, size, meta = classify_data_file(via)
            file_cache[via] = (classification, size, meta)
        else:
            classification, size, meta = file_cache[via]

        wire_audit.append({
            "from": wire["from"],
            "to": wire["to"],
            "via": via,
            "classification": classification,
            "size": size,
        })

    # Aggregate
    counts = {"REAL": 0, "THIN": 0, "STUB": 0, "DEAD": 0, "STALE": 0}
    for w in wire_audit:
        c = w["classification"]
        counts[c] = counts.get(c, 0) + 1

    return wire_audit, counts, file_cache


def audit_engines(engines, file_cache):
    """Score each engine by the quality of its actual data production."""
    engine_scores = {}

    for name, info in engines.items():
        writes = info.get("writes", [])
        reads = info.get("reads", [])

        write_quality = []
        for f in writes:
            if f in file_cache:
                classification, size, meta = file_cache[f]
            else:
                classification, size, meta = classify_data_file(f)
                file_cache[f] = (classification, size, meta)
            write_quality.append(classification)

        read_quality = []
        for f in reads:
            if f in file_cache:
                classification, size, meta = file_cache[f]
            else:
                classification, size, meta = classify_data_file(f)
                file_cache[f] = (classification, size, meta)
            read_quality.append(classification)

        # Score: REAL=3, THIN=2, STALE=1, STUB=0, DEAD=0
        quality_scores = {"REAL": 3, "THIN": 2, "STALE": 1, "STUB": 0, "DEAD": 0}
        write_score = sum(quality_scores.get(q, 0) for q in write_quality)
        read_score = sum(quality_scores.get(q, 0) for q in read_quality)
        total = write_score + read_score
        max_possible = (len(writes) + len(reads)) * 3

        engine_scores[name] = {
            "total_score": total,
            "max_possible": max_possible,
            "percentage": round(total * 100 / max(max_possible, 1)),
            "writes": len(writes),
            "reads": len(reads),
            "write_quality": {q: write_quality.count(q) for q in set(write_quality)} if write_quality else {},
            "read_quality": {q: read_quality.count(q) for q in set(read_quality)} if read_quality else {},
        }

    return engine_scores


def run():
    print("SIGNAL INTEGRITY -- The Honest Audit")
    print("=" * 50)

    wire_report = load_json(DATA / "live_wire_report.json")
    if not wire_report:
        print("  No live_wire_report.json -- run LIVE_WIRE first")
        return

    stats = wire_report.get("stats", {})
    print(f"  Claimed: {stats.get('total_engines', 0)} engines, {stats.get('total_wires_discovered', 0)} wires")

    # Audit wires
    print("\n  [1/3] Auditing every wire...")
    wire_audit, counts, file_cache = audit_wires(wire_report)
    total_wires = len(wire_audit)

    print(f"    REAL:  {counts['REAL']:>5} wires ({counts['REAL']*100//max(total_wires,1)}%) -- actual data flowing")
    print(f"    THIN:  {counts['THIN']:>5} wires ({counts['THIN']*100//max(total_wires,1)}%) -- minimal but present")
    print(f"    STALE: {counts['STALE']:>5} wires ({counts['STALE']*100//max(total_wires,1)}%) -- data older than 7 days")
    print(f"    STUB:  {counts['STUB']:>5} wires ({counts['STUB']*100//max(total_wires,1)}%) -- placeholder only")
    print(f"    DEAD:  {counts['DEAD']:>5} wires ({counts['DEAD']*100//max(total_wires,1)}%) -- file missing/empty")

    honest_real = counts["REAL"] + counts["THIN"]
    honest_pct = honest_real * 100 // max(total_wires, 1)
    print(f"\n    HONEST COUNT: {honest_real}/{total_wires} wires carry real data ({honest_pct}%)")

    # Audit engines
    print("\n  [2/3] Scoring engine data quality...")
    engines = wire_report.get("engines", {})
    engine_scores = audit_engines(engines, file_cache)

    # Top real producers
    sorted_engines = sorted(engine_scores.items(), key=lambda x: -x[1]["percentage"])
    top_real = [e for e in sorted_engines if e[1]["percentage"] >= 50][:10]
    bottom = [e for e in sorted_engines if e[1]["percentage"] == 0]

    print(f"    Top real data producers:")
    for name, score in top_real[:10]:
        print(f"      [{score['percentage']:>3}%] {name} ({score['writes']}w/{score['reads']}r)")

    print(f"\n    Engines with 0% real data: {len(bottom)}")
    for name, score in bottom[:5]:
        print(f"      [  0%] {name}")
    if len(bottom) > 5:
        print(f"      ... and {len(bottom)-5} more")

    # Unique data files analysis
    print("\n  [3/3] Analyzing data file landscape...")
    file_stats = {}
    for fname, (classification, size, meta) in file_cache.items():
        file_stats[fname] = {
            "classification": classification,
            "size": size,
            "age_days": meta.get("age_days", 0),
        }

    file_counts = {}
    for f in file_stats.values():
        c = f["classification"]
        file_counts[c] = file_counts.get(c, 0) + 1

    total_files = len(file_stats)
    print(f"    Unique data files: {total_files}")
    for c in ["REAL", "THIN", "STALE", "STUB", "DEAD"]:
        n = file_counts.get(c, 0)
        print(f"      {c}: {n} ({n*100//max(total_files,1)}%)")

    # Build report
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "claimed_wires": stats.get("total_wires_discovered", 0),
        "audited_wires": total_wires,
        "wire_classifications": counts,
        "real_wires": counts["REAL"],
        "thin_wires": counts["THIN"],
        "stub_wires": counts["STUB"],
        "dead_wires": counts["DEAD"],
        "stale_wires": counts["STALE"],
        "honest_real_count": honest_real,
        "honest_percentage": honest_pct,
        "unique_data_files": total_files,
        "file_classifications": file_counts,
        "top_real_engines": [{"name": n, **s} for n, s in top_real],
        "zero_real_engines": len(bottom),
        "engine_scores_summary": {
            "total": len(engine_scores),
            "above_50pct": len([e for e in engine_scores.values() if e["percentage"] >= 50]),
            "above_0pct": len([e for e in engine_scores.values() if e["percentage"] > 0]),
            "at_0pct": len(bottom),
        },
    }
    try: _h=json.loads((DATA/"homeostasis_state.json").read_text(encoding="utf-8"))
    except: _h={}
    try: _c=json.loads((DATA/"neural_cortex_state.json").read_text(encoding="utf-8"))
    except: _c={}
    report["nervous_system"]={"equilibrium":_h.get("equilibrium",0),"trend":_h.get("trend","unknown"),"brain_confidence":_c.get("decision_confidence",0)}
    save_json(DATA / "signal_integrity_report.json", report)

    print(f"\n  === SIGNAL INTEGRITY VERDICT ===")
    print(f"  Claimed wires:  {stats.get('total_wires_discovered', 0)}")
    print(f"  Real wires:     {honest_real} ({honest_pct}%)")
    print(f"  Stub wires:     {counts['STUB']}")
    print(f"  Dead wires:     {counts['DEAD']}")
    print(f"  Unique files:   {total_files}")
    print(f"\n  The truth hurts. But it's the only thing that heals.")


if __name__ == "__main__":
    run()

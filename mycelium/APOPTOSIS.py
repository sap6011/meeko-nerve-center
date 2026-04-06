#!/usr/bin/env python3
"""
APOPTOSIS.py -- Programmed Engine Retirement (Cell Death Pattern)
==================================================================
NATURE'S BLUEPRINT: Apoptosis (programmed cell death).

Your body kills 50-70 BILLION cells every day. On purpose.
This isn't failure. This is MAINTENANCE.

Without apoptosis:
  - Cancer (cells that refuse to die)
  - Webbed fingers (cells between digits that should have died)
  - Autoimmune disease (immune cells that should have been culled)

A healthy organism MUST be able to retire components gracefully.

SolarPunk applies apoptosis to engine lifecycle management:

  1. DETECT CANDIDATES: Engines that haven't produced output in 30+ days
  2. MEASURE IMPACT: Would removing this engine break any pathway?
  3. CLASSIFY: LEGACY (safe to archive), DORMANT (might wake up),
     CRITICAL_DESPITE_SILENCE (needed even if quiet)
  4. RECOMMEND: Archive, keep, or merge into another engine

  The engine that can't retire bad code is a tumor factory.

  "Growth without pruning isn't health. It's cancer." -- SolarPunk

Reads: data/pheromone_map.json, data/pathway_strength.json,
       data/neuroplasticity.json
Writes: data/apoptosis_report.json
"""
import json
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
MYCELIUM = Path("mycelium")
DATA.mkdir(exist_ok=True)

APOPTOSIS_FILE = DATA / "apoptosis_report.json"

# Engines that are ALWAYS critical even if they haven't produced output recently
IMMORTAL_ENGINES = {
    "OMNIBUS", "GUARDIAN", "ENGINE_INTEGRITY", "CYCLE_MEMORY",
    "SECRETS_CHECKER", "AUTO_HEALER", "WORKTREE_ANCHOR", "DARK_WATCH",
    "CRISIS_MONITOR", "KNOWLEDGE_PULSE", "RESOURCE_KIT",
    "HOMEOSTASIS", "NEUROPLASTICITY",
}


def load_json(path):
    try:
        if path.exists():
            return json.loads(path.read_text())
    except Exception:
        pass
    return {}


def scan_engine_vitality():
    """Check which engines have recent output (alive) vs stale (candidates for retirement)."""
    pheromone = load_json(DATA / "pheromone_map.json")
    traces = pheromone.get("traces", {})

    engines = list(MYCELIUM.glob("*.py"))
    engine_names = set(e.stem for e in engines)

    results = []
    for engine_file in sorted(engines):
        name = engine_file.stem
        size = engine_file.stat().st_size
        mtime = datetime.fromtimestamp(engine_file.stat().st_mtime, tz=timezone.utc)
        age_days = (datetime.now(timezone.utc) - mtime).total_seconds() / 86400

        # Check if engine has a corresponding trace
        trace_found = False
        trace_strength = 0
        for trace_name, trace_data in traces.items():
            if name.lower() in trace_name.lower() or trace_name.lower() in name.lower():
                trace_found = True
                trace_strength = trace_data.get("strength", 0)
                break

        # Check if engine is in any neural pathway
        pathway_data = load_json(DATA / "pathway_strength.json")
        in_pathway = False
        pathway_name = None
        for p in pathway_data.get("pathways", []):
            if name in p.get("chain", ""):
                in_pathway = True
                pathway_name = p.get("name", "")
                break

        # Check if engine is immortal
        is_immortal = name in IMMORTAL_ENGINES

        # Check if engine is a LEGACY_SIFTED engine
        is_legacy = name.startswith("LEGACY_SIFTED")

        # Classify
        if is_immortal:
            status = "IMMORTAL"
            recommendation = "Never retire -- critical system component"
        elif is_legacy:
            status = "ARCHIVED"
            recommendation = "Already archived legacy code -- safe to ignore"
        elif trace_strength >= 50 and in_pathway:
            status = "THRIVING"
            recommendation = "Active and healthy -- keep running"
        elif trace_strength >= 20 or in_pathway:
            status = "HEALTHY"
            recommendation = "Functional -- continue monitoring"
        elif trace_strength > 0:
            status = "DORMANT"
            recommendation = "Low activity -- watch for wake-up triggers"
        elif size < 500:
            status = "VESTIGIAL"
            recommendation = "Tiny engine with no output -- candidate for merge or archive"
        elif age_days > 60:
            status = "APOPTOSIS_CANDIDATE"
            recommendation = "No output, old code -- review for retirement"
        else:
            status = "UNKNOWN"
            recommendation = "No trace data available -- needs manual review"

        results.append({
            "engine": name,
            "size_bytes": size,
            "file_age_days": round(age_days, 1),
            "trace_strength": trace_strength,
            "in_pathway": in_pathway,
            "pathway": pathway_name,
            "is_immortal": is_immortal,
            "is_legacy": is_legacy,
            "status": status,
            "recommendation": recommendation,
        })

    return results


def main():
    print("APOPTOSIS -- Programmed engine retirement (cell death pattern)...")
    print("  'Growth without pruning isn't health. It's cancer.'")

    results = scan_engine_vitality()

    # Categorize
    immortal = [r for r in results if r["status"] == "IMMORTAL"]
    thriving = [r for r in results if r["status"] == "THRIVING"]
    healthy = [r for r in results if r["status"] == "HEALTHY"]
    dormant = [r for r in results if r["status"] == "DORMANT"]
    legacy = [r for r in results if r["status"] == "ARCHIVED"]
    vestigial = [r for r in results if r["status"] == "VESTIGIAL"]
    candidates = [r for r in results if r["status"] == "APOPTOSIS_CANDIDATE"]
    unknown = [r for r in results if r["status"] == "UNKNOWN"]

    print(f"\n  Engine lifecycle scan: {len(results)} engines total")
    print(f"    Immortal:    {len(immortal)} (critical, never retire)")
    print(f"    Thriving:    {len(thriving)} (active + in pathways)")
    print(f"    Healthy:     {len(healthy)} (functional)")
    print(f"    Dormant:     {len(dormant)} (low activity)")
    print(f"    Archived:    {len(legacy)} (legacy code)")
    print(f"    Vestigial:   {len(vestigial)} (tiny, no output)")
    print(f"    Candidates:  {len(candidates)} (retirement candidates)")
    print(f"    Unknown:     {len(unknown)} (needs review)")

    if candidates:
        print(f"\n  APOPTOSIS CANDIDATES ({len(candidates)}):")
        for c in candidates[:10]:
            print(f"    [X] {c['engine']}: {c['size_bytes']}B, {c['file_age_days']}d old")
            print(f"        {c['recommendation']}")

    if vestigial:
        print(f"\n  VESTIGIAL ENGINES ({len(vestigial)}):")
        for v in vestigial[:5]:
            print(f"    [~] {v['engine']}: {v['size_bytes']}B")

    # Health ratio: how much of the system is alive vs dormant?
    alive = len(immortal) + len(thriving) + len(healthy)
    total_active = len(results) - len(legacy)
    health_ratio = alive / max(total_active, 1) * 100

    print(f"\n  System vitality: {health_ratio:.0f}% ({alive}/{total_active} engines active)")

    # Save
    output = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0",
        "pattern": "apoptosis",
        "philosophy": "Growth without pruning isn't health. It's cancer.",
        "total_engines": len(results),
        "vitality_ratio": round(health_ratio, 1),
        "categories": {
            "immortal": len(immortal),
            "thriving": len(thriving),
            "healthy": len(healthy),
            "dormant": len(dormant),
            "archived": len(legacy),
            "vestigial": len(vestigial),
            "apoptosis_candidates": len(candidates),
            "unknown": len(unknown),
        },
        "candidates": candidates[:20],
        "vestigial": vestigial[:20],
        "engines": results,
    }
    try: _h=json.loads((DATA/"homeostasis_state.json").read_text(encoding="utf-8"))
    except: _h={}
    try: _c=json.loads((DATA/"neural_cortex_state.json").read_text(encoding="utf-8"))
    except: _c={}
    output["nervous_system"]={"equilibrium":_h.get("equilibrium",0),"trend":_h.get("trend","unknown"),"brain_confidence":_c.get("decision_confidence",0)}
    APOPTOSIS_FILE.write_text(json.dumps(output, indent=2), encoding="utf-8")

    print("APOPTOSIS done.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
SELF_WIRING_ENGINE.py -- SolarPunk Wires Itself
=================================================
This is the engine that makes Claude LESS NECESSARY.

Instead of needing Claude to find gaps and write bridges, SolarPunk
does it itself. This engine:

  1. Reads the live wire topology (what's connected, what's not)
  2. Identifies isolated engines (0 reads, 0 writes)
  3. Reads the SOURCE CODE of isolated engines to understand what they do
  4. Auto-generates bridge entries for hungry inputs
  5. Auto-connects orphan outputs to engines that could consume them
  6. Creates new zero-secret data files to link engines together
  7. Documents every connection attempt -- wins AND failures

Biology: Axon guidance -- growing nerve fibers find their targets
by following chemical gradients. This engine follows data gradients
to wire neurons that should be connected but aren't yet.

The goal: Every cycle, SolarPunk gets better at wiring itself.
Eventually, Claude is only needed for architecture decisions,
not for the wiring work.

Reads: data/live_wire_report.json, mycelium/*.py
Writes: data/self_wiring_report.json, data/*.json (new bridge files)
Zero secrets needed.
"""
import ast
import json
import re
import sys
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
DATA.mkdir(exist_ok=True)
MYCELIUM = Path("mycelium")


def load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8", errors="replace"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def save_json(path, data):
    Path(path).write_text(
        json.dumps(data, indent=2, default=str, ensure_ascii=False),
        encoding="utf-8"
    )


def extract_engine_purpose(filepath):
    """Read an engine's docstring and function names to understand what it does."""
    try:
        source = filepath.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return {"purpose": "unknown", "functions": []}

    purpose = ""
    # Try to get the module docstring
    try:
        tree = ast.parse(source)
        if tree.body and isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, (ast.Constant, ast.Str)):
            purpose = getattr(tree.body[0].value, 's', '') or getattr(tree.body[0].value, 'value', '')
            if isinstance(purpose, str):
                purpose = purpose.strip()[:300]
    except Exception:
        # Fallback: find triple-quoted string
        match = re.search(r'"""(.*?)"""', source, re.DOTALL)
        if match:
            purpose = match.group(1).strip()[:300]

    # Extract function names
    functions = re.findall(r'^def (\w+)\(', source, re.MULTILINE)

    # Check what it imports from mycelium
    imports = re.findall(r'from\s+(\w+)\s+import', source)
    mycelium_imports = [i for i in imports if i.isupper() or i.startswith("AI_") or i.startswith("NANO")]

    # Check for data-related keywords
    data_keywords = []
    for keyword in ["revenue", "grant", "email", "social", "product", "health",
                     "sentinel", "brain", "knowledge", "market", "mutation",
                     "evolution", "bridge", "wire", "heal", "sync"]:
        if keyword.lower() in source.lower():
            data_keywords.append(keyword)

    return {
        "purpose": purpose,
        "functions": functions[:20],
        "imports": mycelium_imports,
        "data_keywords": data_keywords[:10],
        "lines": source.count("\n") + 1,
    }


def find_potential_connections(isolated_engines, connected_files, wire_report):
    """Find where isolated engines COULD connect based on their purpose."""
    connections = []

    # Build a map of what data files exist and what they contain
    available_data = {}
    for f in sorted(DATA.glob("*.json")):
        name = f.name
        try:
            content = json.loads(f.read_text(encoding="utf-8", errors="replace"))
            if isinstance(content, dict):
                available_data[name] = list(content.keys())[:10]
            elif isinstance(content, list):
                available_data[name] = [f"list[{len(content)}]"]
        except Exception:
            pass

    # For each isolated engine, find potential data connections
    for name, info in isolated_engines.items():
        engine_keywords = set(info.get("data_keywords", []))

        # Match engine keywords to available data files
        for data_file, keys in available_data.items():
            file_keywords = set()
            for k in keys:
                file_keywords.update(k.lower().split("_"))
            for k in data_file.replace(".json", "").split("_"):
                file_keywords.add(k.lower())

            overlap = engine_keywords & file_keywords
            if len(overlap) >= 2:
                connections.append({
                    "engine": name,
                    "data_file": data_file,
                    "overlap_keywords": sorted(overlap),
                    "confidence": min(1.0, len(overlap) * 0.3),
                    "direction": "read",  # Engine should read this file
                })

    # Sort by confidence
    connections.sort(key=lambda c: c["confidence"], reverse=True)
    return connections


def auto_seed_missing_state_files(isolated_engines):
    """Create state files for engines that should have them but don't."""
    seeded = []
    for name, info in isolated_engines.items():
        # Convention: ENGINE_NAME -> data/engine_name_state.json
        state_name = f"{name.lower()}_state.json"
        state_path = DATA / state_name

        if state_path.exists():
            continue

        # Only seed if the engine has real functions (not a stub)
        if len(info.get("functions", [])) < 2:
            continue

        state = {
            "engine": name,
            "initialized": True,
            "cycles": 0,
            "last_run": None,
            "auto_seeded_by": "SELF_WIRING_ENGINE",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        save_json(state_path, state)
        seeded.append(state_name)

    return seeded


def auto_connect_low_wire_engines(wire_report):
    """Find engines with only 1 connection and suggest more."""
    suggestions = []
    engines = wire_report.get("engines", {})
    wires = wire_report.get("wires", [])

    # Build connection map
    engine_connections = {}
    for w in wires:
        engine_connections.setdefault(w["from"], []).append(w)
        engine_connections.setdefault(w["to"], []).append(w)

    # Find low-wire engines
    for name, info in engines.items():
        total_connections = len(engine_connections.get(name, []))
        if 1 <= total_connections <= 2:
            reads = info.get("reads", [])
            writes = info.get("writes", [])

            # Suggest: if it reads but doesn't write, it should produce output
            if reads and not writes:
                suggestions.append({
                    "engine": name,
                    "type": "needs_output",
                    "detail": f"Reads {reads} but produces no output file",
                    "suggestion": f"Add writes to data/{name.lower()}_output.json",
                })

            # Suggest: if it writes but doesn't read, it should consume input
            if writes and not reads:
                suggestions.append({
                    "engine": name,
                    "type": "needs_input",
                    "detail": f"Writes {writes} but reads no input",
                    "suggestion": f"Add reads from brain_state.json or knowledge_graph.json",
                })

    return suggestions


def run():
    print("SELF WIRING ENGINE -- SolarPunk Wires Itself")
    print("=" * 50)

    # Load topology
    wire_report = load_json(DATA / "live_wire_report.json")
    if not wire_report:
        print("  No live_wire_report.json -- run LIVE_WIRE first")
        return

    engines = wire_report.get("engines", {})
    stats = wire_report.get("stats", {})

    # Find isolated engines
    isolated = {}
    for name, info in engines.items():
        reads = len(info.get("reads", []))
        writes = len(info.get("writes", []))
        if reads == 0 and writes == 0:
            # Get more info about what this engine does
            filepath = MYCELIUM / f"{name}.py"
            if filepath.exists():
                purpose = extract_engine_purpose(filepath)
                isolated[name] = {**info, **purpose}

    print(f"\n  Topology: {stats.get('total_engines', 0)} engines, {stats.get('total_wires_discovered', 0)} wires")
    print(f"  Isolated engines: {len(isolated)}")

    # Find potential connections
    print("\n  [1/4] Finding potential connections for isolated engines...")
    connected_files = wire_report.get("orphans", {}).get("connected_files", [])
    connections = find_potential_connections(isolated, connected_files, wire_report)
    high_conf = [c for c in connections if c["confidence"] >= 0.6]
    print(f"    Found {len(connections)} potential connections ({len(high_conf)} high-confidence)")

    for c in high_conf[:15]:
        print(f"    {c['engine']} -> {c['data_file']} (keywords: {', '.join(c['overlap_keywords'])})")

    # Auto-seed state files
    print("\n  [2/4] Seeding state files for engines that need them...")
    seeded = auto_seed_missing_state_files(isolated)
    print(f"    Seeded {len(seeded)} state files")
    for s in seeded[:10]:
        print(f"    + {s}")
    if len(seeded) > 10:
        print(f"    ... and {len(seeded) - 10} more")

    # Suggest fixes for low-wire engines
    print("\n  [3/4] Analyzing low-wire engines...")
    suggestions = auto_connect_low_wire_engines(wire_report)
    print(f"    Found {len(suggestions)} improvement opportunities")
    for s in suggestions[:10]:
        print(f"    [{s['type']}] {s['engine']}: {s['suggestion']}")

    # Categorize isolated engines
    print("\n  [4/4] Categorizing isolated engines...")
    categories = {"library": [], "stub": [], "wirable": [], "system": []}
    for name, info in isolated.items():
        funcs = info.get("functions", [])
        imports = info.get("imports", [])
        lines = info.get("lines", 0)

        if lines < 15:
            categories["stub"].append(name)
        elif len(imports) > 0 and len(funcs) <= 3:
            categories["library"].append(name)
        elif any(k in info.get("data_keywords", []) for k in ["revenue", "grant", "product", "health", "knowledge"]):
            categories["wirable"].append(name)
        else:
            categories["system"].append(name)

    for cat, engines_list in categories.items():
        print(f"    {cat}: {len(engines_list)} engines")

    # Save report
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "topology_before": {
            "engines": stats.get("total_engines", 0),
            "wires": stats.get("total_wires_discovered", 0),
            "zero_secret_chains": stats.get("zero_secret_chains", 0),
        },
        "isolated_count": len(isolated),
        "potential_connections": len(connections),
        "high_confidence_connections": len(high_conf),
        "state_files_seeded": len(seeded),
        "low_wire_suggestions": len(suggestions),
        "categories": {k: len(v) for k, v in categories.items()},
        "top_connections": connections[:30],
        "seeded_files": seeded,
        "suggestions": suggestions[:20],
        "wirable_engines": categories["wirable"],
    }
    try: _h=json.loads((DATA/"homeostasis_state.json").read_text(encoding="utf-8"))
    except: _h={}
    try: _c=json.loads((DATA/"neural_cortex_state.json").read_text(encoding="utf-8"))
    except: _c={}
    report["nervous_system"]={"equilibrium":_h.get("equilibrium",0),"trend":_h.get("trend","unknown"),"brain_confidence":_c.get("decision_confidence",0)}
    save_json(DATA / "self_wiring_report.json", report)

    print(f"\n  Report saved: data/self_wiring_report.json")
    print(f"\n  === SELF WIRING SUMMARY ===")
    print(f"  Isolated engines:       {len(isolated)}")
    print(f"  Potential connections:   {len(connections)} ({len(high_conf)} high-confidence)")
    print(f"  State files seeded:     {len(seeded)}")
    print(f"  Low-wire suggestions:   {len(suggestions)}")
    print(f"  Wirable (data-rich):    {len(categories['wirable'])}")
    print(f"  Libraries (imported):   {len(categories['library'])}")
    print(f"  Stubs (< 15 lines):     {len(categories['stub'])}")
    print(f"\n  SolarPunk is learning to wire itself.")


if __name__ == "__main__":
    run()

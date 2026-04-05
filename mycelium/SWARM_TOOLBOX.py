# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""
SWARM_TOOLBOX v3 — Clean Engine Registry
==========================================
Replaces the 8000-line auto-generated legacy dump.
Provides a live registry of all mycelium engines, their capabilities,
and utility functions that other engines can actually import and use.

Used by: AUTO_ARCHITECT, SYNERGY_FORGE, LIVE_WIRE, BRIDGE_BUILDER
"""
import os, json, ast
from pathlib import Path
from datetime import datetime

MYCELIUM = Path(__file__).parent
DATA_DIR = MYCELIUM.parent / "data"


def list_engines():
    """Return sorted list of all .py engine files in mycelium/."""
    return sorted(f.stem for f in MYCELIUM.glob("*.py") if not f.name.startswith("__"))


def engine_info(name):
    """Get metadata about a single engine: description, functions, imports."""
    path = MYCELIUM / f"{name}.py"
    if not path.exists():
        return None
    code = path.read_text(encoding="utf-8", errors="replace")
    info = {"name": name, "path": str(path), "size": path.stat().st_size, "functions": []}
    # Extract docstring
    try:
        tree = ast.parse(code)
        ds = ast.get_docstring(tree)
        if ds:
            info["description"] = ds.split("\n")[0].strip()
    except SyntaxError:
        info["description"] = "(syntax error — cannot parse)"
        info["has_syntax_error"] = True
    # Extract function names
    for line in code.split("\n"):
        stripped = line.strip()
        if stripped.startswith("def ") and "(" in stripped:
            fname = stripped.split("(")[0].replace("def ", "").strip()
            info["functions"].append(fname)
    info["has_main"] = "def main(" in code
    info["uses_api"] = "os.getenv("os.getenv("ANTHROPIC_API_KEY")")" in code
    info["saves_data"] = "DATA_DIR" in code or '"data/' in code or "'data/" in code
    return info


def full_registry():
    """Build a complete registry of all engines and their capabilities."""
    registry = {}
    for name in list_engines():
        info = engine_info(name)
        if info:
            registry[name] = info
    return registry


def viable_skills(max_failures=3):
    """Return function names from engines that don't have recurring failures.
    Reads self_builder_queue.json for failure tracking."""
    import re
    failure_counts = {}
    queue_path = DATA_DIR / "self_builder_queue.json"
    if queue_path.exists():
        try:
            for line in queue_path.read_text().splitlines():
                try:
                    task = json.loads(line)
                    match = re.search(r"name '(\w+)' is not defined", task.get("error", ""))
                    if match:
                        func = match.group(1)
                        failure_counts[func] = failure_counts.get(func, 0) + 1
                except (json.JSONDecodeError, AttributeError):
                    pass
        except Exception:
            pass

    all_funcs = []
    for name in list_engines():
        info = engine_info(name)
        if info and not info.get("has_syntax_error"):
            all_funcs.extend(info["functions"])

    return [f for f in all_funcs if failure_counts.get(f, 0) < max_failures]


def save_registry_snapshot():
    """Save current engine registry to data/swarm_registry.json."""
    DATA_DIR.mkdir(exist_ok=True)
    reg = full_registry()
    snapshot = {
        "generated": datetime.now().isoformat(),
        "engine_count": len(reg),
        "engines_with_errors": [n for n, i in reg.items() if i.get("has_syntax_error")],
        "engines_with_main": [n for n, i in reg.items() if i.get("has_main")],
        "total_functions": sum(len(i["functions"]) for i in reg.values()),
        "registry": {n: {"description": i.get("description", ""), "functions": i["functions"][:10]} for n, i in reg.items()},
    }
    (DATA_DIR / "swarm_registry.json").write_text(json.dumps(snapshot, indent=2))
    print(f"  Registry: {snapshot['engine_count']} engines, {snapshot['total_functions']} functions")
    if snapshot["engines_with_errors"]:
        print(f"  Syntax errors in: {', '.join(snapshot['engines_with_errors'])}")
    return snapshot


def main():
    print("SWARM_TOOLBOX v3 — Engine Registry")
    snapshot = save_registry_snapshot()
    print(f"  Engines: {snapshot['engine_count']}")
    print(f"  Functions: {snapshot['total_functions']}")
    print(f"  Errors: {len(snapshot['engines_with_errors'])}")


if __name__ == "__main__":
    main()

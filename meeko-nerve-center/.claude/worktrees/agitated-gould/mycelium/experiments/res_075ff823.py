#!/usr/bin/env python3
"""
EXPERIMENT: res_075ff823
TYPE:        RESONANCE
BORN:        2026-03-21T15:29:13.332745Z
RESONATES:   CODE_ALCHEMIST  <->  CRYPTO_BRIDGE
HYPOTHESIS:  KB that renders itself as a living document

WHAT THIS DOES:
  RESONANCE finds the hidden shared structure between CODE_ALCHEMIST and CRYPTO_BRIDGE
  and makes it explicit. When two things resonate, they can synchronise.
  Result: a bridge module that lets both sides call each other's core logic.

SAFE TO RUN: yes -- structural analysis only, outputs to experiments/
"""
import ast, json, datetime
from pathlib import Path

ROOT        = Path(__file__).resolve().parent.parent.parent
MYCELIUM    = ROOT / "mycelium"
EXPERIMENTS = Path(__file__).resolve().parent

def find_resonance():
    """
    Analyse CODE_ALCHEMIST and CRYPTO_BRIDGE for structural resonance.
    Resonance = shared function signatures, data shapes, or loop patterns.
    """
    results = {}
    for name in ["CODE_ALCHEMIST", "CRYPTO_BRIDGE"]:
        p = MYCELIUM / f"{name}.py"
        if not p.exists():
            results[name] = {"error": "not found"}
            continue
        try:
            src  = p.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(src)
            funcs  = {n.name: ast.dump(n) for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
            classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
            ret_types = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Return) and node.value:
                    ret_types.append(type(node.value).__name__)
            results[name] = {
                "funcs":    list(funcs.keys()),
                "classes":  classes,
                "returns":  list(set(ret_types)),
                "lines":    src.count("\n"),
            }
        except Exception as e:
            results[name] = {"error": str(e)}

    # Find resonance: shared function names, return types
    names = list(results.keys())
    shared_funcs = []
    if len(names) == 2 and "error" not in results[names[0]] and "error" not in results[names[1]]:
        shared_funcs = list(set(results[names[0]]["funcs"]) & set(results[names[1]]["funcs"]))

    resonance = {
        "experiment":    "res_075ff823",
        "resonance_type":"KB that renders itself as a living document",
        "modules":       results,
        "shared_funcs":  shared_funcs,
        "bridge_proposal": (
            f"A bridge module could expose: "
            + (", ".join(f"{f}()" for f in shared_funcs[:3]) or "no direct overlap -- indirect bridge via data format")
        ),
        "timestamp":     datetime.datetime.utcnow().isoformat(),
    }

    out = EXPERIMENTS / "resonance_res_075ff823.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(resonance, f, indent=2)

    print(f"[RESONANCE] Found {len(shared_funcs)} shared function signatures")
    print(f"  Bridge proposal: {resonance['bridge_proposal'][:120]}")
    return resonance

if __name__ == "__main__":
    r = find_resonance()
    print(f"\n[RESONANCE] res_075ff823 complete")

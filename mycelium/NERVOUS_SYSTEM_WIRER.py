#!/usr/bin/env python3
"""
NERVOUS_SYSTEM_WIRER.py -- Autonomous Nervous System Integrator
================================================================
The engine that wires all other engines into the shared nervous system
so Claude doesn't have to do it manually one-by-one.

Biology: Like stem cells differentiating and connecting to the nervous
system automatically, this engine scans every engine in mycelium/,
detects if it saves state to JSON, and injects the nervous system
read pattern so every engine pulse carries equilibrium + brain data.

What it does:
  1. Scans all .py files in mycelium/
  2. Skips files that already contain "nervous_system"
  3. Identifies save patterns (write_text, save_json, _save, save())
  4. Injects homeostasis + neural_cortex read before the save
  5. Syntax-checks every modification
  6. Rolls back if syntax breaks
  7. Reports everything to data/nervous_system_wirer_report.json

What it does NOT do:
  - Delete files (never destructive)
  - Change logic (only adds nervous_system awareness)
  - Require API keys (zero secrets)
  - Touch files it already wired

Safety:
  - Always checks syntax BEFORE and AFTER modification
  - Creates backup of original code in memory
  - Rolls back any file that fails syntax check after edit
  - Reports failures for manual review

Reports to: data/nervous_system_wirer_report.json
Emits to: SYNAPTIC_BUS
"""
import json
import os
import py_compile
import re
import sys
import textwrap
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
DATA.mkdir(exist_ok=True)
MYCELIUM = Path("mycelium")


def load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return {}


def check_syntax(filepath):
    """Check if a Python file compiles cleanly."""
    try:
        py_compile.compile(str(filepath), doraise=True)
        return True, None
    except py_compile.PyCompileError as e:
        return False, str(e)


def already_wired(code):
    """Check if file already has nervous_system integration."""
    return "nervous_system" in code


def find_save_patterns(code, lines):
    """
    Find state-saving patterns in the code.
    Returns list of (line_number, indent, pattern_type, dict_var) tuples.

    Detects:
      - write_text(json.dumps(DICT, ...))
      - save_json(PATH, DICT)
      - _save(PATH, DICT)
      - save(DICT)  / save_state(DICT)
    """
    saves = []

    for i, line in enumerate(lines):
        stripped = line.lstrip()
        indent = line[:len(line) - len(stripped)]

        # Pattern 1: (PATH).write_text(json.dumps(VAR, ...))
        m = re.search(r'\.write_text\(json\.dumps\((\w+)', stripped)
        if m and "nervous_system" not in stripped:
            var = m.group(1)
            # Skip if it's writing a list or non-dict
            if var not in ("True", "False", "None"):
                saves.append((i, indent, "write_text", var))
                continue

        # Pattern 2: save_json(PATH, VAR)
        m = re.search(r'save_json\(\s*\S+\s*,\s*(\w+)\s*\)', stripped)
        if m:
            saves.append((i, indent, "save_json", m.group(1)))
            continue

        # Pattern 3: _save(PATH, VAR) or _save("fname", VAR)
        m = re.search(r'_save\(\s*(?:DATA\s*/\s*)?["\']?\S+["\']?\s*,\s*(\w+)\s*\)', stripped)
        if m:
            saves.append((i, indent, "_save", m.group(1)))
            continue

        # Pattern 4: save(VAR) — wrapper function calls
        m = re.match(r'save\((\w+)\)', stripped)
        if m:
            saves.append((i, indent, "save_call", m.group(1)))
            continue

        # Pattern 5: save_state(VAR)
        m = re.match(r'save_state\((\w+)\)', stripped)
        if m:
            saves.append((i, indent, "save_state_call", m.group(1)))
            continue

        # Pattern 6: json.dump(VAR, f...) inside with-open context
        m = re.search(r'json\.dump\((\w+)\s*,\s*\w+', stripped)
        if m and "nervous_system" not in stripped and "json.dumps" not in stripped:
            var = m.group(1)
            if var not in ("True", "False", "None"):
                saves.append((i, indent, "json_dump", var))
                continue

        # Pattern 7: .write_text(json.dumps({...inline dict...}))
        # Matches write_text(json.dumps({ with an inline dict literal
        if re.search(r'\.write_text\(json\.dumps\(\{', stripped) and "nervous_system" not in stripped:
            saves.append((i, indent, "inline_dict", None))
            continue

    return saves


def find_wrapper_save_functions(code, lines):
    """
    Find wrapper save function DEFINITIONS like:
      def save(s):
          (DATA / "foo.json").write_text(...)

    Returns list of (func_line, body_start, indent, func_name, param_name)
    """
    wrappers = []

    for i, line in enumerate(lines):
        stripped = line.lstrip()

        # Match: def save(s):  or  def save_state(s):  or  def save_tracker(state):
        m = re.match(r'def (save\w*)\((\w+)\)\s*:', stripped)
        if m:
            fname = m.group(1)
            param = m.group(2)
            # Check if the body contains a write_text call (confirms it's a state saver)
            # Look at next 10 lines for write_text
            body = "\n".join(lines[i+1:i+12])
            if "write_text" in body and "json.dumps" in body:
                # Find the write_text line in the body
                for j in range(i+1, min(i+12, len(lines))):
                    if "write_text" in lines[j] and "json.dumps" in lines[j]:
                        body_indent = lines[j][:len(lines[j]) - len(lines[j].lstrip())]
                        wrappers.append((i, j, body_indent, fname, param))
                        break

    return wrappers


def build_injection(indent, dict_var):
    """Build the nervous system injection code block."""
    return (
        f'{indent}try: _h=json.loads((DATA/"homeostasis_state.json").read_text(encoding="utf-8"))\n'
        f'{indent}except: _h={{}}\n'
        f'{indent}try: _c=json.loads((DATA/"neural_cortex_state.json").read_text(encoding="utf-8"))\n'
        f'{indent}except: _c={{}}\n'
        f'{indent}{dict_var}["nervous_system"]={{"equilibrium":_h.get("equilibrium",0),"trend":_h.get("trend","unknown"),"brain_confidence":_c.get("decision_confidence",0)}}\n'
    )


def build_reads_only(indent):
    """Build just the nervous system reads (for inline dict injection)."""
    return (
        f'{indent}try: _h=json.loads((DATA/"homeostasis_state.json").read_text(encoding="utf-8"))\n'
        f'{indent}except: _h={{}}\n'
        f'{indent}try: _c=json.loads((DATA/"neural_cortex_state.json").read_text(encoding="utf-8"))\n'
        f'{indent}except: _c={{}}\n'
    )


NS_INLINE = '"nervous_system":{"equilibrium":_h.get("equilibrium",0),"trend":_h.get("trend","unknown"),"brain_confidence":_c.get("decision_confidence",0)}'


def inject_inline_dict(line):
    """
    Inject nervous_system key into an inline dict literal on a write_text line.
    Finds the last '}' before ', indent=' or '})' and inserts the NS key.
    """
    # Find the closing brace of the dict literal (before indent= or before ))
    # Pattern: ...{"key": "val"}, indent=2)
    m = re.search(r'(\},\s*indent\s*=)', line)
    if m:
        pos = m.start()
        return line[:pos] + ',' + NS_INLINE + line[pos:]

    # Pattern: ...{"key": "val"}))  or  ...{"key": "val"})
    m = re.search(r'(\}\s*\)\s*,?\s*encoding)', line)
    if m:
        pos = m.start()
        return line[:pos] + ',' + NS_INLINE + line[pos:]

    # Pattern: ...{"key": "val"}), encoding=...)
    m = re.search(r'(\}\s*\))', line)
    if m:
        pos = m.start()
        return line[:pos] + ',' + NS_INLINE + line[pos:]

    return None  # Can't find insertion point


def wire_engine(filepath):
    """
    Attempt to wire a single engine into the nervous system.
    Returns (success: bool, method: str, detail: str)
    """
    code = filepath.read_text(encoding="utf-8", errors="replace")

    # Skip if already wired
    if already_wired(code):
        return False, "skip", "already wired"

    # Skip if no json import (can't save state)
    if "import json" not in code and "from json" not in code:
        return False, "skip", "no json usage"

    # Check syntax before modifying
    ok, err = check_syntax(filepath)
    if not ok:
        return False, "skip", f"pre-existing syntax error: {err[:80]}"

    lines = code.split("\n")
    backup = code  # Keep backup for rollback

    # Strategy 1: Find wrapper save function definitions and inject there
    wrappers = find_wrapper_save_functions(code, lines)
    if wrappers:
        # Pick the first (most common pattern)
        func_line, write_line, indent, fname, param = wrappers[0]
        injection = build_injection(indent, param)
        # Insert before the write_text line
        lines.insert(write_line, injection.rstrip("\n"))
        new_code = "\n".join(lines)
        filepath.write_text(new_code, encoding="utf-8")
        ok, err = check_syntax(filepath)
        if ok:
            return True, f"wrapper:{fname}", f"injected before write_text in {fname}()"
        else:
            # Rollback
            filepath.write_text(backup, encoding="utf-8")
            return False, "rollback", f"syntax error after wrapper inject: {err[:80]}"

    # Strategy 2: Find save calls in run() and inject before them
    saves = find_save_patterns(code, lines)
    if saves:
        # Separate inline_dict patterns from variable-based patterns
        var_saves = [(ln, ind, pat, dv) for ln, ind, pat, dv in saves if pat != "inline_dict"]
        inline_saves = [(ln, ind, pat, dv) for ln, ind, pat, dv in saves if pat == "inline_dict"]

        # Try variable-based save first (cleaner injection)
        if var_saves:
            line_num, indent, pattern, dict_var = var_saves[-1]
            injection = build_injection(indent, dict_var)
            lines.insert(line_num, injection.rstrip("\n"))
            new_code = "\n".join(lines)
            filepath.write_text(new_code, encoding="utf-8")
            ok, err = check_syntax(filepath)
            if ok:
                return True, f"inline:{pattern}", f"injected before {pattern} call at line {line_num+1}"
            else:
                filepath.write_text(backup, encoding="utf-8")
                lines = backup.split("\n")

        # Strategy 3: Inline dict injection — modify the write_text line itself
        if inline_saves:
            line_num, indent, pattern, _ = inline_saves[-1]
            reads = build_reads_only(indent)
            modified_line = inject_inline_dict(lines[line_num])
            if modified_line:
                lines[line_num] = modified_line
                lines.insert(line_num, reads.rstrip("\n"))
                new_code = "\n".join(lines)
                filepath.write_text(new_code, encoding="utf-8")
                ok, err = check_syntax(filepath)
                if ok:
                    return True, "inline_dict", f"injected NS key into inline dict at line {line_num+1}"
                else:
                    filepath.write_text(backup, encoding="utf-8")
                    lines = backup.split("\n")

        # Strategy 3b: json.dump(var, f) — inject before it
        json_dump_saves = [(ln, ind, pat, dv) for ln, ind, pat, dv in saves if pat == "json_dump"]
        if json_dump_saves:
            line_num, indent, pattern, dict_var = json_dump_saves[-1]
            injection = build_injection(indent, dict_var)
            lines.insert(line_num, injection.rstrip("\n"))
            new_code = "\n".join(lines)
            filepath.write_text(new_code, encoding="utf-8")
            ok, err = check_syntax(filepath)
            if ok:
                return True, f"json_dump", f"injected before json.dump({dict_var}) at line {line_num+1}"
            else:
                filepath.write_text(backup, encoding="utf-8")
                return False, "rollback", f"syntax error after json_dump inject: {err[:80]}"

    return False, "skip", "no save pattern detected"


def run():
    print("=" * 70)
    print("  NERVOUS_SYSTEM_WIRER -- Autonomous Nervous System Integrator")
    print("=" * 70)
    ts = datetime.now(timezone.utc).isoformat()

    # Scan all engines
    engine_files = sorted(MYCELIUM.glob("*.py"))
    print(f"\n  Scanning {len(engine_files)} engine files...")

    results = {
        "wired": [],
        "skipped": [],
        "failed": [],
        "rolled_back": [],
    }

    for fp in engine_files:
        name = fp.stem
        # Skip ourselves to prevent infinite recursion
        if name == "NERVOUS_SYSTEM_WIRER":
            continue
        # Skip __init__ and __pycache__
        if name.startswith("__"):
            continue

        success, method, detail = wire_engine(fp)

        entry = {"engine": name, "method": method, "detail": detail}

        if success:
            results["wired"].append(entry)
            print(f"  [OK] {name}: {detail}")
        elif method == "rollback":
            results["rolled_back"].append(entry)
            print(f"  [!!] {name}: ROLLED BACK - {detail}")
        elif method == "skip" and "already wired" in detail:
            results["skipped"].append(entry)
        else:
            results["failed"].append(entry)

    # Summary
    wired_count = len(results["wired"])
    skip_count = len(results["skipped"])
    fail_count = len(results["failed"])
    rollback_count = len(results["rolled_back"])

    print(f"\n  === NERVOUS SYSTEM WIRER REPORT ===")
    print(f"  Total engines:     {len(engine_files)}")
    print(f"  Already wired:     {skip_count}")
    print(f"  Newly wired:       {wired_count}")
    print(f"  Failed/no pattern: {fail_count}")
    print(f"  Rolled back:       {rollback_count}")
    print(f"  Coverage:          {skip_count + wired_count}/{len(engine_files)} ({round((skip_count + wired_count) / max(len(engine_files), 1) * 100)}%)")

    # Read nervous system for meta-awareness
    try: _h = json.loads((DATA / "homeostasis_state.json").read_text(encoding="utf-8"))
    except: _h = {}
    try: _c = json.loads((DATA / "neural_cortex_state.json").read_text(encoding="utf-8"))
    except: _c = {}

    report = {
        "timestamp": ts,
        "engine": "NERVOUS_SYSTEM_WIRER",
        "total_scanned": len(engine_files),
        "newly_wired": wired_count,
        "already_wired": skip_count,
        "failed": fail_count,
        "rolled_back": rollback_count,
        "coverage_pct": round((skip_count + wired_count) / max(len(engine_files), 1) * 100),
        "results": results,
        "nervous_system": {
            "equilibrium": _h.get("equilibrium", 0),
            "trend": _h.get("trend", "unknown"),
            "brain_confidence": _c.get("decision_confidence", 0),
        },
    }

    (DATA / "nervous_system_wirer_report.json").write_text(
        json.dumps(report, indent=2, default=str), encoding="utf-8"
    )
    print(f"\n  Report: data/nervous_system_wirer_report.json")

    # Emit to SYNAPTIC_BUS
    try:
        sys.path.insert(0, str(MYCELIUM))
        from SYNAPTIC_BUS import emit_batch
        emit_batch("NERVOUS_SYSTEM_WIRER", {
            "newly_wired": wired_count,
            "coverage_pct": report["coverage_pct"],
            "total_engines": len(engine_files),
            "equilibrium": _h.get("equilibrium", 0),
        })
        print("  Emitted to SYNAPTIC_BUS")
    except Exception:
        pass

    return report


if __name__ == "__main__":
    run()

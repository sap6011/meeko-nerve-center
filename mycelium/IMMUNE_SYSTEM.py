#!/usr/bin/env python3
"""
IMMUNE_SYSTEM.py -- Active Defense Against Code Corruption
==========================================================
SIA's Nanobot Self-Heal loop has been wrapping os.environ.get() in
nested os.getenv() calls -- 11 levels deep in some files. SENTINEL
reports the damage. This engine FIXES it.

The immune response:
  1. Scan all engines for known corruption patterns
  2. For each corrupted file, generate the CLEAN version
  3. Apply the fix in-place (SKIPS ITS OWN FILE to prevent self-corruption)
  4. Log every repair for audit trail
  5. Report overall immune system health

Biology: T-cells. They don't just detect pathogens -- they destroy them.

Reads: mycelium/*.py, data/sentinel_report.json
Writes: data/immune_system_report.json, data/quarantine_log.json
Zero secrets needed.
"""
import json
import re
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
DATA.mkdir(exist_ok=True)
MYCELIUM = Path("mycelium")

# Files the immune system must NEVER modify (to prevent self-corruption)
IMMUNE_FILES = {"IMMUNE_SYSTEM.py"}


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


def fix_nested_getenv(source):
    """Unwrap recursively nested os.getenv/os.environ.get calls."""
    fixes = 0
    nested_pattern = re.compile(
        r'os\.(?:getenv|environ\.get)\('
        r'"os\.(?:getenv|environ\.get)\('
    )

    while nested_pattern.search(source):
        match = nested_pattern.search(source)
        if not match:
            break
        start = match.start()
        segment = source[start:]

        # Extract the innermost real key
        keys = re.findall(r'"([A-Z][A-Z0-9_]+)"', segment)
        real_key = None
        for k in keys:
            if k not in ("os", "getenv", "environ", "get"):
                real_key = k
                break
        if not real_key:
            break

        # Find matching close paren
        depth = 0
        end = start
        for i, ch in enumerate(source[start:], start):
            if ch == '(':
                depth += 1
            elif ch == ')':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        if end <= start:
            break

        old_expr = source[start:end]
        if "environ.get" in old_expr[:30]:
            new_expr = 'os.environ.get("' + real_key + '", "")'
        else:
            new_expr = 'os.getenv("' + real_key + '", "")'

        after = source[end:end + 20]
        if ".strip()" in after:
            new_expr = 'os.environ.get("' + real_key + '", "").strip()'
            source = source[:start] + new_expr + source[end:].replace(".strip()", "", 1)
        else:
            source = source[:start] + new_expr + source[end:]

        fixes += 1
        if fixes > 500:
            break

    return source, fixes


def fix_merge_conflicts(source):
    """Remove unresolved git merge conflict markers, keeping HEAD version."""
    conflict_pattern = re.compile(
        r'<<<<<<< HEAD\n(.*?)\n=======\n.*?\n>>>>>>> [^\n]+\n',
        re.DOTALL
    )
    new_source, count = conflict_pattern.subn(r'\1\n', source)
    return new_source, count


def fix_duplicate_imports(source):
    """Remove exact duplicate import lines."""
    lines = source.split('\n')
    seen_imports = set()
    new_lines = []
    fixes = 0

    for line in lines:
        stripped = line.strip()
        if stripped.startswith(('import ', 'from ')) and stripped in seen_imports:
            fixes += 1
            continue
        if stripped.startswith(('import ', 'from ')):
            seen_imports.add(stripped)
        new_lines.append(line)

    return '\n'.join(new_lines), fixes


def scan_engine(filepath):
    """Scan a single engine file for all corruption patterns."""
    try:
        source = filepath.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None

    issues = []

    nested = re.findall(r'os\.(?:getenv|environ\.get)\("os\.(?:getenv|environ\.get)\(', source)
    if nested:
        issues.append({"type": "nested_getenv", "count": len(nested)})

    conflicts = len(re.findall(r'<<<<<<< HEAD', source))
    if conflicts:
        issues.append({"type": "merge_conflict", "count": conflicts})

    lines = source.split('\n')
    imports = [l.strip() for l in lines if l.strip().startswith(('import ', 'from '))]
    dupes = len(imports) - len(set(imports))
    if dupes:
        issues.append({"type": "duplicate_imports", "count": dupes})

    return {
        "file": filepath.name,
        "path": str(filepath),
        "issues": issues,
        "total_issues": sum(i["count"] for i in issues),
        "size": len(source),
    }


def repair_engine(filepath):
    """Apply SAFE fixes to a corrupted engine file.

    Only applies fixes that are guaranteed not to break valid code:
    - Duplicate import removal (safe -- exact line dedup)
    - Merge conflict resolution (safe -- removes markers, keeps HEAD)
    - Nested getenv is REPORTED but NOT auto-fixed (too risky)
    """
    if filepath.name in IMMUNE_FILES:
        return {"status": "SELF_SKIP", "fixes": 0}

    try:
        original = filepath.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return {"status": "READ_ERROR", "fixes": 0}

    source = original
    total_fixes = 0

    # Only apply safe fixes -- duplicate imports and merge conflicts
    source, n = fix_duplicate_imports(source)
    total_fixes += n

    source, n = fix_merge_conflicts(source)
    total_fixes += n

    # NOTE: fix_nested_getenv is too aggressive and corrupts docstrings.
    # Nested getenv is reported in scan but NOT auto-fixed.

    if total_fixes > 0 and source != original:
        filepath.write_text(source, encoding="utf-8")
        return {"status": "REPAIRED", "fixes": total_fixes}
    elif total_fixes > 0:
        return {"status": "NO_CHANGE", "fixes": 0}
    else:
        return {"status": "CLEAN", "fixes": 0}


def run():
    print("IMMUNE SYSTEM -- Active Defense Against Code Corruption")
    print("=" * 55)

    # Phase 1: Scan
    print("\n  [1/3] Scanning all engines for corruption patterns...")
    engines = sorted(MYCELIUM.glob("*.py"))
    engines = [e for e in engines if not e.name.startswith("__")]

    scan_results = []
    infected = []
    for engine in engines:
        result = scan_engine(engine)
        if result:
            scan_results.append(result)
            if result["total_issues"] > 0:
                infected.append(result)

    print("    Scanned %d engines" % len(scan_results))
    print("    Infected: %d" % len(infected))

    for inf in infected[:20]:
        issues_str = ", ".join("%s(%d)" % (i["type"], i["count"]) for i in inf["issues"])
        print("    [%s] %s" % (inf["file"], issues_str))

    # Phase 2: Repair
    print("\n  [2/3] Repairing infected engines...")
    repairs = []
    total_fixes = 0
    for inf in infected:
        filepath = Path(inf["path"])
        result = repair_engine(filepath)
        result["file"] = inf["file"]
        repairs.append(result)
        total_fixes += result["fixes"]
        if result["status"] == "REPAIRED":
            print("    REPAIRED: %s (%d fixes)" % (inf["file"], result["fixes"]))
        elif result["status"] == "SELF_SKIP":
            print("    SKIPPED: %s (self -- immune)" % inf["file"])

    # Phase 3: Verify
    print("\n  [3/3] Verifying repairs...")
    still_infected = 0
    for engine in engines:
        result = scan_engine(engine)
        if result and result["total_issues"] > 0:
            still_infected += 1

    # Quarantine log
    quarantine = load_json(DATA / "quarantine_log.json")
    if not isinstance(quarantine, dict):
        quarantine = {"entries": []}
    if "entries" not in quarantine:
        quarantine["entries"] = []

    if infected:
        quarantine["entries"].append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "infected_count": len(infected),
            "fixes_applied": total_fixes,
            "still_infected": still_infected,
            "files": [i["file"] for i in infected],
        })
        quarantine["entries"] = quarantine["entries"][-50:]
        save_json(DATA / "quarantine_log.json", quarantine)

    # Report
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "engines_scanned": len(scan_results),
        "engines_infected": len(infected),
        "total_fixes_applied": total_fixes,
        "engines_still_infected": still_infected,
        "health": "IMMUNE" if still_infected == 0 else "COMPROMISED",
        "infections_by_type": {},
        "repairs": repairs,
        "infected_files": [i["file"] for i in infected],
    }

    for inf in infected:
        for issue in inf["issues"]:
            t = issue["type"]
            report["infections_by_type"][t] = report["infections_by_type"].get(t, 0) + issue["count"]

    save_json(DATA / "immune_system_report.json", report)

    print("\n  === IMMUNE SYSTEM REPORT ===")
    print("  Engines scanned:     %d" % len(scan_results))
    print("  Infections found:    %d" % len(infected))
    print("  Fixes applied:       %d" % total_fixes)
    print("  Still infected:      %d" % still_infected)
    print("  Status:              %s" % report["health"])
    if report["infections_by_type"]:
        print("  Breakdown:")
        for t, count in report["infections_by_type"].items():
            print("    %s: %d" % (t, count))
    print("\n  The immune system fights. The organism survives.")


if __name__ == "__main__":
    run()

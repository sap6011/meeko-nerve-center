# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""
CORRUPTION_SENTINEL — Immune System for the Codebase
=====================================================
Scans all mycelium engines for known corruption patterns BEFORE commit.
If corruption is found, blocks the commit and reports what to fix.
Prevents SIA bot and other automated repair loops from re-introducing bugs.

Known corruption patterns:
  1. os.getenv nesting (recursive SIA corruption)
  2. Broken string context with env vars
  3. Unterminated triple-quotes (odd count)
  4. Bare os.getenv("os.getenv("os.getenv("ANTHROPIC_API_KEY")")") self-assignment
  5. PowerShell artifacts in Python files

Exit code 0 = clean, Exit code 1 = corruption found (blocks commit)
"""
import re, sys, ast
from pathlib import Path

MYCELIUM = Path(__file__).parent
DATA_DIR = MYCELIUM.parent / "data"

# Patterns that indicate known corruption
CORRUPTION_PATTERNS = [
    # os.getenv nesting — the #1 recurring bug
    (r'os\.getenv\(\s*["\']os\.getenv', "os.getenv nesting (recursive SIA corruption)"),
    # Bare os.getenv("os.getenv("ANTHROPIC_API_KEY")") self-assignment
    (r'os.getenv("os.getenv("ANTHROPIC_API_KEY")")\s*=\s*os.getenv("os.getenv("ANTHROPIC_API_KEY")")', "bare os.getenv("os.getenv("ANTHROPIC_API_KEY")") self-assignment"),
    # PowerShell in Python files
    (r'^\$[A-Z][a-zA-Z]+\s*=\s*', "PowerShell variable assignment in Python file"),
    (r'^Write-Host\s', "PowerShell Write-Host in Python file"),
    # Unterminated raise RuntimeError with env var
    (r'raise RuntimeError\(["\']os\.getenv', "RuntimeError with os.getenv string corruption"),
]


def check_file(filepath):
    """Check a single file for corruption patterns. Returns list of issues."""
    issues = []
    try:
        code = filepath.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return [f"Cannot read: {e}"]

    lines = code.split("\n")

    # Pattern-based checks
    for i, line in enumerate(lines, 1):
        for pattern, desc in CORRUPTION_PATTERNS:
            if re.search(pattern, line):
                issues.append(f"  L{i}: {desc}")
                issues.append(f"       {line.strip()[:120]}")

    # AST parse check — catches syntax errors including unbalanced quotes
    try:
        ast.parse(code)
    except SyntaxError as e:
        issues.append(f"  SyntaxError at line {e.lineno}: {e.msg}")

    return issues


def scan_all():
    """Scan all mycelium engines. Returns {filename: [issues]} for corrupted files."""
    corrupted = {}
    for f in sorted(MYCELIUM.glob("*.py")):
        if f.name == "__pycache__":
            continue
        issues = check_file(f)
        if issues:
            corrupted[f.name] = issues
    return corrupted


def main():
    print("CORRUPTION_SENTINEL — Codebase Immune System")
    corrupted = scan_all()

    # Save report
    DATA_DIR.mkdir(exist_ok=True)
    import json
    from datetime import datetime
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_engines": len(list(MYCELIUM.glob("*.py"))),
        "corrupted_count": len(corrupted),
        "clean": len(corrupted) == 0,
        "issues": corrupted,
    }
    (DATA_DIR / "sentinel_scan.json").write_text(json.dumps(report, indent=2))

    if corrupted:
        print(f"  CORRUPTION DETECTED in {len(corrupted)} file(s):")
        for fname, issues in corrupted.items():
            print(f"\n  {fname}:")
            for issue in issues:
                print(f"    {issue}")
        print(f"\n  BLOCKED — fix these before committing.")
        return 1
    else:
        print(f"  All {report['total_engines']} engines clean. No corruption detected.")
        return 0


if __name__ == "__main__":
    sys.exit(main())

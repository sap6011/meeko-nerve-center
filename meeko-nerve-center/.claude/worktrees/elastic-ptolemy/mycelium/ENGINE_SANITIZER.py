#!/usr/bin/env python3
"""
ENGINE_SANITIZER.py — SolarPunk Corruption Guard
Scans all mycelium/*.py for corruption patterns and fixes them in-place.
Run before every git commit to keep engines clean.

Known corruption patterns:
  1. Recursive env var nesting: os.environ.get(_ak, "")
  2. Stale model names
"""
import os, re
from pathlib import Path
from datetime import datetime, timezone
_ak = "ANTHROP" + "IC_API_KEY"

# Split strings prevent this file from self-corrupting when scanned
KEYS = [
    "ANTHROP" + "IC_API_KEY",
    "GROQ_API_KEY", "HF_TOKEN", "OPENROUTER_KEY",
    "GEMINI_API_KEY", "GMAIL_ADDRESS", "GMAIL_APP_PASSWORD",
    "GUMROAD_ACCESS_TOKEN", "GUMROAD_SECRET",
    "X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_SECRET",
    "REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET", "REDDIT_USERNAME", "REDDIT_PASSWORD",
    "SAMGOV_API_KEY", "GITHUB_TOKEN", "PAYPAL_CLIENT_ID", "PAYPAL_CLIENT_SECRET",
    "TELEGRAM_BOT_TOKEN", "BLUESKY_APP_PASSWORD", "MASTODON_ACCESS_TOKEN",
    "DEV_TO_API_KEY", "BLUESKY_HANDLE", "MASTODON_API_BASE_URL",
    "OCTOEVERYWHERE_APP_API_KEY", "OCTOEVERYWHERE_APP_TOKEN",
    "RENTAHUMAN_API_KEY", "SOLARPUNK_WALLET_ADDRESS",
]

# Map old stale names -> current names
# Stored as tuples to avoid self-corruption when this file is scanned
_OLD_MODELS = [
    ("claude-sonnet-4-2" + "0250514", "claude-sonnet-4-6"),
    ("claude-3-5-sonnet-2" + "0241022", "claude-sonnet-4-6"),
    ("claude-3-5-haiku-2" + "0241022", "claude-haiku-4-5-20251001"),
    ("claude-3-haiku-2" + "0240307", "claude-haiku-4-5-20251001"),
    ("claude-3-opus-2" + "0240229", "claude-opus-4-6"),
]


def _fix_line(line):
    """Fix a single line's corruption.

    SAFETY RULES:
    - ONLY fix lines that contain the nested corruption pattern: os.environ.get("os.getenv(...)...")
    - NEVER replace os.getenv("KEY") standalone — that could corrupt valid code
    - NEVER assign to a function call (os.getenv(...) = ...) — that is invalid Python
    - SKIP lines that already use the _ak split-key pattern (already safe)
    """
    # Skip lines already using the split-key pattern — they're correct
    if '_ak' in line:
        return line

    for key in KEYS:
        # Fix ONLY the deeply nested corruption: os.environ.get("os.getenv(...KEY...)", default)
        # This pattern only fires when the key appears INSIDE a nested os.getenv() string argument
        nested_pattern = r'os\.environ\.get\("os\.getenv\([^)]*' + re.escape(key) + r'[^)]*\)[^"]*"'
        if re.search(nested_pattern, line):
            line = re.sub(nested_pattern, f'os.environ.get("{key}"', line)

    return line


def sanitize_file(path: Path) -> int:
    """Fix one file. Returns number of changes made."""
    try:
        original = path.read_text(encoding="utf-8")
    except Exception:
        return 0

    lines = original.split("\n")
    fixed_lines = []
    changes = 0
    for line in lines:
        new_line = _fix_line(line)
        if new_line != line:
            changes += 1
        fixed_lines.append(new_line)

    text = "\n".join(fixed_lines)

    # Fix stale model names
    for old, new_model in _OLD_MODELS:
        if old in text:
            changes += text.count(old)
            text = text.replace(old, new_model)

    if text != original:
        path.write_text(text, encoding="utf-8")
    return changes


def main():
    myc = Path("mycelium")
    scripts = Path(".github/scripts")
    if not myc.exists():
        print("ENGINE_SANITIZER: mycelium/ not found")
        return

    files = sorted(myc.glob("*.py"))
    script_files = sorted(scripts.glob("*.py")) if scripts.exists() else []
    all_files = files + script_files

    total_files = 0
    total_changes = 0
    dirty = []

    for f in all_files:
        c = sanitize_file(f)
        if c > 0:
            dirty.append((f.name, c))
            total_files += 1
            total_changes += c

    if dirty:
        print(f"ENGINE_SANITIZER: fixed {total_changes} corruptions in {total_files} files")
        for fname, count in dirty:
            print(f"  {fname}: {count} fixes")
    else:
        print(f"ENGINE_SANITIZER: {len(all_files)} engines clean")

    # Write report for OMNIBRAIN
    Path("data").mkdir(exist_ok=True)
    report = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "engines_scanned": len(all_files),
        "engines_fixed": total_files,
        "total_fixes": total_changes,
        "fixed_files": [f for f, _ in dirty],
    }
    Path("data/sanitizer_report.json").write_text(
        __import__("json").dumps(report, indent=2)
    )


if __name__ == "__main__":
    main()
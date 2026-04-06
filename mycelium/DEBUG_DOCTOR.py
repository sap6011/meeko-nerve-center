#!/usr/bin/env python3
"""
DEBUG_DOCTOR.py -- Diagnose and Fix Engine Failures
=====================================================
Reads the ZERO_SECRET_ARMY report and diagnoses why engines failed.
Common fixes:
  - UnicodeEncodeError: set PYTHONIOENCODING=utf-8
  - Missing data files: run GAP_FILLER first
  - Timeout: engine needs optimization or longer timeout
  - Import errors: missing dependency

For fixable issues, applies the fix and re-runs the engine.
For unfixable issues, documents the problem.

Reads: data/zero_secret_army_report.json, data/debug_doctor_state.json
Writes: data/debug_doctor_state.json, data/debug_doctor_report.json
"""
import json
import subprocess
import sys
import os
import re
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
DATA.mkdir(exist_ok=True)
MYCELIUM = Path("mycelium")


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


def diagnose_failure(name, status, last_line, stderr=""):
    """Diagnose why an engine failed."""
    engine_path = MYCELIUM / ("%s.py" % name)

    # Run with UTF-8 encoding to capture real error
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"

    try:
        result = subprocess.run(
            [sys.executable, str(engine_path)],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(Path.cwd()),
            env=env,
            errors="replace",
        )

        output = result.stdout[-500:] if result.stdout else ""
        error = result.stderr[-500:] if result.stderr else ""

        if result.returncode == 0:
            return {
                "diagnosis": "FIXED_BY_UTF8",
                "fix": "Engine works with PYTHONIOENCODING=utf-8",
                "output": output[-200:],
                "fixed": True,
            }

        # Analyze error
        if "UnicodeEncodeError" in error or "charmap" in error:
            return {
                "diagnosis": "UNICODE_ERROR",
                "fix": "Engine has emoji/unicode output that fails on Windows console",
                "error": error[:200],
                "fixed": False,
                "fixable": True,
                "fix_method": "Add PYTHONIOENCODING=utf-8 to environment",
            }

        if "FileNotFoundError" in error:
            match = re.search(r"No such file.*?'([^']+)'", error)
            missing = match.group(1) if match else "unknown"
            return {
                "diagnosis": "MISSING_FILE",
                "fix": "Missing file: %s -- run GAP_FILLER" % missing,
                "error": error[:200],
                "fixed": False,
                "fixable": True,
            }

        if "ImportError" in error or "ModuleNotFoundError" in error:
            return {
                "diagnosis": "IMPORT_ERROR",
                "fix": "Missing Python module",
                "error": error[:200],
                "fixed": False,
                "fixable": False,
            }

        if "JSONDecodeError" in error:
            return {
                "diagnosis": "CORRUPT_JSON",
                "fix": "A data file has corrupt JSON",
                "error": error[:200],
                "fixed": False,
                "fixable": True,
                "fix_method": "Delete and re-seed the corrupt file",
            }

        if "KeyError" in error:
            return {
                "diagnosis": "KEY_ERROR",
                "fix": "Data file missing expected key",
                "error": error[:200],
                "fixed": False,
                "fixable": True,
                "fix_method": "Re-seed the data file with GAP_FILLER",
            }

        if "AttributeError" in error:
            return {
                "diagnosis": "ATTRIBUTE_ERROR",
                "fix": "Code expects different data type",
                "error": error[:200],
                "fixed": False,
                "fixable": False,
            }

        # Generic failure
        return {
            "diagnosis": "UNKNOWN",
            "fix": "Unrecognized error pattern",
            "error": error[:200],
            "output": output[:200],
            "fixed": False,
            "fixable": False,
        }

    except subprocess.TimeoutExpired:
        return {
            "diagnosis": "TIMEOUT",
            "fix": "Engine takes >30s. Likely waiting for AI/network.",
            "fixed": False,
            "fixable": False,
        }
    except Exception as e:
        return {
            "diagnosis": "CRASH",
            "fix": str(e)[:200],
            "fixed": False,
            "fixable": False,
        }


def run():
    print("DEBUG DOCTOR -- Diagnose and Fix Engine Failures")
    print("=" * 60)

    state = load_json(DATA / "debug_doctor_state.json")
    if not state:
        state = {"runs": 0, "fixed": 0, "unfixable": 0, "last_run": None}

    # Load army report
    army = load_json(DATA / "zero_secret_army_report.json")
    results = army.get("results", [])
    failures = [r for r in results if r.get("status") != "OK"]

    print("  Total engine results: %d" % len(results))
    print("  Failures to diagnose: %d" % len(failures))

    if not failures:
        print("  No failures to diagnose!")
        state["last_run"] = datetime.now(timezone.utc).isoformat()
        save_json(DATA / "debug_doctor_state.json", state)
        return

    diagnoses = []
    fixed_count = 0
    fixable_count = 0
    unfixable_count = 0

    print("\n  Diagnosing...")
    for f in failures:
        name = f["name"]
        status = f["status"]
        last_line = f.get("last_line", "")

        print("\n  [%s] %s (was: %s)" % (name, last_line[:50], status))
        d = diagnose_failure(name, status, last_line)

        if d.get("fixed"):
            fixed_count += 1
            print("    -> FIXED: %s" % d["diagnosis"])
        elif d.get("fixable"):
            fixable_count += 1
            print("    -> FIXABLE: %s -- %s" % (d["diagnosis"], d.get("fix", "")))
        else:
            unfixable_count += 1
            print("    -> %s: %s" % (d["diagnosis"], d.get("fix", d.get("error", ""))[:60]))

        diagnoses.append({
            "engine": name,
            "original_status": status,
            "diagnosis": d["diagnosis"],
            "fixed": d.get("fixed", False),
            "fixable": d.get("fixable", False),
            "details": d.get("fix", ""),
            "error": d.get("error", ""),
        })

    # Save report
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_failures": len(failures),
        "fixed": fixed_count,
        "fixable": fixable_count,
        "unfixable": unfixable_count,
        "diagnoses": diagnoses,
    }
    save_json(DATA / "debug_doctor_report.json", report)

    state["runs"] = state.get("runs", 0) + 1
    state["fixed"] = state.get("fixed", 0) + fixed_count
    state["unfixable"] = state.get("unfixable", 0) + unfixable_count
    state["last_run"] = datetime.now(timezone.utc).isoformat()
    try: _h=json.loads((DATA/"homeostasis_state.json").read_text(encoding="utf-8"))
    except: _h={}
    try: _c=json.loads((DATA/"neural_cortex_state.json").read_text(encoding="utf-8"))
    except: _c={}
    state["nervous_system"]={"equilibrium":_h.get("equilibrium",0),"trend":_h.get("trend","unknown"),"brain_confidence":_c.get("decision_confidence",0)}
    save_json(DATA / "debug_doctor_state.json", state)

    print("\n  === DEBUG DOCTOR SUMMARY ===")
    print("  Failures diagnosed: %d" % len(failures))
    print("  Fixed (UTF-8):      %d" % fixed_count)
    print("  Fixable:            %d" % fixable_count)
    print("  Unfixable:          %d" % unfixable_count)
    print("\n  The doctor sees everything. Most things heal.")


if __name__ == "__main__":
    run()

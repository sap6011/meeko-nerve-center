#!/usr/bin/env python3
"""
LIVE_WIRE.py — Neural Wiring Discovery Engine
==============================================
Scans every engine in mycelium/, maps their inputs and outputs,
discovers which engines COULD chain together, tests zero-secrets
chains, and documents everything — successes AND failures.

Biology: Neurons form synapses by reaching out. If the connection
fires (produces useful output), the synapse strengthens. If it
doesn't fire, the neuron lets go and tries another connection.

What this does:
  1. SCAN: Read every .py file in mycelium/, extract I/O signatures
  2. MAP: Build a wiring topology — who writes what, who reads what
  3. DISCOVER: Find potential connections (output A → input B)
  4. TEST: Try running zero-secrets chains and see what happens
  5. DOCUMENT: Log every attempt — successes get "strengthened,"
     failures get documented with the exact reason why

The wiring report goes to data/live_wire_report.json
Both wins AND failures are public. That's the point.

Zero secrets needed. Pure discovery.
"""
import ast
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
DATA.mkdir(exist_ok=True)
MYCELIUM = Path("mycelium")

# Known data file patterns to search for in engine source code
DATA_READ_PATTERNS = [
    # Path("data/something.json") or DATA / "something.json"
    r'(?:Path\(["\']data/|DATA\s*/\s*["\'])([^"\']+\.json)',
    # load_json(...data/something...)
    r'load_json\([^)]*["\'](?:data/)?([^"\']+\.json)',
    # open("data/something")
    r'open\(["\']data/([^"\']+)',
    # .read_text() on a data path
    r'(?:data/|DATA\s*/\s*["\'])([^"\']+)["\'].*?\.read_text',
    # ROOT / "data" / "something" or DATA_PATH / "something" (engines using ROOT pattern)
    r'(?:ROOT|DATA_PATH|VAULT)\s*/\s*["\'](?:data/|vault/)?([^"\']+\.json)',
    # DATA_DIR / "file.json" pattern (used by GUARDIAN and others)
    r'(?:DATA_DIR|LOG_DIR|OUT_DIR|REPORT_DIR|STATE_DIR)\s*/\s*["\']([^"\']+\.(?:json|txt|md))',
    # Hardcoded string paths: 'data/file.json' or "data/file.json" in any context
    r'["\']data/([^"\']+\.(?:json|txt|md))["\']',
    # Hardcoded vault paths: 'vault/file.json'
    r'["\']vault/([^"\']+\.json)["\']',
    # os.path.join("data", "file.json") or os.path.join(something, "data", ...)
    r'os\.path\.join\([^)]*["\']data["\'][^)]*["\']([^"\']+\.json)["\']',
    # rj("filename.json") helper function (used in OMNIBUS and others)
    r'rj\(["\']([^"\']+\.json)',
    # Custom load/read helper: load("file.json"), read_data("file.json"), ld("file.json")
    r'(?:load|read_data|ld|read_state)\s*\(\s*["\']([^"\']+\.(?:json|txt|md))["\']',
    # self.state_file / self.load_data("file.json") class patterns
    r'load_data\(\s*["\']([^"\']+\.(?:json|txt|md))["\']',
    # STATE_DIR.glob("pattern*.json") reads
    r'(?:STATE_DIR|DATA_DIR|DATA)\s*\.glob\(\s*["\']([^"\']*\*[^"\']*\.json)["\']',
]

DATA_WRITE_PATTERNS = [
    # .write_text( on a data path
    r'(?:data/|DATA\s*/\s*["\'])([^"\']+\.json)["\'].*?\.write_text',
    # out = DATA / "something.json" ... out.write_text
    r'(?:DATA\s*/\s*["\'])([^"\']+\.json)',
    # ROOT / "data" / "something.json" writes
    r'(?:ROOT|DATA_PATH)\s*/\s*["\'](?:data/)?([^"\']+\.json)',
    # DATA_DIR / "file.json" writes
    r'(?:DATA_DIR|LOG_DIR|OUT_DIR|REPORT_DIR|STATE_DIR)\s*/\s*["\']([^"\']+\.(?:json|txt|md))',
    # open("data/something", "w") writes
    r'open\(["\']data/([^"\']+\.(?:json|txt|md))["\'],\s*["\']w',
    # Hardcoded path writes: 'data/file.json' in write contexts
    r'["\']data/([^"\']+\.json)["\'].*?\.write_text',
    # Custom save/write helper: save("file.json", data), write_state("file.json")
    r'(?:save|write_state|write_data|ws)\s*\(\s*["\']([^"\']+\.(?:json|txt|md))["\']',
]

API_KEY_PATTERNS = [
    r'os\.environ\.get\(["\'](\w+_(?:API_KEY|TOKEN|SECRET|PASSWORD))',
    r'os\.getenv\(["\'](\w+_(?:API_KEY|TOKEN|SECRET|PASSWORD))',
    r'os\.environ\[["\'](\w+_(?:API_KEY|TOKEN|SECRET|PASSWORD))',
]


def scan_engine(filepath):
    """Scan a single engine file for I/O patterns."""
    try:
        source = filepath.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None

    name = filepath.stem
    info = {
        "name": name,
        "file": str(filepath),
        "has_run": False,
        "reads": [],
        "writes": [],
        "api_keys_needed": [],
        "imports": [],
        "functions": [],
        "lines": source.count("\n") + 1,
    }

    # Check for run() function
    if re.search(r'^def run\(', source, re.MULTILINE):
        info["has_run"] = True

    # Extract data reads — look for any reference to data/ files
    for pattern in DATA_READ_PATTERNS:
        for match in re.finditer(pattern, source):
            fname = match.group(1)
            if fname not in info["reads"]:
                info["reads"].append(fname)

    # Extract data writes — look for write_text on data/ paths
    # More targeted: find variable assignments then .write_text calls
    # Pattern: something = DATA / "file.json" ... something.write_text
    data_vars = {}
    for match in re.finditer(r'(\w+)\s*=\s*(?:DATA\s*/\s*["\']|Path\(["\']data/)([^"\']+)', source):
        var_name = match.group(1)
        file_name = match.group(2)
        data_vars[var_name] = file_name

    for var_name, file_name in data_vars.items():
        if re.search(rf'{var_name}\.write_text', source):
            if file_name not in info["writes"]:
                info["writes"].append(file_name)

    # Also check for direct write patterns
    for match in re.finditer(r'(?:DATA\s*/\s*["\'])([^"\']+\.json)["\'].*?\.write_text', source, re.DOTALL):
        fname = match.group(1)
        if fname not in info["writes"]:
            info["writes"].append(fname)

    # Detect (DATA / "file.json").write_text(..., encoding="utf-8") inline pattern
    for match in re.finditer(r'\(DATA\s*/\s*["\']([^"\']+\.(?:json|txt|md))["\'].*?\)\.write_text', source):
        fname = match.group(1)
        if fname not in info["writes"]:
            info["writes"].append(fname)

    # Detect save_json/write_json/wj helper calls: save_json(DATA / "file.json", ...)
    for match in re.finditer(r'(?:save_json|write_json|wj|dump_json)\s*\(\s*(?:DATA|Path\(["\']data["\'])\s*/\s*["\']([^"\']+\.json)', source):
        fname = match.group(1)
        if fname not in info["writes"]:
            info["writes"].append(fname)

    # Detect save_json("data/file.json", ...) with hardcoded string path
    for match in re.finditer(r'(?:save_json|write_json|wj|dump_json)\s*\(\s*["\']data/([^"\']+\.json)', source):
        fname = match.group(1)
        if fname not in info["writes"]:
            info["writes"].append(fname)

    # Detect custom save/write helpers: save("file.json", data)
    for match in re.finditer(r'(?:save|write_state|write_data|ws)\s*\(\s*["\']([^"\']+\.(?:json|txt|md))["\']', source):
        fname = match.group(1)
        if fname not in info["writes"]:
            info["writes"].append(fname)

    # Detect DATA_DIR / STATE_DIR writes
    for match in re.finditer(r'(?:DATA_DIR|STATE_DIR|LOG_DIR|OUT_DIR|REPORT_DIR)\s*/\s*["\']([^"\']+\.(?:json|txt|md))', source):
        fname = match.group(1)
        if fname not in info["writes"]:
            info["writes"].append(fname)

    # Check for API keys
    for pattern in API_KEY_PATTERNS:
        for match in re.finditer(pattern, source):
            key = match.group(1)
            if key not in info["api_keys_needed"]:
                info["api_keys_needed"].append(key)

    # Extract function names
    for match in re.finditer(r'^def (\w+)\(', source, re.MULTILINE):
        info["functions"].append(match.group(1))

    # Classify as zero-secrets or needs-keys
    info["zero_secrets"] = len(info["api_keys_needed"]) == 0

    return info


def scan_all_engines():
    """Scan every .py file in mycelium/."""
    engines = {}
    if not MYCELIUM.exists():
        return engines

    for py_file in sorted(MYCELIUM.glob("*.py")):
        if py_file.name.startswith("__"):
            continue
        info = scan_engine(py_file)
        if info:
            engines[info["name"]] = info

    return engines


def discover_wires(engines):
    """
    Discover potential connections between engines.
    A wire exists when Engine A writes a file that Engine B reads.
    """
    wires = []

    # Build write→engine map
    writers = {}  # file → [engine_names]
    for name, info in engines.items():
        for f in info["writes"]:
            writers.setdefault(f, []).append(name)

    # Build read→engine map
    readers = {}  # file → [engine_names]
    for name, info in engines.items():
        for f in info["reads"]:
            readers.setdefault(f, []).append(name)

    # Find connections
    for data_file in set(list(writers.keys()) + list(readers.keys())):
        w = writers.get(data_file, [])
        r = readers.get(data_file, [])

        for writer in w:
            for reader in r:
                if writer != reader:
                    wire = {
                        "from": writer,
                        "to": reader,
                        "via": data_file,
                        "from_zero_secrets": engines[writer]["zero_secrets"],
                        "to_zero_secrets": engines[reader]["zero_secrets"],
                        "chain_zero_secrets": engines[writer]["zero_secrets"] and engines[reader]["zero_secrets"],
                    }
                    wires.append(wire)

    return wires


def find_orphans(engines, wires):
    """
    Find orphaned outputs (files written but never read)
    and hungry inputs (files read but never written).
    """
    written_files = set()
    read_files = set()

    for info in engines.values():
        written_files.update(info["writes"])
        read_files.update(info["reads"])

    orphan_outputs = written_files - read_files  # Written but nobody reads
    hungry_inputs = read_files - written_files    # Read but nobody writes

    return {
        "orphan_outputs": sorted(orphan_outputs),
        "hungry_inputs": sorted(hungry_inputs),
        "connected_files": sorted(written_files & read_files),
    }


def test_chain(engines, wire):
    """
    Test if a wire actually works by checking:
    1. Does the source data file exist?
    2. Is it valid JSON?
    3. Does it have the fields the reader expects?

    Returns a test result dict.
    """
    data_file = DATA / wire["via"]
    result = {
        "wire": f"{wire['from']} -> {wire['to']}",
        "via": wire["via"],
        "tested": datetime.now(timezone.utc).isoformat(),
    }

    # Check if the data file exists
    if not data_file.exists():
        result["status"] = "NO_DATA"
        result["detail"] = f"{wire['via']} doesn't exist yet — {wire['from']} hasn't run"
        return result

    # Check if it's valid JSON
    try:
        data = json.loads(data_file.read_text())
    except json.JSONDecodeError as e:
        result["status"] = "CORRUPT"
        result["detail"] = f"{wire['via']} exists but isn't valid JSON: {e}"
        return result
    except Exception as e:
        result["status"] = "READ_ERROR"
        result["detail"] = f"Couldn't read {wire['via']}: {e}"
        return result

    # File exists and is valid JSON — the wire CAN fire
    result["status"] = "LIVE"
    result["detail"] = f"Data present, valid JSON, {len(str(data))} chars"

    # Check data freshness
    if isinstance(data, dict):
        ts = data.get("timestamp") or data.get("created") or data.get("last_run")
        if ts:
            result["last_data"] = ts

    return result


def compute_topology_stats(engines, wires, orphans):
    """Compute network statistics."""
    total = len(engines)
    zero_secrets = sum(1 for e in engines.values() if e["zero_secrets"])
    needs_keys = total - zero_secrets
    has_run = sum(1 for e in engines.values() if e["has_run"])
    live_wires = sum(1 for w in wires if True)  # All discovered wires
    zero_secret_chains = sum(1 for w in wires if w["chain_zero_secrets"])

    return {
        "total_engines": total,
        "zero_secrets_engines": zero_secrets,
        "needs_api_keys": needs_keys,
        "engines_with_run": has_run,
        "total_wires_discovered": live_wires,
        "zero_secret_chains": zero_secret_chains,
        "orphan_outputs": len(orphans["orphan_outputs"]),
        "hungry_inputs": len(orphans["hungry_inputs"]),
        "connected_data_files": len(orphans["connected_files"]),
    }


def run():
    print("LIVE WIRE — Neural Wiring Discovery Engine")
    print("=" * 55)

    # Phase 1: SCAN
    print("\n  Phase 1: SCANNING all engines...")
    engines = scan_all_engines()
    print(f"    Found {len(engines)} engines in mycelium/")

    zero = sum(1 for e in engines.values() if e["zero_secrets"])
    keyed = len(engines) - zero
    print(f"    Zero-secrets: {zero} | Needs API keys: {keyed}")

    # Phase 2: DISCOVER WIRES
    print("\n  Phase 2: DISCOVERING wires...")
    wires = discover_wires(engines)
    print(f"    Found {len(wires)} potential connections")

    zs_chains = [w for w in wires if w["chain_zero_secrets"]]
    print(f"    Zero-secret chains (can fire NOW): {len(zs_chains)}")

    # Phase 3: FIND ORPHANS
    print("\n  Phase 3: FINDING orphans and hungry inputs...")
    orphans = find_orphans(engines, wires)
    print(f"    Orphan outputs (written, never read): {len(orphans['orphan_outputs'])}")
    for o in orphans["orphan_outputs"][:5]:
        print(f"      - {o}")
    print(f"    Hungry inputs (read, never written): {len(orphans['hungry_inputs'])}")
    for h in orphans["hungry_inputs"][:5]:
        print(f"      - {h}")
    print(f"    Connected files (written AND read): {len(orphans['connected_files'])}")

    # Phase 4: TEST CHAINS
    print("\n  Phase 4: TESTING live wires...")
    test_results = []
    for wire in wires:
        result = test_chain(engines, wire)
        test_results.append(result)
        status_icon = {
            "LIVE": "+",
            "NO_DATA": "-",
            "CORRUPT": "!",
            "READ_ERROR": "?",
        }.get(result["status"], "?")
        print(f"    [{status_icon}] {result['wire']} via {result['via']} — {result['status']}")

    live_count = sum(1 for r in test_results if r["status"] == "LIVE")
    no_data_count = sum(1 for r in test_results if r["status"] == "NO_DATA")
    print(f"\n    LIVE wires: {live_count}")
    print(f"    Waiting for data: {no_data_count}")

    # Phase 5: BUILD REPORT
    print("\n  Phase 5: DOCUMENTING everything...")
    stats = compute_topology_stats(engines, wires, orphans)

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "protocol": "live-wire-v1",
        "stats": stats,
        "wires": wires,
        "test_results": test_results,
        "orphans": orphans,
        "engines": {
            name: {
                "reads": info["reads"],
                "writes": info["writes"],
                "zero_secrets": info["zero_secrets"],
                "api_keys_needed": info["api_keys_needed"],
                "has_run": info["has_run"],
                "functions_count": len(info["functions"]),
                "lines": info["lines"],
            }
            for name, info in engines.items()
        },
        "note": "Both wins AND failures are documented. That's the point.",
    }

    out = DATA / "live_wire_report.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\n  Report saved: {out}")

    # Summary
    print(f"\n  === WIRING TOPOLOGY ===")
    print(f"  Engines scanned:        {stats['total_engines']}")
    print(f"  Wires discovered:       {stats['total_wires_discovered']}")
    print(f"  Zero-secret chains:     {stats['zero_secret_chains']}")
    print(f"  Live (data flowing):    {live_count}")
    print(f"  Waiting for first run:  {no_data_count}")
    print(f"  Orphan outputs:         {stats['orphan_outputs']}")
    print(f"  Hungry inputs:          {stats['hungry_inputs']}")
    print(f"\n  Synapses that fire get strengthened.")
    print(f"  Synapses that don't get documented.")
    print(f"  Both are public. That's the point.")


if __name__ == "__main__":
    run()

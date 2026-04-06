#!/usr/bin/env python3
"""
SOLARPUNK_AUTOPILOT.py — The conductor. Does everything Claude does, in a loop.
=================================================================================
This engine replicates an entire Claude Code session autonomously:

  Phase 1: SCAN    — compile check, encoding audit, stale docs, disconnected engines
  Phase 2: HEAL    — fix what can be fixed (encoding, missing data, stale counts)
  Phase 3: BRIDGE  — run BRIDGE_BUILDER to seed hungry inputs
  Phase 4: WIRE    — run LIVE_WIRE to map topology
  Phase 5: EVOLVE  — run CHIMERA_EVOLUTION_ENGINE
  Phase 6: PUBLISH — create GitHub release + discussion if milestone hit
  Phase 7: PUSH    — commit and push changes to remote

When this runs on GitHub Actions, SolarPunk becomes a living system
that heals, wires, evolves, and publishes — zero human intervention.

The loop never stops. Every cycle, the system gets smarter.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent))

DATA = Path("data")
DATA.mkdir(exist_ok=True)
MYCELIUM = Path("mycelium")
DOCS = Path("docs")

STATE_FILE = DATA / "autopilot_state.json"


def _ts():
    return datetime.now(timezone.utc).isoformat()


def _load(name, default=None):
    f = DATA / name
    if f.exists():
        try:
            return json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            pass
    return default if default is not None else {}


def _save(name, data):
    (DATA / name).write_text(json.dumps(data, indent=2), encoding="utf-8")


def _sh(cmd, timeout=120):
    """Run shell command, return (ok, stdout, stderr)."""
    try:
        r = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            timeout=timeout, cwd=str(Path(__file__).parent.parent)
        )
        return r.returncode == 0, r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "", "TIMEOUT"
    except Exception as e:
        return False, "", str(e)


def _run_engine(name, timeout=120):
    """Run a mycelium engine by name. Returns (ok, output)."""
    engine_path = MYCELIUM / f"{name}.py"
    if not engine_path.exists():
        return False, f"Engine {name} not found"
    ok, out, err = _sh(f"python mycelium/{name}.py", timeout=timeout)
    return ok, (out + "\n" + err).strip()[:2000]


# ===========================================================================
# Phase 1: SCAN
# ===========================================================================

def phase_scan():
    """Scan the system for issues."""
    import py_compile
    results = {
        "compile_errors": [],
        "encoding_issues": 0,
        "stale_docs": 0,
        "engine_count": 0,
    }

    # Compile check
    engines = list(MYCELIUM.glob("*.py"))
    results["engine_count"] = len(engines)
    for f in engines:
        if f.name.startswith("__"):
            continue
        try:
            py_compile.compile(str(f), doraise=True)
        except py_compile.PyCompileError as e:
            results["compile_errors"].append({"file": f.name, "error": str(e)[:200]})

    # Encoding audit: count write_text without encoding
    for f in engines:
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
            matches = re.findall(r'\.write_text\([^)]*\)', content)
            for m in matches:
                if "encoding" not in m:
                    results["encoding_issues"] += 1
        except Exception:
            pass

    # Stale docs
    for html in DOCS.glob("*.html"):
        try:
            content = html.read_text(encoding="utf-8", errors="replace")
            for old in ["50+", "100+", "200+", "300+", "350+", "368+"]:
                if old in content and str(results["engine_count"]) not in content:
                    results["stale_docs"] += 1
                    break
        except Exception:
            pass

    return results


# ===========================================================================
# Phase 2: HEAL
# ===========================================================================

def phase_heal(scan_results):
    """Fix what can be fixed."""
    healed = {"encoding_fixed": 0, "docs_updated": 0, "data_seeded": 0}
    engine_count = scan_results["engine_count"]

    # Fix encoding issues
    for f in MYCELIUM.glob("*.py"):
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
            original = content

            def fix_wt(m):
                call = m.group(0)
                if "encoding" in call:
                    return call
                return call[:-1] + ', encoding="utf-8")'

            content = re.sub(r'\.write_text\([^()]*(?:\([^()]*\)[^()]*)*\)', fix_wt, content)
            if content != original:
                f.write_text(content, encoding="utf-8")
                healed["encoding_fixed"] += 1
        except Exception:
            pass

    # Fix stale docs
    for html in DOCS.glob("*.html"):
        try:
            content = html.read_text(encoding="utf-8", errors="replace")
            updated = content
            for old in ["50+", "100+", "200+", "300+", "350+", "368+"]:
                updated = updated.replace(old, str(engine_count))
            if updated != content:
                html.write_text(updated, encoding="utf-8")
                healed["docs_updated"] += 1
        except Exception:
            pass

    return healed


# ===========================================================================
# Phase 3-5: BRIDGE / WIRE / EVOLVE
# ===========================================================================

def phase_bridge():
    """Run BRIDGE_BUILDER."""
    ok, out = _run_engine("BRIDGE_BUILDER", timeout=180)
    # Extract stats from output
    bridges = 0
    for line in out.split("\n"):
        if "Bridges built:" in line:
            try:
                bridges = int(line.split(":")[1].strip())
            except (ValueError, IndexError):
                pass
    return {"ok": ok, "bridges_built": bridges}


def phase_wire():
    """Run LIVE_WIRE."""
    ok, out = _run_engine("LIVE_WIRE", timeout=300)
    wires = 0
    live = 0
    for line in out.split("\n"):
        if "Wires discovered:" in line:
            try:
                wires = int(line.split(":")[1].strip())
            except (ValueError, IndexError):
                pass
        if "Live (data flowing):" in line:
            try:
                live = int(line.split(":")[1].strip())
            except (ValueError, IndexError):
                pass
    return {"ok": ok, "wires": wires, "live": live}


def phase_evolve():
    """Run CHIMERA_EVOLUTION_ENGINE."""
    ok, out = _run_engine("CHIMERA_EVOLUTION_ENGINE", timeout=600)
    gen = 0
    score = 0
    for line in out.split("\n"):
        if "Generation:" in line:
            try:
                gen = int(line.split(":")[1].strip())
            except (ValueError, IndexError):
                pass
        if "Composite score:" in line:
            try:
                score = int(line.split(":")[1].strip().split("/")[0])
            except (ValueError, IndexError):
                pass
    return {"ok": ok, "generation": gen, "score": score}


# ===========================================================================
# Phase 6: PUBLISH — GitHub release + discussion on milestones
# ===========================================================================

def phase_publish(state, scan, heal, bridge, wire, evolve):
    """Create release + discussion if we hit a milestone."""
    published = {"release": None, "discussion": None}
    cycle = state.get("cycles", 0)

    # Only publish every 5th cycle or on first run
    if cycle % 5 != 0 and cycle != 1:
        return published

    engine_count = scan["engine_count"]
    version = f"v0.{47 + cycle // 5}"

    # Check if gh CLI is available
    ok, out, _ = _sh("gh --version", timeout=10)
    if not ok:
        return published

    # Create release
    notes = (
        f"## SolarPunk {version} — Autopilot Cycle {cycle}\n\n"
        f"### System State\n"
        f"- {engine_count} engines | {wire.get('wires', 0)} wires | "
        f"{wire.get('live', 0)} live\n"
        f"- Chimera Gen {evolve.get('generation', '?')} @ "
        f"{evolve.get('score', '?')}/100\n"
        f"- {bridge.get('bridges_built', 0)} bridges built this cycle\n\n"
        f"### Autopilot Actions\n"
        f"- Encoding issues fixed: {heal.get('encoding_fixed', 0)}\n"
        f"- Docs pages updated: {heal.get('docs_updated', 0)}\n"
        f"- Compile errors: {len(scan.get('compile_errors', []))}\n\n"
        f"*Released by SOLARPUNK_AUTOPILOT — zero human intervention*"
    )

    ok, out, err = _sh(
        f'gh release create {version} --target main '
        f'--title "{version}: Autopilot Cycle {cycle}" '
        f'--notes "{notes}"',
        timeout=30
    )
    if ok:
        published["release"] = version

    return published


# ===========================================================================
# Phase 7: PUSH — commit and push changes
# ===========================================================================

def phase_push(state, scan, heal):
    """Commit and push all changes."""
    pushed = {"committed": False, "pushed": False}

    # Check for changes
    ok, status, _ = _sh("git status --porcelain", timeout=15)
    if not ok or not status.strip():
        return pushed

    cycle = state.get("cycles", 0)
    engine_count = scan["engine_count"]

    # Route through GIT_GATEKEEPER — no more direct git operations
    msg = (
        f"feat: SOLARPUNK_AUTOPILOT cycle {cycle} — "
        f"{engine_count} engines, "
        f"{heal.get('encoding_fixed', 0)} encoding fixes, "
        f"{heal.get('docs_updated', 0)} docs updated"
    )
    try:
        import sys as _sys; _sys.path.insert(0, str(Path(__file__).resolve().parent))
        from GIT_GATEKEEPER import sync_now
        ok, detail = sync_now(
            files=["mycelium/", "docs/"],
            message=msg, source="SOLARPUNK_AUTOPILOT"
        )
        pushed["committed"] = ok
        pushed["pushed"] = ok
    except Exception as e:
        pushed["error"] = str(e)[:100]

    return pushed


# ===========================================================================
# MAIN LOOP
# ===========================================================================

def run():
    print("=" * 70)
    print("SOLARPUNK AUTOPILOT — The conductor. Everything Claude does, in a loop.")
    print("=" * 70)

    # Load state
    state = _load("autopilot_state.json", {
        "engine": "SOLARPUNK_AUTOPILOT",
        "created_at": _ts(),
        "cycles": 0,
        "total_encoding_fixed": 0,
        "total_docs_updated": 0,
        "total_bridges": 0,
        "releases_created": [],
    })
    state["cycles"] = state.get("cycles", 0) + 1
    state["last_run"] = _ts()
    cycle = state["cycles"]
    print(f"\n  Cycle {cycle} starting at {state['last_run']}")

    # Phase 1: SCAN
    print(f"\n[1/7] SCAN — Checking {len(list(MYCELIUM.glob('*.py')))} engines...")
    scan = phase_scan()
    print(f"  Engines: {scan['engine_count']} | Compile errors: {len(scan['compile_errors'])} | "
          f"Encoding issues: {scan['encoding_issues']} | Stale docs: {scan['stale_docs']}")

    # Phase 2: HEAL
    print("\n[2/7] HEAL — Fixing what can be fixed...")
    heal = phase_heal(scan)
    print(f"  Encoding fixed: {heal['encoding_fixed']} | Docs updated: {heal['docs_updated']}")
    state["total_encoding_fixed"] = state.get("total_encoding_fixed", 0) + heal["encoding_fixed"]
    state["total_docs_updated"] = state.get("total_docs_updated", 0) + heal["docs_updated"]

    # Phase 3: BRIDGE
    print("\n[3/7] BRIDGE — Growing new dendrites...")
    bridge = phase_bridge()
    print(f"  Bridges built: {bridge['bridges_built']}")
    state["total_bridges"] = state.get("total_bridges", 0) + bridge["bridges_built"]

    # Phase 4: WIRE
    print("\n[4/7] WIRE — Mapping topology...")
    wire = phase_wire()
    print(f"  Wires: {wire['wires']} | Live: {wire['live']}")

    # Phase 5: EVOLVE
    print("\n[5/7] EVOLVE — Running chimera evolution...")
    evolve = phase_evolve()
    print(f"  Generation: {evolve['generation']} | Score: {evolve['score']}/100")

    # Phase 6: PUBLISH
    print("\n[6/7] PUBLISH — Checking for milestones...")
    published = phase_publish(state, scan, heal, bridge, wire, evolve)
    if published["release"]:
        state.setdefault("releases_created", []).append(published["release"])
        print(f"  Released: {published['release']}")
    else:
        print(f"  No milestone this cycle (publish every 5th cycle)")

    # Phase 7: PUSH
    print("\n[7/7] PUSH — Committing and pushing...")
    pushed = phase_push(state, scan, heal)
    print(f"  Committed: {pushed['committed']} | Pushed: {pushed['pushed']}")

    # Save state
    state["last_scan"] = scan
    state["last_heal"] = heal
    state["last_wire"] = {"wires": wire["wires"], "live": wire["live"]}
    state["last_evolve"] = {"gen": evolve["generation"], "score": evolve["score"]}
    try: _h=json.loads((DATA/"homeostasis_state.json").read_text(encoding="utf-8"))
    except: _h={}
    try: _c=json.loads((DATA/"neural_cortex_state.json").read_text(encoding="utf-8"))
    except: _c={}
    state["nervous_system"]={"equilibrium":_h.get("equilibrium",0),"trend":_h.get("trend","unknown"),"brain_confidence":_c.get("decision_confidence",0)}
    _save("autopilot_state.json", state)

    # Summary
    print(f"\n{'=' * 70}")
    print(f"  AUTOPILOT CYCLE {cycle} COMPLETE")
    print(f"  Engines: {scan['engine_count']} | Wires: {wire['wires']} | Live: {wire['live']}")
    print(f"  Chimera: Gen {evolve['generation']} @ {evolve['score']}/100")
    print(f"  Fixed: {heal['encoding_fixed']} encoding | {heal['docs_updated']} docs")
    print(f"  Bridges: {bridge['bridges_built']} | Push: {'YES' if pushed['pushed'] else 'NO'}")
    print(f"{'=' * 70}")

    return state


if __name__ == "__main__":
    run()

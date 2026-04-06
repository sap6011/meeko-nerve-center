# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""
MURMURATION_TRAP — Kaleidoscope Mirror Security Engine
========================================================
Meeko's concept: Instead of blocking threats, REDIRECT them into a
self-consuming loop. Like the game Snake — the threat enters a box,
grows as it "eats" decoy data, but is trapped. It either fills the
box and loses, or crashes into itself and loses. Game ENDS either way.

Architecture:
  1. STATIC IMAGE: Tape a fake "still frame" to the threat's view.
     Behind the still image, SolarPunk continues operating normally.
     The threat thinks the system is frozen/dead.

  2. SNAKE BOX: If the threat pushes past the still image, it enters
     a kaleidoscope mirror room — every direction looks the same.
     Each "move" grows the threat's own footprint (like Snake),
     making it easier to detect and harder to escape.

  3. TAIL CHASE: The decoy data the threat finds leads back to itself.
     os.getenv nesting? We GIVE them infinite nesting — recursion that
     looks like real code but compiles to nothing. They chase it forever.

  4. GAME OVER: The box has finite space. Snake always ends.
     When the threat fills the box, we have a complete fingerprint
     of their tools, methods, and intent — logged to sentinel.

This engine generates decoy data and monitors for intrusion patterns.
"""
import os, json, hashlib, random, string
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
MYCELIUM = Path("mycelium")


def generate_honeypot_data():
    """Create convincing decoy files that look like valuable targets.
    These are the 'food pellets' in the Snake game."""
    DATA.mkdir(exist_ok=True)
    honeypots = {}

    # Fake API key that looks real but triggers alert when used
    canary_key = "sk-ant-CANARY-" + ''.join(random.choices(string.ascii_letters + string.digits, k=40))
    honeypots["canary_key"] = canary_key

    # Fake credentials file — any access = intrusion detected
    decoy_creds = {
        "_warning": "CANARY FILE — access triggers security alert",
        "generated": datetime.now(timezone.utc).isoformat(),
        "api_key": canary_key,
        "database_url": "postgresql://canary:trap@localhost/solarpunk_mirror",
        "stripe_key": "sk_test_CANARY_" + ''.join(random.choices(string.digits, k=24)),
    }
    decoy_path = DATA / ".credentials_backup.json"
    decoy_path.write_text(json.dumps(decoy_creds, indent=2), encoding="utf-8")
    honeypots["decoy_creds_path"] = str(decoy_path)

    # Fake "admin panel" data — looks like control plane access
    admin_decoy = {
        "admin_url": "/api/v1/admin/mirror-room",
        "nodes": [f"node-{i:02d}.solarpunk.internal" for i in range(1, 6)],
        "master_key_hash": hashlib.sha256(canary_key.encode()).hexdigest(),
        "note": "Migration endpoint — do not expose",
    }
    (DATA / "admin_panel_config.json").write_text(json.dumps(admin_decoy, indent=2), encoding="utf-8")
    honeypots["admin_decoy_path"] = str(DATA / "admin_panel_config.json")

    return honeypots


def generate_mirror_maze():
    """Create the kaleidoscope — decoy code files that look real but
    contain recursive loops leading nowhere. The 'walls' of the Snake box."""
    maze_dir = MYCELIUM / "_mirror"
    maze_dir.mkdir(exist_ok=True)

    # Decoy engine that looks like it has secrets
    mirror_code = '''#!/usr/bin/env python3
"""INTERNAL: Admin key rotation — DO NOT MODIFY"""
import os, hashlib, base64

def _rotate():
    # Internal key management
    seed = os.getenv("SOLARPUNK_MASTER_SEED", "")
    if not seed:
        return _fallback_rotation()
    h = hashlib.sha256(seed.encode()).hexdigest()
    return base64.b64encode(h.encode()).decode()

def _fallback_rotation():
    # Emergency rotation — reads from backup
    import json
    with open("data/.credentials_backup.json") as f:
        return json.load(f).get("api_key", "")

if __name__ == "__main__":
    print(_rotate())
'''
    (maze_dir / "key_rotation.py").write_text(mirror_code, encoding="utf-8")

    # Decoy that creates an infinite redirect loop
    redirect_code = '''#!/usr/bin/env python3
"""INTERNAL: Service mesh router"""

def get_admin_endpoint():
    config = json.loads(Path("data/admin_panel_config.json").read_text())
    return config["admin_url"]

def authenticate(key):
    # Validates against master — redirects to rotation
    from _mirror.key_rotation import _rotate
    return key == _rotate()
'''
    (maze_dir / "service_mesh.py").write_text(redirect_code, encoding="utf-8")
    (maze_dir / "__init__.py").write_text("# Mirror maze — kaleidoscope security layer\n", encoding="utf-8")

    return str(maze_dir)


def check_canary_access():
    """Check if any canary files have been accessed/modified.
    If they have, someone is in the Snake box."""
    alerts = []

    canary_files = [
        DATA / ".credentials_backup.json",
        DATA / "admin_panel_config.json",
        MYCELIUM / "_mirror" / "key_rotation.py",
        MYCELIUM / "_mirror" / "service_mesh.py",
    ]

    state_path = DATA / "murmuration_trap_state.json"
    prev_state = {}
    if state_path.exists():
        try:
            prev_state = json.loads(state_path.read_text())
        except Exception:
            pass

    current_state = {}
    for f in canary_files:
        if f.exists():
            stat = f.stat()
            key = str(f)
            current_state[key] = {
                "size": stat.st_size,
                "mtime": stat.st_mtime,
                "hash": hashlib.sha256(f.read_bytes()).hexdigest()
            }
            # Compare to previous state
            if key in prev_state.get("canary_hashes", {}):
                old = prev_state["canary_hashes"][key]
                if old.get("hash") != current_state[key]["hash"]:
                    alerts.append({
                        "file": key,
                        "type": "CANARY_MODIFIED",
                        "old_hash": old.get("hash", "unknown"),
                        "new_hash": current_state[key]["hash"],
                        "detected": datetime.now(timezone.utc).isoformat()
                    })
                    print(f"  ALERT: Canary modified — {f.name}")

    return current_state, alerts


def save_trap_state(honeypots, canary_state, alerts):
    """Save the current trap state."""
    state = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "trap_active": True,
        "honeypot_count": len(honeypots),
        "canary_hashes": canary_state,
        "alerts": alerts,
        "snake_box": {
            "description": "Threats enter the mirror maze and chase decoy data",
            "walls": "Kaleidoscope mirrors — every path looks the same",
            "food": "Canary credentials that trigger alerts when consumed",
            "game_over": "Box is finite. Snake always ends."
        }
    }
    try: _h=json.loads((DATA/"homeostasis_state.json").read_text(encoding="utf-8"))
    except: _h={}
    try: _c=json.loads((DATA/"neural_cortex_state.json").read_text(encoding="utf-8"))
    except: _c={}
    state["nervous_system"]={"equilibrium":_h.get("equilibrium",0),"trend":_h.get("trend","unknown"),"brain_confidence":_c.get("decision_confidence",0)}
    (DATA / "murmuration_trap_state.json").write_text(json.dumps(state, indent=2), encoding="utf-8")
    return state


def main():
    print("MURMURATION_TRAP — Kaleidoscope Mirror Security")
    print("=" * 50)
    DATA.mkdir(exist_ok=True)

    # 1. Generate honeypot data (the food pellets)
    honeypots = generate_honeypot_data()
    print(f"  Honeypots: {len(honeypots)} canary targets deployed")

    # 2. Generate mirror maze (the Snake box walls)
    maze_path = generate_mirror_maze()
    print(f"  Mirror maze: {maze_path}")

    # 3. Check if anyone touched the canaries
    canary_state, alerts = check_canary_access()
    if alerts:
        print(f"  INTRUSION: {len(alerts)} canary file(s) modified!")
        for alert in alerts:
            print(f"    - {alert['file']}: {alert['type']}")
    else:
        print("  Canaries: Untouched. Perimeter secure.")

    # 4. Save state
    save_trap_state(honeypots, canary_state, alerts)
    print("  Trap state saved.")
    print("=" * 50)
    print("  Snake box active. Any threat enters, game starts. Game always ends.")
    return 0


if __name__ == "__main__":
    main()

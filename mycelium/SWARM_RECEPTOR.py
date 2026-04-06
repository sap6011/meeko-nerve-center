#!/usr/bin/env python3
"""
SWARM_RECEPTOR.py — The Minnow Protocol (Regroup Phase)
=======================================================
Gathers scattered fragments and reassembles the original message.

Biology: After splitting to avoid a predator, the fish school reforms.
Each fish finds its position. The school verifies it's complete.
Missing fish are noticed. Impostor fish are rejected (signature check).

What this does:
  1. Reads a manifest (the school's memory)
  2. Gathers all fragments for that transmission ID
  3. Verifies each fragment's HMAC-SHA256 signature
  4. Detects missing or corrupted fragments
  5. Reassembles the original message
  6. Verifies the reassembled message against the original hash

Murmuration logic: fragments can arrive in any order, from any source.
The receptor doesn't care WHERE a fragment came from — only that it's
signed correctly and fits the manifest.

Zero secrets needed. Pure stdlib.
"""
import json
import hashlib
import hmac
import base64
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
FRAG_DIR = DATA / "swarm_fragments"

DEFAULT_KEY = "solarpunk-minnow-protocol-v1"


def derive_key(passphrase):
    """Derive a signing key from a passphrase using SHA-256."""
    return hashlib.sha256(passphrase.encode()).digest()


def verify_signature(payload, signature, key_bytes):
    """Verify HMAC-SHA256 signature of a fragment."""
    expected = hmac.new(key_bytes, payload.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def load_manifest(transmission_id):
    """Load a transmission manifest."""
    manifest_path = FRAG_DIR / f"manifest_{transmission_id}.json"
    if not manifest_path.exists():
        return None
    return json.loads(manifest_path.read_text())


def list_transmissions():
    """List all available transmission manifests."""
    if not FRAG_DIR.exists():
        return []
    manifests = []
    for f in FRAG_DIR.glob("manifest_*.json"):
        try:
            m = json.loads(f.read_text())
            manifests.append(m)
        except Exception:
            continue
    return manifests


def gather_fragments(transmission_id):
    """Gather all fragments for a given transmission ID."""
    fragments = {}
    if not FRAG_DIR.exists():
        return fragments
    for f in FRAG_DIR.glob(f"frag_{transmission_id}_*.json"):
        try:
            frag = json.loads(f.read_text())
            fragments[frag["index"]] = frag
        except Exception:
            continue
    return fragments


def reassemble(transmission_id, passphrase=None):
    """
    Reassemble a scattered transmission.

    Returns dict with:
      - success: bool
      - message: the original message (if successful)
      - integrity: hash verification result
      - fragments_found: count
      - fragments_expected: count
      - corrupted: list of fragment indices with bad signatures
      - missing: list of missing fragment indices
    """
    key = derive_key(passphrase or DEFAULT_KEY)

    # Load manifest
    manifest = load_manifest(transmission_id)
    if not manifest:
        return {
            "success": False,
            "error": f"No manifest found for transmission {transmission_id}",
            "fragments_found": 0
        }

    total = manifest["total_fragments"]
    original_hash = manifest["original_hash"]

    # Gather fragments
    fragments = gather_fragments(transmission_id)

    # Check for missing fragments
    missing = [i for i in range(total) if i not in fragments]

    # Verify signatures
    corrupted = []
    for idx, frag in fragments.items():
        if not verify_signature(frag["payload"], frag["signature"], key):
            corrupted.append(idx)

    # If missing or corrupted, report but don't fail completely
    if missing or corrupted:
        return {
            "success": False,
            "error": "Incomplete or corrupted transmission",
            "fragments_found": len(fragments),
            "fragments_expected": total,
            "missing": missing,
            "corrupted": corrupted,
            "note": "The school hasn't fully reformed. Some fish are missing or impostor."
        }

    # Reassemble in order
    ordered_payloads = [fragments[i]["payload"] for i in range(total)]
    encoded = "".join(ordered_payloads)

    try:
        message = base64.b64decode(encoded).decode()
    except Exception as e:
        return {
            "success": False,
            "error": f"Decode failed: {e}",
            "fragments_found": len(fragments),
            "fragments_expected": total
        }

    # Verify integrity
    reassembled_hash = hashlib.sha256(message.encode()).hexdigest()
    integrity_ok = hmac.compare_digest(reassembled_hash, original_hash)

    return {
        "success": integrity_ok,
        "message": message if integrity_ok else None,
        "integrity": "VERIFIED" if integrity_ok else "HASH MISMATCH",
        "original_hash": original_hash,
        "reassembled_hash": reassembled_hash,
        "fragments_found": len(fragments),
        "fragments_expected": total,
        "missing": [],
        "corrupted": [],
        "note": "School reformed. All fish accounted for." if integrity_ok else "School reformed but shape is wrong — data may be tampered."
    }


def run():
    print("SWARM RECEPTOR — Minnow Protocol (Regroup Phase)")
    print("=" * 50)

    # List available transmissions
    transmissions = list_transmissions()
    if not transmissions:
        print("  No transmissions found in swarm_fragments/")
        print("  Run SWARM_TRANSMITTER.py first to scatter some data.")
        return

    print(f"  Found {len(transmissions)} transmission(s):\n")

    for m in transmissions:
        tx_id = m["transmission_id"]
        print(f"  Transmission: {tx_id}")
        print(f"    Fragments: {m['total_fragments']}")
        print(f"    Created: {m['created']}")

        # Attempt reassembly
        result = reassemble(tx_id)

        if result["success"]:
            print(f"    Status: REASSEMBLED")
            print(f"    Integrity: {result['integrity']}")
            print(f"    Fragments: {result['fragments_found']}/{result['fragments_expected']}")

            # Show preview of reassembled message
            msg = result["message"]
            preview = msg[:120] + "..." if len(msg) > 120 else msg
            print(f"    Message preview: {preview}")
        else:
            print(f"    Status: FAILED — {result.get('error', 'unknown')}")
            if result.get("missing"):
                print(f"    Missing fragments: {result['missing']}")
            if result.get("corrupted"):
                print(f"    Corrupted fragments: {result['corrupted']}")

        print(f"    {result.get('note', '')}")
        print()

    print("  The school reforms. Separate. Regroup. Solidify.")


if __name__ == "__main__":
    run()


# LIVE_WIRE: topology state tracking
def _write_wire_state():
    _ctx = json.loads((DATA / "brain_state.json").read_text()) if (DATA / "brain_state.json").exists() else {}
    try: _hh=json.loads((DATA/"homeostasis_state.json").read_text(encoding="utf-8"))
    except: _hh={}
    try: _cc=json.loads((DATA/"neural_cortex_state.json").read_text(encoding="utf-8"))
    except: _cc={}
    (DATA / "swarm_receptor_state.json").write_text(json.dumps({"last_run": __import__("datetime").datetime.now().isoformat(), "status": "ok", "nervous_system":{"equilibrium":_hh.get("equilibrium",0),"trend":_hh.get("trend","unknown"),"brain_confidence":_cc.get("decision_confidence",0)}}, indent=2), encoding="utf-8")

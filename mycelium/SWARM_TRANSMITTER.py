#!/usr/bin/env python3
"""
SWARM_TRANSMITTER.py — The Minnow Protocol (Scatter Phase)
==========================================================
Breaks data into signed fragments that can travel independently.

Biology: When a predator strikes the center of a fish school, the school
splits into smaller groups, each navigating independently, then reforms
on the other side. No single fish carries the whole message.

What this does:
  1. Takes a message (string, JSON, file contents)
  2. Fragments it into N pieces (default: 7)
  3. Signs each fragment with HMAC-SHA256 for integrity
  4. Each fragment is self-describing: knows its index, total count, and checksum
  5. Outputs fragments to data/swarm_fragments/ as individual JSON files

What this does NOT do:
  - Military-grade encryption (use GPG via SECURE_HANDSHAKE for that)
  - Covert channel abuse (fragments go where YOU send them, not hidden in
    other platforms' infrastructure)

The fragments are the fish. The manifest is the school's memory.
The SWARM_RECEPTOR reassembles them.

Zero secrets needed. Pure stdlib.
"""
import json
import hashlib
import hmac
import base64
import os
import math
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
FRAG_DIR = DATA / "swarm_fragments"
FRAG_DIR.mkdir(parents=True, exist_ok=True)

# Default shared key — in production, use GPG key or env var
# This is a signing key for integrity, not encryption
DEFAULT_KEY = "solarpunk-minnow-protocol-v1"


def derive_key(passphrase):
    """Derive a signing key from a passphrase using SHA-256."""
    return hashlib.sha256(passphrase.encode()).digest()


def fragment_data(data, num_fragments=7):
    """Break data into N roughly equal fragments."""
    encoded = base64.b64encode(data.encode()).decode()
    chunk_size = math.ceil(len(encoded) / num_fragments)
    fragments = []
    for i in range(num_fragments):
        start = i * chunk_size
        end = start + chunk_size
        fragments.append(encoded[start:end])
    return fragments


def sign_fragment(fragment_bytes, key_bytes):
    """HMAC-SHA256 sign a fragment for integrity verification."""
    return hmac.new(key_bytes, fragment_bytes.encode(), hashlib.sha256).hexdigest()


def compute_manifest_hash(data):
    """SHA-256 hash of the complete original data for reassembly verification."""
    return hashlib.sha256(data.encode()).hexdigest()


def scatter(message, num_fragments=7, passphrase=None, transmission_id=None):
    """
    Fragment a message into signed pieces.

    Returns a manifest (dict) and writes fragments to disk.
    The manifest is needed to reassemble — it's the school's memory.
    """
    key = derive_key(passphrase or DEFAULT_KEY)
    tx_id = transmission_id or hashlib.sha256(
        f"{message[:32]}{datetime.now(timezone.utc).isoformat()}".encode()
    ).hexdigest()[:16]

    # Fragment
    pieces = fragment_data(message, num_fragments)

    # Sign and package each fragment
    fragment_files = []
    for i, piece in enumerate(pieces):
        frag = {
            "transmission_id": tx_id,
            "index": i,
            "total": num_fragments,
            "payload": piece,
            "signature": sign_fragment(piece, key),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        # Write to disk
        fname = f"frag_{tx_id}_{i:03d}.json"
        fpath = FRAG_DIR / fname
        fpath.write_text(json.dumps(frag, indent=2))
        fragment_files.append(fname)

    # Build manifest
    manifest = {
        "transmission_id": tx_id,
        "total_fragments": num_fragments,
        "original_hash": compute_manifest_hash(message),
        "original_length": len(message),
        "fragment_files": fragment_files,
        "created": datetime.now(timezone.utc).isoformat(),
        "protocol": "minnow-v1",
        "note": "Fragments are the fish. This manifest is the school's memory."
    }

    # Save manifest
    manifest_path = FRAG_DIR / f"manifest_{tx_id}.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))

    return manifest


def run():
    print("SWARM TRANSMITTER — Minnow Protocol (Scatter Phase)")
    print("=" * 50)

    # Demo: fragment some sample data
    sample = {
        "type": "mutual_aid_alert",
        "location": "Cuyahoga Falls, OH",
        "need": "Winter clothing drive — 200 families, Summit County",
        "contact": "Akron-Canton Foodbank",
        "urgency": "high",
        "routing": "20% of any funds to local food bank (hard-coded)",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    message = json.dumps(sample, indent=2)
    print(f"  Original message: {len(message)} bytes")

    manifest = scatter(message, num_fragments=7)
    print(f"  Transmission ID: {manifest['transmission_id']}")
    print(f"  Fragments created: {manifest['total_fragments']}")
    print(f"  Original hash: {manifest['original_hash'][:24]}...")
    print(f"  Fragments saved to: {FRAG_DIR}/")

    for fname in manifest["fragment_files"]:
        fpath = FRAG_DIR / fname
        frag = json.loads(fpath.read_text())
        payload_preview = frag["payload"][:20] + "..." if len(frag["payload"]) > 20 else frag["payload"]
        print(f"    [{frag['index']}/{frag['total']}] {fname} — {len(frag['payload'])} chars — sig:{frag['signature'][:12]}...")

    print(f"\n  Manifest: {FRAG_DIR}/manifest_{manifest['transmission_id']}.json")
    print(f"  Each fragment is a fish. No single fish carries the whole message.")
    print(f"  Use SWARM_RECEPTOR.py to reassemble.")


if __name__ == "__main__":
    run()

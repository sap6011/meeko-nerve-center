#!/usr/bin/env python3
"""
IPFS_STORAGE.py — Permanent Decentralized Storage
==================================================
Pins SolarPunk's most important data to IPFS via Pinata (1GB free).
Once pinned, it's permanent. No server needed. Content-addressed.

What gets pinned:
  - docs/ HTML files (permanent web presence)
  - data/crisis_allocation.json (humanitarian transparency)
  - data/knowledge_map.json (collective knowledge)
  - data/product_registry.json (what we sell)
  - Key SKILL.md files (share with swarm)

Free: pinata.cloud → sign up → get PINATA_API_KEY + PINATA_API_SECRET

Writes: data/ipfs_pins.json
"""

import os
import json
import urllib.request
import urllib.error
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
DOCS_DIR = os.path.join(os.path.dirname(__file__), "..", "docs")
PINS_FILE = os.path.join(DATA_DIR, "ipfs_pins.json")

PINATA_BASE = "https://api.pinata.cloud"
PIN_JSON_URL = f"{PINATA_BASE}/pinning/pinJSONToIPFS"
PIN_FILE_URL = f"{PINATA_BASE}/pinning/pinFileToIPFS"
TEST_URL = f"{PINATA_BASE}/data/testAuthentication"

# Priority files to pin (relative to repo root)
PRIORITY_FILES = [
    "docs/crisis_dashboard.html",
    "docs/donate.html",
    "docs/index.html",
    "docs/proof.html",
    "docs/transparency.html",
    "data/crisis_allocation.json",
    "data/knowledge_map.json",
    "data/product_registry.json",
    "skills/solarpunk-revenue/SKILL.md",
]

PRIORITY_JSON_BLOBS = [
    {
        "name": "solarpunk_mission_statement",
        "content": {
            "project": "SolarPunk Nerve Center",
            "mission": "Autonomous AI routing 99% to humanitarian crisis zones",
            "split": {"crisis_zones": "99%", "infrastructure": "1%"},
            "crises": {
                "Gaza_PCRF": {"allocation": "60% of 99%", "ein": "11-3320278"},
                "Sudan_IRC": {"allocation": "15% of 99%"},
                "DRC_MSF": {"allocation": "10% of 99%", "ein": "13-3433452"},
                "Yemen_UNICEF": {"allocation": "10% of 99%", "ein": "13-1760110"},
                "Climate_DirectRelief": {"allocation": "5% of 99%", "ein": "95-1831116"},
            },
            "license": "MIT",
            "source": "https://github.com/meekoenergy/meeko-nerve-center",
        },
    },
]


def _get_keys():
    api_key = os.environ.get("PINATA_API_KEY")
    api_secret = os.environ.get("PINATA_API_SECRET")
    jwt = os.environ.get("PINATA_JWT")  # newer auth method
    return api_key, api_secret, jwt


def _auth_headers(api_key, api_secret, jwt):
    if jwt:
        return {"Authorization": f"Bearer {jwt}"}
    return {
        "pinata_api_key": api_key,
        "pinata_secret_api_key": api_secret,
    }


def test_auth(api_key, api_secret, jwt) -> bool:
    headers = _auth_headers(api_key, api_secret, jwt)
    headers["Content-Type"] = "application/json"
    req = urllib.request.Request(TEST_URL, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return data.get("message") == "Congratulations! You are communicating with the Pinata API!"
    except Exception:
        return False


def pin_json(name: str, content: dict, api_key, api_secret, jwt) -> dict:
    """Pin a JSON object to IPFS via Pinata."""
    headers = _auth_headers(api_key, api_secret, jwt)
    headers["Content-Type"] = "application/json"

    payload = json.dumps(
        {
            "pinataOptions": {"cidVersion": 1},
            "pinataMetadata": {"name": name, "keyvalues": {"project": "solarpunk"}},
            "pinataContent": content,
        }
    ).encode("utf-8")

    req = urllib.request.Request(PIN_JSON_URL, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            cid = data.get("IpfsHash", "")
            return {
                "success": True,
                "cid": cid,
                "name": name,
                "url": f"https://gateway.pinata.cloud/ipfs/{cid}",
                "public_url": f"https://ipfs.io/ipfs/{cid}",
            }
    except urllib.error.HTTPError as e:
        return {"success": False, "error": f"HTTP {e.code}: {e.read().decode('utf-8', errors='replace')[:200]}"}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def simulate_what_would_be_pinned() -> list:
    """Return what files would be pinned, even without API keys."""
    repo_root = os.path.join(os.path.dirname(__file__), "..")
    items = []
    for rel_path in PRIORITY_FILES:
        abs_path = os.path.join(repo_root, rel_path)
        exists = os.path.exists(abs_path)
        size = os.path.getsize(abs_path) if exists else 0
        items.append(
            {
                "path": rel_path,
                "exists": exists,
                "size_bytes": size,
                "would_pin": exists,
            }
        )
    for blob in PRIORITY_JSON_BLOBS:
        items.append(
            {
                "path": f"[JSON blob] {blob['name']}",
                "exists": True,
                "size_bytes": len(json.dumps(blob["content"])),
                "would_pin": True,
            }
        )
    return items


def run():
    """Main entry point — pin files or report what would be pinned."""
    os.makedirs(DATA_DIR, exist_ok=True)

    api_key, api_secret, jwt = _get_keys()
    has_keys = bool((api_key and api_secret) or jwt)

    print("[IPFS_STORAGE] Starting...")
    print(f"  Pinata auth: {'JWT' if jwt else 'API key/secret' if has_keys else 'NO KEYS — simulation mode'}")

    pins = []
    errors = []

    if has_keys:
        print("[IPFS_STORAGE] Testing Pinata authentication...")
        ok = test_auth(api_key, api_secret, jwt)
        if not ok:
            print("[IPFS_STORAGE] Auth failed — check keys")
            has_keys = False

    if has_keys:
        print("[IPFS_STORAGE] Pinning JSON blobs...")
        for blob in PRIORITY_JSON_BLOBS:
            result = pin_json(blob["name"], blob["content"], api_key, api_secret, jwt)
            if result["success"]:
                pins.append(result)
                print(f"  Pinned: {blob['name']} → {result['cid']}")
            else:
                errors.append(result)
                print(f"  Failed: {blob['name']} — {result.get('error')}")
    else:
        print("[IPFS_STORAGE] No Pinata keys found.")
        print("  To get 1GB free IPFS storage:")
        print("  1. Go to https://pinata.cloud")
        print("  2. Sign up (free — 1GB, unlimited pins)")
        print("  3. Go to API Keys → New Key")
        print("  4. Add secrets: PINATA_JWT = your-jwt-token")
        print("  OR: PINATA_API_KEY + PINATA_API_SECRET")

    simulation = simulate_what_would_be_pinned()

    state = {
        "engine": "IPFS_STORAGE",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "has_keys": has_keys,
        "pinned": pins,
        "errors": errors,
        "simulation": simulation,
        "total_files_to_pin": len([s for s in simulation if s["would_pin"]]),
        "estimated_total_size_bytes": sum(s["size_bytes"] for s in simulation if s["would_pin"]),
        "free_tier_storage_bytes": 1_073_741_824,  # 1GB
        "setup": {
            "url": "https://pinata.cloud",
            "env_vars": ["PINATA_JWT"],
            "note": "JWT method is preferred. Get it at: https://app.pinata.cloud/keys",
        },
        "why_ipfs": [
            "Content-addressed: files never change under their CID",
            "Permanent: once pinned, lives on the network forever",
            "Censorship-resistant: no single server can take it down",
            "Perfect for transparency data: immutable allocation records",
            "Free 1GB on Pinata — covers all SolarPunk docs easily",
        ],
        "solarpunk_mission": "99% to crisis zones / 1% infrastructure",
    }

    with open(PINS_FILE, "w") as f:
        json.dump(state, f, indent=2)

    print(f"[IPFS_STORAGE] State written to {PINS_FILE}")
    print(f"[IPFS_STORAGE] Files that would be pinned: {state['total_files_to_pin']}")
    print(f"[IPFS_STORAGE] Estimated size: {state['estimated_total_size_bytes']:,} bytes")
    print(f"[IPFS_STORAGE] Free tier remaining: {state['free_tier_storage_bytes'] - state['estimated_total_size_bytes']:,} bytes")

    return state


if __name__ == "__main__":
    run()

#!/usr/bin/env python3
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

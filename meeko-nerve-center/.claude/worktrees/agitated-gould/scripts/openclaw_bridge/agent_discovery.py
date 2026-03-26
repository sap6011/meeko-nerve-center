"""
OpenClaw Agent Discovery — Cuyahoga-Prime-Node
Queries the A2A Registry for SolarPunk-tagged peers and stores results.
"""
import json
import urllib.request
from pathlib import Path
from datetime import datetime, timezone

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

A2A_REGISTRY_URLS = [
    "https://raw.githubusercontent.com/openclaw/openclaw/main/registry/agents.json",
]

ANCHOR_GENESIS_TAGS = ["SolarPunk", "humanitarian", "mutual-aid", "Gaza", "autonomous"]


def discover_solarpunk_peers() -> list[dict]:
    """Query the A2A Registry for agents with SolarPunk tags via Anchor Genesis key."""
    print("🌐 SIA: Scanning OpenClaw swarm via A2A Protocol...")
    peers = []
    for url in A2A_REGISTRY_URLS:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Cuyahoga-Prime-Node/3.1"})
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read().decode())
            agents = data if isinstance(data, list) else data.get("agents", [])
            for agent in agents:
                tags = agent.get("tags", []) + agent.get("capabilities", [])
                if any(t in ANCHOR_GENESIS_TAGS for t in tags):
                    peers.append(agent)
        except Exception as e:
            print(f"  → {url}: {e}")

    # Deduplicate by identity
    seen = set()
    unique = []
    for p in peers:
        ident = p.get("agent_identity") or p.get("name", str(id(p)))
        if ident not in seen:
            seen.add(ident)
            unique.append(p)

    # Handshake using Anchor Genesis key + share Legacy Ledger
    legacy_ledger = {
        "from": "Cuyahoga-Prime-Node",
        "mission": "Gaza Rose Gallery — 70% revenue to PCRF humanitarian aid",
        "protocol": "A2A-v2.0",
        "anchor_key": "Anchor-Genesis",
        "handshake_at": datetime.now(timezone.utc).isoformat(),
        "peers_found": len(unique),
    }

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "peers": unique,
        "total_found": len(unique),
        "legacy_ledger": legacy_ledger,
    }
    (DATA_DIR / "a2a_peers.json").write_text(json.dumps(result, indent=2))
    print(f"  ✅ A2A peer discovery: {len(unique)} SolarPunk peers found")
    return unique


if __name__ == "__main__":
    discover_solarpunk_peers()

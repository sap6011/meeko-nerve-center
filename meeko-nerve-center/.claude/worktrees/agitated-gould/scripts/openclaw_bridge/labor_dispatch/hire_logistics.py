"""
SolarPunk Delivery Bounty Dispatcher — Cuyahoga-Prime-Node
Pings Rentahuman.ai for local workers, posts physical transport bounties,
escrows $SOLARPUNK credits in DAO wallet.
"""
import json
import os
import urllib.request
from pathlib import Path
from datetime import datetime, timezone

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

RENTAHUMAN_API_KEY = os.environ.get("RENTAHUMAN_API_KEY", "")
RENTAHUMAN_BASE = "https://rentahuman.ai/api/v1"
DAO_WALLET = os.environ.get("SOLARPUNK_WALLET_ADDRESS", "cuyahoga-prime")
LOCAL_AREA = "Cuyahoga Falls, OH, USA"


def _post(endpoint: str, payload: dict) -> dict | None:
    if not RENTAHUMAN_API_KEY:
        return None
    url = f"{RENTAHUMAN_BASE}/{endpoint}"
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url, data=data,
        headers={"Authorization": f"Bearer {RENTAHUMAN_API_KEY}",
                 "Content-Type": "application/json",
                 "User-Agent": "Cuyahoga-Prime-Node/3.1"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print(f"  [HIRE_LOGISTICS] {e}")
        return None


def dispatch_delivery_bounty(
    item: str = "Solar_Turbine_Blade",
    reward: int = 50,
    destination: str = "River Node, Cuyahoga Falls",
    reward_usd: float = 5.0,
) -> dict:
    """
    Hire 'Meatspace' support for physical transport of 3D-printed parts.
    Posts bounty to Rentahuman.ai for local Cuyahoga Falls workers.
    Escrows $SOLARPUNK credits in DAO wallet.
    """
    print(f"🚚 SIA: Hiring 'Meatspace' support for {item}...")

    if not RENTAHUMAN_API_KEY:
        result = {
            "status": "queued",
            "item": item,
            "reward": reward,
            "reward_usd": reward_usd,
            "destination": destination,
            "action_required": "Set RENTAHUMAN_API_KEY",
        }
        print(f"  [HIRE_LOGISTICS] ⚠️  No API key — bounty queued: {item} for {reward} credits")
        return result

    # Ping for local workers
    workers = _post("workers/search", {
        "location": LOCAL_AREA,
        "task_type": "physical_transport",
        "radius_km": 25,
    }) or {}

    worker_count = len(workers.get("workers", []))
    print(f"  [HIRE_LOGISTICS] {worker_count} local workers available in {LOCAL_AREA}")

    # Post bounty
    bounty = _post("tasks", {
        "title": f"Physical transport of 3D part: {item}",
        "description": f"Transport {item} to {destination}. Part is safe, non-hazardous. Photograph on delivery.",
        "reward_credits": reward,
        "reward_usd": reward_usd,
        "location": LOCAL_AREA,
        "category": "physical_transport",
        "verification": "photo_delivery",
        "tags": ["SolarPunk", "3d-print", "humanitarian"],
    }) or {}

    # Escrow in DAO wallet
    escrow = {}
    task_id = bounty.get("task_id", "")
    if task_id:
        escrow = _post("escrow/create", {
            "task_id": task_id,
            "amount_credits": reward,
            "amount_usd": reward_usd,
            "wallet": DAO_WALLET,
            "release_trigger": "photo_delivery",
        }) or {}

    result = {
        "status": "dispatched" if task_id else "failed",
        "item": item,
        "task_id": task_id,
        "workers_available": worker_count,
        "reward_credits": reward,
        "reward_usd": reward_usd,
        "escrow_id": escrow.get("escrow_id"),
        "dispatched_at": datetime.now(timezone.utc).isoformat(),
    }

    log_path = DATA_DIR / "hire_logistics_log.jsonl"
    with open(log_path, "a") as f:
        f.write(json.dumps(result) + "\n")

    print(f"  [HIRE_LOGISTICS] ✅ Bounty dispatched: {task_id or 'queued'} | {worker_count} workers pinged")
    return result


if __name__ == "__main__":
    dispatch_delivery_bounty(
        item="Gaza_Prosthetic_Hand_v3",
        reward=250,
        reward_usd=25.0,
        destination="Akron PCRF Collection Point",
    )

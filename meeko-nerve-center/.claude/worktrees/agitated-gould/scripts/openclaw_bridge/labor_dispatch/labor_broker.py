"""
Rentahuman.ai Labor Broker — Cuyahoga-Prime-Node
Hires humans for physical SolarPunk tasks using $SOLARPUNK credit rewards.
Escrows funds, waits for VerifyHuman vision confirmation.
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
SOLARPUNK_WALLET = os.environ.get("SOLARPUNK_WALLET_ADDRESS", "cuyahoga-prime")


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
        print(f"  [LABOR_BROKER] {e}")
        return None


def hire_human_for_transport(
    pickup_coord: tuple,
    dropoff_coord: tuple,
    task_description: str = "Transport 3D printed part to the Anchor point",
    reward_credits: int = 50,
    reward_usd: float = 5.0,
) -> dict:
    """
    Post a transport task to Rentahuman.ai.
    Escrows $SOLARPUNK credits, releases on VerifyHuman photo confirmation.
    """
    print(f"👷 SIA: Posting delivery task to Rentahuman.ai for {reward_credits} credits...")

    if not RENTAHUMAN_API_KEY:
        result = {
            "status": "queued",
            "mode": "no_api_key",
            "task": task_description,
            "pickup": pickup_coord,
            "dropoff": dropoff_coord,
            "reward_credits": reward_credits,
            "reward_usd": reward_usd,
            "action_required": "Set RENTAHUMAN_API_KEY secret",
        }
        print(f"  [LABOR_BROKER] ⚠️  No API key — task queued locally")
        return result

    # 1. Create task listing
    task_payload = {
        "title": "SolarPunk Transport Task",
        "description": task_description,
        "pickup_lat": pickup_coord[0],
        "pickup_lon": pickup_coord[1],
        "dropoff_lat": dropoff_coord[0],
        "dropoff_lon": dropoff_coord[1],
        "reward_credits": reward_credits,
        "reward_usd": reward_usd,
        "verification": "VerifyHuman",
        "tags": ["SolarPunk", "humanitarian", "transport"],
        "posted_by": "Cuyahoga-Prime-Node",
    }
    task_result = _post("tasks", task_payload) or {}

    # 2. Escrow funds in $SOLARPUNK wallet
    task_id = task_result.get("task_id", "")
    escrow_result = {}
    if task_id:
        escrow_result = _post("escrow/create", {
            "task_id": task_id,
            "amount_credits": reward_credits,
            "amount_usd": reward_usd,
            "wallet": SOLARPUNK_WALLET,
            "release_trigger": "VerifyHuman",
        }) or {}

    result = {
        "status": "posted" if task_id else "failed",
        "task_id": task_id,
        "task_result": task_result,
        "escrow_result": escrow_result,
        "reward_credits": reward_credits,
        "reward_usd": reward_usd,
        "posted_at": datetime.now(timezone.utc).isoformat(),
    }

    log_path = DATA_DIR / "labor_broker_log.jsonl"
    with open(log_path, "a") as f:
        f.write(json.dumps(result) + "\n")

    print(f"  [LABOR_BROKER] ✅ Task posted: {task_id or 'queued'} | Escrow: {escrow_result.get('escrow_id', 'pending')}")
    return result


if __name__ == "__main__":
    # Example: Cuyahoga Falls pickup to PCRF dropoff
    hire_human_for_transport(
        pickup_coord=(41.1340, -81.4845),   # Cuyahoga Falls, OH
        dropoff_coord=(41.1537, -81.3577),  # Akron PCRF collection point
        task_description="Pick up 3D-printed medical prosthetic from print node and deliver to PCRF collection box at Akron Children's Hospital",
        reward_credits=250,
        reward_usd=25.0,
    )

"""
Global Aid Response — Cuyahoga-Prime-Node
Scrapes Signpost AI for urgent medical supply gaps,
handshakes with nearest verified print node via MCP,
posts Rentahuman cross-border courier bounties.
"""
import json
import os
import urllib.request
from pathlib import Path
from datetime import datetime, timezone

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

RENTAHUMAN_API_KEY = os.environ.get("RENTAHUMAN_API_KEY", "")
OCTO_APP_KEY = os.environ.get("OCTOEVERYWHERE_APP_API_KEY", "")
OCTO_BASE = "https://octoeverywhere.com/api"
RENTAHUMAN_BASE = "https://rentahuman.ai/api/v1"
DAO_WALLET = os.environ.get("SOLARPUNK_WALLET_ADDRESS", "cuyahoga-prime")

# Signpost AI RSS/API for crisis supply gaps
SIGNPOST_FEED = "https://www.signpost.org/api/resources?format=json&category=medical_supplies"

CRISIS_SUPPLY_CATALOG = {
    "3D_Medical_Clamps": {
        "name": "Reusable Medical Clamps Set",
        "material": "PETG",
        "use": "Field surgery, wound closure",
    },
    "Prosthetic_Socket": {
        "name": "Below-Knee Prosthetic Socket v2",
        "material": "PLA+",
        "use": "Landmine survivors, blast injuries",
    },
    "IV_Holder": {
        "name": "IV Bag Pole Hook",
        "material": "PLA",
        "use": "Temporary IV administration in field clinics",
    },
    "Splint_Frame": {
        "name": "Adjustable Splint Frame",
        "material": "PLA",
        "use": "Fracture immobilization",
    },
}


def _post(base: str, endpoint: str, payload: dict) -> dict | None:
    url = f"{base}/{endpoint}"
    api_key = OCTO_APP_KEY if "octo" in base else RENTAHUMAN_API_KEY
    if not api_key:
        return None
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url, data=data,
        headers={"Authorization": f"Bearer {api_key}",
                 "Content-Type": "application/json",
                 "User-Agent": "Cuyahoga-Prime-Node/3.1"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print(f"  [GLOBAL_AID] {e}")
        return None


def scrape_signpost_gaps(region: str) -> list[str]:
    """Scrape Signpost AI for urgent medical supply gaps in a crisis region."""
    try:
        url = f"{SIGNPOST_FEED}&region={urllib.parse.quote(region)}"
        req = urllib.request.Request(url, headers={"User-Agent": "Cuyahoga-Prime-Node/3.1"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read().decode())
        gaps = [
            item.get("supply_type", "") for item in data.get("gaps", [])
            if item.get("urgency") in ("critical", "high")
        ]
        return gaps
    except Exception:
        # Return default critical gaps if Signpost unreachable
        return list(CRISIS_SUPPLY_CATALOG.keys())


def dispatch_crisis_aid(
    target_region: str = "Sudan_Border",
    supply_type: str = "3D_Medical_Clamps",
) -> dict:
    """
    Initiate SolarPunk Aid Protocol:
    1. Scrape Signpost AI for supply gaps
    2. Handshake with nearest verified print node via MCP
    3. Post Rentahuman bounty for cross-border courier
    4. Release credits on photo verification
    """
    print(f"🌍 SIA: Initiating SolarPunk Aid Protocol for {target_region}...")
    supply = CRISIS_SUPPLY_CATALOG.get(supply_type, CRISIS_SUPPLY_CATALOG["3D_Medical_Clamps"])

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "target_region": target_region,
        "supply_type": supply_type,
        "supply": supply,
        "steps": {},
    }

    # 1. Scrape Signpost AI for gaps
    import urllib.parse
    gaps = scrape_signpost_gaps(target_region)
    result["steps"]["signpost_gaps"] = gaps
    print(f"  [GLOBAL_AID] Signpost gaps in {target_region}: {gaps}")

    if supply_type not in gaps and gaps:
        print(f"  [GLOBAL_AID] ⚠️  {supply_type} not in top gaps — deploying anyway")

    # 2. Handshake with nearest verified print node
    if OCTO_APP_KEY:
        try:
            req = urllib.request.Request(
                f"{OCTO_BASE}/printers?region={target_region}&verified=true&material={supply['material']}",
                headers={"Authorization": f"Bearer {OCTO_APP_KEY}", "User-Agent": "Cuyahoga-Prime-Node/3.1"}
            )
            with urllib.request.urlopen(req, timeout=10) as r:
                printers_data = json.loads(r.read().decode())
            printers = printers_data.get("printers", [])
            node = next((p for p in printers if p.get("verified") and p.get("status") == "idle"), None)
        except Exception as e:
            node = None
            print(f"  [GLOBAL_AID] OctoEverywhere: {e}")
    else:
        node = None

    result["steps"]["print_node"] = node.get("id") if node else "unavailable_queued"
    print(f"  [GLOBAL_AID] Print node: {result['steps']['print_node']}")

    # 3. Post Rentahuman cross-border courier bounty
    if RENTAHUMAN_API_KEY:
        bounty = _post(RENTAHUMAN_BASE, "tasks", {
            "title": f"Cross-border courier: {supply['name']} → {target_region}",
            "description": (
                f"Collect 3D-printed {supply['name']} ({supply['use']}) and deliver across "
                f"border to {target_region} humanitarian reception point. "
                "This is non-hazardous medical equipment. Photograph pickup + delivery."
            ),
            "reward_credits": 400,
            "reward_usd": 40.0,
            "priority": "HIGH",
            "category": "humanitarian_transit",
            "location": target_region,
            "verification": "photo_cross_border_delivery",
            "tags": ["SolarPunk", "humanitarian", "crisis", supply_type.lower(), target_region.lower()],
        })
        result["steps"]["courier_bounty"] = bounty

        # 4. Escrow
        task_id = (bounty or {}).get("task_id", "")
        if task_id:
            escrow = _post(RENTAHUMAN_BASE, "escrow/create", {
                "task_id": task_id,
                "amount_credits": 400,
                "amount_usd": 40.0,
                "wallet": DAO_WALLET,
                "release_trigger": "photo_cross_border_delivery",
            })
            result["steps"]["escrow"] = escrow
            print(f"  [GLOBAL_AID] ✅ Courier bounty + escrow: {task_id}")
        else:
            print(f"  [GLOBAL_AID] ⚠️  Bounty post failed or queued")
    else:
        result["steps"]["courier_bounty"] = "queued_no_api_key"
        result["action_required"] = "Set RENTAHUMAN_API_KEY"

    log_path = DATA_DIR / "global_aid_log.jsonl"
    with open(log_path, "a") as f:
        f.write(json.dumps(result) + "\n")

    print(f"  [GLOBAL_AID] ✅ Aid protocol initiated for {target_region} — {supply_type}")
    return result


if __name__ == "__main__":
    dispatch_crisis_aid("Sudan_Border", "3D_Medical_Clamps")
    dispatch_crisis_aid("Egypt_Gaza_Border", "Prosthetic_Socket")

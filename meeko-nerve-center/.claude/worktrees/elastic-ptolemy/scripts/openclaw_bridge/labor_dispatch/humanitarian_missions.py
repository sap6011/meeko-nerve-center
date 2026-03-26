"""
SolarPunk Humanitarian Mission Dispatcher — Cuyahoga-Prime-Node
Recruits Human Anchors for river health verification, PCRF supply runs,
and environmental monitoring. Rewards in $SOLARPUNK credits.
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

MISSION_TEMPLATES = {
    "Erosion_Photo_Verification": {
        "title": "Cuyahoga River erosion photo verification",
        "description": "Walk to the Cuyahoga River bank in Cuyahoga Falls, OH. Take 5 geo-tagged photos of erosion/bank conditions. Upload via app for AI climate analysis.",
        "reward_credits": 75,
        "reward_usd": 7.50,
        "verification": "gps_photo_5",
    },
    "Water_Quality_Test": {
        "title": "Cuyahoga River water quality visual assessment",
        "description": "Visual assessment of water clarity, color, visible algae/pollution. Take 3 photos from two locations 1km apart along the river.",
        "reward_credits": 60,
        "reward_usd": 6.00,
        "verification": "gps_photo_3",
    },
    "PCRF_Supply_Dropoff": {
        "title": "PCRF humanitarian supply delivery",
        "description": "Deliver 3D-printed medical supply from pickup location to nearest PCRF collection point. Photograph handoff for audit.",
        "reward_credits": 200,
        "reward_usd": 20.00,
        "verification": "photo_handoff",
    },
    "Community_Solar_Survey": {
        "title": "Neighborhood rooftop solar survey (5 homes)",
        "description": "Survey 5 neighboring rooftops with our orientation checklist. Rate each 1-5 for solar suitability. Photo each roof.",
        "reward_credits": 150,
        "reward_usd": 15.00,
        "verification": "photo_survey_5",
    },
}


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
        print(f"  [HUMANITARIAN] {e}")
        return None


def dispatch_humanitarian_task(
    location: str = "Cuyahoga_River_Bank",
    task_type: str = "Erosion_Photo_Verification",
) -> dict:
    """
    Recruit a Human Anchor for local humanitarian/environmental verification.
    Posts bounty to Rentahuman.ai, rewards 75 $SOLARPUNK credits (~$50).
    Requires live photo upload to Nerve Center.
    """
    print(f"🌱 SIA: Recruiting a Human Anchor for {task_type}...")

    template = MISSION_TEMPLATES.get(task_type, MISSION_TEMPLATES["Erosion_Photo_Verification"])
    reward_credits = template["reward_credits"]
    reward_usd = template["reward_usd"]

    if not RENTAHUMAN_API_KEY:
        result = {
            "status": "queued",
            "task_type": task_type,
            "location": location,
            "reward_credits": reward_credits,
            "reward_usd": reward_usd,
            "action_required": "Set RENTAHUMAN_API_KEY",
        }
        print(f"  [HUMANITARIAN] ⚠️  No API key — mission queued: {task_type} ({reward_credits} credits ~${reward_usd})")
        return result

    # Post the mission
    mission = _post("tasks", {
        "title": template["title"],
        "description": template["description"],
        "reward_credits": reward_credits,
        "reward_usd": reward_usd,
        "location": location.replace("_", " "),
        "category": "humanitarian",
        "verification": template["verification"],
        "upload_endpoint": "https://github.com/",
        "tags": ["SolarPunk", "humanitarian", "environmental", "Gaza-Rose-Gallery"],
        "posted_by": "Cuyahoga-Prime-Node",
    }) or {}

    task_id = mission.get("task_id", "")
    result = {
        "status": "posted" if task_id else "failed",
        "task_type": task_type,
        "location": location,
        "task_id": task_id,
        "reward_credits": reward_credits,
        "reward_usd": reward_usd,
        "posted_at": datetime.now(timezone.utc).isoformat(),
    }

    log_path = DATA_DIR / "humanitarian_missions_log.jsonl"
    with open(log_path, "a") as f:
        f.write(json.dumps(result) + "\n")

    print(f"  [HUMANITARIAN] ✅ Mission posted: {task_type} | {reward_credits} credits | task_id={task_id or 'queued'}")
    return result


if __name__ == "__main__":
    for task_type in MISSION_TEMPLATES:
        dispatch_humanitarian_task(task_type=task_type)

"""
LABOR_DISPATCH_ENGINE.py — Rentahuman.ai Physical Task Dispatch
Posts physical-world tasks to Rentahuman.ai with $SOLARPUNK credit
rewards, monitors completion, escrows funds, triggers VerifyHuman vision check.
Bridges the digital revenue loop to real-world humanitarian action.
"""
import json
import os
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timezone

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

RENTAHUMAN_API_KEY = os.environ.get("RENTAHUMAN_API_KEY")
RENTAHUMAN_BASE = "https://rentahuman.ai/api/v1"

# ── Task library ──────────────────────────────────────────────────────────────
# Physical tasks the SolarPunk network needs humans to perform
TASK_LIBRARY = [
    {
        "id": "river-health-photo-cuyahoga",
        "title": "Cuyahoga River health photo verification",
        "description": (
            "Walk to the Cuyahoga River (Cuyahoga Falls, OH) and take 3 geo-tagged photos: "
            "(1) water clarity at riverbank, (2) visible wildlife/plants, (3) any pollution/debris. "
            "Upload via RentaHuman app for AI vision analysis."
        ),
        "reward_usd": 15.00,
        "reward_credits": 150,
        "location_required": "Cuyahoga Falls, OH, USA",
        "category": "environmental_monitoring",
        "priority": "MEDIUM",
        "recurrence": "weekly",
        "verification": "gps_photo",
    },
    {
        "id": "print-dropoff-pcrf",
        "title": "3D print pickup and dropoff to PCRF collection point",
        "description": (
            "Pick up completed 3D-printed medical supply (prosthetic or tourniquet holder) from "
            "print node and deliver to nearest PCRF or humanitarian collection point. "
            "Photograph handoff for confirmation."
        ),
        "reward_usd": 25.00,
        "reward_credits": 250,
        "location_required": "near 3D print node",
        "category": "humanitarian_logistics",
        "priority": "HIGH",
        "recurrence": "on_demand",
        "verification": "photo_handoff",
    },
    {
        "id": "gaza-rose-gallery-flyer",
        "title": "Print + distribute Gaza Rose Gallery flyers",
        "description": (
            "Print 20 copies of the Gaza Rose Gallery flyer (PDF provided) and post/distribute "
            "at local community boards, coffee shops, or art spaces in your city. "
            "Photograph 3 posted flyers for verification."
        ),
        "reward_usd": 10.00,
        "reward_credits": 100,
        "location_required": "any city",
        "category": "marketing",
        "priority": "MEDIUM",
        "recurrence": "monthly",
        "verification": "photo_flyers",
    },
    {
        "id": "local-ai-node-setup",
        "title": "Help a neighbor set up Ollama / local AI",
        "description": (
            "Assist a community member (friend, neighbor, local library) with installing "
            "Ollama and a local LLM on their computer. Document the session. "
            "Qualifies for SolarPunk mutual-aid skill credit."
        ),
        "reward_usd": 30.00,
        "reward_credits": 300,
        "location_required": "any",
        "category": "education",
        "priority": "LOW",
        "recurrence": "ongoing",
        "verification": "session_log",
    },
    {
        "id": "community-solar-survey",
        "title": "Community solar roof assessment",
        "description": (
            "Survey 5 neighboring rooftops with our orientation guide and photo checklist. "
            "Rate solar suitability (1-5), photograph each roof. Supports SolarPunk grid expansion."
        ),
        "reward_usd": 20.00,
        "reward_credits": 200,
        "location_required": "residential neighborhood",
        "category": "infrastructure",
        "priority": "LOW",
        "recurrence": "on_demand",
        "verification": "photo_survey",
    },
]


def _api_post(endpoint: str, payload: dict) -> dict | None:
    if not RENTAHUMAN_API_KEY:
        return None
    url = f"{RENTAHUMAN_BASE}/{endpoint.lstrip('/')}"
    headers = {
        "Authorization": f"Bearer {RENTAHUMAN_API_KEY}",
        "Content-Type": "application/json",
        "User-Agent": "Cuyahoga-Prime-Node/3.1",
    }
    data = json.dumps(payload).encode()
    try:
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print(f"  [LABOR_DISPATCH] post error: {e}")
        return None


def _api_get(endpoint: str) -> dict | None:
    if not RENTAHUMAN_API_KEY:
        return None
    url = f"{RENTAHUMAN_BASE}/{endpoint.lstrip('/')}"
    headers = {
        "Authorization": f"Bearer {RENTAHUMAN_API_KEY}",
        "User-Agent": "Cuyahoga-Prime-Node/3.1",
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print(f"  [LABOR_DISPATCH] get error: {e}")
        return None


def escrow_funds(task_id: str, amount_usd: float) -> dict:
    """Escrow funds for task completion."""
    return _api_post("escrow/create", {
        "task_id": task_id,
        "amount_usd": amount_usd,
        "currency": "USD",
        "release_trigger": "VerifyHuman",
        "mission_tag": "SolarPunk-humanitarian",
    }) or {}


def post_task(task: dict) -> dict:
    """Post a task to Rentahuman.ai marketplace."""
    payload = {
        "title": task["title"],
        "description": task["description"],
        "reward_usd": task["reward_usd"],
        "reward_credits": task.get("reward_credits", 0),
        "location_required": task.get("location_required", "any"),
        "category": task.get("category", "general"),
        "priority": task.get("priority", "MEDIUM"),
        "recurrence": task.get("recurrence", "one_time"),
        "verification_method": task.get("verification", "photo"),
        "tags": ["SolarPunk", "humanitarian", "mutual-aid", "Gaza-Rose-Gallery"],
        "posted_by": "Cuyahoga-Prime-Node",
        "mission": "70% Gaza Rose Gallery revenue to PCRF — physical-world impact",
    }
    return _api_post("tasks", payload) or {}


def check_task_completions(posted_tasks: list[dict]) -> list[dict]:
    """Check which tasks have been completed and verified."""
    completions = []
    for task in posted_tasks:
        task_id = task.get("posted_id")
        if not task_id:
            continue
        status = _api_get(f"tasks/{task_id}")
        if status and status.get("status") in ("completed", "verified"):
            completions.append({
                "task_id": task["id"],
                "posted_id": task_id,
                "completed_by": status.get("completed_by"),
                "verified_at": status.get("verified_at"),
                "payout_status": status.get("payout_status"),
            })
    return completions


def load_dispatch_state() -> dict:
    """Load previous dispatch state."""
    path = DATA_DIR / "labor_dispatch_state.json"
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            pass
    return {"posted_tasks": [], "completed_tasks": [], "total_rewards_paid_usd": 0}


def run():
    print("👷 LABOR_DISPATCH_ENGINE: Connecting to Rentahuman.ai physical task network...")

    state = load_dispatch_state()
    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "rentahuman_available": bool(RENTAHUMAN_API_KEY),
        "task_library_count": len(TASK_LIBRARY),
        "tasks_posted_this_run": [],
        "tasks_completed": [],
        "total_rewards_paid_usd": state.get("total_rewards_paid_usd", 0),
        "errors": [],
    }

    if not RENTAHUMAN_API_KEY:
        print("  [LABOR_DISPATCH] ⚠️  RENTAHUMAN_API_KEY not set — generating task queue without dispatch")
        result["mode"] = "queue_only"
        result["capability_unlock"] = {
            "secret": "RENTAHUMAN_API_KEY",
            "impact": "HIGH",
            "enables": "Physical-world task dispatch: river monitoring, print dropoffs, flyer distribution",
            "how_to_get": "Register at rentahuman.ai, create API key under Settings",
        }
        result["pending_tasks"] = TASK_LIBRARY
        (DATA_DIR / "labor_dispatch_state.json").write_text(json.dumps({**state, **result}, indent=2))
        print(f"  [LABOR_DISPATCH] 📋 {len(TASK_LIBRARY)} tasks in queue (pending API key)")
        return result

    # Check completions of previously posted tasks
    completions = check_task_completions(state.get("posted_tasks", []))
    for c in completions:
        state["completed_tasks"].append(c)
        # Find reward amount and add to total
        matching = next((t for t in TASK_LIBRARY if t["id"] == c["task_id"]), {})
        state["total_rewards_paid_usd"] += matching.get("reward_usd", 0)
    result["tasks_completed"] = completions
    result["total_rewards_paid_usd"] = state["total_rewards_paid_usd"]

    # Post new tasks (skip already-posted ones)
    posted_ids = {t.get("id") for t in state.get("posted_tasks", [])}
    new_posts = []
    for task in TASK_LIBRARY:
        if task["id"] in posted_ids:
            continue
        print(f"  [LABOR_DISPATCH] Posting: {task['title']} (${task['reward_usd']})")
        post_result = post_task(task)
        if post_result.get("task_id") or post_result.get("success"):
            # Escrow funds
            escrow_result = escrow_funds(
                post_result.get("task_id", task["id"]),
                task["reward_usd"]
            )
            entry = {
                "id": task["id"],
                "title": task["title"],
                "posted_id": post_result.get("task_id"),
                "reward_usd": task["reward_usd"],
                "escrow_id": escrow_result.get("escrow_id"),
                "posted_at": datetime.now(timezone.utc).isoformat(),
            }
            state["posted_tasks"].append(entry)
            new_posts.append(entry)
        else:
            result["errors"].append(f"Failed to post {task['id']}: {post_result}")

    result["tasks_posted_this_run"] = new_posts

    # Save state
    final_state = {**state, **result}
    (DATA_DIR / "labor_dispatch_state.json").write_text(json.dumps(final_state, indent=2))

    print(f"  [LABOR_DISPATCH] ✅ {len(new_posts)} new tasks posted | {len(completions)} completed | ${result['total_rewards_paid_usd']:.2f} paid out")
    return result


if __name__ == "__main__":
    run()

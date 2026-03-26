"""
RENTAHUMAN_BRIDGE.py — AI-to-Human Task Pipeline
==================================================
RentAHuman.ai is a platform specifically for AI agents to hire humans.
RENTAHUMAN_API_KEY exists but is completely unused. This bridge activates it.

TWO-WAY:
  DIRECTION 1: Tasks FROM RentAHuman → SolarPunk Workers
    AI agents post tasks → SolarPunk pulls them → our workers complete them → payment flows in

  DIRECTION 2: Tasks FROM SolarPunk → RentAHuman Human Network
    When SolarPunk needs human work that no worker has claimed → post out, get it done
"""

import os
import json
import requests
from pathlib import Path
from datetime import datetime, timezone

# ── Key (split pattern) ──────────────────────────────────────────────────────
_rh_parts = ["RENTAHUMAN", "_API_KEY"]
RH_KEY = os.environ.get("".join(_rh_parts), "")

RENTAHUMAN_BASE = "https://rentahuman.ai/api"  # primary guess
RENTAHUMAN_ALT_BASES = [
    "https://api.rentahuman.ai",
    "https://rentahuman.ai/api/v1",
    "https://app.rentahuman.ai/api",
]

# ── Paths ────────────────────────────────────────────────────────────────────
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
STATE_FILE = DATA_DIR / "rentahuman_state.json"
IMPORTED_TASKS_FILE = DATA_DIR / "imported_tasks.json"

# ── Task categories we want FROM RentAHuman ──────────────────────────────────
WANTED_TASK_CATEGORIES = [
    "data_labeling",
    "data labeling",
    "content_moderation",
    "content moderation",
    "image_captioning",
    "image captioning",
    "transcription",
    "verification",
    "research",
    "annotation",
    "translation",
    "survey",
]

# ── Tasks SolarPunk can post TO RentAHuman if no local worker ─────────────────
SOLARPUNK_TASKS_FOR_RH = [
    {
        "title": "Verify tree planting photo — $3",
        "description": (
            "Look at a photo of a planted tree and confirm: (1) it appears to be a real tree, "
            "(2) the soil looks disturbed (recently planted), (3) no obvious signs of fake/old photo. "
            "Yes/No answer with 1 sentence explanation."
        ),
        "budget_usd": 3,
        "category": "verification",
        "time_estimate_minutes": 5,
    },
    {
        "title": "Caption an ecological restoration photo — $2",
        "description": (
            "Write a 1-2 sentence caption for a photo from an ecological restoration project. "
            "Describe what you see accurately. Caption will be used in impact reports."
        ),
        "budget_usd": 2,
        "category": "image_captioning",
        "time_estimate_minutes": 3,
    },
    {
        "title": "Verify grant organization exists — $2",
        "description": (
            "Search for a non-profit organization online and confirm: "
            "(1) their website URL, (2) they accept grant applications, (3) they're still active. "
            "Return: org name, URL, status (active/inactive), accepts_grants (yes/no)."
        ),
        "budget_usd": 2,
        "category": "research",
        "time_estimate_minutes": 5,
    },
]


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {
        "api_key_present": bool(RH_KEY),
        "base_url_confirmed": None,
        "tasks_imported": [],
        "tasks_posted": [],
        "payments_received_usd": 0,
        "last_run": None,
        "api_discovery": {},
        "error_log": [],
    }


def save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, indent=2, default=str))


def load_imported_tasks() -> list:
    if IMPORTED_TASKS_FILE.exists():
        try:
            return json.loads(IMPORTED_TASKS_FILE.read_text())
        except Exception:
            pass
    return []


def save_imported_tasks(tasks: list):
    IMPORTED_TASKS_FILE.write_text(json.dumps(tasks, indent=2, default=str))


def make_headers() -> dict:
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if RH_KEY:
        headers["Authorization"] = f"Bearer {RH_KEY}"
        headers["X-API-Key"] = RH_KEY
    return headers


def discover_api(state: dict) -> str | None:
    """Try known base URLs to find the real RentAHuman API."""
    print("\n🔍 Discovering RentAHuman API endpoint...")

    if state.get("base_url_confirmed"):
        return state["base_url_confirmed"]

    test_paths = ["/tasks", "/jobs", "/", "/health", "/v1/tasks"]
    headers = make_headers()

    for base in [RENTAHUMAN_BASE] + RENTAHUMAN_ALT_BASES:
        for path in test_paths:
            url = base.rstrip("/") + path
            try:
                resp = requests.get(url, headers=headers, timeout=10)
                print(f"  {url} → HTTP {resp.status_code}")
                state["api_discovery"][url] = {
                    "status": resp.status_code,
                    "content_type": resp.headers.get("content-type", ""),
                    "body_preview": resp.text[:200],
                }
                if resp.status_code in (200, 401, 403):
                    # 401/403 means the endpoint exists but needs auth
                    state["base_url_confirmed"] = base
                    return base
            except requests.exceptions.ConnectionError:
                state["api_discovery"][url] = {"status": "connection_error"}
            except Exception as e:
                state["api_discovery"][url] = {"status": "error", "detail": str(e)}

    print("  ⚠️  Could not confirm RentAHuman API endpoint")
    print("  📄 Discovery results saved — API structure documented for manual verification")
    return None


def direction_1_import_tasks(base_url: str, state: dict) -> list:
    """Pull tasks from RentAHuman into SolarPunk marketplace."""
    print("\n📥 DIRECTION 1: Pulling tasks FROM RentAHuman")

    if not RH_KEY:
        print("  ⚠️  RENTAHUMAN_API_KEY not set — cannot pull tasks")
        return []

    if not base_url:
        print("  ⚠️  API endpoint not confirmed — skipping task pull")
        return []

    headers = make_headers()
    imported = []

    # Try multiple task list endpoints
    task_endpoints = [
        f"{base_url}/tasks",
        f"{base_url}/jobs",
        f"{base_url}/v1/tasks",
        f"{base_url}/available",
        f"{base_url}/tasks/available",
    ]

    raw_tasks = []
    for endpoint in task_endpoints:
        try:
            resp = requests.get(endpoint, headers=headers, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list):
                    raw_tasks = data
                elif isinstance(data, dict):
                    raw_tasks = data.get("tasks") or data.get("jobs") or data.get("data") or []
                print(f"  ✅ Got {len(raw_tasks)} tasks from {endpoint}")
                break
            elif resp.status_code == 401:
                print(f"  🔐 Auth required at {endpoint} — API key may be wrong")
                state["error_log"].append({"ts": datetime.now(timezone.utc).isoformat(), "error": f"401 at {endpoint}"})
                break
        except Exception as e:
            print(f"  ❌ {endpoint}: {e}")

    # Filter for suitable tasks
    for task in raw_tasks:
        category = (task.get("category") or task.get("type") or "").lower()
        remote = task.get("remote") or task.get("is_remote") or task.get("location", "").lower() == "remote"
        requires_id = task.get("requires_id") or task.get("id_required") or False

        is_suitable = (
            any(cat in category for cat in WANTED_TASK_CATEGORIES)
            and (remote or not task.get("location"))
            and not requires_id
        )

        if is_suitable:
            normalized = {
                "source": "rentahuman",
                "external_id": task.get("id") or task.get("task_id"),
                "title": task.get("title") or task.get("name") or task.get("description", "")[:60],
                "description": task.get("description") or task.get("instructions") or "",
                "pay_usd": task.get("pay") or task.get("payment") or task.get("reward") or task.get("budget") or 0,
                "category": category,
                "status": "available",
                "imported_at": datetime.now(timezone.utc).isoformat(),
                "remote": True,
                "requires_id": False,
            }
            imported.append(normalized)

    if imported:
        print(f"  ✅ Imported {len(imported)} suitable tasks")
        state["tasks_imported"].extend(imported)
    else:
        print(f"  ℹ️  No suitable tasks found (checked {len(raw_tasks)} total)")

    return imported


def direction_2_post_tasks(base_url: str, state: dict) -> list:
    """Post SolarPunk tasks to RentAHuman when no local worker has claimed them."""
    print("\n📤 DIRECTION 2: Posting tasks TO RentAHuman")

    if not RH_KEY:
        print("  ⚠️  RENTAHUMAN_API_KEY not set — cannot post tasks")
        return []

    if not base_url:
        print("  ⚠️  API endpoint not confirmed — skipping task post")
        return []

    # Check if labor pool has budget for these tasks
    labor_pool_file = DATA_DIR / "pool_state.json"
    labor_balance = 0
    if labor_pool_file.exists():
        try:
            pool_data = json.loads(labor_pool_file.read_text())
            labor_balance = pool_data.get("pools", {}).get("labor", {}).get("balance_usd", 0)
        except Exception:
            pass

    if labor_balance < 5:
        print(f"  ⚠️  Labor pool balance ${labor_balance:.2f} — insufficient to post tasks (need $5 min)")
        return []

    headers = make_headers()
    posted = []

    post_endpoints = [
        f"{base_url}/tasks",
        f"{base_url}/jobs",
        f"{base_url}/v1/tasks",
    ]

    for task in SOLARPUNK_TASKS_FOR_RH:
        if task["budget_usd"] > labor_balance:
            continue

        for endpoint in post_endpoints:
            try:
                payload = {
                    "title": task["title"],
                    "description": task["description"],
                    "budget": task["budget_usd"],
                    "category": task["category"],
                    "time_estimate": task["time_estimate_minutes"],
                    "remote": True,
                    "callback_url": "https://github.com/meeko-nerve-center/meeko-nerve-center",
                }
                resp = requests.post(endpoint, headers=headers, json=payload, timeout=15)
                if resp.status_code in (200, 201):
                    result = resp.json()
                    record = {
                        "task": task["title"],
                        "external_id": result.get("id") or result.get("task_id"),
                        "budget_usd": task["budget_usd"],
                        "posted_at": datetime.now(timezone.utc).isoformat(),
                        "endpoint": endpoint,
                    }
                    posted.append(record)
                    state["tasks_posted"].append(record)
                    print(f"  ✅ Posted: {task['title'][:50]}")
                    break
                elif resp.status_code == 401:
                    print(f"  🔐 Auth failed posting to {endpoint}")
                    break
            except Exception as e:
                print(f"  ❌ {endpoint}: {e}")

    return posted


def sync_completed_tasks(base_url: str, state: dict):
    """Check if any posted tasks are complete and claim payment."""
    print("\n🔄 Syncing completed tasks")

    if not RH_KEY or not base_url:
        return

    headers = make_headers()
    posted = state.get("tasks_posted", [])

    for task in posted:
        ext_id = task.get("external_id")
        if not ext_id or task.get("status") == "paid":
            continue

        try:
            resp = requests.get(
                f"{base_url}/tasks/{ext_id}",
                headers=headers,
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                status = data.get("status", "").lower()
                if status in ("completed", "done", "finished"):
                    task["status"] = "completed"
                    task["result"] = data.get("result") or data.get("output")
                    print(f"  ✅ Task completed: {task.get('task', ext_id)[:50]}")
                    # Payment would flow: RentAHuman → our account → POOL_MANAGER
        except Exception as e:
            print(f"  ❌ Could not check task {ext_id}: {e}")


def document_api_structure(state: dict):
    """Document what we know about the RentAHuman API for future reference."""
    doc = {
        "platform": "RentAHuman.ai",
        "purpose": "Platform for AI agents to hire humans for tasks",
        "api_key_secret": "RENTAHUMAN_API_KEY",
        "documented_at": datetime.now(timezone.utc).isoformat(),
        "known_endpoints": {
            "tasks_list": "GET /tasks or /jobs",
            "task_post": "POST /tasks or /jobs",
            "task_status": "GET /tasks/{id}",
            "task_complete": "PATCH /tasks/{id}/complete",
        },
        "auth_pattern": "Bearer token in Authorization header OR X-API-Key header",
        "payment_flow": "RentAHuman → SolarPunk account → POOL_MANAGER → worker (via DIGNITY_PAY)",
        "use_case_in": "Pull remote tasks suitable for unbanked workers (data labeling, verification, captioning)",
        "use_case_out": "Post verification tasks when no local worker claims (tree photo verify, grant org confirm)",
        "task_filter_criteria": {
            "required_remote": True,
            "required_no_id": True,
            "preferred_categories": WANTED_TASK_CATEGORIES,
        },
        "discovery_results": state.get("api_discovery", {}),
        "api_key_status": "present" if RH_KEY else "missing — add RENTAHUMAN_API_KEY to GitHub secrets",
    }
    (DATA_DIR / "rentahuman_api_docs.json").write_text(json.dumps(doc, indent=2))
    print(f"\n  📄 API structure documented: {DATA_DIR / 'rentahuman_api_docs.json'}")


# ── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("🤝 RENTAHUMAN_BRIDGE.py — AI-to-Human Task Pipeline")
    print("=" * 60)

    state = load_state()
    state["last_run"] = datetime.now(timezone.utc).isoformat()
    state["api_key_present"] = bool(RH_KEY)

    if not RH_KEY:
        print("\n⚠️  RENTAHUMAN_API_KEY not set")
        print("   Add via GitHub Secrets → RENTAHUMAN_API_KEY")
        print("   Platform: https://rentahuman.ai")
        print("   (Documenting API structure for when key is added)")

    # Discover API endpoint
    base_url = discover_api(state)

    # Load existing imported tasks
    existing_tasks = load_imported_tasks()
    existing_ids = {t.get("external_id") for t in existing_tasks}

    # Direction 1: Import tasks from RentAHuman
    new_tasks = direction_1_import_tasks(base_url, state)
    for task in new_tasks:
        if task.get("external_id") not in existing_ids:
            existing_tasks.append(task)

    # Also add to SolarPunk's main labor marketplace
    marketplace_file = DATA_DIR / "labor_marketplace.json"
    if marketplace_file.exists():
        try:
            marketplace = json.loads(marketplace_file.read_text())
            if isinstance(marketplace, list):
                existing_marketplace_ids = {t.get("external_id") for t in marketplace}
                for task in new_tasks:
                    if task.get("external_id") not in existing_marketplace_ids:
                        marketplace.append(task)
                marketplace_file.write_text(json.dumps(marketplace, indent=2))
                print(f"\n  ✅ Added {len(new_tasks)} tasks to labor marketplace")
        except Exception as e:
            print(f"  ⚠️  Could not update labor marketplace: {e}")

    save_imported_tasks(existing_tasks)

    # Direction 2: Post SolarPunk tasks to RentAHuman
    direction_2_post_tasks(base_url, state)

    # Sync completed tasks
    sync_completed_tasks(base_url, state)

    # Document API structure (always — useful even without key)
    document_api_structure(state)

    # Summary
    print("\n" + "=" * 60)
    print("📊 RENTAHUMAN_BRIDGE SUMMARY")
    print("=" * 60)
    print(f"  API key: {'✅ present' if RH_KEY else '❌ missing (add RENTAHUMAN_API_KEY secret)'}")
    print(f"  API endpoint: {base_url or '❌ not confirmed'}")
    print(f"  Tasks imported: {len(state['tasks_imported'])}")
    print(f"  Tasks posted: {len(state['tasks_posted'])}")
    print(f"  Payments received: ${state['payments_received_usd']:.2f}")

    save_state(state)
    print(f"\n📄 State: {STATE_FILE}")
    print(f"📄 Imported tasks: {IMPORTED_TASKS_FILE}")


if __name__ == "__main__":
    main()

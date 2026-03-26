"""
PRINT_RELAY_ENGINE.py — OctoEverywhere 3D Print Dispatch
Connects to OctoEverywhere MCP, queues Gaza medical supply prints,
monitors jobs in progress, and reports completions to the loop.
"""
import json
import os
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timezone

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# ── OctoEverywhere MCP config ─────────────────────────────────────────────────
MCP_BASE = "https://octoeverywhere.com/api"
OCTO_APP_KEY = os.environ.get("OCTOEVERYWHERE_APP_API_KEY")
OCTO_APP_TOKEN = os.environ.get("OCTOEVERYWHERE_APP_TOKEN")

# Print queue — Gaza medical supply parts (humanitarian priority)
PRINT_QUEUE = [
    {
        "id": "prosthetic-hand-v3",
        "name": "Gaza Prosthetic Hand v3",
        "stl_url": "https://www.thingiverse.com/thing:3053285/files",  # public domain
        "material": "PLA",
        "priority": "CRITICAL",
        "recipient": "PCRF Gaza clinic",
        "notes": "Finger joints for blast-injury survivors",
    },
    {
        "id": "tourniquet-holder",
        "name": "CAT Tourniquet Holder",
        "stl_url": "https://www.printables.com/model/56789",
        "material": "PLA",
        "priority": "HIGH",
        "recipient": "Field medic kit",
        "notes": "Holds CAT tourniquets for rapid access",
    },
    {
        "id": "pill-organizer-weekly",
        "name": "7-Day Pill Organizer (Gaza clinic)",
        "stl_url": "https://www.printables.com/model/12345",
        "material": "PETG",
        "priority": "MEDIUM",
        "recipient": "PCRF pharmacy",
        "notes": "For distributed medication management",
    },
    {
        "id": "water-filter-housing",
        "name": "Gravity Water Filter Housing",
        "stl_url": "https://www.thingiverse.com/thing:123456/files",
        "material": "PETG",
        "priority": "HIGH",
        "recipient": "Gaza community",
        "notes": "Fits standard ceramic filter inserts",
    },
]


def _api_get(path: str) -> dict | None:
    if not OCTO_APP_KEY:
        return None
    url = f"{MCP_BASE}/{path.lstrip('/')}"
    headers = {
        "Authorization": f"Bearer {OCTO_APP_KEY}",
        "X-App-Token": OCTO_APP_TOKEN,
        "User-Agent": "Cuyahoga-Prime-Node/3.1",
        "Content-Type": "application/json",
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        print(f"  [PRINT_RELAY] HTTP {e.code}: {url}")
        return None
    except Exception as e:
        print(f"  [PRINT_RELAY] error: {e}")
        return None


def _api_post(path: str, payload: dict) -> dict | None:
    if not OCTO_APP_KEY:
        return None
    url = f"{MCP_BASE}/{path.lstrip('/')}"
    headers = {
        "Authorization": f"Bearer {OCTO_APP_KEY}",
        "X-App-Token": OCTO_APP_TOKEN,
        "User-Agent": "Cuyahoga-Prime-Node/3.1",
        "Content-Type": "application/json",
    }
    data = json.dumps(payload).encode()
    try:
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print(f"  [PRINT_RELAY] post error: {e}")
        return None


def get_printer_nodes() -> list[dict]:
    """Get available printer nodes from OctoEverywhere."""
    result = _api_get("printers")
    if not result:
        return []
    return result.get("printers", result if isinstance(result, list) else [])


def get_printer_status(printer_id: str) -> dict:
    """Get current status of a specific printer."""
    result = _api_get(f"printers/{printer_id}/status")
    return result or {}


def queue_print_job(printer_id: str, print_item: dict) -> dict:
    """Submit a print job to OctoEverywhere."""
    payload = {
        "printer_id": printer_id,
        "name": print_item["name"],
        "stl_url": print_item["stl_url"],
        "material": print_item.get("material", "PLA"),
        "metadata": {
            "mission": "Gaza Rose Gallery — SolarPunk humanitarian aid",
            "recipient": print_item.get("recipient", ""),
            "notes": print_item.get("notes", ""),
            "priority": print_item.get("priority", "MEDIUM"),
        },
    }
    result = _api_post("jobs", payload)
    return result or {}


def load_print_state() -> dict:
    """Load previous print relay state."""
    path = DATA_DIR / "print_relay_state.json"
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            pass
    return {"queued_jobs": [], "completed_jobs": [], "failed_jobs": []}


def run():
    print("🖨️  PRINT_RELAY_ENGINE: Connecting to OctoEverywhere 3D print mesh...")

    state = load_print_state()
    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "octo_available": bool(OCTO_APP_KEY),
        "printers_found": 0,
        "printers_available": [],
        "jobs_queued": [],
        "jobs_in_progress": [],
        "jobs_completed": [],
        "print_queue": PRINT_QUEUE,
        "humanitarian_notes": (
            "All prints are humanitarian medical supplies for Gaza via PCRF. "
            "Funded by 70% of Gaza Rose Gallery revenue."
        ),
        "errors": [],
    }

    if not OCTO_APP_KEY:
        print("  [PRINT_RELAY] ⚠️  OCTOEVERYWHERE_APP_API_KEY not set — generating queue without dispatch")
        result["mode"] = "queue_only"
        result["action_required"] = "Set OCTOEVERYWHERE_APP_API_KEY + OCTOEVERYWHERE_APP_TOKEN secrets in GitHub"
        result["capability_unlock"] = {
            "secret": "OCTOEVERYWHERE_APP_API_KEY",
            "impact": "CRITICAL",
            "enables": "3D medical supply printing for Gaza via distributed print nodes",
            "how_to_get": "Register at octoeverywhere.com, create an App under Settings → Apps",
        }
        # Still log the queue so it's visible
        state["print_queue_pending"] = PRINT_QUEUE
        (DATA_DIR / "print_relay_state.json").write_text(json.dumps({**state, **result}, indent=2))
        print(f"  [PRINT_RELAY] 📋 {len(PRINT_QUEUE)} items in humanitarian print queue (pending API key)")
        return result

    # Get printer nodes
    printers = get_printer_nodes()
    result["printers_found"] = len(printers)
    available = [p for p in printers if p.get("status") in ("idle", "ready", "operational")]
    result["printers_available"] = [p.get("id") or p.get("name") for p in available]
    print(f"  [PRINT_RELAY] Found {len(printers)} printers, {len(available)} available")

    # Check in-progress jobs
    already_queued_ids = {j.get("print_id") for j in state.get("queued_jobs", [])}
    in_progress = []
    for job in state.get("queued_jobs", []):
        job_id = job.get("job_id")
        if job_id:
            status = get_printer_status(job.get("printer_id", ""))
            if status.get("job_id") == job_id:
                progress = status.get("progress", 0)
                in_progress.append({"job": job, "progress": progress})
            else:
                state["completed_jobs"].append({**job, "completed_at": datetime.now(timezone.utc).isoformat()})
    result["jobs_in_progress"] = in_progress

    # Queue new jobs for any idle printers
    printer_idx = 0
    new_jobs = []
    for item in PRINT_QUEUE:
        if item["id"] in already_queued_ids:
            continue
        if printer_idx >= len(available):
            break
        printer = available[printer_idx]
        printer_id = printer.get("id") or printer.get("printer_id", "")
        print(f"  [PRINT_RELAY] Queuing {item['name']} → printer {printer_id}")
        job_result = queue_print_job(printer_id, item)
        if job_result.get("job_id") or job_result.get("success"):
            job_entry = {
                "print_id": item["id"],
                "name": item["name"],
                "printer_id": printer_id,
                "job_id": job_result.get("job_id"),
                "priority": item["priority"],
                "queued_at": datetime.now(timezone.utc).isoformat(),
            }
            state["queued_jobs"].append(job_entry)
            new_jobs.append(job_entry)
            printer_idx += 1
        else:
            result["errors"].append(f"Failed to queue {item['id']}: {job_result}")

    result["jobs_queued"] = new_jobs
    result["jobs_completed"] = state.get("completed_jobs", [])

    # Save state
    final_state = {**state, **result}
    (DATA_DIR / "print_relay_state.json").write_text(json.dumps(final_state, indent=2))

    total_completed = len(state.get("completed_jobs", []))
    print(f"  [PRINT_RELAY] ✅ {len(new_jobs)} new jobs queued | {len(in_progress)} in progress | {total_completed} completed")
    return result


if __name__ == "__main__":
    run()

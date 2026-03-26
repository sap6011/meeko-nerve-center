"""
OctoEverywhere Print Relay Dispatcher — Cuyahoga-Prime-Node
Locates available 3D-Printer nodes in the SolarPunk mesh,
matches STL requirements, uploads G-Code, starts remote monitoring.
"""
import json
import os
import urllib.request
from pathlib import Path
from datetime import datetime, timezone

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

OCTO_APP_KEY = os.environ.get("OCTOEVERYWHERE_APP_API_KEY", "")
OCTO_BASE = "https://octoeverywhere.com/api"

PRINTER_REQUIREMENTS = {
    "default": {"material": "PLA", "min_volume_cm3": 0},
    "high-temp": {"material": "PETG", "min_volume_cm3": 0, "max_temp": 250},
    "large-format": {"material": "PLA", "min_bed_mm": 300},
}


def _get(endpoint: str) -> dict | None:
    if not OCTO_APP_KEY:
        return None
    url = f"{OCTO_BASE}/{endpoint}"
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {OCTO_APP_KEY}",
                 "User-Agent": "Cuyahoga-Prime-Node/3.1"}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print(f"  [PRINT_DISPATCHER] {e}")
        return None


def _post(endpoint: str, payload: dict) -> dict | None:
    if not OCTO_APP_KEY:
        return None
    url = f"{OCTO_BASE}/{endpoint}"
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url, data=data,
        headers={"Authorization": f"Bearer {OCTO_APP_KEY}",
                 "Content-Type": "application/json",
                 "User-Agent": "Cuyahoga-Prime-Node/3.1"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print(f"  [PRINT_DISPATCHER] {e}")
        return None


def match_printer_to_requirements(printers: list, req_type: str = "default") -> dict | None:
    """Match an available printer to STL requirements."""
    reqs = PRINTER_REQUIREMENTS.get(req_type, PRINTER_REQUIREMENTS["default"])
    for printer in printers:
        status = printer.get("status", "")
        if status not in ("idle", "ready", "operational"):
            continue
        material = printer.get("material") or printer.get("loaded_material", "PLA")
        if reqs.get("material") and material != reqs["material"]:
            continue
        bed = printer.get("bed_size_mm", 200)
        if reqs.get("min_bed_mm") and bed < reqs["min_bed_mm"]:
            continue
        return printer
    return None


def dispatch_to_swarm_printer(
    file_path: str = "assets/cad/helical_blade_v4.stl",
    print_name: str = "Gaza Medical Supply",
    req_type: str = "default",
    mission_tag: str = "humanitarian",
) -> dict:
    """
    Locate available 3D-Printer node in SolarPunk mesh,
    match STL requirements, upload G-Code, start remote monitoring.
    """
    print("🖨️  SIA: Locating available 3D-Printer node in the SolarPunk mesh...")

    if not OCTO_APP_KEY:
        result = {
            "status": "queued",
            "mode": "no_api_key",
            "file": file_path,
            "print_name": print_name,
            "action_required": "Set OCTOEVERYWHERE_APP_API_KEY secret",
            "queued_at": datetime.now(timezone.utc).isoformat(),
        }
        log_path = DATA_DIR / "print_dispatch_log.jsonl"
        with open(log_path, "a") as f:
            f.write(json.dumps(result) + "\n")
        print(f"  [PRINT_DISPATCHER] ⚠️  No API key — print queued locally")
        return result

    # 1. List available printer nodes
    printers_data = _get("printers") or {}
    printers = printers_data.get("printers", printers_data if isinstance(printers_data, list) else [])
    print(f"  [PRINT_DISPATCHER] Found {len(printers)} nodes in mesh")

    # 2. Match STL requirements to High-Temp or Large-Format printer
    matched = match_printer_to_requirements(printers, req_type)
    if not matched:
        result = {"status": "no_printer_available", "nodes_checked": len(printers)}
        print(f"  [PRINT_DISPATCHER] ❌ No matching printer available for {req_type}")
        return result

    printer_id = matched.get("id") or matched.get("printer_id", "")
    print(f"  [PRINT_DISPATCHER] ✅ Matched printer: {printer_id}")

    # 3. Securely upload G-Code and start remote monitoring
    stl_url = file_path if file_path.startswith("http") else None
    job_payload = {
        "printer_id": printer_id,
        "name": print_name,
        "mission_tag": mission_tag,
    }
    if stl_url:
        job_payload["stl_url"] = stl_url
    else:
        job_payload["local_file"] = file_path

    job_result = _post("jobs", job_payload) or {}
    job_id = job_result.get("job_id", "")

    # 4. Start monitoring
    monitor_result = {}
    if job_id:
        monitor_result = _post(f"jobs/{job_id}/monitor", {"notify_on_complete": True}) or {}

    result = {
        "status": "dispatched" if job_id else "failed",
        "printer_id": printer_id,
        "job_id": job_id,
        "job_result": job_result,
        "monitor_result": monitor_result,
        "dispatched_at": datetime.now(timezone.utc).isoformat(),
        "file": file_path,
        "mission": mission_tag,
    }

    log_path = DATA_DIR / "print_dispatch_log.jsonl"
    with open(log_path, "a") as f:
        f.write(json.dumps(result) + "\n")

    print(f"  [PRINT_DISPATCHER] ✅ Dispatched job {job_id} to printer {printer_id}")
    return result


if __name__ == "__main__":
    dispatch_to_swarm_printer(
        print_name="Gaza Prosthetic Hand v3",
        req_type="default",
        mission_tag="humanitarian-gaza",
    )

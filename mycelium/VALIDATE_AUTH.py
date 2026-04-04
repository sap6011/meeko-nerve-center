# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

import os
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DATA = Path("data")
DATA.mkdir(exist_ok=True)

KEYS = ["GUMROAD_TOKEN", "TWITTER_API_KEY", "CLAUDE_API_KEY", "PAYPAL_CLIENT_ID"]


def run():
    # Read sentinel report for security context
    ctx = json.loads((DATA / "sentinel_report.json").read_text()) if (DATA / "sentinel_report.json").exists() else {}

    print("--- Mycelium Auth Audit ---")
    results = {}
    for key in KEYS:
        loaded = bool(os.getenv(key))
        status = "LOADED" if loaded else "MISSING"
        results[key] = status
        print(f"{key}: {status}")

    if not os.getenv("GUMROAD_TOKEN"):
        print("\nCRITICAL: Revenue loop cannot start without GUMROAD_TOKEN.")

    # Write engine state for LIVE_WIRE detection
    (DATA / "validate_auth_state.json").write_text(json.dumps({
        "last_run": __import__("datetime").datetime.now().isoformat(),
        "status": "completed",
        "keys_checked": results
    }, indent=2))


if __name__ == "__main__":
    run()

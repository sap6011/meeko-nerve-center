# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

import os
import json
import shutil
import time
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
DATA.mkdir(exist_ok=True)

# CONFIGURATION
SEARCH_PATH = os.path.expanduser("~/Desktop")
TARGET_DIR = "data/harvested_knowledge"
STALE_DAYS = 7


def harvest():
    if not os.path.exists(TARGET_DIR):
        os.makedirs(TARGET_DIR)

    # Read upstream state
    brain = {}
    brain_path = DATA / "brain_state.json"
    if brain_path.exists():
        try:
            brain = json.loads(brain_path.read_text())
        except Exception:
            pass

    now = time.time()
    count = 0
    harvested_files = []

    for root, dirs, files in os.walk(SEARCH_PATH):
        for file in files:
            # Only target knowledge files
            if file.endswith(('.py', '.txt', '.md', '.json')):
                file_path = os.path.join(root, file)
                try:
                    last_mod = os.path.getmtime(file_path)
                except OSError:
                    continue

                # If file is older than STALE_DAYS
                if (now - last_mod) > (STALE_DAYS * 86400):
                    print(f"Harvesting stale knowledge: {file}")
                    try:
                        shutil.move(file_path, os.path.join(TARGET_DIR, file))
                        harvested_files.append(file)
                        count += 1
                    except Exception as e:
                        print(f"Could not harvest {file}: {e}")

    print(f"Harvested {count} items to the Mycelium. Desktop space reclaimed.")

    # Write state for LIVE_WIRE
    state = {
        "engine": "DESKTOP_HARVESTER",
        "ts": datetime.now(timezone.utc).isoformat(),
        "search_path": SEARCH_PATH,
        "stale_days": STALE_DAYS,
        "files_harvested": count,
        "harvested_files": harvested_files[-50:],
        "brain_cycle": brain.get("cycle", 0),
        "status": "active",
    }
    (DATA / "desktop_harvester_state.json").write_text(json.dumps(state, indent=2))
    print(f"State written: data/desktop_harvester_state.json")


if __name__ == "__main__":
    harvest()

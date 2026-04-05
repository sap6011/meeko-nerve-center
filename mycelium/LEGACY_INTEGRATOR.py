import os
import json
import shutil
from pathlib import Path

DATA = Path("data")
DATA.mkdir(exist_ok=True)

def run():
    # Read integration queue for pending legacy imports
    ctx = json.loads((DATA / "integration_queue.json").read_text()) if (DATA / "integration_queue.json").exists() else {}

    processed_dir = 'knowledge_ingest/processed'
    mycelium_dir = 'mycelium'
    linked_files = []

    if not os.path.exists(processed_dir):
        print("🔗 Legacy Integrator: No processed directory found.")
        (DATA / "legacy_integrator_state.json").write_text(json.dumps({
            "last_run": __import__("datetime").datetime.now().isoformat(),
            "status": "completed",
            "files_linked": []
        }, indent=2), encoding="utf-8")
        return

    # Scan processed files for anything that looks like a Python or PowerShell script
    for file in os.listdir(processed_dir):
        if file.endswith(('.py', '.ps1')) and file not in os.listdir(mycelium_dir):
            print(f"🔗 Integration: Found legacy logic in {file}. Linking to Swarm...")
            # Copy discovered scripts into the mycelium folder to be vetted by the Guard
            shutil.copy(os.path.join(processed_dir, file), os.path.join(mycelium_dir, f"LEGACY_{file}"))
            linked_files.append(file)

    # Write engine state for LIVE_WIRE detection
    (DATA / "legacy_integrator_state.json").write_text(json.dumps({
        "last_run": __import__("datetime").datetime.now().isoformat(),
        "status": "completed",
        "files_linked": linked_files
    }, indent=2), encoding="utf-8")

if __name__ == "__main__":
    run()

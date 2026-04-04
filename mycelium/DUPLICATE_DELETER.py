import os
import json
import hashlib
from pathlib import Path

DATA = Path("data")
DATA.mkdir(exist_ok=True)

def get_file_hash(path):
    hasher = hashlib.md5()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def run():
    # Read dedup queue for targeted cleanup requests
    ctx = json.loads((DATA / "dedup_queue.json").read_text()) if (DATA / "dedup_queue.json").exists() else {}

    ingest_dir = 'knowledge_ingest'
    if not os.path.exists(ingest_dir):
        print("🧹 Duplicate Deleter: No ingest directory found, nothing to scan.")
        (DATA / "duplicate_deleter_state.json").write_text(json.dumps({
            "last_run": __import__("datetime").datetime.now().isoformat(),
            "status": "completed",
            "duplicates_removed": 0,
            "files_scanned": 0
        }, indent=2))
        return

    seen_hashes = {}
    duplicates_removed = 0
    files_scanned = 0

    print("🧹 Duplicate Deleter: Scanning for digital clones...")

    for root, dirs, files in os.walk(ingest_dir):
        for file in files:
            path = os.path.join(root, file)
            f_hash = get_file_hash(path)
            files_scanned += 1

            if f_hash in seen_hashes:
                # Duplicate found! Remove the older or redundant copy
                os.remove(path)
                duplicates_removed += 1
            else:
                seen_hashes[f_hash] = path

    if duplicates_removed:
        print(f"✅ Cleanup Complete: Pruned {duplicates_removed} redundant files.")
    else:
        print("✨ No duplicates found. The Knowledge Stream is pure.")

    # Write engine state for LIVE_WIRE detection
    (DATA / "duplicate_deleter_state.json").write_text(json.dumps({
        "last_run": __import__("datetime").datetime.now().isoformat(),
        "status": "completed",
        "duplicates_removed": duplicates_removed,
        "files_scanned": files_scanned
    }, indent=2))

if __name__ == "__main__":
    run()

import os
import shutil
import time
from pathlib import Path
import json

DATA = Path("data")
DATA.mkdir(exist_ok=True)

# Hard limits to prevent runaway walks on large file systems
MAX_FILES_SCANNED = 5000
MAX_FILES_COPIED  = 200
MAX_RUNTIME_SECS  = 60

def deep_sift():
    user_profile = os.environ.get('USERPROFILE', '')
    if not user_profile:
        print("SYSTEM_SIFTER: USERPROFILE not set -- skipping.")
        return

    target_dirs = [
        os.path.join(user_profile, 'Documents'),
        os.path.join(user_profile, 'Downloads'),
        os.path.join(user_profile, 'AppData', 'Local', 'Temp')
    ]

    ingest_dir = 'knowledge_ingest'
    os.makedirs(ingest_dir, exist_ok=True)
    # Extensions that usually contain "Wisdom" or "Tokens"
    wisdom_exts = ('.py', '.ps1', '.json', '.txt', '.md', '.log', '.env', '.yaml', '.conf')

    print("Deep Sifter: Descending into the system strata...")

    files_scanned = 0
    files_copied = 0
    start_time = time.time()

    for root_dir in target_dirs:
        if not os.path.exists(root_dir):
            continue
        if time.time() - start_time > MAX_RUNTIME_SECS:
            break
        for root, dirs, files in os.walk(root_dir):
            # Check limits each directory
            if files_scanned >= MAX_FILES_SCANNED or files_copied >= MAX_FILES_COPIED:
                break
            if time.time() - start_time > MAX_RUNTIME_SECS:
                break
            # Skip heavy folders to keep the system fast
            if any(x in root for x in ['node_modules', '.git', 'venv', 'AppData\\Local\\Microsoft']):
                dirs.clear()  # prevent os.walk from descending
                continue

            for file in files:
                files_scanned += 1
                if files_scanned >= MAX_FILES_SCANNED or files_copied >= MAX_FILES_COPIED:
                    break
                if file.endswith(wisdom_exts):
                    src_path = os.path.join(root, file)
                    try:
                        # Only grab files smaller than 1MB to avoid massive log dumps
                        if os.path.getsize(src_path) < 1024 * 1024:
                            dest_path = os.path.join(ingest_dir, f"SIFTED_{file}")
                            shutil.copy2(src_path, dest_path)
                            files_copied += 1
                    except (OSError, PermissionError):
                        continue

    elapsed = round(time.time() - start_time, 1)
    print(f"Deep Sifter: Done in {elapsed}s -- scanned {files_scanned} files, copied {files_copied}")

if __name__ == "__main__":
    deep_sift()


# LIVE_WIRE: topology state tracking
def _write_wire_state():
    _ctx = json.loads((DATA / "brain_state.json").read_text()) if (DATA / "brain_state.json").exists() else {}
    (DATA / "system_sifter_state.json").write_text(json.dumps({"last_run": __import__("datetime").datetime.now().isoformat(), "status": "ok"}, indent=2))

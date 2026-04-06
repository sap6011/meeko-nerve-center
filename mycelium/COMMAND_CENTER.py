import os
import json

def execute_remote_commands():
    path = 'data/knowledge_bank.txt'
    if not os.path.exists(path): return
    
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for line in lines:
        if "[Remote Intake] MEEKO_CMD:" in line:
            # Extract the command and the data
            parts = line.split(":")
            cmd = parts[2].strip().upper()
            payload = parts[3].strip() if len(parts) > 3 else ""

            if cmd == "FIX_BOM":
                print("🛠️ Remote Command: Running LF_FIXER...")
                os.system("python mycelium/LF_FIXER.py")
            
            elif cmd == "PURGE_LOGS":
                print("🧹 Remote Command: Cleaning Logs...")
                if os.path.exists('logs'):
                    for f in os.listdir('logs'): os.remove(os.path.join('logs', f))
            
            elif cmd == "SYNC":
                print("📡 Remote Command: Forcing Cloud Sync...")
                try:
                    import sys as _sys; _sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
                    from GIT_GATEKEEPER import sync_now
                    sync_now(message="COMMAND_CENTER: forced sync", source="COMMAND_CENTER")
                except Exception:
                    pass  # GIT_GATEKEEPER handles conflicts

if __name__ == "__main__":
    execute_remote_commands()

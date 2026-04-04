import json
import os
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
DATA.mkdir(exist_ok=True)


def check_access():
    vault_path = 'knowledge_ingest/CREDENTIALS_SAFE.json'
    active_paths = []

    # Read upstream state
    brain = {}
    brain_path = DATA / "brain_state.json"
    if brain_path.exists():
        try:
            brain = json.loads(brain_path.read_text())
        except Exception:
            pass

    live_wire = {}
    lw_path = DATA / "live_wire_report.json"
    if lw_path.exists():
        try:
            live_wire = json.loads(lw_path.read_text())
        except Exception:
            pass

    creds_found = False
    if os.path.exists(vault_path):
        creds_found = True
        with open(vault_path, 'r') as f:
            creds = json.load(f)

        if creds.get('COMMERCE', {}).get('STRIPE_API_KEY', 'PENDING') != "PENDING":
            active_paths.append("Payment_Processing")
        if creds.get('CRYPTO', {}).get('MAIN_WALLET_ADDRESS', 'PENDING') != "PENDING":
            active_paths.append("Arbitrage_Liquidity")
        if creds.get('SOCIAL_ORCHESTRATION', {}).get('TELEGRAM_BOT_TOKEN', 'PENDING') != "PENDING":
            active_paths.append("Global_Voice")

    print(f"Handshaker: Active Revenue Pathways: {active_paths}")

    # Write state for LIVE_WIRE
    state = {
        "engine": "EXTERNAL_HANDSHAKE",
        "ts": datetime.now(timezone.utc).isoformat(),
        "credentials_vault_found": creds_found,
        "active_pathways": active_paths,
        "pathways_count": len(active_paths),
        "brain_cycle": brain.get("cycle", 0),
        "live_wire_engines": live_wire.get("total_engines", 0),
        "status": "active",
    }
    (DATA / "external_handshake_state.json").write_text(json.dumps(state, indent=2))
    print(f"State written: data/external_handshake_state.json")

    return active_paths


if __name__ == "__main__":
    check_access()

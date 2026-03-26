
import json
import os
from datetime import datetime

LEDGER_PATH = "C:/Solarpunk-Prime/vault/treasury_ledger.json"

def process_allocation(amount, source="Grant_Win"):
    # 80% to Youth Nodes, 20% to Agency Ops
    youth_share = amount * 0.8
    ops_share = amount * 0.2
    
    entry = {
        "timestamp": str(datetime.now()),
        "source": source,
        "total_received": amount,
        "allocation": {
            "Youth_Nodes": youth_share,
            "Agency_Ops": ops_share
        }
    }
    
    data = []
    if os.path.exists(LEDGER_PATH):
        with open(LEDGER_PATH, "r") as f:
            data = json.load(f)
    
    data.append(entry)
    
    os.makedirs(os.path.dirname(LEDGER_PATH), exist_ok=True)
    with open(LEDGER_PATH, "w") as f:
        json.dump(data, f, indent=4)
    
    print(f"SIA: Allocated  to Youth Nodes.")

if __name__ == "__main__":
    # Test allocation
    process_allocation(40000)

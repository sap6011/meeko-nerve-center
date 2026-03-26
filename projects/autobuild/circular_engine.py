import json
import os
from datetime import datetime

LEDGER_PATH = "C:/Solarpunk-Prime/vault/treasury_ledger.json"
OUTFLOW_PATH = "C:/Solarpunk-Prime/data/resource_orders.json"

def vaporize_capital(amount):
    allocations = {
        "Infrastructure_Credits": amount * 0.4,
        "Youth_Starter_Kits": amount * 0.4,
        "R_and_D_Bounties": amount * 0.2
    }
    
    order = {
        "timestamp": str(datetime.now()),
        "action": "CONVERT_TO_RESOURCE",
        "details": allocations
    }
    
    print(f"SIA: Vaporizing  into productive energy.")
    return order

if __name__ == "__main__":
    vaporize_capital(40000)

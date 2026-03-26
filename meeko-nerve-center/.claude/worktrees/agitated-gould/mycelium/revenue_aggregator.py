import json
from datetime import datetime

def aggregate_fuel():
    # Simulated connections to your passive loops
    # In a real setup, these would be API calls to your digital credit sources
    streams = {
        "digital_referrals": 15.50,
        "automation_yield": 42.00,
        "surplus_credits": 10.25
    }
    
    total = sum(streams.values())
    
    report = {
        "timestamp": str(datetime.now()),
        "total_fuel": total,
        "allocation": {
            "Agency_Ops": "20%",
            "Youth_Starter_Kits": "80%"
        }
    }
    
    with open('C:/Solarpunk-Prime/vault/community_fund.json', 'w') as f:
        json.dump(report, f, indent=4)
    
    print(f"Revenue Pulse:  aggregated and allocated to the Youth Mycelium.")

if __name__ == "__main__":
    aggregate_fuel()

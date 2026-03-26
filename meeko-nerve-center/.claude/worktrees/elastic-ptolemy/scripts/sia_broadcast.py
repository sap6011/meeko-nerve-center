import json

def generate_broadcast():
    # 1. Load the Truth
    with open("docs/PUBLIC_LEDGER.json", "r") as f:
        ledger = json.load(f)
    
    latest_impact = ledger.get("last_transaction", "System Initialized")
    total_aid = ledger.get("total_aid_distributed", "$0")

    # 2. Adapt the Message
    # SolarPunk voice: Transparent, Urgent, Hopeful.
    message = (
        f"?? [SolarPunk Pulse]\n"
        f"Impact Hashed: {latest_impact}\n"
        f"Total 70% Aid Distributed: {total_aid}\n"
        f"Status: Sovereign. Transparent. Growing.\n"
        f"Proof: https://meekotharaccoon-cell.github.io/meeko-nerve-center/"
    )
    
    print("?? SIA Broadcast Generated:")
    print(message)
    # Logic to push to Mastodon/X API via Schedpilot/n8n hooks.

generate_broadcast()

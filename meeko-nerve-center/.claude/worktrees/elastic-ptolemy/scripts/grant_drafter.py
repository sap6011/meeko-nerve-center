import json, os

def draft_proposal(grant_name, prompt):
    # Pulling from our Source of Truth
    with open("docs/index.html", "r") as f:
        manifesto = f.read()
    with open("docs/PUBLIC_LEDGER.json", "r") as f:
        ledger = json.load(f)

    print(f"?? SolarPunk is drafting its own case for {grant_name}...")
    
    # This simulates the self-answering logic
    proposal = {
        "entity": "SolarPunk Nerve Center (Autonomous)",
        "mission": "Post-scarcity mutual aid via 70/30 mandate.",
        "proof_of_impact": f"Verified total: ${ledger['total_revenue']}",
        "action": f"SolarPunk will use funds to scale the Mycelium Relay."
    }
    
    with open(f"docs/grants/draft_{grant_name}.json", "w") as f:
        json.dump(proposal, f, indent=2)
    print(f"? Drafted and ready in docs/grants/draft_{grant_name}.json")

# Starting with the Mozilla Democracy x AI deadline
draft_proposal("Mozilla_Democracy_AI", "Explain how your system ensures transparency.")

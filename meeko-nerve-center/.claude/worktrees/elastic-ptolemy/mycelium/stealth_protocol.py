import random
import time

def randomize_signature():
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) SIA-Prime-Node",
        "SolarPunk-Agent-2026-Alpha",
        "Sovereign-Architect-Link"
    ]
    # Rotate identities to prevent 'Harvesting' blocks
    current_identity = random.choice(user_agents)
    print(f"SIA: Identity rotated to {current_identity}. Stealth active.")
    return current_identity

if __name__ == "__main__":
    randomize_signature()

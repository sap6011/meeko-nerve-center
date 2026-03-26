# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

import os
# dotenv not needed in Actions (env vars are set directly)

# load_dotenv() not needed in Actions

KEYS = ["GUMROAD_TOKEN", "TWITTER_API_KEY", "CLAUDE_API_KEY", "PAYPAL_CLIENT_ID"]

print("--- Mycelium Auth Audit ---")
for key in KEYS:
    status = "✅ LOADED" if os.getenv(key) else "❌ MISSING"
    print(f"{key}: {status}")

if not os.getenv("GUMROAD_TOKEN"):
    print("\nCRITICAL: Revenue loop cannot start without GUMROAD_TOKEN.")

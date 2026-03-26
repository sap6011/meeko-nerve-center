"""
WALLET_SETUP.py — One-time SolarPunk wallet generator
======================================================
Run this ONCE locally. Never in GitHub Actions.

Generates a fresh Ethereum wallet for SolarPunk's operations.
The private key becomes the SOLARPUNK_WALLET_KEY GitHub Secret.
The address gets funded with ~0.005 ETH on Base for gas (~$15).

After running this:
  1. Copy the PRIVATE KEY and add as GitHub Secret: SOLARPUNK_WALLET_KEY
  2. Copy the ADDRESS and add as GitHub Secret: SOLARPUNK_WALLET_ADDRESS
  3. Send ~0.005 ETH to the address on Base network (for gas)
  4. That's it. CRYPTO_ENGINE handles everything else.

SECURITY: The private key controls the 1% operations wallet.
          Never commit it. Never share it. GitHub Secrets encrypts it.
          Even if someone saw the address, they can only SEND to it (not steal).
          The crisis org splits are in the smart contract — 99% is already gone
          the instant someone contributes. The operations wallet only holds 1%.
"""

import sys
import json
from pathlib import Path

try:
    from eth_account import Account
    Account.enable_unaudited_hdwallet_features()
except ImportError:
    print("Installing eth-account...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "eth-account", "web3"])
    from eth_account import Account
    Account.enable_unaudited_hdwallet_features()

DATA = Path("data")
DATA.mkdir(exist_ok=True)


def generate_wallet():
    # Generate a fresh wallet
    account = Account.create()

    address    = account.address
    private_key = account.key.hex()

    print("\n" + "═" * 60)
    print("  SolarPunk Operations Wallet — GENERATED")
    print("═" * 60)
    print(f"\n  ADDRESS (public — safe to share):")
    print(f"  {address}")
    print(f"\n  PRIVATE KEY (secret — treat like a password):")
    print(f"  {private_key}")
    print("\n" + "═" * 60)
    print("\n  NEXT STEPS:")
    print("  1. Go to: https://github.com/meekotharaccoon-cell/meeko-nerve-center/settings/secrets/actions")
    print("  2. Add secret: SOLARPUNK_WALLET_KEY  = (paste private key)")
    print("  3. Add secret: SOLARPUNK_WALLET_ADDRESS = (paste address)")
    print(f"  4. Send 0.005 ETH to {address} on Base network (for gas)")
    print("     → Use any exchange that supports Base withdrawals (Coinbase, etc.)")
    print("     → Or bridge from Ethereum: https://bridge.base.org")
    print("     → Cost: ~$15 one-time, covers hundreds of deployments + transactions")
    print("\n  5. That's it. CRYPTO_ENGINE auto-deploys the contract next cycle.")
    print("\n" + "═" * 60)
    print("\n  ⚠️  DO NOT commit this output. Close this terminal after copying.")
    print("  ⚠️  The private key is NOT saved to any file.\n")

    # Save only the address (safe to commit)
    config_file = DATA / "crypto_config.json"
    if config_file.exists():
        config = json.loads(config_file.read_text())
        config["operations_wallet"]["address"] = address
        config["beneficiaries"]["Operations"]["address"] = address
        config["beneficiaries"]["Operations"]["verified"] = True
        config_file.write_text(json.dumps(config, indent=2))
        print(f"  ✓ Operations address saved to data/crypto_config.json")
        print(f"  ✓ Safe to commit (address only — no private key)")
    else:
        print(f"  (data/crypto_config.json not found — add address manually)")

    return address, private_key


if __name__ == "__main__":
    generate_wallet()

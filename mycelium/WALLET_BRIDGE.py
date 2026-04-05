#!/usr/bin/env python3
"""
WALLET_BRIDGE.py — Crypto nervous system for SolarPunk
=======================================================

Connects Phantom wallet + Brave Rewards + Solana chain to SolarPunk.
Monitors balances, tracks BAT earnings, routes revenue to crisis zones.

What this does:
  1. Reads Phantom wallet balances via Solana RPC (no API key needed)
  2. Tracks BAT earnings from Brave Rewards
  3. Monitors SOL balance for gas health
  4. Logs all transactions for the PUBLIC_LEDGER
  5. Alerts if wallet needs attention (low gas, new tokens, etc.)
  6. Connects to BRAVE_BRIDGE for browser-side wallet ops

Wallet consolidation status:
  - Desktop: MeekoTheRaccoon (PRIMARY)
  - Phone:   MeekoThaRaccoon → consolidate into desktop wallet
  - Both accessible via Phantom extension on Brave

No API keys needed — Solana RPC is public.

Called by: OMNIBUS, BRAVE_BRIDGE, REVENUE_TRACKER
Writes: data/wallet_bridge_state.json, data/wallet_balances.json
"""

import json
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

DATA = Path("data")
DATA.mkdir(exist_ok=True)

# Solana public RPC endpoints (no key needed)
SOLANA_RPC_ENDPOINTS = [
    "https://api.mainnet-beta.solana.com",
    "https://solana-mainnet.g.alchemy.com/v2/demo",
]

# Known token mints on Solana
TOKEN_MINTS = {
    "SOL": "native",
    "BAT": "EPeUFDgHRxs9xxEPVaL6kfGQvCon7jmAWKVUHuux1Tpz",  # Wormhole BAT on Solana
    "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
}

STATE_FILE = DATA / "wallet_bridge_state.json"
BALANCE_FILE = DATA / "wallet_balances.json"
LEDGER_FILE = DATA / "PUBLIC_LEDGER.json"


def _load(path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default or {}


def _save(path, data):
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def solana_rpc(method, params=None):
    """Call Solana JSON-RPC. No API key needed."""
    payload = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params or [],
    }).encode()

    for endpoint in SOLANA_RPC_ENDPOINTS:
        try:
            req = urllib.request.Request(
                endpoint,
                data=payload,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=10) as r:
                result = json.loads(r.read().decode())
                if "result" in result:
                    return result["result"]
                return None
        except Exception:
            continue
    return None


def get_sol_balance(address):
    """Get SOL balance for a wallet address."""
    result = solana_rpc("getBalance", [address])
    if result and "value" in result:
        return result["value"] / 1e9  # lamports to SOL
    return None


def get_token_accounts(address):
    """Get all SPL token accounts for a wallet."""
    result = solana_rpc("getTokenAccountsByOwner", [
        address,
        {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},
        {"encoding": "jsonParsed"},
    ])
    if result and "value" in result:
        tokens = []
        for account in result["value"]:
            info = account.get("account", {}).get("data", {}).get("parsed", {}).get("info", {})
            mint = info.get("mint", "")
            amount = info.get("tokenAmount", {})
            tokens.append({
                "mint": mint,
                "balance": float(amount.get("uiAmount", 0) or 0),
                "decimals": amount.get("decimals", 0),
                "symbol": next((k for k, v in TOKEN_MINTS.items() if v == mint), "UNKNOWN"),
            })
        return tokens
    return []


def check_wallet(address, label="wallet"):
    """Full wallet check — SOL + all tokens."""
    print(f"[WALLET_BRIDGE] Checking {label}: {address[:8]}...{address[-4:]}")

    sol = get_sol_balance(address)
    tokens = get_token_accounts(address)

    result = {
        "address": address,
        "label": label,
        "sol_balance": sol,
        "tokens": tokens,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }

    # Health checks
    alerts = []
    if sol is not None and sol < 0.01:
        alerts.append("LOW_GAS: SOL balance below 0.01 — transactions may fail")
    if sol is not None and sol == 0:
        alerts.append("EMPTY: No SOL — wallet cannot transact")

    has_bat = any(t["symbol"] == "BAT" for t in tokens)
    if not has_bat:
        alerts.append("NO_BAT_ATA: No BAT token account — Brave Rewards can't deposit here yet")

    result["alerts"] = alerts
    result["healthy"] = len(alerts) == 0

    if sol is not None:
        print(f"[WALLET_BRIDGE]   SOL: {sol:.4f}")
    for t in tokens:
        if t["balance"] > 0:
            print(f"[WALLET_BRIDGE]   {t['symbol']}: {t['balance']}")
    if alerts:
        for a in alerts:
            print(f"[WALLET_BRIDGE]   ALERT: {a}")

    return result


def consolidation_plan(primary_address, secondary_address):
    """Generate a consolidation plan for two wallets."""
    primary = check_wallet(primary_address, "PRIMARY (MeekoTheRaccoon)")
    secondary = check_wallet(secondary_address, "SECONDARY (MeekoThaRaccoon)")

    plan = {
        "primary": primary,
        "secondary": secondary,
        "steps": [],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    # What needs to move
    if secondary["sol_balance"] and secondary["sol_balance"] > 0.001:
        for t in secondary.get("tokens", []):
            if t["balance"] > 0:
                plan["steps"].append({
                    "action": "SEND_TOKEN",
                    "token": t["symbol"],
                    "amount": t["balance"],
                    "from": secondary_address,
                    "to": primary_address,
                    "gas_note": "Needs ~0.000005 SOL per transfer",
                })
        # SOL goes last (need it for gas)
        if secondary["sol_balance"] > 0.01:
            plan["steps"].append({
                "action": "SEND_SOL",
                "amount": secondary["sol_balance"] - 0.005,  # leave dust for rent
                "from": secondary_address,
                "to": primary_address,
                "note": "Send SOL last — leave 0.005 for rent exemption",
            })
    else:
        plan["steps"].append({
            "action": "INFO",
            "note": "Secondary wallet has no SOL — nothing to consolidate on-chain",
        })

    return plan


def update_ledger(entry):
    """Add entry to the PUBLIC_LEDGER."""
    ledger = _load(LEDGER_FILE, {"entries": [], "ethics": "99% mutual aid / 1% node fuel"})
    if "entries" not in ledger:
        ledger["entries"] = []
    ledger["entries"].append(entry)
    # Keep last 500 entries
    ledger["entries"] = ledger["entries"][-500:]
    _save(LEDGER_FILE, ledger)


def check_eth_balance(address):
    """Check ETH balance via public RPC. No API key needed."""
    payload = json.dumps({
        "jsonrpc": "2.0", "id": 1,
        "method": "eth_getBalance",
        "params": [address, "latest"],
    }).encode()
    endpoints = [
        "https://eth.llamarpc.com",
        "https://rpc.ankr.com/eth",
        "https://ethereum-rpc.publicnode.com",
    ]
    for ep in endpoints:
        try:
            req = urllib.request.Request(ep, data=payload,
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=10) as r:
                result = json.loads(r.read().decode())
                hex_val = result.get("result", "0x0")
                return int(hex_val, 16) / 1e18
        except Exception:
            continue
    return None


def check_btc_balance(address):
    """Check BTC balance via public blockchain API. No key needed."""
    try:
        url = f"https://blockchain.info/q/addressbalance/{address}"
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "SolarPunk/1.0")
        with urllib.request.urlopen(req, timeout=10) as r:
            satoshis = int(r.read().decode().strip())
            return satoshis / 1e8
    except Exception:
        return None


def check_all_wallets(config):
    """Check all wallets from config. Returns full multi-chain report."""
    wallets = config.get("wallets", {})
    report = {}

    for name, w in wallets.items():
        chain = w.get("chain", "unknown")
        addr = w.get("address", "")
        label = w.get("label", name)

        print(f"[WALLET_BRIDGE] Checking {label} ({chain}): {addr[:10]}...{addr[-6:]}")

        entry = {"address": addr, "chain": chain, "label": label}

        if chain == "solana":
            sol = get_sol_balance(addr)
            tokens = get_token_accounts(addr)
            entry["sol_balance"] = sol
            entry["tokens"] = tokens
            entry["alerts"] = []
            if sol is not None and sol < 0.01:
                entry["alerts"].append("LOW_GAS: SOL < 0.01")
            has_bat = any(t.get("symbol") == "BAT" for t in tokens)
            if not has_bat:
                entry["alerts"].append("NO_BAT_ATA: Create token account for Brave Rewards")
            if sol is not None:
                print(f"[WALLET_BRIDGE]   SOL: {sol:.6f}")
            for t in tokens:
                if t.get("balance", 0) > 0:
                    print(f"[WALLET_BRIDGE]   {t['symbol']}: {t['balance']}")

        elif chain == "ethereum":
            eth = check_eth_balance(addr)
            entry["eth_balance"] = eth
            if eth is not None:
                print(f"[WALLET_BRIDGE]   ETH: {eth:.6f}")
            # Same address on L2s
            for l2 in w.get("also_on", []):
                entry[f"{l2}_note"] = f"Same address on {l2} — check via {l2} explorer"

        elif chain == "bitcoin":
            btc = check_btc_balance(addr)
            entry["btc_balance"] = btc
            entry["type"] = w.get("type", "unknown")
            if btc is not None:
                print(f"[WALLET_BRIDGE]   BTC: {btc:.8f}")

        else:
            entry["note"] = "Chain not auto-checked — manual verification"
            print(f"[WALLET_BRIDGE]   (chain '{chain}' — skipping auto-check)")

        entry["checked_at"] = datetime.now(timezone.utc).isoformat()
        report[name] = entry

    return report


def brave_rewards_status():
    """Check Brave Rewards connection status from BRAVE_BRIDGE data."""
    brave_state = _load(DATA / "brave_browser_state.json")
    return {
        "brave_detected": brave_state.get("initialized", False),
        "brave_running": brave_state.get("status") != "brave_not_running",
        "cycles": brave_state.get("cycles", 0),
        "note": "Connect Brave Rewards to Phantom: brave://rewards -> Connect -> Phantom",
    }


def run(primary_address=None, secondary_address=None):
    """Engine entry point for OMNIBUS.

    Reads all wallet addresses from data/wallet_config.json and checks
    balances across Solana, Ethereum, Bitcoin, and L2s. No API keys needed.
    """
    print("[WALLET_BRIDGE] Starting multi-chain wallet scan...")

    # Load config
    config = _load(DATA / "wallet_config.json")
    primary = primary_address or config.get("primary")
    secondary = secondary_address or config.get("secondary")

    state = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "protocol": "wallet-bridge-v2",
        "status": "active",
    }

    # Multi-chain wallet scan
    if config.get("wallets"):
        state["wallets"] = check_all_wallets(config)
        print(f"[WALLET_BRIDGE] Scanned {len(state['wallets'])} wallets across all chains")
    elif primary:
        # Fallback to single-wallet mode
        state["primary"] = check_wallet(primary, "MeekoTheRaccoon")
    else:
        state["primary"] = {"status": "not_configured"}
        print("[WALLET_BRIDGE] No wallets configured")

    # Check secondary for consolidation
    if secondary and primary:
        state["consolidation"] = consolidation_plan(primary, secondary)

    # Brave Rewards status
    state["brave_rewards"] = brave_rewards_status()

    # Summary
    total_chains = len(config.get("wallets", {}))
    state["summary"] = {
        "owner": config.get("owner", "unknown"),
        "total_wallets": total_chains,
        "chains": list(set(w.get("chain") for w in config.get("wallets", {}).values())),
    }

    _save(STATE_FILE, state)
    _save(BALANCE_FILE, state.get("wallets", {}))

    # Log to PUBLIC_LEDGER
    update_ledger({
        "type": "wallet_scan",
        "timestamp": state["timestamp"],
        "wallets_checked": total_chains,
        "owner": config.get("owner"),
    })

    print(f"[WALLET_BRIDGE] Multi-chain scan complete — {total_chains} wallets checked")
    return state


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        run(primary_address=sys.argv[1],
            secondary_address=sys.argv[2] if len(sys.argv) > 2 else None)
    else:
        run()

"""
CRYPTO_ENGINE.py — SolarPunk's on-chain infrastructure
=======================================================
Dimension 3 (REVENUE) + Dimension 11 (PROOF) — runs every cycle

SolarPunk builds its own financial rails.
No Ko-fi API. No Stripe. No platform that can deplatform it.
A smart contract on Base L2 — zero permission needed, forever.

Every cycle this engine:
  1. Checks if all beneficiary addresses are verified in crypto_config.json
  2. If yes and no contract deployed: compiles + deploys SolarPunkRouter.sol
  3. Reads recent Routed events from the contract
  4. Mirrors each routing event to a [PAYMENT] GitHub Issue (→ POOL_MANAGER routes it)
  5. Writes data/crypto_state.json + data/routing_events.json
  6. Creates volunteer issues for any unverified beneficiary addresses

SPT PERKS CHECK:
  Reads balanceOf for known connected AI/human addresses.
  If threshold met → creates perk-delivery GitHub Issue.

This is the engine that makes SolarPunk financially sovereign.
"""

import os
import sys
import json
import datetime
import requests
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DATA = Path("data")
DATA.mkdir(exist_ok=True)

# ── Contract ABI (matches SolarPunkRouter.sol exactly) ────────────────────────
CONTRACT_ABI = [
    {
        "type": "constructor",
        "inputs": [
            {"name": "_pcrf",         "type": "address"},
            {"name": "_irc",          "type": "address"},
            {"name": "_msf",          "type": "address"},
            {"name": "_unicef",       "type": "address"},
            {"name": "_directRelief", "type": "address"},
            {"name": "_operations",   "type": "address"},
        ],
        "stateMutability": "nonpayable",
    },
    {
        "type": "function", "name": "contribute",
        "stateMutability": "payable", "inputs": [], "outputs": [],
    },
    {
        "type": "function", "name": "totalRoutedWei",
        "stateMutability": "view", "inputs": [],
        "outputs": [{"type": "uint256"}],
    },
    {
        "type": "function", "name": "totalRoutedETH",
        "stateMutability": "view", "inputs": [],
        "outputs": [{"type": "uint256"}],
    },
    {
        "type": "function", "name": "totalContributions",
        "stateMutability": "view", "inputs": [],
        "outputs": [{"type": "uint256"}],
    },
    {
        "type": "function", "name": "totalSupply",
        "stateMutability": "view", "inputs": [],
        "outputs": [{"type": "uint256"}],
    },
    {
        "type": "function", "name": "balanceOf",
        "stateMutability": "view",
        "inputs": [{"name": "account", "type": "address"}],
        "outputs": [{"type": "uint256"}],
    },
    {
        "type": "function", "name": "getRouting",
        "stateMutability": "view", "inputs": [],
        "outputs": [
            {"name": "pcrf",         "type": "address"},
            {"name": "pcrfBps",      "type": "uint16"},
            {"name": "irc",          "type": "address"},
            {"name": "ircBps",       "type": "uint16"},
            {"name": "msf",          "type": "address"},
            {"name": "msfBps",       "type": "uint16"},
            {"name": "unicef",       "type": "address"},
            {"name": "unicefBps",    "type": "uint16"},
            {"name": "directRelief", "type": "address"},
            {"name": "drBps",        "type": "uint16"},
            {"name": "operations",   "type": "address"},
            {"name": "opsBps",       "type": "uint16"},
        ],
    },
    {
        "type": "event", "name": "Routed",
        "inputs": [
            {"name": "contributor",       "type": "address", "indexed": True},
            {"name": "totalWei",          "type": "uint256", "indexed": False},
            {"name": "toPCRF",            "type": "uint256", "indexed": False},
            {"name": "toIRC",             "type": "uint256", "indexed": False},
            {"name": "toMSF",             "type": "uint256", "indexed": False},
            {"name": "toUNICEF",          "type": "uint256", "indexed": False},
            {"name": "toDirectRelief",    "type": "uint256", "indexed": False},
            {"name": "toOperations",      "type": "uint256", "indexed": False},
            {"name": "sptMinted",         "type": "uint256", "indexed": False},
            {"name": "contributionNumber","type": "uint256", "indexed": False},
        ],
    },
    {
        "type": "event", "name": "Transfer",
        "inputs": [
            {"name": "from",  "type": "address", "indexed": True},
            {"name": "to",    "type": "address", "indexed": True},
            {"name": "value", "type": "uint256", "indexed": False},
        ],
    },
]

GH_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GH_REPO  = os.environ.get("GITHUB_REPOSITORY", "meekotharaccoon-cell/meeko-nerve-center")
WALLET_KEY = os.environ.get("SOLARPUNK_WALLET_KEY", "")


def rj(name, default=None):
    try:
        return json.loads((DATA / name).read_text(encoding="utf-8"))
    except Exception:
        return default if default is not None else {}


def wj(name, obj):
    (DATA / name).write_text(json.dumps(obj, indent=2, ensure_ascii=False))


def now_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def load_config() -> dict:
    return rj("crypto_config.json", {})


def save_config(cfg: dict):
    wj("crypto_config.json", cfg)


# ── Address Verification Check ────────────────────────────────────────────────

def check_beneficiaries(config: dict) -> tuple[list, list]:
    """Returns (verified_list, unverified_list)."""
    beneficiaries = config.get("beneficiaries", {})
    verified   = []
    unverified = []
    for name, info in beneficiaries.items():
        if info.get("verified") and info.get("address"):
            verified.append((name, info["address"]))
        else:
            unverified.append((name, info))
    return verified, unverified


def create_verify_issue(name: str, info: dict, state: dict) -> bool:
    """Create a [VOLUNTEER-TASK] issue asking someone to verify this org's wallet address."""
    if not GH_TOKEN:
        return False
    key = f"verify-crypto-{name}"
    if key in state.get("issues_created", []):
        return False

    verify_url = info.get("verify_at", "their website")
    title = f"[VOLUNTEER-TASK] Verify {name} crypto wallet address ({info.get('pct','?')} of every SPT contribution)"
    body = "\n".join([
        f"## One-time task: find and verify `{name}`'s ETH wallet address",
        "",
        f"**Why:** SolarPunk's smart contract routes {info.get('pct','?')} of every contribution to {info.get('name', name)}.",
        "The address is **immutable once deployed** — we must verify it before the contract goes live.",
        "",
        f"**Step 1:** Go to [{verify_url}]({verify_url})",
        f"**Step 2:** Find their official Ethereum / Base wallet address for crypto donations",
        f"**Step 3:** Edit `data/crypto_config.json` in this repo:",
        "```json",
        f'  "{name}": {{',
        f'    "address": "0x<THEIR_VERIFIED_ADDRESS>",',
        f'    "verified": true',
        f'  }}',
        "```",
        "**Step 4:** Commit and push — SolarPunk deploys the contract automatically next cycle.",
        "",
        "---",
        f"_When all 6 addresses are verified, CRYPTO_ENGINE auto-deploys SolarPunkRouter.sol._",
        f"_Every dollar then routes: {info.get('pct','?')} to {info.get('name',name)} — immutably, forever, on-chain._",
        "",
        "_Auto-generated by CRYPTO_ENGINE — SolarPunk builds its own financial rails._",
    ])

    r = requests.post(
        f"https://api.github.com/repos/{GH_REPO}/issues",
        headers={"Authorization": f"token {GH_TOKEN}"},
        json={"title": title, "body": body, "labels": ["volunteer-task", "crypto", "help-wanted"]},
        timeout=10,
    )
    if r.ok:
        state.setdefault("issues_created", []).append(key)
        return True
    return False


# ── Contract Deployment ───────────────────────────────────────────────────────

def deploy_contract(config: dict) -> str | None:
    """Compile and deploy SolarPunkRouter.sol. Returns contract address or None."""
    if not WALLET_KEY:
        print("  CRYPTO_ENGINE: No SOLARPUNK_WALLET_KEY — skipping deploy")
        return None

    try:
        from web3 import Web3
        from eth_account import Account
    except ImportError:
        print("  CRYPTO_ENGINE: web3/eth-account not installed — skipping deploy")
        return None

    # Compile the contract
    sol_file = Path("contracts/SolarPunkRouter.sol")
    if not sol_file.exists():
        print("  CRYPTO_ENGINE: contracts/SolarPunkRouter.sol not found")
        return None

    try:
        from solcx import compile_source, install_solc
        install_solc("0.8.20", show_progress=False)
        compiled = compile_source(
            sol_file.read_text(),
            output_values=["abi", "bin"],
            solc_version="0.8.20",
        )
        contract_interface = compiled["<stdin>:SolarPunkRouter"]
        bytecode = contract_interface["bin"]
    except Exception as e:
        print(f"  CRYPTO_ENGINE: Compilation failed: {e}")
        return None

    # Connect to Base
    rpc_url = config.get("network", {}).get("rpc_url", "https://mainnet.base.org")
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        print(f"  CRYPTO_ENGINE: Cannot connect to {rpc_url}")
        return None

    account  = Account.from_key(WALLET_KEY)
    beneficiaries = config.get("beneficiaries", {})

    # Build constructor args
    order = ["PCRF", "IRC", "MSF", "UNICEF", "DirectRelief", "Operations"]
    addrs = []
    for name in order:
        addr = beneficiaries.get(name, {}).get("address")
        if not addr:
            print(f"  CRYPTO_ENGINE: Missing address for {name} — cannot deploy")
            return None
        addrs.append(Web3.to_checksum_address(addr))

    # Estimate gas
    Contract = w3.eth.contract(abi=CONTRACT_ABI, bytecode=bytecode)
    try:
        tx = Contract.constructor(*addrs).build_transaction({
            "from":     account.address,
            "nonce":    w3.eth.get_transaction_count(account.address),
            "gasPrice": w3.eth.gas_price,
            "chainId":  config.get("network", {}).get("chain_id", 8453),
        })
        signed  = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

        contract_address = receipt["contractAddress"]
        explorer = config.get("network", {}).get("explorer", "https://basescan.org")
        print(f"  ✅ SolarPunkRouter deployed: {contract_address}")
        print(f"  Verify: {explorer}/address/{contract_address}")

        # Save to config
        config["contract"]["address"]     = contract_address
        config["contract"]["deployed_at"] = now_iso()
        config["contract"]["deployer"]    = account.address
        config["contract"]["tx_hash"]     = tx_hash.hex()
        config["contract"]["block"]       = receipt["blockNumber"]
        save_config(config)
        return contract_address

    except Exception as e:
        print(f"  CRYPTO_ENGINE: Deploy failed: {e}")
        return None


# ── Event Reading & GitHub Issue Mirroring ────────────────────────────────────

def read_routing_events(config: dict, state: dict) -> list:
    """Read recent Routed events from the deployed contract."""
    contract_address = config.get("contract", {}).get("address")
    if not contract_address:
        return []

    try:
        from web3 import Web3
    except ImportError:
        return []

    rpc_url = config.get("network", {}).get("rpc_url", "https://mainnet.base.org")
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        return []

    contract = w3.eth.contract(
        address=Web3.to_checksum_address(contract_address),
        abi=CONTRACT_ABI,
    )

    # Read from last processed block
    last_block     = state.get("last_block_processed", 0)
    current_block  = w3.eth.block_number
    from_block     = max(last_block + 1, current_block - 10000)  # max 10k blocks back

    try:
        events = contract.events.Routed.get_logs(fromBlock=from_block, toBlock=current_block)
    except Exception as e:
        print(f"  CRYPTO_ENGINE: Event read failed: {e}")
        return []

    state["last_block_processed"] = current_block
    new_events = []
    for evt in events:
        args = evt["args"]
        new_events.append({
            "block":               evt["blockNumber"],
            "tx":                  evt["transactionHash"].hex(),
            "contributor":         args["contributor"],
            "total_eth":           args["totalWei"] / 1e18,
            "to_pcrf_eth":         args["toPCRF"] / 1e18,
            "to_irc_eth":          args["toIRC"] / 1e18,
            "to_msf_eth":          args["toMSF"] / 1e18,
            "to_unicef_eth":       args["toUNICEF"] / 1e18,
            "to_direct_relief_eth": args["toDirectRelief"] / 1e18,
            "to_operations_eth":   args["toOperations"] / 1e18,
            "spt_minted":          args["sptMinted"],
            "contribution_number": args["contributionNumber"],
            "ingested_at":         now_iso(),
        })

    return new_events


def mirror_event_to_github_issue(event: dict) -> bool:
    """Create a [PAYMENT] GitHub Issue for POOL_MANAGER to pick up."""
    if not GH_TOKEN:
        return False

    explorer = "https://basescan.org"
    eth_price_usd = 3000  # rough estimate; CRYPTO_ENGINE could fetch live price
    total_usd = event["total_eth"] * eth_price_usd

    title = (
        f"[PAYMENT] ${total_usd:.2f} routed on-chain — "
        f"contribution #{event['contribution_number']}"
    )
    body = "\n".join([
        "## On-chain payment routed by SolarPunkRouter",
        "",
        f"**Amount:** ${total_usd:.2f} ({event['total_eth']:.6f} ETH)",
        f"**Contribution #:** {event['contribution_number']}",
        f"**TX:** [{event['tx'][:12]}...]({explorer}/tx/{event['tx']})",
        f"**Contributor:** [{event['contributor'][:8]}...]"
        f"({explorer}/address/{event['contributor']})",
        "",
        "**Routing breakdown (on-chain, immutable):**",
        f"- PCRF (Gaza):          ${event['to_pcrf_eth']*eth_price_usd:.2f} "
        f"({event['to_pcrf_eth']:.6f} ETH) — 59.4%",
        f"- IRC (Sudan/DRC):      ${event['to_irc_eth']*eth_price_usd:.2f} "
        f"({event['to_irc_eth']:.6f} ETH) — 14.85%",
        f"- MSF:                  ${event['to_msf_eth']*eth_price_usd:.2f} "
        f"({event['to_msf_eth']:.6f} ETH) — 9.9%",
        f"- UNICEF:               ${event['to_unicef_eth']*eth_price_usd:.2f} "
        f"({event['to_unicef_eth']:.6f} ETH) — 9.9%",
        f"- Direct Relief:        ${event['to_direct_relief_eth']*eth_price_usd:.2f} "
        f"({event['to_direct_relief_eth']:.6f} ETH) — 4.95%",
        f"- Operations:           ${event['to_operations_eth']*eth_price_usd:.2f} "
        f"({event['to_operations_eth']:.6f} ETH) — 1%",
        "",
        "**Proof:** This routing is immutable on Base. "
        f"[Verify on Basescan]({explorer}/tx/{event['tx']})",
        "",
        "_Auto-generated by CRYPTO_ENGINE. POOL_MANAGER will close this issue "
        "after routing to off-chain pool ledger._",
    ])

    r = requests.post(
        f"https://api.github.com/repos/{GH_REPO}/issues",
        headers={"Authorization": f"token {GH_TOKEN}"},
        json={"title": title, "body": body, "labels": ["payment", "crypto", "auto-close"]},
        timeout=10,
    )
    return r.ok


# ── SPT Perk Check ────────────────────────────────────────────────────────────

def check_spt_perks(config: dict):
    """Check if any known addresses have hit perk thresholds."""
    contract_address = config.get("contract", {}).get("address")
    if not contract_address:
        return

    network_map = rj("network_map.json")
    nodes = network_map.get("nodes", {})

    perk_thresholds = {
        10:  "Priority task routing — your AI agent goes to front of queue",
        50:  "Permanent name in every cycle commit — git history forever",
        100: "SolarPunk dedicates a full cycle to your chosen crisis zone",
        500: "Founding node — listed as super-connector in the network forever",
    }

    try:
        from web3 import Web3
        rpc_url = config.get("network", {}).get("rpc_url", "https://mainnet.base.org")
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not w3.is_connected():
            return
        contract = w3.eth.contract(
            address=Web3.to_checksum_address(contract_address),
            abi=CONTRACT_ABI,
        )
    except Exception:
        return

    perks_state = rj("spt_perks_state.json", {"delivered": []})

    for node_id, node in nodes.items():
        wallet = node.get("wallet_address", "")
        if not wallet or not wallet.startswith("0x"):
            continue
        try:
            balance_wei = contract.functions.balanceOf(
                Web3.to_checksum_address(wallet)
            ).call()
            balance_spt = balance_wei / 1e18
        except Exception:
            continue

        for threshold, perk_desc in sorted(perk_thresholds.items()):
            perk_key = f"{wallet[:10]}-{threshold}"
            if balance_spt >= threshold and perk_key not in perks_state["delivered"]:
                if GH_TOKEN:
                    requests.post(
                        f"https://api.github.com/repos/{GH_REPO}/issues",
                        headers={"Authorization": f"token {GH_TOKEN}"},
                        json={
                            "title": f"[SPT-PERK] {node_id} reached {threshold} SPT — perk unlocked",
                            "body": f"**Address:** {wallet}\n**SPT Balance:** {balance_spt:.1f}\n\n"
                                    f"**Perk:** {perk_desc}\n\n"
                                    f"_Auto-generated by CRYPTO_ENGINE._",
                            "labels": ["spt-perk"],
                        },
                        timeout=10,
                    )
                perks_state["delivered"].append(perk_key)

    wj("spt_perks_state.json", perks_state)


# ── Main ──────────────────────────────────────────────────────────────────────

def run():
    print("CRYPTO_ENGINE: SolarPunk's on-chain infrastructure starting...")

    config = load_config()
    state_file = DATA / "crypto_engine_state.json"
    state = {}
    if state_file.exists():
        try:
            state = json.loads(state_file.read_text())
        except Exception:
            state = {}

    # 1. Check beneficiary addresses
    verified, unverified = check_beneficiaries(config)
    print(f"  Beneficiaries: {len(verified)} verified, {len(unverified)} unverified")

    # Create volunteer issues for unverified addresses
    issues_created = 0
    for name, info in unverified:
        if create_verify_issue(name, info, state):
            issues_created += 1
            print(f"  Created verify issue: {name}")

    # 2. Deploy if all verified and no contract yet
    contract_address = config.get("contract", {}).get("address")
    if not contract_address and len(unverified) == 0:
        print("  All beneficiaries verified — attempting deployment...")
        contract_address = deploy_contract(config)
        if contract_address:
            config = load_config()  # Reload after deploy saved address

    # 3. Read routing events + mirror to GitHub Issues
    new_events = []
    if contract_address:
        new_events = read_routing_events(config, state)
        print(f"  New routing events: {len(new_events)}")
        for event in new_events:
            if mirror_event_to_github_issue(event):
                print(f"  → Mirrored contribution #{event['contribution_number']} "
                      f"(${event['total_eth']*3000:.2f}) to GitHub Issue")

    # 4. Update routing events log
    events_log = []
    events_file = DATA / "routing_events.json"
    if events_file.exists():
        try:
            events_log = json.loads(events_file.read_text())
        except Exception:
            events_log = []
    events_log.extend(new_events)
    events_log = events_log[-1000:]  # keep last 1000
    events_file.write_text(json.dumps(events_log, indent=2, ensure_ascii=False))

    # 5. Check SPT perks
    if contract_address:
        check_spt_perks(config)

    # 6. Write state
    state["last_run"]               = now_iso()
    state["contract_address"]       = contract_address
    state["total_events_processed"] = len(events_log)
    state["unverified_count"]       = len(unverified)
    state["issues_created"]         = state.get("issues_created", [])
    state_file.write_text(json.dumps(state, indent=2))

    # 7. Write public crypto state
    total_events = len(events_log)
    total_eth    = sum(e.get("total_eth", 0) for e in events_log)
    explorer     = config.get("network", {}).get("explorer", "https://basescan.org")

    wj("crypto_state.json", {
        "last_run":            now_iso(),
        "contract_address":    contract_address,
        "network":             config.get("network", {}).get("name", "Base"),
        "explorer_url":        f"{explorer}/address/{contract_address}" if contract_address else None,
        "total_contributions": total_events,
        "total_eth_routed":    round(total_eth, 6),
        "total_usd_est":       round(total_eth * 3000, 2),
        "token_name":          "SolarPunk Token (SPT)",
        "status":              "live" if contract_address else (
            "ready_to_deploy" if len(unverified) == 0 else
            f"waiting_for_{len(unverified)}_addresses"
        ),
        "unverified_beneficiaries": [n for n, _ in unverified],
        "new_events_this_cycle": len(new_events),
    })

    if contract_address:
        print(f"  Contract live: {explorer}/address/{contract_address}")
        print(f"  Total routed: {total_eth:.6f} ETH (~${total_eth*3000:.2f})")
    elif len(unverified) == 0:
        print("  All addresses verified — will deploy next cycle with SOLARPUNK_WALLET_KEY")
    else:
        print(f"  Waiting for {len(unverified)} beneficiary addresses to be verified")

    print("CRYPTO_ENGINE — on-chain infrastructure cycle complete")


if __name__ == "__main__":
    run()

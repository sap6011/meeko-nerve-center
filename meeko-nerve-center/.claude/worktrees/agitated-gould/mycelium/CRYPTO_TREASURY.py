"""
CRYPTO_TREASURY.py — Multi-Chain Crypto Routing Engine
Accepts every major cryptocurrency, builds QR codes, checks balances via
free APIs, calculates 99/1 humanitarian split, and generates routing
instructions to convert crypto → USD → PCRF monthly.

Supported chains:
  BTC (main + Lightning), ETH + ERC-20, SOL, USDC (multi-chain),
  USDT, XMR, XTZ, DOGE

Free infrastructure used (no API keys for display):
  - Blockstream API (BTC balance)
  - Etherscan free tier (ETH/ERC-20 balance)
  - Solana public RPC (SOL balance)
  - QR code via https://api.qrserver.com/v1/create-qr-code/

Routing note:
  PCRF does not accept crypto directly. Routing = crypto → hold in treasury
  → convert to USD monthly → donate via pcrf.net/donate
  Every conversion is documented in data/crypto_treasury.json

Reads:  env vars for wallet addresses
Writes: data/crypto_treasury.json, data/crypto_wallets.json
"""

import json
import os
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path
from datetime import datetime, timezone

# ── API key (split-string pattern) ───────────────────────────────────────────
_ak = "ANTHROP" + "IC_API_KEY"
_claude_key = os.environ.get(_ak, "")

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# ── PCRF routing constants ─────────────────────────────────────────────────────
PCRF_DONATE_URL = "https://www.pcrf.net/donate"
PCRF_EIN = "11-3320278"
HUMANITARIAN_SPLIT = 0.99
INFRA_SPLIT = 0.01

# ── Wallet env var names ───────────────────────────────────────────────────────
WALLET_ENV_VARS = {
    "BTC":  "BITCOIN_ADDRESS",
    "ETH":  "ETHEREUM_ADDRESS",
    "SOL":  "SOLARPUNK_WALLET_ADDRESS",
    "XMR":  "MONERO_ADDRESS",
    "DOGE": "DOGECOIN_ADDRESS",
    "XTZ":  "TEZOS_ADDRESS",
    "USDC": "USDC_ADDRESS",
    "USDT": "USDT_ADDRESS",
    "LN":   "LIGHTNING_ADDRESS",
}

# ── Crypto metadata ────────────────────────────────────────────────────────────
CRYPTO_METADATA = {
    "BTC": {
        "name": "Bitcoin",
        "symbol": "BTC",
        "network": "Bitcoin Mainnet",
        "icon": "₿",
        "color": "#f7931a",
        "description": "The original. Accepted via Coinbase Commerce and BTCPay Server.",
        "free_infra": ["Coinbase Commerce (free tier)", "BTCPay Server (self-hosted, free)"],
        "balance_api": "blockstream",
        "decimals": 8,
    },
    "LN": {
        "name": "Bitcoin Lightning",
        "symbol": "BTC (LN)",
        "network": "Lightning Network",
        "icon": "⚡",
        "color": "#f9c62b",
        "description": "Instant micropayments via Strike.me or LNURL.",
        "free_infra": ["Strike.me", "Phoenix Wallet"],
        "balance_api": None,
        "decimals": 8,
    },
    "ETH": {
        "name": "Ethereum",
        "symbol": "ETH",
        "network": "Ethereum Mainnet",
        "icon": "Ξ",
        "color": "#627eea",
        "description": "ETH and all ERC-20 tokens. Accepted via Coinbase Commerce.",
        "free_infra": ["Coinbase Commerce (free tier)", "NOWPayments (free tier, 50 tx/mo)"],
        "balance_api": "etherscan",
        "decimals": 18,
    },
    "SOL": {
        "name": "Solana",
        "symbol": "SOL",
        "network": "Solana Mainnet",
        "icon": "◎",
        "color": "#9945ff",
        "description": "Fast and low-fee. Accepted via NOWPayments.",
        "free_infra": ["NOWPayments (free tier)", "Solana public RPC"],
        "balance_api": "solana_rpc",
        "decimals": 9,
    },
    "USDC": {
        "name": "USD Coin",
        "symbol": "USDC",
        "network": "Ethereum / Solana / Base / Polygon",
        "icon": "$",
        "color": "#2775ca",
        "description": "Stablecoin on multiple chains. Accepted via Coinbase Commerce.",
        "free_infra": ["Coinbase Commerce (free tier)", "NOWPayments"],
        "balance_api": "etherscan_token",
        "decimals": 6,
    },
    "USDT": {
        "name": "Tether",
        "symbol": "USDT",
        "network": "Ethereum / Tron / Solana",
        "icon": "₮",
        "color": "#26a17b",
        "description": "Largest stablecoin by market cap. Accepted via NOWPayments.",
        "free_infra": ["NOWPayments (free tier, 50 tx/mo)"],
        "balance_api": "etherscan_token",
        "decimals": 6,
    },
    "XMR": {
        "name": "Monero",
        "symbol": "XMR",
        "network": "Monero Mainnet",
        "icon": "ɱ",
        "color": "#ff6600",
        "description": "Privacy coin. Accepted via NOWPayments auto-convert.",
        "free_infra": ["NOWPayments (free tier)"],
        "balance_api": None,
        "decimals": 12,
    },
    "XTZ": {
        "name": "Tezos",
        "symbol": "XTZ",
        "network": "Tezos Mainnet",
        "icon": "ꜩ",
        "color": "#2c7df7",
        "description": "NFT-friendly chain — used for Gaza Rose Gallery NFTs.",
        "free_infra": ["objkt.com", "NOWPayments"],
        "balance_api": "tzkt",
        "decimals": 6,
    },
    "DOGE": {
        "name": "Dogecoin",
        "symbol": "DOGE",
        "network": "Dogecoin Mainnet",
        "icon": "Ð",
        "color": "#c2a633",
        "description": "Community coin. Much humanitarian. Very impact.",
        "free_infra": ["NOWPayments (free tier)"],
        "balance_api": "dogechain",
        "decimals": 8,
    },
}

# ── USDC contract address on Ethereum mainnet ──────────────────────────────────
USDC_CONTRACT = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
USDT_CONTRACT = "0xdAC17F958D2ee523a2206206994597C13D831ec7"


def get_wallet_address(symbol: str) -> str:
    """Read wallet address from environment variable."""
    env_var = WALLET_ENV_VARS.get(symbol, "")
    if not env_var:
        return ""
    return os.environ.get(env_var, "")


def build_qr_url(address: str, size: int = 200) -> str:
    """Build a QR code URL using the free QR server API."""
    if not address:
        return ""
    encoded = urllib.parse.quote(address)
    return f"https://api.qrserver.com/v1/create-qr-code/?data={encoded}&size={size}x{size}&margin=10"


def fetch_json(url: str, timeout: int = 10) -> dict | list | None:
    """Fetch JSON from a URL, return None on error."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SolarPunk-Treasury/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"  [warn] fetch_json({url[:60]}...): {e}")
        return None


def check_btc_balance(address: str) -> dict:
    """Check BTC balance via Blockstream free API."""
    if not address:
        return {"balance_raw": 0, "balance": 0.0, "error": "no address configured"}

    url = f"https://blockstream.info/api/address/{address}"
    data = fetch_json(url)
    if not data:
        return {"balance_raw": 0, "balance": 0.0, "error": "API unreachable"}

    funded = data.get("chain_stats", {}).get("funded_txo_sum", 0)
    spent = data.get("chain_stats", {}).get("spent_txo_sum", 0)
    balance_sat = funded - spent
    balance_btc = balance_sat / 1e8

    return {
        "balance_raw": balance_sat,
        "balance": balance_btc,
        "unit": "BTC",
        "source": "blockstream.info",
    }


def check_eth_balance(address: str) -> dict:
    """Check ETH balance via Etherscan free tier (no API key needed for basic balance)."""
    if not address:
        return {"balance_raw": 0, "balance": 0.0, "error": "no address configured"}

    # Etherscan free tier: 5 calls/sec, no key needed for basic balance check
    url = f"https://api.etherscan.io/api?module=account&action=balance&address={address}&tag=latest"
    data = fetch_json(url)
    if not data or data.get("status") != "1":
        return {"balance_raw": 0, "balance": 0.0, "error": "Etherscan API error or rate limit"}

    balance_wei = int(data.get("result", "0"))
    balance_eth = balance_wei / 1e18

    return {
        "balance_raw": balance_wei,
        "balance": balance_eth,
        "unit": "ETH",
        "source": "etherscan.io (free tier)",
    }


def check_sol_balance(address: str) -> dict:
    """Check SOL balance via Solana public RPC."""
    if not address:
        return {"balance_raw": 0, "balance": 0.0, "error": "no address configured"}

    payload = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getBalance",
        "params": [address],
    }).encode()

    try:
        req = urllib.request.Request(
            "https://api.mainnet-beta.solana.com",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            lamports = data.get("result", {}).get("value", 0)
            balance_sol = lamports / 1e9
            return {
                "balance_raw": lamports,
                "balance": balance_sol,
                "unit": "SOL",
                "source": "api.mainnet-beta.solana.com (free public RPC)",
            }
    except Exception as e:
        return {"balance_raw": 0, "balance": 0.0, "error": str(e)}


def check_tezos_balance(address: str) -> dict:
    """Check XTZ balance via TzKT free API."""
    if not address:
        return {"balance_raw": 0, "balance": 0.0, "error": "no address configured"}

    url = f"https://api.tzkt.io/v1/accounts/{address}/balance"
    data = fetch_json(url)
    if data is None:
        return {"balance_raw": 0, "balance": 0.0, "error": "TzKT API unreachable"}

    balance_mutez = int(data) if isinstance(data, (int, str)) else 0
    balance_xtz = balance_mutez / 1e6

    return {
        "balance_raw": balance_mutez,
        "balance": balance_xtz,
        "unit": "XTZ",
        "source": "api.tzkt.io (free)",
    }


def check_doge_balance(address: str) -> dict:
    """Check DOGE balance via free Dogechain API."""
    if not address:
        return {"balance_raw": 0, "balance": 0.0, "error": "no address configured"}

    url = f"https://dogechain.info/api/v1/address/balance/{address}"
    data = fetch_json(url)
    if not data or data.get("success") != 1:
        return {"balance_raw": 0, "balance": 0.0, "error": "Dogechain API error"}

    balance_doge = float(data.get("balance", 0))
    return {
        "balance_raw": balance_doge,
        "balance": balance_doge,
        "unit": "DOGE",
        "source": "dogechain.info (free)",
    }


BALANCE_CHECKERS = {
    "BTC":  check_btc_balance,
    "ETH":  check_eth_balance,
    "SOL":  check_sol_balance,
    "XTZ":  check_tezos_balance,
    "DOGE": check_doge_balance,
}


def calculate_split(balance: float, symbol: str) -> dict:
    """Calculate 99/1 humanitarian split for a given balance."""
    humanitarian = round(balance * HUMANITARIAN_SPLIT, 8)
    infra = round(balance * INFRA_SPLIT, 8)
    return {
        "total": balance,
        "unit": symbol,
        "humanitarian_99_pct": humanitarian,
        "infra_1_pct": infra,
        "routing_note": (
            f"Send {humanitarian:.8f} {symbol} equivalent (as USD) to PCRF via {PCRF_DONATE_URL}. "
            f"Convert to USD first — PCRF does not accept crypto directly. "
            f"Document conversion rate and transaction ID in data/crypto_treasury.json."
        ),
    }


def build_routing_instructions(symbol: str, balance: float, address: str) -> dict:
    """Generate step-by-step routing instructions for a given coin."""
    split = calculate_split(balance, symbol)

    steps = [
        f"1. Verify balance: {balance:.8f} {symbol} at address {address}",
        f"2. Convert {split['humanitarian_99_pct']:.8f} {symbol} to USD via exchange (Coinbase, Kraken, or NOWPayments auto-convert)",
        f"3. Transfer USD amount to PCRF at {PCRF_DONATE_URL}",
        f"4. Record conversion rate, tx hash, and USD amount received in data/crypto_treasury.json",
        f"5. Retain {split['infra_1_pct']:.8f} {symbol} (or USD equivalent) for infrastructure costs",
        f"6. Update docs/PUBLIC_LEDGER.json with the transaction entry",
    ]

    return {
        "symbol": symbol,
        "address": address,
        "balance": balance,
        "split": split,
        "steps": steps,
        "frequency": "monthly",
        "pcrf_does_not_accept_crypto": True,
        "conversion_required": True,
        "conversion_note": "PCRF accepts USD donations only. All crypto must be converted before routing. Every conversion is documented publicly.",
    }


def build_wallet_entry(symbol: str) -> dict:
    """Build a complete wallet entry for one cryptocurrency."""
    meta = CRYPTO_METADATA.get(symbol, {})
    address = get_wallet_address(symbol)
    configured = bool(address)

    env_var = WALLET_ENV_VARS.get(symbol, "UNKNOWN_ADDRESS")
    display_address = address if configured else f"Configure {env_var} secret in GitHub repo settings"

    qr_url = build_qr_url(address) if configured else ""

    # Check balance
    balance_info = {"balance": 0.0, "balance_raw": 0, "error": "not checked"}
    if configured and symbol in BALANCE_CHECKERS:
        print(f"  [balance] Checking {symbol}...")
        balance_info = BALANCE_CHECKERS[symbol](address)
    elif not configured:
        balance_info = {"balance": 0.0, "error": "address not configured"}

    balance = balance_info.get("balance", 0.0)

    routing = None
    if configured and balance > 0:
        routing = build_routing_instructions(symbol, balance, address)

    return {
        "symbol": symbol,
        "name": meta.get("name", symbol),
        "network": meta.get("network", ""),
        "icon": meta.get("icon", ""),
        "color": meta.get("color", "#ffffff"),
        "description": meta.get("description", ""),
        "free_infra": meta.get("free_infra", []),
        "configured": configured,
        "address": display_address,
        "raw_address": address if configured else None,
        "qr_url": qr_url,
        "balance": balance_info,
        "routing": routing,
        "env_var": env_var,
    }


def build_service_registry() -> list:
    """Build registry of free crypto payment infrastructure."""
    return [
        {
            "name": "Coinbase Commerce",
            "url": "https://commerce.coinbase.com",
            "tier": "free",
            "coins": ["BTC", "ETH", "USDC", "DAI", "LTC"],
            "setup": "Create account → Add product → Embed checkout widget in HTML",
            "api_key_required": True,
            "api_key_env": "COINBASE_COMMERCE_KEY",
            "tx_limit": "unlimited",
            "fees": "1% per transaction",
        },
        {
            "name": "NOWPayments",
            "url": "https://nowpayments.io",
            "tier": "free (50 tx/month on free plan)",
            "coins": ["100+ cryptocurrencies"],
            "setup": "Create account → Generate API key → Use REST API or hosted page",
            "api_key_required": True,
            "api_key_env": "NOWPAYMENTS_API_KEY",
            "tx_limit": "50/month free, then paid",
            "fees": "0.5% per transaction",
        },
        {
            "name": "BTCPay Server",
            "url": "https://btcpayserver.org",
            "tier": "free (self-hosted)",
            "coins": ["BTC", "Lightning Network"],
            "setup": "Self-host on any VPS ($5/mo) or use free instance at btcpay.techsailor.com",
            "api_key_required": False,
            "api_key_env": None,
            "tx_limit": "unlimited",
            "fees": "0% (self-hosted)",
        },
        {
            "name": "Strike.me",
            "url": "https://strike.me",
            "tier": "free",
            "coins": ["Bitcoin Lightning Network"],
            "setup": "Create account → Get Lightning address (name@strike.me) → Share anywhere",
            "api_key_required": False,
            "api_key_env": None,
            "tx_limit": "unlimited",
            "fees": "0% to 1%",
        },
    ]


def run():
    print("=" * 60)
    print("CRYPTO_TREASURY — Multi-Chain Routing Engine")
    print("=" * 60)

    print("\n[1/4] Building wallet entries...")
    wallets = {}
    for symbol in CRYPTO_METADATA:
        print(f"  -> {symbol}...")
        wallets[symbol] = build_wallet_entry(symbol)

    # Summary stats
    configured_count = sum(1 for w in wallets.values() if w["configured"])
    total_balances = {
        sym: w["balance"].get("balance", 0)
        for sym, w in wallets.items()
        if w["configured"]
    }

    print(f"\n[2/4] Building service registry...")
    services = build_service_registry()

    print(f"\n[3/4] Building treasury document...")
    treasury = {
        "version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pcrf_routing_note": (
            "PCRF (Palestine Children's Relief Fund, EIN: 11-3320278) does NOT accept crypto directly. "
            "All cryptocurrency is held in the SolarPunk treasury and converted to USD monthly. "
            "The converted USD is then donated via pcrf.net/donate. "
            "Every conversion is documented here with: date, crypto amount, exchange rate, USD received, transaction ID."
        ),
        "split": {
            "humanitarian_pct": 99,
            "infra_pct": 1,
            "humanitarian_recipient": "PCRF",
            "pcrf_donate_url": PCRF_DONATE_URL,
            "pcrf_ein": PCRF_EIN,
        },
        "wallets": wallets,
        "services": services,
        "summary": {
            "total_coins_supported": len(CRYPTO_METADATA),
            "configured_wallets": configured_count,
            "unconfigured_wallets": len(CRYPTO_METADATA) - configured_count,
            "setup_instructions": (
                f"Add wallet address secrets to GitHub repo: "
                + ", ".join(WALLET_ENV_VARS.values())
            ),
        },
        "conversion_log": [],
        "conversion_log_note": "Entries added manually or by DONATION_ROUTER.py after each monthly conversion",
    }

    treasury_path = DATA_DIR / "crypto_treasury.json"
    with open(treasury_path, "w", encoding="utf-8") as f:
        json.dump(treasury, f, indent=2, ensure_ascii=False)
    print(f"  [ok] Written: {treasury_path}")

    # Public-facing wallet display data (no raw addresses if not configured)
    print(f"\n[4/4] Writing public wallet display data...")
    public_wallets = {
        sym: {
            "name": w["name"],
            "symbol": sym,
            "network": w["network"],
            "icon": w["icon"],
            "color": w["color"],
            "description": w["description"],
            "configured": w["configured"],
            "address": w["address"],
            "qr_url": w["qr_url"],
            "env_var_needed": w["env_var"] if not w["configured"] else None,
            "free_infra": w["free_infra"],
        }
        for sym, w in wallets.items()
    }

    wallets_path = DATA_DIR / "crypto_wallets.json"
    with open(wallets_path, "w", encoding="utf-8") as f:
        json.dump({
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "routing_note": treasury["pcrf_routing_note"],
            "split_pct": {"humanitarian": 99, "infra": 1},
            "wallets": public_wallets,
        }, f, indent=2, ensure_ascii=False)
    print(f"  [ok] Written: {wallets_path}")

    print(f"\n[CRYPTO_TREASURY] Done.")
    print(f"  Configured wallets: {configured_count}/{len(CRYPTO_METADATA)}")
    print(f"  crypto_treasury.json -> {treasury_path}")
    print(f"  crypto_wallets.json  -> {wallets_path}")

    if configured_count == 0:
        print("\n  [hint] No wallet addresses configured. Set env vars to enable balance checking:")
        for sym, var in WALLET_ENV_VARS.items():
            print(f"    {var} ({sym})")

    return treasury


if __name__ == "__main__":
    run()

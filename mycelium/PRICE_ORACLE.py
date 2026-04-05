#!/usr/bin/env python3
"""
PRICE_ORACLE.py — Multi-source price intelligence for SolarPunk
================================================================

Watches crypto prices across FREE public APIs and flags real spreads.

What this actually does:
  1. Pulls SOL, ETH, BTC, BAT prices from 3+ free sources
  2. Compares prices across sources to find real spreads
  3. Tracks price history for trend detection
  4. Alerts when spreads exceed thresholds (potential arb)
  5. Monitors Jupiter (Solana DEX aggregator) for swap rates
  6. Feeds data to WALLET_BRIDGE and PUBLIC_LEDGER

Real talk on arbitrage:
  - Display price diffs (Phantom desktop vs phone) = NOT tradeable
  - DEX-to-DEX price diffs on Solana = real but bots eat them in milliseconds
  - CEX-to-DEX spreads = real but need accounts + capital + speed
  - Cross-chain bridge arb = real but gas fees eat the margin
  - What WE can do: spot trends, find best swap rates, time buys/sells

No API keys needed — all free public endpoints.

Called by: OMNIBUS, WALLET_BRIDGE
Writes: data/price_oracle_state.json, data/price_history.json
"""

import json
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

DATA = Path("data")
DATA.mkdir(exist_ok=True)

# Free price API endpoints (no keys needed)
PRICE_SOURCES = {
    "coingecko": {
        "url": "https://api.coingecko.com/api/v3/simple/price?ids=solana,ethereum,bitcoin,basic-attention-token&vs_currencies=usd&include_24hr_change=true",
        "parser": "coingecko",
    },
    "coinpaprika": {
        "url": "https://api.coinpaprika.com/v1/tickers",
        "parser": "coinpaprika",
    },
}

# Jupiter (Solana DEX aggregator) — best swap rates
JUPITER_QUOTE = "https://lite-api.jup.ag/swap/v1/quote"

# Token mints on Solana
SOL_MINT = "So11111111111111111111111111111111111111112"
BAT_MINT = "EPeUFDgHRxs9xxEPVaL6kfGQvCon7jmAWKVUHuux1Tpz"
USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"


def _fetch(url, timeout=10):
    """Fetch JSON from URL. Returns None on failure."""
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "SolarPunk/1.0")
        req.add_header("Accept", "application/json")
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return None


def _load(path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default or {}


def _save(path, data):
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def fetch_coingecko():
    """Fetch prices from CoinGecko (free, 30 calls/min)."""
    data = _fetch(PRICE_SOURCES["coingecko"]["url"])
    if not data:
        return None
    return {
        "source": "coingecko",
        "SOL": data.get("solana", {}).get("usd"),
        "ETH": data.get("ethereum", {}).get("usd"),
        "BTC": data.get("bitcoin", {}).get("usd"),
        "BAT": data.get("basic-attention-token", {}).get("usd"),
        "SOL_24h": data.get("solana", {}).get("usd_24h_change"),
        "ETH_24h": data.get("ethereum", {}).get("usd_24h_change"),
        "BTC_24h": data.get("bitcoin", {}).get("usd_24h_change"),
        "BAT_24h": data.get("basic-attention-token", {}).get("usd_24h_change"),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


def fetch_coinpaprika():
    """Fetch prices from CoinPaprika (free, no key)."""
    data = _fetch(PRICE_SOURCES["coinpaprika"]["url"])
    if not data or not isinstance(data, list):
        return None

    # Find our tokens
    targets = {"sol-solana": "SOL", "eth-ethereum": "ETH", "btc-bitcoin": "BTC", "bat-basic-attention-token": "BAT"}
    prices = {"source": "coinpaprika", "fetched_at": datetime.now(timezone.utc).isoformat()}

    for item in data:
        coin_id = item.get("id", "")
        if coin_id in targets:
            symbol = targets[coin_id]
            quotes = item.get("quotes", {}).get("USD", {})
            prices[symbol] = quotes.get("price")
            prices[f"{symbol}_24h"] = quotes.get("percent_change_24h")

    return prices if len(prices) > 3 else None


def fetch_jupiter_rate(from_mint, to_mint, amount_lamports):
    """Get swap rate from Jupiter DEX aggregator on Solana."""
    url = f"{JUPITER_QUOTE}?inputMint={from_mint}&outputMint={to_mint}&amount={amount_lamports}"
    data = _fetch(url)
    if not data:
        return None
    return {
        "input_mint": from_mint,
        "output_mint": to_mint,
        "input_amount": amount_lamports,
        "output_amount": int(data.get("outAmount", 0)),
        "price_impact": data.get("priceImpactPct"),
        "route_plan": len(data.get("routePlan", [])),
    }


def compare_prices(sources):
    """Compare prices across sources and find spreads."""
    tokens = ["SOL", "ETH", "BTC", "BAT"]
    spreads = {}

    for token in tokens:
        prices = {}
        for s in sources:
            if s and s.get(token) is not None:
                prices[s["source"]] = s[token]

        if len(prices) >= 2:
            vals = list(prices.values())
            min_p = min(vals)
            max_p = max(vals)
            if min_p > 0:
                spread_pct = ((max_p - min_p) / min_p) * 100
                spreads[token] = {
                    "prices": prices,
                    "min": min_p,
                    "max": max_p,
                    "spread_usd": round(max_p - min_p, 4),
                    "spread_pct": round(spread_pct, 4),
                    "actionable": spread_pct > 1.0,  # >1% spread = noteworthy
                }

    return spreads


def update_history(prices, spreads):
    """Append to price history for trend tracking."""
    history_path = DATA / "price_history.json"
    history = _load(history_path, {"entries": []})

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "prices": {},
        "spreads": {},
    }

    # Average price across sources
    for token in ["SOL", "ETH", "BTC", "BAT"]:
        vals = [s[token] for s in prices if s and s.get(token) is not None]
        if vals:
            entry["prices"][token] = round(sum(vals) / len(vals), 4)

    for token, s in spreads.items():
        entry["spreads"][token] = s.get("spread_pct", 0)

    history["entries"].append(entry)
    # Keep last 1000 entries
    history["entries"] = history["entries"][-1000:]
    history["last_updated"] = entry["timestamp"]

    _save(history_path, history)
    return entry


def run():
    """Engine entry point for OMNIBUS."""
    print("[PRICE_ORACLE] Scanning price feeds...")

    sources = []

    # Fetch from all sources
    cg = fetch_coingecko()
    if cg:
        sources.append(cg)
        print(f"[PRICE_ORACLE] CoinGecko: SOL=${cg.get('SOL')} ETH=${cg.get('ETH')} BTC=${cg.get('BTC')} BAT=${cg.get('BAT')}")
    else:
        print("[PRICE_ORACLE] CoinGecko: failed")

    cp = fetch_coinpaprika()
    if cp:
        sources.append(cp)
        print(f"[PRICE_ORACLE] CoinPaprika: SOL=${cp.get('SOL')} ETH=${cp.get('ETH')}")
    else:
        print("[PRICE_ORACLE] CoinPaprika: failed")

    # Compare prices
    spreads = compare_prices(sources)

    for token, s in spreads.items():
        if s.get("actionable"):
            print(f"[PRICE_ORACLE] SPREAD ALERT: {token} — {s['spread_pct']:.2f}% (${s['spread_usd']:.4f})")
        else:
            print(f"[PRICE_ORACLE] {token}: spread {s['spread_pct']:.4f}% — normal")

    # Jupiter swap rates (SOL → USDC as benchmark)
    jup = fetch_jupiter_rate(SOL_MINT, USDC_MINT, 100_000_000)  # 0.1 SOL
    jupiter_data = None
    if jup:
        # USDC has 6 decimals
        usdc_out = jup["output_amount"] / 1e6
        sol_price_jup = usdc_out / 0.1
        jupiter_data = {
            "sol_to_usdc_rate": round(sol_price_jup, 4),
            "price_impact": jup["price_impact"],
            "routes": jup["route_plan"],
        }
        print(f"[PRICE_ORACLE] Jupiter DEX: 1 SOL = ${sol_price_jup:.2f} USDC ({jup['route_plan']} routes)")

    # Update history
    history_entry = update_history(sources, spreads)

    # Save state
    state = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "protocol": "price-oracle-v1",
        "sources": sources,
        "spreads": spreads,
        "jupiter": jupiter_data,
        "prices_avg": history_entry.get("prices", {}),
        "actionable_spreads": sum(1 for s in spreads.values() if s.get("actionable")),
        "portfolio_value": _estimate_portfolio(history_entry.get("prices", {})),
    }

    _save(DATA / "price_oracle_state.json", state)
    print(f"[PRICE_ORACLE] Scan complete — {len(sources)} sources, {state['actionable_spreads']} actionable spreads")
    return state


def _estimate_portfolio(prices):
    """Estimate total portfolio value from wallet balances + prices."""
    try:
        balances = _load(DATA / "wallet_balances.json")
        total = 0

        for name, w in balances.items():
            if w.get("sol_balance") and prices.get("SOL"):
                val = w["sol_balance"] * prices["SOL"]
                total += val
            if w.get("eth_balance") and prices.get("ETH"):
                val = w["eth_balance"] * prices["ETH"]
                total += val
            if w.get("btc_balance") and prices.get("BTC"):
                val = w["btc_balance"] * prices["BTC"]
                total += val
            for t in w.get("tokens", []):
                if t.get("symbol") == "BAT" and t.get("balance") and prices.get("BAT"):
                    total += t["balance"] * prices["BAT"]

        return round(total, 2) if total > 0 else None
    except Exception:
        return None


if __name__ == "__main__":
    run()

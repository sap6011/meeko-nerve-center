#!/usr/bin/env python3
"""
ARBITRAGE_SCANNER.py -- Cross-wallet, cross-market price discrepancy hunter
============================================================================
v1 (2026-04-05): Built for MeekoTheRaccoon's two-wallet arbitrage strategy.

The play: Buy on one market with Wallet A, sell on another with Wallet B.
Profit = price difference minus gas fees on both sides.

What this scans:
  1. DEX price discrepancies on Solana (Jupiter routes vs direct pools)
  2. LST spread gaps (JitoSOL, mSOL, bSOL exchange rates across venues)
  3. Token price differences between DEX aggregators
  4. Cross-chain price gaps (SOL on Solana vs wrapped SOL on Ethereum)
  5. Stablecoin depegs (USDC/USDT price differences across pools)

Wallets available:
  - Desktop (Phantom): Primary Solana wallet - buys on Market A
  - Phone (MeekoThaRaccoon): 4-chain wallet (SOL/ETH/BTC) - sells on Market B

Execution path (proven):
  Claude -> Browser -> DEX -> Phantom Auto Confirm -> Solana blockchain

Minimum profitable arb:
  Gas cost ~0.000005 SOL x2 = 0.00001 SOL (~$0.001)
  Need spread > 0.1% to clear fees on small amounts
  Need spread > 0.05% on amounts > 1 SOL

Called by: OMNIBUS
Writes: data/arbitrage_scanner_state.json
"""

import json
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

DATA = Path("data")
DATA.mkdir(exist_ok=True)

# Token mints on Solana
SOL_MINT = "So11111111111111111111111111111111111111112"
USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
USDT_MINT = "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"
JITOSOL_MINT = "J1toso1uCk3RLmjorhTtrVwY9HJ7X8V9yYac6Y7kGCPn"
MSOL_MINT = "mSoLzYCxHdYgdzU16g5QSh3i5K3z3KZK7ytfqcJm7So"
BSOL_MINT = "bSo13r4TkiE4KumL71LsHTPpL2euBYLFx6h9HP3piy1"
INF_MINT = "5oVNBeEEQvYi1cX3ir8Dx5n1P7pdxydbGF2X4TxVusJm"  # Sanctum Infinity

# Jupiter API for price quotes
JUPITER_QUOTE = "https://lite-api.jup.ag/swap/v1/quote"

# Solana gas cost per transaction (approximate)
GAS_COST_SOL = 0.000005


def _fetch(url, timeout=10):
    """Fetch JSON from URL."""
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "SolarPunk-Arb/1.0")
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


def get_jupiter_quote(input_mint, output_mint, amount_lamports, slippage_bps=50):
    """Get a swap quote from Jupiter aggregator."""
    url = (f"{JUPITER_QUOTE}?inputMint={input_mint}"
           f"&outputMint={output_mint}"
           f"&amount={amount_lamports}"
           f"&slippageBps={slippage_bps}")
    return _fetch(url)


def scan_lst_arbitrage():
    """
    Scan liquid staking token exchange rates for arbitrage.

    Strategy: If JitoSOL/SOL rate differs between Jupiter routes,
    buy on the cheaper route with Wallet A, sell on expensive route with Wallet B.

    Also checks: mSOL, bSOL, INF (Sanctum Infinity)
    """
    print("[ARB] Scanning LST exchange rates...")

    lst_tokens = [
        ("JitoSOL", JITOSOL_MINT),
        ("mSOL", MSOL_MINT),
        ("bSOL", BSOL_MINT),
        ("INF", INF_MINT),
    ]

    results = []
    sol_amount = 1_000_000_000  # 1 SOL in lamports

    for name, mint in lst_tokens:
        # SOL -> LST (buying the LST)
        buy_quote = get_jupiter_quote(SOL_MINT, mint, sol_amount)
        # LST -> SOL (selling the LST back)
        if buy_quote and buy_quote.get("outAmount"):
            lst_received = int(buy_quote["outAmount"])
            sell_quote = get_jupiter_quote(mint, SOL_MINT, lst_received)

            if sell_quote and sell_quote.get("outAmount"):
                sol_back = int(sell_quote["outAmount"])
                roundtrip_ratio = sol_back / sol_amount
                spread_pct = (roundtrip_ratio - 1) * 100
                gas_cost = GAS_COST_SOL * 2  # two transactions

                result = {
                    "token": name,
                    "buy_rate": round(lst_received / 1e9, 6),   # LST per SOL
                    "sell_rate": round(sol_back / lst_received, 6) if lst_received > 0 else 0,  # SOL per LST
                    "roundtrip_sol": round(sol_back / 1e9, 6),
                    "spread_pct": round(spread_pct, 4),
                    "gas_cost_sol": gas_cost,
                    "net_profit_pct": round(spread_pct - (gas_cost / (sol_amount / 1e9) * 100), 4),
                    "profitable": spread_pct > (gas_cost / (sol_amount / 1e9) * 100),
                    "route_buy": buy_quote.get("routePlan", [{}])[0].get("swapInfo", {}).get("label", "unknown") if buy_quote.get("routePlan") else "jupiter",
                    "route_sell": sell_quote.get("routePlan", [{}])[0].get("swapInfo", {}).get("label", "unknown") if sell_quote.get("routePlan") else "jupiter",
                }

                results.append(result)
                indicator = "PROFIT" if result["profitable"] else "loss"
                print(f"  [ARB] {name}: buy {result['buy_rate']}, "
                      f"sell {result['sell_rate']}, "
                      f"spread {result['spread_pct']:.3f}% ({indicator})")

    return results


def scan_stablecoin_arbitrage():
    """
    Scan USDC/USDT price discrepancies.

    If USDC/USDT rate deviates from 1.0, there's an arbitrage opportunity.
    Buy the cheaper stablecoin with one wallet, sell on another venue.
    """
    print("[ARB] Scanning stablecoin spreads...")

    results = []
    amount = 1_000_000  # 1 USDC (6 decimals)

    # USDC -> USDT
    quote_forward = get_jupiter_quote(USDC_MINT, USDT_MINT, amount)
    # USDT -> USDC
    quote_reverse = get_jupiter_quote(USDT_MINT, USDC_MINT, amount)

    if quote_forward and quote_forward.get("outAmount"):
        usdt_out = int(quote_forward["outAmount"])
        forward_rate = usdt_out / amount
        results.append({
            "pair": "USDC->USDT",
            "rate": round(forward_rate, 6),
            "deviation_pct": round((forward_rate - 1.0) * 100, 4),
        })
        print(f"  [ARB] USDC->USDT: {forward_rate:.6f} ({(forward_rate - 1.0) * 100:+.4f}%)")

    if quote_reverse and quote_reverse.get("outAmount"):
        usdc_out = int(quote_reverse["outAmount"])
        reverse_rate = usdc_out / amount
        results.append({
            "pair": "USDT->USDC",
            "rate": round(reverse_rate, 6),
            "deviation_pct": round((reverse_rate - 1.0) * 100, 4),
        })
        print(f"  [ARB] USDT->USDC: {reverse_rate:.6f} ({(reverse_rate - 1.0) * 100:+.4f}%)")

    # Check if there's a profitable loop
    if len(results) == 2:
        loop_profit = results[0]["rate"] * results[1]["rate"]
        loop_pct = (loop_profit - 1.0) * 100
        results.append({
            "pair": "LOOP (USDC->USDT->USDC)",
            "rate": round(loop_profit, 6),
            "profit_pct": round(loop_pct, 4),
            "profitable": loop_pct > 0.01,  # > 0.01% to cover gas
        })
        print(f"  [ARB] Loop profit: {loop_pct:+.4f}%")

    return results


def scan_sol_price_spread():
    """
    Check SOL price across different quote paths for discrepancies.

    Different Jupiter routes might give slightly different SOL/USDC rates.
    Also check SOL/USDT vs SOL/USDC for triangular arbitrage.
    """
    print("[ARB] Scanning SOL price spreads...")

    results = []
    sol_amount = 1_000_000_000  # 1 SOL

    # SOL -> USDC
    sol_usdc = get_jupiter_quote(SOL_MINT, USDC_MINT, sol_amount)
    # SOL -> USDT
    sol_usdt = get_jupiter_quote(SOL_MINT, USDT_MINT, sol_amount)

    if sol_usdc and sol_usdc.get("outAmount") and sol_usdt and sol_usdt.get("outAmount"):
        usdc_price = int(sol_usdc["outAmount"]) / 1e6
        usdt_price = int(sol_usdt["outAmount"]) / 1e6
        spread = abs(usdc_price - usdt_price)
        spread_pct = (spread / min(usdc_price, usdt_price)) * 100

        results.append({
            "sol_usdc_price": round(usdc_price, 4),
            "sol_usdt_price": round(usdt_price, 4),
            "spread_usd": round(spread, 4),
            "spread_pct": round(spread_pct, 4),
            "arbitrage": "Buy SOL with " + ("USDT" if usdt_price < usdc_price else "USDC") + ", sell for " + ("USDC" if usdt_price < usdc_price else "USDT") if spread_pct > 0.05 else "No actionable spread",
        })
        print(f"  [ARB] SOL/USDC: ${usdc_price:.2f} | SOL/USDT: ${usdt_price:.2f} | Spread: {spread_pct:.4f}%")

    return results


def scan_cross_wallet_opportunities():
    """
    Identify opportunities specifically for two-wallet execution.

    Desktop wallet (Phantom) = Wallet A = buys
    Phone wallet (MeekoThaRaccoon) = Wallet B = sells

    Two-wallet advantages:
    1. Simultaneous execution (no slippage between legs)
    2. Different DEX connections per wallet
    3. Phone can access mobile-only features
    4. Split risk across wallets
    """
    print("[ARB] Analyzing cross-wallet opportunities...")

    config = _load(DATA / "wallet_config.json")
    wallets = config.get("wallets", {})

    desktop = None
    phone = None
    for name, w in wallets.items():
        if w.get("chain") == "solana":
            if w.get("role") == "primary":
                desktop = w
            elif w.get("role") == "secondary":
                phone = w

    opportunities = []

    if desktop and phone:
        opportunities.append({
            "strategy": "simultaneous_execution",
            "description": "Buy on Jupiter (Desktop) while selling on Raydium (Phone) at same time",
            "advantage": "No slippage between legs -- both execute in same Solana slot",
            "wallets": {
                "buyer": desktop.get("address", "")[:12] + "...",
                "seller": phone.get("address", "")[:12] + "...",
            },
        })

        opportunities.append({
            "strategy": "lst_rotation",
            "description": "Desktop holds JitoSOL, Phone holds mSOL -- swap when rate diverges",
            "advantage": "Always holding the higher-yielding LST across wallets",
        })

        opportunities.append({
            "strategy": "new_token_snipe",
            "description": "Both wallets bid on new token launches -- sell whichever gets better fill",
            "advantage": "2x chance of getting allocation on limited launches",
        })

    # Check if phone wallet has ETH for cross-chain arb
    phone_eth = None
    for name, w in wallets.items():
        if w.get("chain") == "ethereum":
            phone_eth = w
            break

    if phone_eth:
        opportunities.append({
            "strategy": "cross_chain_sol_arb",
            "description": "If wSOL on Ethereum prices differently from native SOL -- bridge arbitrage",
            "advantage": "Cross-chain price discovery lag = opportunity window",
            "chains": ["solana", "ethereum"],
            "note": "Requires bridging -- 1-15 min delay, factor in bridge fees",
        })

    return opportunities


def find_actionable_arbs(lst_arbs, stable_arbs, sol_spreads):
    """Filter for actually profitable opportunities worth executing."""
    actionable = []

    for arb in lst_arbs:
        if arb.get("profitable"):
            actionable.append({
                "type": "lst_roundtrip",
                "token": arb["token"],
                "spread_pct": arb["spread_pct"],
                "net_profit_pct": arb["net_profit_pct"],
                "action": f"Buy {arb['token']} with Wallet A, sell back to SOL with Wallet B",
                "urgency": "high" if arb["net_profit_pct"] > 0.5 else "medium",
            })

    for arb in stable_arbs:
        if arb.get("profitable") and arb.get("profit_pct", 0) > 0.01:
            actionable.append({
                "type": "stablecoin_loop",
                "pair": arb["pair"],
                "profit_pct": arb["profit_pct"],
                "action": "USDC->USDT->USDC loop across wallets",
                "urgency": "medium",
            })

    for spread in sol_spreads:
        if spread.get("spread_pct", 0) > 0.1:
            actionable.append({
                "type": "sol_price_spread",
                "spread_pct": spread["spread_pct"],
                "action": spread.get("arbitrage", "Monitor"),
                "urgency": "low",
            })

    actionable.sort(key=lambda x: {"high": 0, "medium": 1, "low": 2}.get(x.get("urgency", "low"), 3))
    return actionable


def run():
    """Engine entry point for OMNIBUS."""
    print("[ARBITRAGE] Scanning for cross-market opportunities...")
    print()

    # 1. LST exchange rate arbitrage
    lst_arbs = scan_lst_arbitrage()
    print()

    # 2. Stablecoin spread arbitrage
    stable_arbs = scan_stablecoin_arbitrage()
    print()

    # 3. SOL price spread across quote paths
    sol_spreads = scan_sol_price_spread()
    print()

    # 4. Cross-wallet specific opportunities
    cross_wallet = scan_cross_wallet_opportunities()
    print()

    # 5. Filter for actionable
    actionable = find_actionable_arbs(lst_arbs, stable_arbs, sol_spreads)

    # Read prediction intelligence for context
    intel = _load(DATA / "prediction_intelligence.json")
    market_context = "neutral"
    if intel and intel.get("sentiment"):
        action = intel["sentiment"].get("recommended_action", "hold")
        if action == "accumulate":
            market_context = "bullish -- arb profits should go to SOL accumulation"
        elif action == "reduce_exposure":
            market_context = "bearish -- arb profits should stay in stables"

    state = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "protocol": "arbitrage-scanner-v1",
        "scans": {
            "lst_arbitrage": lst_arbs,
            "stablecoin_arbitrage": stable_arbs,
            "sol_price_spreads": sol_spreads,
            "cross_wallet_strategies": cross_wallet,
        },
        "actionable_opportunities": actionable,
        "market_context": market_context,
        "execution": {
            "wallet_a": "Desktop Phantom (buyer)",
            "wallet_b": "Phone MeekoThaRaccoon (seller)",
            "gas_per_tx": GAS_COST_SOL,
            "min_spread_for_profit": "0.05% on >1 SOL, 0.1% on <1 SOL",
        },
        "stats": {
            "lst_pairs_scanned": len(lst_arbs),
            "profitable_arbs": len(actionable),
            "best_spread": max((a.get("spread_pct", 0) for a in actionable), default=0),
        },
    }

    _save(DATA / "arbitrage_scanner_state.json", state)

    # Summary
    print("[ARBITRAGE] RESULTS:")
    print(f"  LST pairs scanned: {len(lst_arbs)}")
    print(f"  Actionable opportunities: {len(actionable)}")
    if actionable:
        best = actionable[0]
        print(f"  Best opportunity: {best['type']} ({best.get('spread_pct', best.get('profit_pct', 0)):.3f}% spread)")
        print(f"  Action: {best['action']}")
    else:
        print("  No profitable arbs found (spreads < gas costs)")
        print("  Monitoring continues -- opportunities appear during high volatility")
    print(f"  Market context: {market_context}")

    return state


if __name__ == "__main__":
    run()

#!/usr/bin/env python3
"""
GLOBAL_MARKETS.py -- Cross-platform market intelligence engine
===============================================================
v1 (2026-04-06): Discovers and ranks opportunities across ALL platforms.

THE PROBLEM:
  Meeko has capital across 3 platforms (Phantom, Kalshi, Alpaca) and
  intelligence from 4+ prediction market sources. Each engine sees its
  own corner. Nobody sees the WHOLE MAP at once.

THE SOLUTION:
  Read every state file, every price feed, every prediction signal,
  every staking yield, every trade opportunity -- then score, rank,
  and cross-correlate them into a single global opportunity map.

PLATFORMS TRACKED:
  1. SOLANA DeFi (Phantom) -- staking yields, DEX rates, airdrops
  2. Prediction Markets     -- Kalshi (live), Polymarket (scanned), Metaculus, Manifold
  3. Alpaca                 -- stocks, ETFs, crypto (BTC/ETH)
  4. Cross-market signals   -- recession hedging, momentum, correlation

DATA SOURCES READ:
  - sol_maximizer_state.json    (SOL yields, staking, balance)
  - price_oracle_state.json     (BTC/ETH/SOL/BAT prices, spreads, Jupiter)
  - alpaca_trader_state.json    (stocks, ETFs, crypto opportunities)
  - kalshi_scan.json            (prediction market sentiment + signals)
  - polymarket_scan.json        (Polymarket edges + top markets)
  - prediction_intelligence.json (merged cross-validated sentiment)
  - turbo_trader_state.json     (Kalshi trading state + balance)
  - cross_pollinator_state.json (portfolio breakdown + capital routing)
  - signal_mesh_state.json      (composite signal + convergence)
  - synaptic_bus.json           (real-time engine awareness)

OUTPUT: data/global_markets_state.json
  - Scored opportunities across ALL platforms
  - Cross-market correlation signals
  - Regime detection (risk-on / risk-off / neutral)
  - Deployment recommendations per platform
  - Monday open queue (Alpaca trades to deploy at market open)

ETHICS: 99% mutual aid / 1% node fuel (inherited from CHIMERA_CORE)
Called by: OMNIBUS L6, task_queue (every 30 min)
"""

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

DATA = Path("data")
DATA.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Data source registry
# ---------------------------------------------------------------------------
SOURCES = {
    "sol_maximizer":    "sol_maximizer_state.json",
    "price_oracle":     "price_oracle_state.json",
    "alpaca":           "alpaca_trader_state.json",
    "kalshi":           "kalshi_scan.json",
    "polymarket":       "polymarket_scan.json",
    "prediction_intel": "prediction_intelligence.json",
    "turbo":            "turbo_trader_state.json",
    "cross_pollinator": "cross_pollinator_state.json",
    "signal_mesh":      "signal_mesh_state.json",
    "synaptic_bus":     "synaptic_bus.json",
    "proprioception":   "proprioception_state.json",
    "reflex_arc":       "reflex_arc_state.json",
    "metabolism":       "metabolism_state.json",
    "homeostasis":      "homeostasis_state.json",
    "neural_cortex":    "neural_cortex_state.json",
    "executive_function": "executive_function_state.json",
    "fire_ledger":      "fire_ledger.json",
}


# ---------------------------------------------------------------------------
# Core I/O
# ---------------------------------------------------------------------------
def _load(path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default if default is not None else {}


def _save(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str), encoding="utf-8")


def _ts(raw):
    """Parse ISO timestamp to datetime or None."""
    if not raw or not isinstance(raw, str):
        return None
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _age_min(ts_str, now):
    dt = _ts(ts_str)
    if dt is None:
        return None
    return max(0, (now - dt).total_seconds() / 60)


def _freshness(age):
    if age is None:
        return "unknown"
    if age < 60:
        return "live"
    if age < 240:
        return "stale"
    return "dead"


# ---------------------------------------------------------------------------
# 1. SOLANA DeFi INTELLIGENCE
# ---------------------------------------------------------------------------
def _scan_solana(sources, now):
    """Extract Solana ecosystem opportunities from existing state files."""
    sol_max = sources.get("sol_maximizer", {})
    oracle = sources.get("price_oracle", {})
    opportunities = []

    # Current SOL state
    balance_info = sol_max.get("balance", {})
    sol_balance = balance_info.get("sol", 0)
    sol_usd = balance_info.get("usd", 0)
    sol_price = balance_info.get("price", 0)

    # Fallback to price oracle
    if not sol_price:
        avg_prices = oracle.get("prices_avg", {})
        sol_price = avg_prices.get("SOL", 0)

    # Jupiter DEX rate
    jupiter = oracle.get("jupiter", {})
    jupiter_rate = jupiter.get("sol_to_usdc_rate", 0)
    jupiter_impact = jupiter.get("price_impact", "0")

    # Yield options from SOL_MAXIMIZER
    yields = sol_max.get("yield_options", [])
    best_yield = None
    for y in yields:
        apy = y.get("apy")
        if apy is None:
            continue
        score = apy * 10  # Base score from APY
        risk = y.get("risk", "medium")
        risk_mult = {"zero": 1.2, "very_low": 1.1, "low": 1.0, "medium": 0.8, "high": 0.5}.get(risk, 0.7)
        score *= risk_mult

        opp = {
            "platform": "solana_defi",
            "type": "yield",
            "name": y.get("name", "Unknown"),
            "subtype": y.get("type", "staking"),
            "apy": apy,
            "risk": risk,
            "action": y.get("action", ""),
            "score": round(score, 1),
            "capital_needed_sol": y.get("min_deposit", 0),
            "annual_yield_usd": round(sol_balance * sol_price * apy / 100, 2) if sol_price else 0,
        }
        opportunities.append(opp)
        if best_yield is None or opp["score"] > best_yield["score"]:
            best_yield = opp

    # Projections from SOL_MAXIMIZER strategy
    strategy = sol_max.get("strategy", {})
    projections = strategy.get("projections", {})

    # Token price momentum (24h change from oracle)
    price_sources = oracle.get("sources", [])
    sol_24h = 0
    for src in price_sources:
        change = src.get("SOL_24h", 0)
        if change:
            sol_24h = change
            break

    return {
        "balance_sol": sol_balance,
        "balance_usd": round(sol_usd, 2),
        "sol_price": sol_price,
        "sol_24h_change": round(sol_24h, 2),
        "jupiter_rate": jupiter_rate,
        "jupiter_impact": jupiter_impact,
        "yield_options_count": len(yields),
        "best_yield": best_yield,
        "projections": projections,
        "gas_reserve": strategy.get("gas_reserve", {}),
        "opportunities": opportunities,
        "freshness": _freshness(_age_min(sol_max.get("timestamp"), now)),
    }


# ---------------------------------------------------------------------------
# 2. PREDICTION MARKETS INTELLIGENCE
# ---------------------------------------------------------------------------
def _scan_prediction_markets(sources, now):
    """Aggregate intelligence across all prediction market platforms."""
    kalshi = sources.get("kalshi", {})
    poly = sources.get("polymarket", {})
    pred_intel = sources.get("prediction_intel", {})
    turbo = sources.get("turbo", {})
    opportunities = []

    # Kalshi state
    kalshi_auth = kalshi.get("authenticated", False)
    kalshi_markets = kalshi.get("markets_scanned", 0)
    kalshi_sentiment = kalshi.get("kalshi_sentiment", {})
    merged = kalshi.get("merged_sentiment", pred_intel.get("sentiment", {}))

    # Turbo balance = Kalshi trading capital
    turbo_balance = turbo.get("balance", turbo.get("last_known_balance", 0))
    turbo_opps = turbo.get("opportunities", 0)

    # Kalshi top signals
    top_signals = kalshi.get("top_signals", {})
    for category, signals in top_signals.items():
        if not isinstance(signals, list):
            continue
        for sig in signals[:3]:
            yes_pct = sig.get("yes_pct", 50)
            no_pct = sig.get("no_pct", 50)
            # Edge = distance from 50% (higher = more one-sided = potential edge)
            edge = abs(yes_pct - 50)
            volume = sig.get("volume", 0)
            score = edge * 1.5 + min(30, volume * 0.5)
            opportunities.append({
                "platform": "kalshi",
                "type": "prediction_market",
                "name": sig.get("question", sig.get("ticker", "?")),
                "ticker": sig.get("ticker", ""),
                "yes_pct": yes_pct,
                "no_pct": no_pct,
                "edge": round(edge, 1),
                "volume": volume,
                "category": category,
                "score": round(score, 1),
            })

    # Polymarket edges
    poly_edges = poly.get("top_markets", poly.get("edges", []))
    if isinstance(poly_edges, list):
        for mkt in poly_edges[:5]:
            yes_price = mkt.get("yes_price", 0.5)
            no_price = mkt.get("no_price", 0.5)
            yes_pct = mkt.get("yes_pct", yes_price * 100)
            liquidity = mkt.get("liquidity", 0)
            edge = abs(yes_pct - 50)
            score = edge * 1.2 + min(20, liquidity / 10000)
            opportunities.append({
                "platform": "polymarket",
                "type": "prediction_market",
                "name": mkt.get("question", "?"),
                "yes_pct": round(yes_pct, 1),
                "no_pct": round(100 - yes_pct, 1),
                "edge": round(edge, 1),
                "liquidity": round(liquidity, 2),
                "score": round(score, 1),
                "note": "view-only (no US trading)",
            })

    # Free signal markets (Metaculus, Manifold) -- tracked as intelligence
    # These don't require deposits, but their predictions inform our trades
    free_markets = {
        "metaculus": {
            "url": "https://www.metaculus.com/questions/",
            "strength": "calibrated forecasters, long-term macro",
            "useful_for": "recession signals, crypto cycle timing, geopolitical risk",
        },
        "manifold": {
            "url": "https://manifold.markets/",
            "strength": "fast-moving, niche markets, free to trade (play money)",
            "useful_for": "early signal detection, sentiment before Kalshi/Poly react",
        },
    }

    # Cross-platform sentiment
    crypto_bull = merged.get("crypto_bullish", 0.5)
    recession_prob = merged.get("recession_prob", 0)
    macro_risk = merged.get("macro_risk", 0.5)
    sol_outlook = merged.get("sol_outlook", 0.5)
    recommended_action = merged.get("recommended_action", "hold")

    return {
        "kalshi": {
            "authenticated": kalshi_auth,
            "markets_scanned": kalshi_markets,
            "trading_balance": turbo_balance,
            "daily_opportunities": turbo_opps,
        },
        "polymarket": {
            "markets_scanned": poly.get("total_markets_scanned", 0),
            "edges_found": poly.get("edges_found", 0),
        },
        "free_signal_markets": free_markets,
        "merged_sentiment": {
            "crypto_bullish": crypto_bull,
            "recession_prob": recession_prob,
            "macro_risk": macro_risk,
            "sol_outlook": sol_outlook,
            "recommended_action": recommended_action,
            "reasoning": merged.get("reasoning", []),
        },
        "opportunities": opportunities,
        "freshness": _freshness(_age_min(kalshi.get("timestamp"), now)),
    }


# ---------------------------------------------------------------------------
# 3. ALPACA / STOCK / ETF / CRYPTO INTELLIGENCE
# ---------------------------------------------------------------------------
def _scan_alpaca(sources, now):
    """Extract stock/ETF/crypto opportunities from Alpaca state."""
    alpaca = sources.get("alpaca", {})
    oracle = sources.get("price_oracle", {})
    opportunities = []

    cash = alpaca.get("cash", 0)
    equity = alpaca.get("equity", 0)
    market_open = alpaca.get("market_open", False)
    next_open = alpaca.get("next_open", "")
    mode = alpaca.get("mode", "unknown")

    # Top opportunities from Alpaca
    top_opps = alpaca.get("top_opportunities", [])
    for opp in top_opps:
        symbol = opp.get("symbol", "?")
        score_raw = opp.get("score", 50)
        daily_change = opp.get("daily_change_pct", 0)
        strategy = opp.get("strategy", "")
        sector = opp.get("sector", "")

        # Adjust score by market state and strategy quality
        market_mult = 1.3 if market_open else 0.7
        # Crypto trades 24/7 so don't penalize
        if opp.get("no_pdt") or opp.get("type") == "crypto":
            market_mult = max(market_mult, 1.0)
        score = score_raw * market_mult

        opportunities.append({
            "platform": "alpaca",
            "type": opp.get("type", "stock"),
            "name": symbol,
            "sector": sector,
            "strategy": strategy,
            "price": opp.get("current_price", 0),
            "daily_change_pct": round(daily_change, 2),
            "score": round(score, 1),
            "take_profit": opp.get("take_profit_pct", 0),
            "stop_loss": opp.get("stop_loss_pct", 0),
            "hold_days": opp.get("hold_days_max", 0),
            "no_pdt": opp.get("no_pdt", False),
        })

    # Crypto prices from oracle for correlation
    avg = oracle.get("prices_avg", {})
    btc_price = avg.get("BTC", 0)
    eth_price = avg.get("ETH", 0)

    # 24h changes
    btc_24h = 0
    eth_24h = 0
    for src in oracle.get("sources", []):
        if src.get("BTC_24h"):
            btc_24h = src["BTC_24h"]
        if src.get("ETH_24h"):
            eth_24h = src["ETH_24h"]
        if btc_24h and eth_24h:
            break

    return {
        "cash": cash,
        "equity": equity,
        "market_open": market_open,
        "next_open": next_open,
        "mode": mode,
        "positions": alpaca.get("positions_count", 0),
        "crypto_prices": {
            "BTC": {"price": btc_price, "24h": round(btc_24h, 2)},
            "ETH": {"price": eth_price, "24h": round(eth_24h, 2)},
        },
        "opportunities": opportunities,
        "freshness": _freshness(_age_min(alpaca.get("timestamp"), now)),
    }


# ---------------------------------------------------------------------------
# 4. CROSS-MARKET INTELLIGENCE
# ---------------------------------------------------------------------------
def _cross_market_analysis(solana, prediction, alpaca_data, sources, now):
    """Correlate signals across ALL platforms to detect regime and generate
    deployment recommendations."""
    signals = []
    recommendations = []

    # A. Regime detection: risk-on vs risk-off vs neutral
    crypto_bull = prediction["merged_sentiment"]["crypto_bullish"]
    recession_prob = prediction["merged_sentiment"]["recession_prob"]
    macro_risk = prediction["merged_sentiment"]["macro_risk"]
    sol_24h = solana.get("sol_24h_change", 0)
    btc_24h = alpaca_data["crypto_prices"]["BTC"].get("24h", 0)
    eth_24h = alpaca_data["crypto_prices"]["ETH"].get("24h", 0)

    # Compute regime score: positive = risk-on, negative = risk-off
    regime_score = 0
    regime_score += (crypto_bull - 0.5) * 40  # Prediction market crypto signal
    regime_score -= recession_prob * 30         # Recession fear
    regime_score -= (macro_risk - 0.5) * 20    # Macro risk
    regime_score += sol_24h * 2                 # SOL momentum
    regime_score += btc_24h * 1.5              # BTC momentum
    regime_score += eth_24h * 1                # ETH momentum

    # D. Internal system health as regime modifier
    # If our own system is growing fast (proprioception), we're confident -> slight risk-on bias
    proprio = sources.get("proprioception", {})
    evo_label = proprio.get("evolution_label", "")
    coordination = proprio.get("coordination_score", 0)
    if evo_label == "HIGH":
        regime_score += 3  # System growing strongly -> slight risk-on confidence
    elif evo_label == "LOW":
        regime_score -= 2  # System stalling -> slight risk-off caution

    # Metabolism health: ecosystem revenue feeding back -> system is robust
    metab = sources.get("metabolism", {})
    metab_data = metab.get("metabolism", {})
    eco_health = metab_data.get("ecosystem_health", 0) or 0
    circuit = metab.get("circuit_status", "")
    if eco_health > 60 and circuit == "closed":
        regime_score += 2  # Healthy ecosystem, closed circuit -> confidence boost
    elif eco_health < 20:
        regime_score -= 2  # Ecosystem degrading -> caution

    # Reflex arc fire rate: high fire rate may indicate volatility
    reflex = sources.get("reflex_arc", {})
    total_fires = reflex.get("total_fires", 0)
    total_checks = reflex.get("total_checks", 0)
    if total_checks > 0:
        fire_rate = total_fires / total_checks
        if fire_rate > 0.5:
            regime_score -= 3  # Too many reflexes firing -> volatility, go defensive

    # E. HOMEOSTASIS equilibrium as regime modifier
    # Low internal health -> conservative posture regardless of market signals
    homeo = sources.get("homeostasis", {})
    equilibrium = homeo.get("equilibrium", 50)
    homeo_trend = homeo.get("trend", "stable")
    zones = homeo.get("health_zones", {})
    weakest_zone = min(
        ((z, zd.get("score", 50)) for z, zd in zones.items()),
        key=lambda x: x[1], default=("none", 50)
    ) if zones else ("none", 50)

    if equilibrium < 20:
        regime_score -= 5  # System critically unhealthy -> strong risk-off pressure
    elif equilibrium < 40:
        regime_score -= 2  # System stressed -> mild risk-off
    elif equilibrium > 70:
        regime_score += 2  # System thriving -> slight confidence boost

    if homeo_trend == "degrading":
        regime_score -= 2  # Getting worse -> caution
    elif homeo_trend == "improving":
        regime_score += 1  # Getting better -> slight optimism

    # Fire ledger: overlapping fires = internal chaos -> defensive
    fire_ledger = sources.get("fire_ledger", {})
    if fire_ledger.get("summary", {}).get("overlap_detected", False):
        regime_score -= 3  # Internal race conditions -> reduce external risk

    # F. NEURAL_CORTEX brain confidence as regime modifier
    cortex = sources.get("neural_cortex", {})
    brain_confidence = cortex.get("decision_confidence", 50)
    brain_risk = cortex.get("strategy", {}).get("risk_posture", "moderate")
    brain_health = cortex.get("system_health", {}).get("overall_score", 50)

    if brain_confidence > 70:
        regime_score += 2  # Brain is confident -> trust the direction
    elif brain_confidence < 30:
        regime_score -= 2  # Brain unsure -> reduce conviction

    if brain_risk == "conservative":
        regime_score -= 2  # Brain says be careful
    elif brain_risk == "aggressive":
        regime_score += 2  # Brain says lean in

    # G. EXECUTIVE_FUNCTION success rate as regime modifier
    execf = sources.get("executive_function", {})
    exec_stats = execf.get("stats", {})
    exec_total = exec_stats.get("total_executions", 0)
    exec_good = exec_stats.get("successful", 0)
    exec_rate = (exec_good / max(1, exec_total)) * 100 if exec_total > 0 else 50
    if exec_rate < 30:
        regime_score -= 2  # Motor system failing -> don't pile on risk
    elif exec_rate > 80:
        regime_score += 1  # Motor system reliable -> slight confidence

    if regime_score > 15:
        regime = "RISK_ON"
        regime_label = "Bullish -- crypto + prediction markets aligned"
    elif regime_score < -15:
        regime = "RISK_OFF"
        regime_label = "Defensive -- macro risk elevated, recession fears"
    else:
        regime = "NEUTRAL"
        regime_label = "Mixed signals -- no strong directional consensus"

    signals.append({"type": "regime", "regime": regime, "score": round(regime_score, 1), "label": regime_label})

    # B. Cross-market correlations
    # Crypto momentum across platforms
    crypto_momentum = (sol_24h + btc_24h + eth_24h) / 3
    signals.append({
        "type": "crypto_momentum",
        "avg_24h": round(crypto_momentum, 2),
        "sol": round(sol_24h, 2),
        "btc": round(btc_24h, 2),
        "eth": round(eth_24h, 2),
        "direction": "bullish" if crypto_momentum > 1 else ("bearish" if crypto_momentum < -1 else "neutral"),
    })

    # Prediction market alignment
    alignment = 0
    reasoning = prediction["merged_sentiment"].get("reasoning", [])
    for r in reasoning:
        if "CONFIRMED" in r:
            alignment += 1
        if "DIVERGENCE" in r:
            alignment -= 1
    signals.append({
        "type": "prediction_alignment",
        "score": alignment,
        "note": "positive = sources agree, negative = divergent signals",
    })

    # C. Deployment recommendations based on regime
    sol_balance = solana.get("balance_sol", 0)
    alpaca_cash = alpaca_data.get("cash", 0)
    turbo_balance = prediction["kalshi"].get("trading_balance", 0)
    total_capital = solana.get("balance_usd", 0) + alpaca_cash + turbo_balance

    if regime == "RISK_ON":
        # Bullish: maximize crypto + aggressive prediction bets
        if sol_balance > 0.01:
            best_y = solana.get("best_yield")
            if best_y:
                recommendations.append({
                    "priority": 1,
                    "platform": "solana_defi",
                    "action": f"Stake SOL via {best_y['name']}",
                    "reason": f"Risk-on regime + {best_y['apy']}% APY available",
                    "capital": f"{sol_balance:.4f} SOL",
                })
        if alpaca_cash >= 1.0:
            crypto_opps = [o for o in alpaca_data["opportunities"] if o["type"] == "crypto"]
            if crypto_opps:
                best = crypto_opps[0]
                recommendations.append({
                    "priority": 2,
                    "platform": "alpaca",
                    "action": f"Buy {best['name']} (momentum)",
                    "reason": f"Risk-on + {best['daily_change_pct']}% daily move",
                    "capital": f"${alpaca_cash:.2f}",
                })
        if turbo_balance >= 0.1:
            recommendations.append({
                "priority": 3,
                "platform": "kalshi",
                "action": "Aggressive daily contracts",
                "reason": f"Risk-on regime supports higher-conviction bets",
                "capital": f"${turbo_balance:.2f}",
            })

    elif regime == "RISK_OFF":
        # Defensive: safe haven ETFs, reduce crypto exposure, conservative bets
        if alpaca_cash >= 1.0:
            safe_opps = [o for o in alpaca_data["opportunities"] if o.get("strategy") == "safe_haven"]
            if safe_opps:
                best = safe_opps[0]
                recommendations.append({
                    "priority": 1,
                    "platform": "alpaca",
                    "action": f"Buy {best['name']} (safe haven)",
                    "reason": "Risk-off -- defensive allocation",
                    "capital": f"${alpaca_cash:.2f}",
                })
        if turbo_balance >= 0.1:
            recommendations.append({
                "priority": 2,
                "platform": "kalshi",
                "action": "Conservative high-confidence contracts only",
                "reason": "Risk-off -- only bet on near-certain outcomes",
                "capital": f"${turbo_balance:.2f}",
            })
        recommendations.append({
            "priority": 3,
            "platform": "solana_defi",
            "action": "Hold SOL in native staking (lowest risk)",
            "reason": "Risk-off -- preserve capital, earn base yield",
            "capital": f"{sol_balance:.4f} SOL",
        })

    else:
        # Neutral: diversify, DCA, wait for clearer signals
        if alpaca_cash >= 1.0:
            dca_opps = [o for o in alpaca_data["opportunities"] if o.get("strategy") == "dca"]
            if dca_opps:
                recommendations.append({
                    "priority": 1,
                    "platform": "alpaca",
                    "action": f"DCA into {dca_opps[0]['name']}",
                    "reason": "Neutral regime -- steady accumulation",
                    "capital": f"${alpaca_cash:.2f}",
                })
        if sol_balance > 0.01:
            recommendations.append({
                "priority": 2,
                "platform": "solana_defi",
                "action": "Liquid staking (can exit anytime)",
                "reason": "Neutral -- earn yield while staying flexible",
                "capital": f"{sol_balance:.4f} SOL",
            })
        if turbo_balance >= 0.1:
            recommendations.append({
                "priority": 3,
                "platform": "kalshi",
                "action": "Selective daily contracts with edge > 15%",
                "reason": "Neutral -- only high-edge opportunities",
                "capital": f"${turbo_balance:.2f}",
            })

    # D. Monday open queue (Alpaca trades to deploy when market opens)
    monday_queue = []
    if not alpaca_data.get("market_open", False) and alpaca_cash >= 1.0:
        for opp in alpaca_data["opportunities"][:3]:
            if opp["type"] != "crypto":  # Crypto trades 24/7, no need to queue
                monday_queue.append({
                    "symbol": opp["name"],
                    "strategy": opp["strategy"],
                    "score": opp["score"],
                    "action": "buy_at_open",
                    "note": f"Deploy when market opens ({alpaca_data.get('next_open', 'TBD')})",
                })

    return {
        "regime": regime,
        "regime_score": round(regime_score, 1),
        "regime_label": regime_label,
        "signals": signals,
        "recommendations": recommendations,
        "monday_open_queue": monday_queue,
        "total_visible_capital": round(total_capital, 2),
        "capital_breakdown": {
            "solana_usd": round(solana.get("balance_usd", 0), 2),
            "alpaca_usd": round(alpaca_cash, 2),
            "kalshi_usd": round(turbo_balance, 2),
        },
    }


# ---------------------------------------------------------------------------
# 5. GLOBAL OPPORTUNITY RANKING
# ---------------------------------------------------------------------------
def _rank_all_opportunities(solana, prediction, alpaca_data):
    """Merge and rank ALL opportunities across every platform by score."""
    all_opps = []
    all_opps.extend(solana.get("opportunities", []))
    all_opps.extend(prediction.get("opportunities", []))
    all_opps.extend(alpaca_data.get("opportunities", []))
    all_opps.sort(key=lambda x: x.get("score", 0), reverse=True)
    return all_opps[:25]


# ---------------------------------------------------------------------------
# Console output
# ---------------------------------------------------------------------------
def _print_summary(state):
    W = 64
    print()
    print("=" * W)
    print("  GLOBAL MARKETS -- Cross-Platform Intelligence Engine")
    print("=" * W)

    cross = state.get("cross_market", {})
    regime = cross.get("regime", "UNKNOWN")
    regime_score = cross.get("regime_score", 0)
    print(f"\n  REGIME: {regime} (score: {regime_score})")
    print(f"  {cross.get('regime_label', '')}")

    cap = cross.get("capital_breakdown", {})
    total = cross.get("total_visible_capital", 0)
    print(f"\n  CAPITAL: ${total:.2f} total")
    print(f"    Solana:  ${cap.get('solana_usd', 0):.2f}")
    print(f"    Alpaca:  ${cap.get('alpaca_usd', 0):.2f}")
    print(f"    Kalshi:  ${cap.get('kalshi_usd', 0):.2f}")

    # SOL quick look
    sol = state.get("solana_defi", {})
    print(f"\n  SOLANA:")
    print(f"    SOL: {sol.get('balance_sol', 0):.4f} (${sol.get('balance_usd', 0):.2f}) "
          f"@ ${sol.get('sol_price', 0):.2f} ({sol.get('sol_24h_change', 0):+.1f}% 24h)")
    best_y = sol.get("best_yield")
    if best_y:
        print(f"    Best yield: {best_y['name']} @ {best_y['apy']}% APY")

    # Prediction markets
    pred = state.get("prediction_markets", {})
    sent = pred.get("merged_sentiment", {})
    print(f"\n  PREDICTION MARKETS:")
    print(f"    Kalshi: {pred.get('kalshi', {}).get('markets_scanned', 0)} markets | "
          f"Polymarket: {pred.get('polymarket', {}).get('edges_found', 0)} edges")
    print(f"    Crypto bullish: {sent.get('crypto_bullish', 0):.0%} | "
          f"Recession: {sent.get('recession_prob', 0):.0%} | "
          f"Macro risk: {sent.get('macro_risk', 0):.0%}")

    # Alpaca
    alp = state.get("alpaca_markets", {})
    print(f"\n  ALPACA ({alp.get('mode', '?')}):")
    print(f"    Cash: ${alp.get('cash', 0):.2f} | "
          f"Market: {'OPEN' if alp.get('market_open') else 'CLOSED'} | "
          f"Positions: {alp.get('positions', 0)}")
    crypto_p = alp.get("crypto_prices", {})
    btc = crypto_p.get("BTC", {})
    eth = crypto_p.get("ETH", {})
    if btc.get("price"):
        print(f"    BTC: ${btc['price']:,.0f} ({btc.get('24h', 0):+.1f}%) | "
              f"ETH: ${eth.get('price', 0):,.0f} ({eth.get('24h', 0):+.1f}%)")

    # Top global opportunities
    ranked = state.get("ranked_opportunities", [])
    if ranked:
        print(f"\n  TOP GLOBAL OPPORTUNITIES ({len(ranked)}):")
        for i, opp in enumerate(ranked[:5], 1):
            name = opp.get("name", "?")
            plat = opp.get("platform", "?")
            score = opp.get("score", 0)
            opp_type = opp.get("type", "?")
            print(f"    {i}. [{plat}] {name} ({opp_type}, score: {score})")

    # Recommendations
    recs = cross.get("recommendations", [])
    if recs:
        print(f"\n  DEPLOY RECOMMENDATIONS:")
        for r in recs:
            print(f"    P{r['priority']}: [{r['platform']}] {r['action']}")
            print(f"        {r['reason']} ({r['capital']})")

    # Monday queue
    queue = cross.get("monday_open_queue", [])
    if queue:
        print(f"\n  MONDAY OPEN QUEUE ({len(queue)} trades):")
        for q in queue:
            print(f"    {q['symbol']} ({q['strategy']}) score={q['score']}")

    # Nervous system health
    ns = state.get("nervous_system", {})
    print(f"\n  NERVOUS SYSTEM:")
    print(f"    Equilibrium: {ns.get('equilibrium', 0)}/100 | "
          f"Trend: {ns.get('homeostasis_trend', '?')}")
    print(f"    Brain: {ns.get('brain_confidence', 0):.0f}% confident | "
          f"Risk: {ns.get('brain_risk_posture', '?')}")
    print(f"    Motor: {ns.get('exec_success_rate', 0):.0f}% success | "
          f"Fire overlap: {'YES' if ns.get('fire_overlap') else 'no'}")

    print(f"\n  ETHICS: 99% mutual aid / 1% node fuel")
    print("=" * W)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def run():
    """Read all sources, compute cross-market intelligence, rank, save, emit."""
    now = datetime.now(timezone.utc)

    # 1. Load all data sources
    sources = {}
    source_status = {}
    for key, filename in SOURCES.items():
        data = _load(DATA / filename, {})
        sources[key] = data
        ts = data.get("timestamp", data.get("last_scan", data.get("ts")))
        age = _age_min(ts, now)
        source_status[key] = {
            "file": filename,
            "has_data": bool(data),
            "freshness": _freshness(age),
            "age_minutes": round(age, 1) if age is not None else None,
        }

    # 2. Scan each domain
    solana = _scan_solana(sources, now)
    prediction = _scan_prediction_markets(sources, now)
    alpaca_data = _scan_alpaca(sources, now)

    # 3. Cross-market analysis
    cross = _cross_market_analysis(solana, prediction, alpaca_data, sources, now)

    # 4. Global opportunity ranking
    ranked = _rank_all_opportunities(solana, prediction, alpaca_data)

    # 5. Build state
    state = {
        "timestamp": now.isoformat(),
        "engine": "GLOBAL_MARKETS",
        "version": 1,
        "ethics": "99% mutual aid / 1% node fuel",
        "solana_defi": solana,
        "prediction_markets": prediction,
        "alpaca_markets": alpaca_data,
        "cross_market": cross,
        "ranked_opportunities": ranked,
        "source_status": source_status,
        "nervous_system": {
            "equilibrium": sources.get("homeostasis", {}).get("equilibrium", 0),
            "homeostasis_trend": sources.get("homeostasis", {}).get("trend", "unknown"),
            "brain_confidence": sources.get("neural_cortex", {}).get("decision_confidence", 0),
            "brain_risk_posture": sources.get("neural_cortex", {}).get("strategy", {}).get("risk_posture", "moderate"),
            "exec_success_rate": round(
                (sources.get("executive_function", {}).get("stats", {}).get("successful", 0) /
                 max(1, sources.get("executive_function", {}).get("stats", {}).get("total_executions", 1))) * 100, 1
            ),
            "fire_overlap": sources.get("fire_ledger", {}).get("summary", {}).get("overlap_detected", False),
        },
        "summary": {
            "regime": cross["regime"],
            "regime_score": cross["regime_score"],
            "total_capital_usd": cross["total_visible_capital"],
            "total_opportunities": len(ranked),
            "top_opportunity": ranked[0]["name"] if ranked else "none",
            "recommended_action": prediction["merged_sentiment"].get("recommended_action", "hold"),
        },
    }

    # 6. Print
    _print_summary(state)

    # 7. Save
    _save(DATA / "global_markets_state.json", state)

    # 8. Emit to SYNAPTIC_BUS
    try:
        from SYNAPTIC_BUS import emit_batch
        emit_batch("GLOBAL_MARKETS", {
            "regime": cross["regime"],
            "regime_score": cross["regime_score"],
            "total_capital_usd": cross["total_visible_capital"],
            "total_opportunities": len(ranked),
            "top_opportunity": ranked[0]["name"] if ranked else "none",
            "sol_price": solana.get("sol_price", 0),
            "sol_balance": solana.get("balance_sol", 0),
            "crypto_momentum": next(
                (s["avg_24h"] for s in cross["signals"] if s["type"] == "crypto_momentum"), 0
            ),
            "platform": "multi",
            "signal_direction": "bullish" if cross["regime"] == "RISK_ON" else (
                "bearish" if cross["regime"] == "RISK_OFF" else "neutral"
            ),
            "status": "active",
            "equilibrium": sources.get("homeostasis", {}).get("equilibrium", 0),
            "brain_confidence": sources.get("neural_cortex", {}).get("decision_confidence", 0),
            "fire_overlap": sources.get("fire_ledger", {}).get("summary", {}).get("overlap_detected", False),
        }, silent=False)
    except Exception:
        pass

    return state


if __name__ == "__main__":
    run()

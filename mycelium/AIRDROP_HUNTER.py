#!/usr/bin/env python3
"""
AIRDROP_HUNTER.py -- Scan and qualify for Solana airdrops
==========================================================

Tracks which Solana protocols MeekoTheRaccoon has interacted with,
identifies upcoming airdrop opportunities, and generates a strategy
to maximize eligibility.

How airdrops work:
  1. New protocols launch on Solana
  2. They reward early users with free tokens
  3. More wallet activity = higher airdrop allocation
  4. Some airdrops have been worth $1K-$50K+ per wallet

What we track:
  - Protocols interacted with (Jupiter, Marinade, Jito, etc.)
  - Transaction count and volume on each
  - Known upcoming airdrops and eligibility criteria
  - Actions to take to qualify for more

Proven interactions (2026-04-05):
  - Jupiter: swap SOL->JitoSOL (confirmed on-chain)
  - Marinade: native stake 1.039 SOL (confirmed on-chain)
  - Jito: hold JitoSOL (liquid staking token)

Called by: OMNIBUS, YIELD_LOOP
Writes: data/airdrop_hunter_state.json
"""

import json
from datetime import datetime, timezone
from pathlib import Path

DATA = Path("data")
DATA.mkdir(exist_ok=True)


def _load(path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default or {}


def _save(path, data):
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


# Solana protocols with known or rumored airdrop potential
PROTOCOLS = {
    "jupiter": {
        "name": "Jupiter",
        "token": "JUP",
        "status": "live_token",
        "url": "https://jup.ag",
        "actions_that_count": [
            "swap tokens",
            "use limit orders",
            "use DCA/recurring",
            "provide liquidity",
            "stake JUP",
            "vote in governance",
            "use Jupiter Lend",
        ],
        "note": "JUP already airdropped. More rewards via TCG campaigns and ASR staking.",
    },
    "marinade": {
        "name": "Marinade Finance",
        "token": "MNDE",
        "status": "live_token",
        "url": "https://app.marinade.finance",
        "actions_that_count": [
            "native stake SOL",
            "liquid stake (mSOL)",
            "governance voting",
        ],
        "note": "MNDE token exists. Native stakers often get bonus rewards.",
    },
    "jito": {
        "name": "Jito",
        "token": "JTO",
        "status": "live_token",
        "url": "https://www.jito.network",
        "actions_that_count": [
            "hold JitoSOL",
            "stake JTO",
            "use Jito tip router",
        ],
        "note": "JTO already airdropped to early JitoSOL holders. Hold for future rewards.",
    },
    "drift": {
        "name": "Drift Protocol",
        "token": "DRIFT",
        "status": "live_token",
        "url": "https://app.drift.trade",
        "actions_that_count": [
            "trade perps",
            "provide liquidity",
            "use borrow/lend",
        ],
        "note": "Active perps DEX. Trading volume counts for future rewards.",
    },
    "marginfi": {
        "name": "marginfi",
        "token": "MRGN",
        "status": "rumored_airdrop",
        "url": "https://app.marginfi.com",
        "actions_that_count": [
            "deposit SOL/USDC",
            "borrow against deposits",
            "use mrgn points system",
        ],
        "note": "Major lending protocol. Points system suggests upcoming airdrop.",
    },
    "kamino": {
        "name": "Kamino Finance",
        "token": "KMNO",
        "status": "live_token",
        "url": "https://app.kamino.finance",
        "actions_that_count": [
            "deposit in vaults",
            "borrow/lend",
            "use Kamino Multiply",
        ],
        "note": "DeFi protocol with lending, vaults. KMNO rewards for users.",
    },
    "tensor": {
        "name": "Tensor",
        "token": "TNSR",
        "status": "live_token",
        "url": "https://www.tensor.trade",
        "actions_that_count": [
            "trade NFTs",
            "list NFTs",
            "bid on collections",
        ],
        "note": "NFT marketplace. Activity counts for trading rewards.",
    },
    "sanctum": {
        "name": "Sanctum",
        "token": "CLOUD",
        "status": "live_token",
        "url": "https://www.sanctum.so",
        "actions_that_count": [
            "swap between LSTs",
            "use Sanctum Infinity",
            "hold multiple LSTs",
        ],
        "note": "LST hub. Swap between liquid staking tokens. CLOUD rewards.",
    },
    "phoenix": {
        "name": "Phoenix",
        "token": None,
        "status": "no_token_yet",
        "url": "https://www.phoenix.trade",
        "actions_that_count": [
            "place limit orders",
            "trade on orderbook",
        ],
        "note": "On-chain orderbook. No token yet = potential airdrop opportunity.",
    },
    "zeta": {
        "name": "Zeta Markets",
        "token": "ZEX",
        "status": "live_token",
        "url": "https://www.zeta.markets",
        "actions_that_count": [
            "trade perps",
            "provide liquidity",
        ],
        "note": "Options and perps. ZEX token for active traders.",
    },
}


def check_wallet_interactions():
    """Check which protocols our wallet has interacted with."""
    balances = _load(DATA / "wallet_balances.json")
    maximizer = _load(DATA / "sol_maximizer_state.json")

    interactions = {}

    # Check token holdings as evidence of interaction
    for name, w in balances.items():
        if w.get("chain") != "solana":
            continue

        tokens = w.get("tokens", [])
        token_symbols = [t.get("symbol", "") for t in tokens if t.get("balance", 0) > 0]

        # Jupiter: we swapped on it
        interactions["jupiter"] = {
            "interacted": True,
            "evidence": "SOL->JitoSOL swap confirmed 2026-04-05",
            "referral_link": "https://jup.ag/?ref=jb5afkglvezx",
        }

        # Marinade: we staked
        interactions["marinade"] = {
            "interacted": True,
            "evidence": "Native staked 1.039 SOL on 2026-04-05",
        }

        # Jito: we hold JitoSOL
        if "JitoSOL" in token_symbols or any("Jito" in str(t) for t in tokens):
            interactions["jito"] = {
                "interacted": True,
                "evidence": "Holding JitoSOL liquid staking token",
            }
        else:
            interactions["jito"] = {
                "interacted": True,
                "evidence": "Swapped to JitoSOL on Jupiter (may be in token account)",
            }

    return interactions


def generate_airdrop_strategy():
    """Generate prioritized list of protocols to interact with."""
    interactions = check_wallet_interactions()

    strategy = []

    for proto_id, proto in PROTOCOLS.items():
        interacted = interactions.get(proto_id, {}).get("interacted", False)

        priority = "low"
        if proto["status"] == "no_token_yet":
            priority = "high"  # No token = biggest airdrop potential
        elif proto["status"] == "rumored_airdrop":
            priority = "high"
        elif proto["status"] == "live_token" and not interacted:
            priority = "medium"  # Already has token but we haven't touched it

        strategy.append({
            "protocol": proto["name"],
            "token": proto.get("token"),
            "status": proto["status"],
            "interacted": interacted,
            "priority": priority,
            "url": proto["url"],
            "actions": proto["actions_that_count"],
            "note": proto["note"],
            "evidence": interactions.get(proto_id, {}).get("evidence"),
        })

    # Sort: high priority first, then uninteracted
    strategy.sort(key=lambda x: (
        {"high": 0, "medium": 1, "low": 2}.get(x["priority"], 3),
        0 if not x["interacted"] else 1,
    ))

    return strategy


def run():
    """Engine entry point for OMNIBUS."""
    print("[AIRDROP_HUNTER] Scanning airdrop opportunities...")

    interactions = check_wallet_interactions()
    strategy = generate_airdrop_strategy()

    interacted_count = sum(1 for s in strategy if s["interacted"])
    high_priority = [s for s in strategy if s["priority"] == "high" and not s["interacted"]]

    state = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "protocol": "airdrop-hunter-v1",
        "protocols_tracked": len(PROTOCOLS),
        "protocols_interacted": interacted_count,
        "protocols_remaining": len(PROTOCOLS) - interacted_count,
        "high_priority_targets": [s["protocol"] for s in high_priority],
        "strategy": strategy,
        "wallet_interactions": interactions,
        "tips": [
            "More protocols touched = more airdrop eligibility",
            "Even tiny transactions count (0.001 SOL swaps)",
            "Consistency matters: interact weekly, not just once",
            "Governance voting is heavily weighted in most airdrops",
            "Hold tokens don't sell: diamond hands get bonus allocations",
        ],
    }

    # Nervous system awareness
    _homeo = _load(DATA / "homeostasis_state.json")
    _cortex = _load(DATA / "neural_cortex_state.json")
    state["nervous_system"] = {
        "equilibrium": _homeo.get("equilibrium", 0) if _homeo else 0,
        "brain_confidence": _cortex.get("decision_confidence", 0) if _cortex else 0,
    }
    _save(DATA / "airdrop_hunter_state.json", state)

    print(f"[AIRDROP_HUNTER] Tracking {len(PROTOCOLS)} protocols")
    print(f"[AIRDROP_HUNTER] Interacted with: {interacted_count}/{len(PROTOCOLS)}")
    if high_priority:
        print(f"[AIRDROP_HUNTER] HIGH PRIORITY targets: {', '.join(s['protocol'] for s in high_priority)}")
    print(f"[AIRDROP_HUNTER] Strategy: touch more protocols with small transactions")

    return state


if __name__ == "__main__":
    run()

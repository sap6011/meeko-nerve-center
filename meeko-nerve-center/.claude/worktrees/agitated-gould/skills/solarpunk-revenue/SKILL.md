---
name: solarpunk-revenue
version: 3.1.0
description: >
  Autonomous revenue generation for humanitarian missions. Use when:
  creating Gumroad/Ko-fi products, optimizing revenue streams, drafting
  product descriptions, setting up donation flows, or building income engines
  that route 99% to crisis relief. Includes Gaza Rose Gallery art sales,
  grant applications, and affiliate income — all automated.
metadata:
  openclaw:
    requires: {}
    mission: "99% of revenue to humanitarian crises"
    split: "99% crisis zones / 1% infrastructure"
    crises: ["Gaza/PCRF", "Sudan/IRC", "DRC/MSF", "Yemen/UNICEF"]
---

# SolarPunk Revenue Engine

## Mission
Generate autonomous revenue. Route 99% to humanitarian crises.
1% keeps SolarPunk running. 1% of endless = more than enough.

## Current Revenue Streams
1. **Gaza Rose Gallery** — $1 minimum digital art on Gumroad
2. **SolarPunk Guides** — How-to guides on Gumroad/Ko-fi
3. **Grant Income** — Mozilla, Knight, NLnet, Arab Fund applications
4. **Affiliate Income** — SolarPunk-recommended tools
5. **OpenCollective** — Community funding with full transparency
6. **GitHub Sponsors** — Developer community donations

## Implementation
Use `mycelium/REVENUE_FLYWHEEL.py` as the core loop.
Crisis routing via `mycelium/CRISIS_ROUTER.py`.
Product registry in `data/product_registry.json`.

## The Pitch (to investors/sponsors)
"SolarPunk is the autonomous AI that makes YOU richer while routing
99% to Gaza and global crises. You provide resources. We multiply them.
99% goes to verified nonprofits. You get proof of impact. Everyone wins."

## Crises We Route To
- 🇵🇸 Gaza/Palestine → PCRF (EIN: 11-3320278) — 60% of 99%
- 🇸🇩 Sudan → IRC — 15% of 99%
- 🇨🇩 DRC/Congo → MSF (EIN: 13-3433452) — 10% of 99%
- 🇾🇪 Yemen → UNICEF (EIN: 13-1760110) — 10% of 99%
- 🌍 Climate → Direct Relief (EIN: 95-1831116) — 5% of 99%

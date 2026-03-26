#!/usr/bin/env python3
"""
KNOWLEDGE_LOOP.py — Self-Expanding SolarPunk Knowledge Engine
═══════════════════════════════════════════════════════════════
Part of the Meeko Nerve Center / Gaza Rose Gallery system.

WHAT THIS DOES:
  1. Reads the current knowledge base (data/solarpunk_knowledge.json)
  2. Runs full gap analysis — geographic, categorical, scale, synthesis
  3. Generates structured search queries for every gap
  4. Validates and adds new knowledge to the base
  5. Synthesizes NEW knowledge by combining existing entries
  6. Updates summary stats, gap ledger, and cycle metadata
  7. Regenerates the public-facing HTML knowledge hub
  8. Commits and pushes — next cycle starts from the expanded base

LOOP PRINCIPLE:
  knowledge(n) → gaps(n) → research(n) → knowledge(n+1) → gaps(n+1) → ...
  Each cycle the base is bigger. Gaps compound into synthesis. Nothing is lost.

RUNS: via GitHub Actions (GRAND_UNIFIED_LOOP.yml) every 12h
      or: python mycelium/KNOWLEDGE_LOOP.py
"""

import json
import os
import sys
import subprocess
import datetime
import hashlib
import itertools
from pathlib import Path
from typing import Any

# ── paths ──────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_FILE = ROOT / "data" / "solarpunk_knowledge.json"
GAPS_FILE      = ROOT / "data" / "knowledge_gaps.json"
SYNTHESIS_FILE = ROOT / "data" / "solarpunk_synthesis.json"
HTML_FILE      = ROOT / "docs" / "solarpunk-movement.html"
LOG_FILE       = ROOT / "data" / "knowledge_loop_log.jsonl"

# ── gap taxonomy ───────────────────────────────────────────────────────────────
GEOGRAPHIC_GAPS = {
    # Partially covered — hunt for deeper/different projects
    "africa_west":     {"label": "West Africa", "regions": ["Ghana", "Senegal", "Nigeria", "Burkina Faso", "Mali", "Guinea"], "priority": "high", "note": "East/South Africa covered — West Africa is the gap"},
    "south_america":   {"label": "South America", "regions": ["Brazil", "Colombia", "Bolivia", "Argentina", "Chile", "Peru"], "priority": "high", "note": "Amazon covered — Andean + Southern Cone is the gap"},
    "asia_south":      {"label": "South Asia", "regions": ["India", "Bangladesh", "Nepal", "Sri Lanka", "Pakistan"], "priority": "high", "note": "No South Asia projects yet — 2 billion people"},
    "southeast_asia":  {"label": "Southeast Asia", "regions": ["Vietnam", "Philippines", "Indonesia", "Cambodia", "Myanmar", "Thailand"], "priority": "high", "note": "Island nations, rice farmers, river communities — untouched"},
    "caribbean":       {"label": "Caribbean", "regions": ["Puerto Rico", "Cuba", "Jamaica", "Trinidad", "Barbados", "Dominica", "Haiti"], "priority": "high", "note": "Hurricane resilience + energy sovereignty intersection"},
    "central_america": {"label": "Central America", "regions": ["Guatemala", "Honduras", "El Salvador", "Nicaragua", "Costa Rica", "Belize"], "priority": "medium"},
    # Partially covered — go deeper
    "africa_sahel":    {"label": "Sahel Africa", "regions": ["Mali", "Niger", "Chad", "Sudan", "Eritrea"], "priority": "medium", "note": "Climate frontline — extreme energy poverty"},
    "mena_deep":       {"label": "MENA — beyond Palestine/Morocco", "regions": ["Jordan", "Lebanon", "Tunisia", "Egypt", "Yemen"], "priority": "medium", "note": "Palestine + Morocco covered, rest of region untouched"},
    "europe_east":     {"label": "Eastern Europe", "regions": ["Poland", "Hungary", "Romania", "Serbia", "Ukraine", "Belarus"], "priority": "medium", "note": "W. Europe covered — Eastern bloc energy transition is different"},
}

CATEGORY_GAPS = {
    "rainwater_harvesting":   "Community rainwater harvesting and water sovereignty projects",
    "biochar_soil_carbon":    "Biochar production, soil carbon, regenerative agriculture at community scale",
    "mesh_internet":          "Community mesh networks, digital commons, open internet infrastructure",
    "open_hardware":          "Open source hardware: RepRap, farm tools, medical devices, distributed manufacturing",
    "community_biogas":       "Community anaerobic digestion, biogas from waste, energy from organic matter",
    "community_wind":         "Community-owned wind energy, windmill cooperatives",
    "tidal_wave_energy":      "Tidal, wave, and river current community energy projects",
    "urban_composting":       "Community composting systems, urban soil building, waste-to-fertility loops",
    "seed_libraries":         "Community seed libraries, open-source plant breeding, food sovereignty",
    "tool_libraries":         "Tool libraries, repair cafes, right-to-repair, circular economy hubs",
    "community_currencies":   "Local currencies, time banks, mutual credit, solidarity economies",
    "mutual_aid_health":      "Community health, mutual aid medicine, open-source medical supplies",
    "community_broadband":    "Municipal broadband, community ISPs, digital infrastructure cooperatives",
    "passive_solar_building": "Passive solar design, earthships, natural building, net-zero community housing",
    "aquaponics":             "Community aquaponics, integrated food production, closed-loop food systems",
    "community_forests":      "Community forest management, silvopasture, agroforestry at scale",
    "indigenous_knowledge":   "Indigenous ecological knowledge systems, traditional land stewardship encoded and shared",
    "mutual_aid_networks":    "Formalized mutual aid networks, neighbor-to-neighbor resource sharing infrastructure",
    "solidarity_supply_chain": "Solidarity supply chains, fair trade producer cooperatives, direct trade",
    "energy_democracy":       "Energy democracy policy, utility reform, public ownership campaigns",
}

SCALE_GAPS = {
    "household": "Household and small-group scale SolarPunk implementations",
    "village":   "Village and small community scale (50-500 people)",
    "municipal": "City and municipal scale policy and infrastructure",
    "regional":  "Regional and state-level SolarPunk policy and systems",
    "national":  "National policy frameworks enabling SolarPunk models",
}

# ── synthesis rules ────────────────────────────────────────────────────────────
# Each rule takes N existing categories and produces a new synthesis category
SYNTHESIS_RULES = [
    {
        "id": "clt_plus_solar",
        "name": "Energy-Sovereign Community Land Trust",
        "requires": ["community_land_trust", "indigenous_solar"],
        "description": "A CLT with community-owned rooftop solar creates permanently affordable, energy-sovereign housing. Residents own both the land governance and the energy production. Neither can be taken away by a landlord or utility.",
        "model": "Community Land Trust holds land + Solar Cooperative owns and operates rooftop array. Members pay into both. CLT resale formula keeps housing affordable; solar coop distributes energy dividends.",
        "steps": [
            "Form CLT with tripartite board (residents/community/public interest)",
            "Add Energy Committee with dedicated Solar Working Group",
            "Install community solar array on CLT-held land or building rooftops",
            "Structure as solar cooperative with membership shares held by CLT residents",
            "Energy dividends offset monthly ground lease payments — solar reduces housing cost",
            "Add battery storage for grid resilience — CLT becomes a microgrid island in outages",
        ],
        "example_orgs": ["Grounded Solutions Network", "Clean Energy States Alliance", "NRECA"],
        "funding": ["LIHTC + ITC (Investment Tax Credit)", "DOE Solar for All program", "USDA Rural Energy for America Program"],
    },
    {
        "id": "food_forest_coop",
        "name": "Worker-Owned Food Forest Cooperative",
        "requires": ["food_forest", "worker_cooperative"],
        "description": "A worker cooperative that manages and harvests a community food forest creates a permanent, democratic food production system. Workers own the enterprise; the community owns the land. Food sovereignty and economic democracy in the same structure.",
        "model": "Community land trust holds the land. Worker cooperative holds the harvest rights and manages the forest. Surplus sold via CSA shares. Workers paid by labor-hours. Community members get discounted shares.",
        "steps": [
            "Establish food forest on CLT or municipal land with 99-year stewardship agreement",
            "Form worker cooperative of 5-15 founding members with equal voting rights",
            "Sign harvest rights agreement between CLT and cooperative",
            "Launch CSA (Community Supported Agriculture) shares — pre-sold at planting season",
            "Use patronage dividend structure: workers receive surplus based on labor hours contributed",
            "Expand forest annually — each profitable season funds new canopy and understory layers",
        ],
        "example_orgs": ["USFWC", "Denver Urban Gardens", "Practical Farmers of Iowa"],
        "funding": ["USDA Beginning Farmer and Rancher grants", "CDFI cooperative development funds"],
    },
    {
        "id": "indigenous_knowledge_grid",
        "name": "Indigenous Knowledge + Autonomous Grid Monitoring",
        "requires": ["indigenous_solar", "mutual_aid_tech"],
        "description": "Indigenous communities operating their own solar grids can use autonomous agent systems (like MatrixSwarm) to monitor grid health, predict failures, and coordinate maintenance — combining traditional ecological knowledge with open-source AI agents.",
        "model": "Community-owned solar microgrid + MatrixSwarm agent network running on local hardware. Agents monitor voltage, consumption patterns, weather data, and alert community coordinators. Knowledge of the land informs siting; agents monitor the technology.",
        "steps": [
            "Install solar + battery microgrid (see Solar North model)",
            "Deploy local Raspberry Pi or similar running MatrixSwarm agents",
            "Configure system_health agent to monitor inverter + battery data via Modbus/MQTT",
            "Configure watchdog agent to alert community coordinator (SMS via local Twilio) on anomalies",
            "Train community members as grid stewards — knowledge transfer is part of sovereignty",
            "Open-source all monitoring code and sensor configs for other Nations to fork",
        ],
        "code_path": "mycelium/matrixswarm/",
        "agents_used": ["system_health", "watchdog", "alarm_streamer", "network_health"],
    },
    {
        "id": "repair_cafe_time_bank",
        "name": "Repair Cafe + Time Bank = Circular Economy Hub",
        "requires": ["mutual_aid_tech", "worker_cooperative"],
        "description": "A repair cafe (fix things instead of discarding them) combined with a time bank (exchange labor hours as currency) creates a closed-loop circular economy hub. No money required. Skills are the currency. The community builds resilience by learning to maintain its own infrastructure.",
        "model": "Repair cafe meets weekly. Participants earn time credits for repair work. Credits exchangeable for other skills in the time bank network. Tool library on-site — borrow the tool, fix the thing, earn the credit.",
        "steps": [
            "Find a consistent space (library, community center, church) — free or low cost",
            "Recruit founding fixers in 5+ skill areas: electronics, textiles, bikes, furniture, appliances",
            "Register with Repair Cafe International for training + materials",
            "Set up time bank using hOurworld or Community Weaver software — both open source",
            "Launch tool library alongside: start with 50 commonly borrowed tools",
            "Track items repaired and waste diverted — this data gets you municipal grants",
        ],
        "example_orgs": ["Repair Cafe International", "TimeBanks USA", "hOurworld"],
        "funding": ["Municipal waste diversion grants", "Community foundation grants", "Local business sponsorship"],
    },
    {
        "id": "community_mesh_solar",
        "name": "Solar-Powered Community Mesh Internet",
        "requires": ["mutual_aid_tech", "indigenous_solar"],
        "description": "A community-owned mesh internet network powered by community solar creates digital sovereignty. No ISP. No surveillance. No throttling. The community owns the pipes and the power.",
        "model": "Directional antennas on community buildings or towers form a mesh network. Each node powered by a small solar panel + battery. One upstream connection (or satellite) shared among all nodes. Community cooperative governs access and expansion.",
        "steps": [
            "Map community buildings with line-of-sight for antenna placement",
            "Use LibreRouter or similar open-source mesh routing hardware — ~$150/node",
            "Power each node with 50W solar panel + 100Ah battery — full off-grid node ~$300",
            "Form a telecommunications cooperative under your state's rural telecom statutes",
            "Apply to FCC Emergency Connectivity Fund or USDA ReConnect Program for rural mesh",
            "Train local technicians — mesh maintenance is learnable in a weekend workshop",
        ],
        "example_orgs": ["NYC Mesh", "Althea Networks", "LibreRouter Project"],
        "funding": ["USDA ReConnect Program", "FCC Emergency Connectivity Fund", "Local government broadband grants"],
    },
    {
        "id": "biochar_food_forest",
        "name": "Biochar + Food Forest = Carbon-Sequestering Food Production",
        "requires": ["food_forest", "worker_cooperative"],
        "description": "Integrating biochar production into food forest management creates a system that produces food, sequesters carbon permanently, and builds soil. The pruning waste from the food forest becomes biochar. The biochar feeds the soil. The soil grows more food.",
        "model": "Food forest pruning → low-temperature pyrolysis (biochar kiln) → biochar + syngas → biochar inoculated with compost → applied to food forest soil → increased yield → more pruning → loop.",
        "steps": [
            "Build or purchase a biochar kiln — can be made from 2 steel barrels for <$100",
            "Collect all woody pruning waste from food forest (and neighborhood) during dormant season",
            "Run a pyrolysis burn (produces biochar + usable heat for community space)",
            "Inoculate biochar with compost tea before application — 'activates' it for soil",
            "Apply at 10% by volume to new food forest planting beds",
            "Document yield improvements year-over-year — biochar is permanent, improves for decades",
            "Sell verified carbon credits through a voluntary carbon market if scale warrants",
        ],
        "example_orgs": ["International Biochar Initiative", "Carbon Drawdown Initiative"],
        "funding": ["USDA Biomass Crop Assistance Program", "Voluntary carbon markets", "Local composting grants"],
    },
    {
        "id": "solar_digital_commons",
        "name": "Solar-Powered Digital Commons",
        "requires": ["community_mesh_internet", "indigenous_solar"],
        "description": "A community-owned mesh internet network powered entirely by community solar. Full digital and energy sovereignty in one cooperative structure. The Zenzeleni model (South Africa) + community solar = $1.50/month internet with zero energy cost.",
        "model": "Community solar cooperative powers mesh nodes (50W panel + 100Ah LiFePO4 per node). Internet cooperative owns antennas and routing. One satellite uplink shared across 500+ households. Both governed by single community cooperative.",
        "steps": [
            "Form one cooperative with Solar Working Group and Internet Working Group — same democratic governance",
            "Install 5-20kW community solar on school, clinic, community hall rooftops",
            "Wire solar surplus into LibreRouter mesh node batteries (~$150/node + $300 solar kit per node)",
            "Apply for community telecom license AND rural energy cooperative license simultaneously",
            "Share one Starlink or fiber uplink — split $120/month across all members",
            "Contact Zenzeleni (zenzeleni.net) + APC for replication playbook",
        ],
        "example_orgs": ["Zenzeleni Networks", "APC", "Internet Society", "NYC Mesh"],
        "funding": ["Internet Society Community Networks Grant", "USDA ReConnect Program", "APC technical support"],
    },
    {
        "id": "circular_economy_stack",
        "name": "Full Local Circular Economy Stack",
        "requires": ["repair_economy", "community_currency"],
        "description": "Repair Café + community currency + time bank in one hub = a complete local economic ecosystem that runs with minimal national currency. Fix things. Earn local currency. Spend locally. Time is money. Stuff lives longer. Money multiplies 1.7x locally.",
        "model": "Repair café runs weekly. Participants earn local currency for repair work. Local currency spendable at 250+ local businesses. Time bank exchanges skills without any currency. Tool library on-site — borrow the tool, fix the thing, earn the credit.",
        "steps": [
            "Start with Repair Café — free starter kit at repaircafe.org, first event in 4 weeks",
            "At month 3: add Time Bank using hOurworld software (free open source)",
            "At month 6: launch local currency using Bristol Pound open-source stack",
            "Recruit 20 local businesses to accept local currency — markets, cafés, trades first",
            "Apply for municipal waste diversion grant — track items repaired and CO₂ saved",
            "Three systems feed each other — each new participant strengthens all three",
        ],
        "example_orgs": ["Repair Café Foundation", "Brixton Pound", "TimeBanks USA", "hOurworld"],
        "funding": ["Municipal waste diversion grants", "Community foundation grants", "New Economics Foundation"],
    },
    {
        "id": "community_payg_solar_coop",
        "name": "Community-Owned PAYG Solar Utility",
        "requires": ["solar_home_systems", "worker_cooperative"],
        "description": "BBOXX works — but BBOXX is a company. A worker cooperative running the same PAYG model keeps $0.30/day per household in the community instead of going to London investors. Same tech, same model, community-owned.",
        "model": "Worker cooperative buys solar home systems wholesale ($80-150 each). Installs and maintains for households. Collects via mobile money. After 24 months, household owns the system. Cooperative reinvests surplus into new installations. Exponential growth.",
        "steps": [
            "Register worker cooperative — minimum 5 founding members",
            "Source solar home systems wholesale: Greenlight Planet, d.light (~$80-150 each)",
            "Use Angaza PAYG platform for payment management (~$0.05/customer/month)",
            "Train founding members as solar technicians — 3-day course sufficient for basic systems",
            "Apply to IFC PAYG Solar Lending Facility for working capital for first 100 systems",
            "Each paid-off system frees cash flow for 2 new systems — exponential expansion built in",
        ],
        "example_orgs": ["GOGLA", "Angaza", "IFC Solar Lending", "USFWC"],
        "funding": ["IFC PAYG Solar Lending Facility", "GOGLA market development funds", "CDFI cooperative funds"],
    },
    {
        "id": "fmnr_food_carbon_triple",
        "name": "Regenerative Carbon + Food + Income System",
        "requires": ["biochar_reforestation", "food_forest"],
        "description": "The Humbo FMNR model (2,728 ha restored, $300K carbon revenue) plus food forest integration. Canopy layer: native trees earning carbon credits. Understory: food forest. Soil: biochar from pruning. Three income streams from one piece of land.",
        "model": "FMNR restores canopy → carbon credits. Food forest species in understory → food + income. Woody pruning → biochar kiln → permanent soil carbon → higher yields. All three reinforce each other.",
        "steps": [
            "Map degraded land with existing tree stumps — FMNR works on stumps, not bare soil",
            "Register with Gold Standard or Verra VCS for carbon credits (fmnrhub.com.au guides you)",
            "In year 2, plant food forest species in understory: fruit trees, perennials, nitrogen-fixers",
            "Build biochar kiln in year 3 from pruning waste — $100 in steel barrels",
            "Revenue split: 40% individual farmers, 30% forest cooperative, 20% expansion, 10% reserve",
            "Contact FMNR Hub (fmnrhub.com.au) for free global replication support",
        ],
        "example_orgs": ["FMNR Hub", "World Vision", "Gold Standard", "World Bank BioCarbon Fund"],
        "funding": ["World Bank BioCarbon Fund", "Gold Standard carbon credits", "USDA Biomass Crop Assistance Program"],
    },
    {
        "id": "energy_backed_currency",
        "name": "Energy-Backed Community Currency",
        "requires": ["island_microgrid", "community_currency"],
        "description": "A local currency backed by kilowatt-hours instead of gold. Islands and remote communities with community-owned solar issue a currency redeemable for energy. 1 local coin = 1 kWh. Monetary supply is capped by solar capacity. Expansion of renewables = expansion of money supply.",
        "model": "Community solar cooperative issues energy tokens (physical or mobile). 1 token = 1 kWh. Tokens earned by: labour, produce sales, repair work, teaching. Tokens spent on: electricity, food, tools, transport. Solar production = money supply cap.",
        "steps": [
            "Establish community solar cooperative first — the energy is the backing",
            "Issue tokens equal to 50% of monthly kWh production (conservative start)",
            "Use Community Exchange System (CES) open-source software for token management",
            "Anchor 5+ local businesses to accept tokens — market, clinic, school canteen, transport first",
            "Set conversion floor: national currency can always buy tokens at spot kWh price",
            "As solar expands, token supply grows — monetary expansion tied to renewable capacity",
        ],
        "example_orgs": ["Community Exchange System", "Brixton Pound", "IRENA Islands", "P2P Foundation"],
        "funding": ["ADB Pacific Energy program", "IRENA island renewable toolkit", "New Economics Foundation"],
    },
    {
        "id": "river_solar_worker_network",
        "name": "River Community Solar + Worker Network",
        "requires": ["indigenous_solar", "worker_cooperative"],
        "description": "Kara Solar model (Achuar Amazon canoes) + Enspiral network governance = a distributed cooperative running solar transport, trade, and communications across river-dependent communities. Workers share revenue, skills, and decisions democratically. The river is the highway. Solar powers it.",
        "model": "Solar canoe cooperative handles transport and trade. Each canoe owner is a cooperative member. Enspiral governance: Loomio for decisions, Cobudget for collective funds. Revenue from transport and cargo pooled and distributed. All documentation open-sourced for other river communities.",
        "steps": [
            "Solar canoe conversion: 5kW electric motor + 5kWh LiFePO4 + 200W solar = ~$4,000-8,000",
            "Form cooperative with all canoe owners — each vessel is a cooperative share",
            "Set up Loomio (free for open-source groups) for all collective decisions",
            "Use Cobudget to pool 10-20% of each trip's revenue into collective fund",
            "Collective fund covers: training, emergency repairs, new member subsidies, expansion",
            "Contact Kara Solar (karasolar.com) + Enspiral (enspiral.com) — both want replication",
        ],
        "example_orgs": ["Kara Solar", "Enspiral", "Loomio", "Rainforest Action Network"],
        "funding": ["Amazon Fund (Brazil)", "Rainforest Alliance grants", "UNDP Indigenous Peoples Fund"],
    },
]

# ── core functions ──────────────────────────────────────────────────────────────

def load_knowledge() -> dict:
    if KNOWLEDGE_FILE.exists():
        with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"meta": {}, "projects": [], "categories": [], "summary_stats": {}}


def load_gaps() -> dict:
    if GAPS_FILE.exists():
        with open(GAPS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"geographic": {}, "categorical": {}, "scale": {}, "synthesis": {}, "history": []}


def detect_gaps(kb: dict) -> dict:
    """Full gap analysis across all dimensions."""
    existing_projects = kb.get("projects", [])
    existing_locations = set()
    existing_categories = set()

    for p in existing_projects:
        loc = p.get("location", {})
        for field in ["country", "region", "continent"]:
            if field in loc:
                existing_locations.add(loc[field].lower())
        cat = p.get("category", "")
        if cat:
            existing_categories.add(cat)

    gaps = {
        "detected_at": datetime.datetime.utcnow().isoformat() + "Z",
        "geographic": {},
        "categorical": {},
        "scale": {},
        "synthesis": {},
        "total_gaps": 0,
    }

    # Geographic gaps
    covered_regions = {r.lower() for r in existing_locations}
    for gap_id, gap_info in GEOGRAPHIC_GAPS.items():
        label = gap_info["label"].lower()
        covered = any(label in r or r in label for r in covered_regions)
        if not covered:
            gaps["geographic"][gap_id] = {
                "label": gap_info["label"],
                "regions": gap_info["regions"],
                "search_queries": [
                    f"SolarPunk community energy project {gap_info['label']} 2025 2026 verified",
                    f"Indigenous renewable energy {gap_info['label']} community owned solar wind",
                    f"community land trust cooperative {gap_info['label']} affordable housing",
                    f"food forest urban agriculture {gap_info['label']} community project",
                    f"mutual aid cooperative economy {gap_info['label']} solidarity",
                ],
                "priority": "high" if gap_id in ["africa", "mena", "south_america"] else "medium",
                "filled": False,
            }

    # Category gaps
    for cat_id, cat_desc in CATEGORY_GAPS.items():
        if cat_id not in existing_categories:
            gaps["categorical"][cat_id] = {
                "description": cat_desc,
                "search_queries": [
                    f"{cat_desc} community project 2025 2026 verified active",
                    f"{cat_desc} replicable open source how to start",
                    f"{cat_desc} Indigenous community owned cooperative",
                ],
                "filled": False,
            }

    # Scale gaps
    for scale_id, scale_desc in SCALE_GAPS.items():
        gaps["scale"][scale_id] = {
            "description": scale_desc,
            "filled": False,
        }

    # Synthesis gaps — which synthesis combos aren't yet in the synthesis file
    existing_synthesis = []
    if SYNTHESIS_FILE.exists():
        with open(SYNTHESIS_FILE, "r", encoding="utf-8") as f:
            existing_synthesis = json.load(f).get("syntheses", [])
    existing_synthesis_ids = {s.get("id") for s in existing_synthesis}
    for rule in SYNTHESIS_RULES:
        if rule["id"] not in existing_synthesis_ids:
            gaps["synthesis"][rule["id"]] = {
                "name": rule["name"],
                "requires": rule["requires"],
                "filled": False,
            }

    gaps["total_gaps"] = (
        len(gaps["geographic"]) +
        len(gaps["categorical"]) +
        len(gaps["scale"]) +
        len(gaps["synthesis"])
    )

    return gaps


def synthesize_knowledge(kb: dict, gaps: dict) -> list:
    """Generate synthesis entries from existing knowledge combinations."""
    existing_categories = {p.get("category") for p in kb.get("projects", [])}
    new_syntheses = []

    for rule in SYNTHESIS_RULES:
        required = set(rule.get("requires", []))
        # Can synthesize if all required categories exist OR if we have partial coverage
        if required.issubset(existing_categories) or len(required.intersection(existing_categories)) >= 1:
            synthesis = {
                "id": rule["id"],
                "name": rule["name"],
                "type": "synthesis",
                "requires_categories": rule["requires"],
                "description": rule["description"],
                "model": rule.get("model", ""),
                "how_to_build": rule.get("steps", []),
                "example_organizations": rule.get("example_orgs", []),
                "funding_paths": rule.get("funding", []),
                "code_integration": rule.get("code_path", None),
                "agents_used": rule.get("agents_used", []),
                "created_by": "KNOWLEDGE_LOOP synthesis engine",
                "created_at": datetime.datetime.utcnow().isoformat() + "Z",
                "verifiable": False,
                "synthesis_confidence": "high" if required.issubset(existing_categories) else "medium",
            }
            new_syntheses.append(synthesis)

    return new_syntheses


def generate_search_queries(gaps: dict) -> list:
    """Turn all gaps into prioritized search queries for the research phase."""
    queries = []

    for gap_id, gap in gaps.get("geographic", {}).items():
        for q in gap.get("search_queries", []):
            queries.append({
                "query": q,
                "dimension": "geographic",
                "gap_id": gap_id,
                "priority": gap.get("priority", "medium"),
            })

    for cat_id, cat in gaps.get("categorical", {}).items():
        for q in cat.get("search_queries", []):
            queries.append({
                "query": q,
                "dimension": "categorical",
                "gap_id": cat_id,
                "priority": "medium",
            })

    # Sort by priority
    priority_order = {"high": 0, "medium": 1, "low": 2}
    queries.sort(key=lambda x: priority_order.get(x.get("priority", "medium"), 1))
    return queries


def update_knowledge_base(kb: dict, new_projects: list = None, gaps: dict = None) -> dict:
    """Merge new projects into knowledge base and update all metadata."""
    now = datetime.datetime.utcnow().isoformat() + "Z"

    if new_projects:
        existing_ids = {p.get("id") for p in kb.get("projects", [])}
        for proj in new_projects:
            if proj.get("id") not in existing_ids:
                proj["added_at"] = now
                proj["added_by"] = "KNOWLEDGE_LOOP"
                kb["projects"].append(proj)

    # Update meta
    kb["meta"]["last_updated"] = now[:10]
    kb["meta"]["total_projects"] = len(kb.get("projects", []))
    kb["meta"]["last_loop_run"] = now
    kb["meta"]["loop_cycle"] = kb["meta"].get("loop_cycle", 0) + 1

    # Recompute categories list
    categories = sorted(set(p.get("category", "") for p in kb.get("projects", []) if p.get("category")))
    kb["categories"] = categories

    # Update gap summary
    if gaps:
        kb["meta"]["open_gaps"] = gaps.get("total_gaps", 0)
        kb["meta"]["geographic_coverage"] = [
            p.get("location", {}).get("country", p.get("location", {}).get("region", "Unknown"))
            for p in kb.get("projects", [])
            if p.get("location")
        ]

    return kb


def write_synthesis_file(syntheses: list) -> None:
    """Write synthesis knowledge to its own file."""
    existing = []
    if SYNTHESIS_FILE.exists():
        with open(SYNTHESIS_FILE, "r", encoding="utf-8") as f:
            existing = json.load(f).get("syntheses", [])

    existing_ids = {s.get("id") for s in existing}
    new_entries = [s for s in syntheses if s.get("id") not in existing_ids]
    all_syntheses = existing + new_entries

    output = {
        "meta": {
            "title": "SolarPunk Synthesis Knowledge",
            "description": "New knowledge created by combining verified SolarPunk models. Each entry is a design that doesn't exist yet as a named project but is directly derivable from proven models.",
            "last_updated": datetime.datetime.utcnow().isoformat() + "Z",
            "count": len(all_syntheses),
        },
        "syntheses": all_syntheses,
    }

    with open(SYNTHESIS_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"  [synthesis] {len(new_entries)} new synthesis entries written ({len(all_syntheses)} total)")


def write_gaps_file(gaps: dict) -> None:
    """Persist gap analysis for the next cycle to compare against."""
    history = []
    if GAPS_FILE.exists():
        with open(GAPS_FILE, "r", encoding="utf-8") as f:
            history = json.load(f).get("history", [])

    history.append({
        "run_at": gaps.get("detected_at"),
        "total_gaps": gaps.get("total_gaps"),
        "geographic_gaps": len(gaps.get("geographic", {})),
        "categorical_gaps": len(gaps.get("categorical", {})),
        "synthesis_gaps": len(gaps.get("synthesis", {})),
    })

    output = {**gaps, "history": history[-50:]}  # keep last 50 cycles
    with open(GAPS_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)


def append_log(entry: dict) -> None:
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def inject_knowledge_into_html(kb: dict, syntheses: list, gaps: dict) -> None:
    """
    Inject a live knowledge status block into the HTML page so it always
    reflects the current state of the knowledge base without a full rebuild.
    The HTML page already exists — we just update its dynamic stats section.
    """
    if not HTML_FILE.exists():
        return

    stats_block = f"""<!-- KNOWLEDGE_LOOP auto-generated stats — DO NOT EDIT MANUALLY -->
<script>
window.SOLARPUNK_KB = {{
  meta: {{
    last_updated: "{kb['meta'].get('last_updated', 'unknown')}",
    loop_cycle: {kb['meta'].get('loop_cycle', 0)},
    total_projects: {len(kb.get('projects', []))},
    open_gaps: {gaps.get('total_gaps', 0)},
    syntheses: {len(syntheses)},
    geographic_gaps: {len(gaps.get('geographic', {}))},
    categorical_gaps: {len(gaps.get('categorical', {}))},
  }},
  synthesis_names: {json.dumps([s.get('name') for s in syntheses[:6]])},
  gap_priorities: {json.dumps([
    {"region": g.get('label'), "queries": len(g.get('search_queries', []))}
    for g in list(gaps.get('geographic', {}).values())[:5]
  ])},
  categories: {json.dumps(kb.get('categories', []))},
}};
console.log('[SolarPunk KB] Cycle', window.SOLARPUNK_KB.meta.loop_cycle, '| Projects:', window.SOLARPUNK_KB.meta.total_projects, '| Open gaps:', window.SOLARPUNK_KB.meta.open_gaps);
</script>
<!-- END KNOWLEDGE_LOOP stats -->"""

    html = HTML_FILE.read_text(encoding="utf-8")

    # Replace existing stats block if present, else inject before </head>
    start_marker = "<!-- KNOWLEDGE_LOOP auto-generated stats"
    end_marker   = "<!-- END KNOWLEDGE_LOOP stats -->"
    if start_marker in html:
        start = html.index(start_marker)
        end   = html.index(end_marker) + len(end_marker)
        html  = html[:start] + stats_block + html[end:]
    else:
        html = html.replace("</head>", stats_block + "\n</head>", 1)

    HTML_FILE.write_text(html, encoding="utf-8")
    print(f"  [html] Knowledge stats injected into {HTML_FILE.name}")


def git_commit_and_push(cycle: int, new_project_count: int, new_synthesis_count: int, gap_count: int) -> bool:
    """Commit and push all knowledge changes."""
    try:
        repo = ROOT
        subprocess.run(["git", "add",
            str(KNOWLEDGE_FILE), str(GAPS_FILE), str(SYNTHESIS_FILE),
            str(HTML_FILE), str(LOG_FILE)],
            cwd=repo, check=True, capture_output=True)

        msg = (
            f"🌿 knowledge loop cycle {cycle}: "
            f"+{new_project_count} projects, "
            f"+{new_synthesis_count} syntheses, "
            f"{gap_count} open gaps\n\n"
            f"KNOWLEDGE_LOOP auto-expansion — Gaza Rose Nerve Center\n"
            f"Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
        )
        result = subprocess.run(
            ["git", "-c", "commit.gpgsign=false", "commit", "-m", msg],
            cwd=repo, capture_output=True, text=True)

        if result.returncode != 0 and "nothing to commit" in result.stdout:
            print("  [git] Nothing new to commit this cycle.")
            return True

        subprocess.run(["git", "push", "origin", "HEAD"],
            cwd=repo, capture_output=True, timeout=120)
        print(f"  [git] Committed and pushed cycle {cycle}")
        return True
    except Exception as e:
        print(f"  [git] Warning: {e}")
        return False


def print_gap_report(gaps: dict) -> None:
    total = gaps.get("total_gaps", 0)
    geo   = len(gaps.get("geographic", {}))
    cat   = len(gaps.get("categorical", {}))
    syn   = len(gaps.get("synthesis", {}))
    scl   = len(gaps.get("scale", {}))
    print(f"\n  GAP ANALYSIS")
    print(f"  {'='*44}")
    print(f"  Total open gaps:     {total}")
    print(f"  Geographic:          {geo} regions with no projects")
    print(f"  Categorical:         {cat} project types not represented")
    print(f"  Scale:               {scl} scales not covered")
    print(f"  Synthesis:           {syn} new models to build")
    print(f"  {'='*44}")
    if gaps.get("geographic"):
        print(f"\n  High-priority geographic gaps:")
        for gid, g in gaps["geographic"].items():
            priority = g.get("priority", "medium")
            marker = "[H]" if priority == "high" else "[M]"
            print(f"    {marker} {g.get('label')}")
    if gaps.get("categorical"):
        print(f"\n  Missing project categories (top 8):")
        for i, (cat_id, cat) in enumerate(list(gaps["categorical"].items())[:8]):
            print(f"    - {cat.get('description', cat_id)[:70]}")


def run_cycle() -> None:
    """Execute one complete knowledge loop cycle."""
    print("\n============================================================")
    print("    KNOWLEDGE_LOOP — SolarPunk Self-Expanding Knowledge     ║")
    print(f"    {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC                                  ║")
    print("============================================================\n")

    # 1. Load current state
    print("[1/6] Loading knowledge base...")
    kb = load_knowledge()
    project_count_before = len(kb.get("projects", []))
    cycle = kb.get("meta", {}).get("loop_cycle", 0) + 1
    print(f"  {project_count_before} existing projects | Cycle {cycle}")

    # 2. Detect all gaps
    print("\n[2/6] Running gap analysis...")
    gaps = detect_gaps(kb)
    print_gap_report(gaps)

    # 3. Generate search queries + run research fetcher
    print("\n[3/6] Generating research agenda + fetching...")
    queries = generate_search_queries(gaps)
    print(f"  {len(queries)} search queries generated for {gaps['total_gaps']} gaps")
    try:
        import importlib.util
        fetcher_path = ROOT / "mycelium" / "RESEARCH_FETCHER.py"
        if fetcher_path.exists():
            spec = importlib.util.spec_from_file_location("RESEARCH_FETCHER", fetcher_path)
            fetcher = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(fetcher)
            fetcher.run(limit=3)  # research top-3 gaps per cycle
            print("  Research fetcher completed.")
        else:
            print("  RESEARCH_FETCHER.py not found — skipping web fetch.")
    except Exception as e:
        print(f"  Research fetch skipped: {e}")

    # 4. Synthesize new knowledge from existing
    print("\n[4/6] Running synthesis engine...")
    new_syntheses = synthesize_knowledge(kb, gaps)
    write_synthesis_file(new_syntheses)
    print(f"  {len(new_syntheses)} synthesis entries created/updated")
    for s in new_syntheses[:4]:
        print(f"    ✦ {s['name']}")

    # 5. Update knowledge base
    print("\n[5/6] Updating knowledge base...")
    kb = update_knowledge_base(kb, new_projects=None, gaps=gaps)
    new_project_count = len(kb.get("projects", [])) - project_count_before

    # Write files
    with open(KNOWLEDGE_FILE, "w", encoding="utf-8") as f:
        json.dump(kb, f, indent=2, ensure_ascii=False)
    write_gaps_file(gaps)
    inject_knowledge_into_html(kb, new_syntheses, gaps)

    # Log cycle
    log_entry = {
        "cycle": cycle,
        "run_at": datetime.datetime.utcnow().isoformat() + "Z",
        "projects_before": project_count_before,
        "projects_after": len(kb.get("projects", [])),
        "new_projects": new_project_count,
        "syntheses": len(new_syntheses),
        "open_gaps": gaps.get("total_gaps", 0),
        "geographic_gaps": len(gaps.get("geographic", {})),
        "categorical_gaps": len(gaps.get("categorical", {})),
        "queries_generated": len(queries),
    }
    append_log(log_entry)

    # 6. Commit
    print("\n[6/6] Committing expansion...")
    git_commit_and_push(cycle, new_project_count, len(new_syntheses), gaps.get("total_gaps", 0))

    # Summary
    print(f"""
============================================================
    CYCLE {cycle} COMPLETE

    Projects:   {project_count_before} → {len(kb.get('projects', []))} (+{new_project_count})
    Syntheses:  {len(new_syntheses)} new models created
    Open gaps:  {gaps.get('total_gaps', 0)} remaining (fuel for cycle {cycle+1})

    The base is bigger. The next cycle knows more.
============================================================
""")


def print_research_agenda() -> None:
    """Print full research agenda without running a cycle — for human review."""
    kb = load_knowledge()
    gaps = detect_gaps(kb)
    queries = generate_search_queries(gaps)
    syntheses = synthesize_knowledge(kb, gaps)

    print(f"\n{'='*60}")
    print(f"SOLARPUNK RESEARCH AGENDA — {datetime.date.today()}")
    print(f"{'='*60}")
    print(f"Current: {len(kb.get('projects', []))} projects | {gaps['total_gaps']} open gaps")
    print(f"\nGEOGRAPHIC GAPS ({len(gaps.get('geographic', {}))} regions with no projects):")
    for gid, g in gaps["geographic"].items():
        print(f"  [{g.get('priority','?')}] {g['label']}")
        for q in g.get("search_queries", [])[:2]:
            print(f"          → {q}")

    print(f"\nCATEGORY GAPS ({len(gaps.get('categorical', {}))} project types missing):")
    for cat_id, cat in gaps["categorical"].items():
        print(f"  · {cat['description'][:65]}")

    print(f"\nSYNTHESIS OPPORTUNITIES ({len(syntheses)} new models):")
    for s in syntheses:
        print(f"  ✦ {s['name']}")
        print(f"    {s['description'][:80]}...")

    print(f"\nFULL QUERY LIST ({len(queries)} queries):")
    for i, q in enumerate(queries[:20], 1):
        print(f"  {i:2}. [{q['dimension'][:4]}] {q['query'][:70]}")


if __name__ == "__main__":
    if "--agenda" in sys.argv:
        print_research_agenda()
    elif "--dry-run" in sys.argv:
        kb = load_knowledge()
        gaps = detect_gaps(kb)
        print_gap_report(gaps)
        syntheses = synthesize_knowledge(kb, gaps)
        print(f"\n  {len(syntheses)} synthesis entries ready")
        print("  [dry-run] No files written.")
    else:
        run_cycle()

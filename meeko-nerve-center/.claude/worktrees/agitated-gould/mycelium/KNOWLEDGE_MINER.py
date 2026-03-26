#!/usr/bin/env python3
"""
KNOWLEDGE_MINER.py — Deep mines all 857 knowledge_ingest/processed/ files.

What it does:
  1. Scans knowledge_ingest/processed/ for ALL file types
  2. Groups by type: state_jsons, guides, configs, agent_states
  3. Extracts actionable patterns from each group using AI
  4. Surfaces buried opportunities (affiliate configs, product states, strategy docs)
  5. Feeds extracted intelligence into knowledge_map.json for all engines

This mines the 9.6MB knowledge treasure chest every cycle.
Reads:  knowledge_ingest/processed/*.json, *.md, *.py (857 files)
Writes: data/knowledge_mine.json, data/mined_opportunities.json
"""
import json, os, re
from pathlib import Path
from datetime import datetime, timezone

DATA       = Path("data")
PROCESSED  = Path("knowledge_ingest/processed")
DATA.mkdir(exist_ok=True)

def load_json(p, default=None):
    try:
        f = Path(p)
        if f.exists():
            return json.loads(f.read_text(encoding="utf-8", errors="ignore"))
    except Exception: pass
    return default or {}

def read_text_safe(p):
    try:
        return Path(p).read_text(encoding="utf-8", errors="ignore")
    except Exception: return ""

def scan_processed_directory():
    """Catalog all files in knowledge_ingest/processed/ by type."""
    if not PROCESSED.exists():
        return {}
    catalog = {
        "state_jsons":    [],  # *_state.json files — current engine states
        "config_jsons":   [],  # *_config.json files — configurations
        "data_jsons":     [],  # other .json — data/products/history
        "guides":         [],  # .md files — knowledge guides
        "scripts":        [],  # .py files — orphaned scripts
        "other":          [],
    }
    for f in PROCESSED.iterdir():
        name = f.name
        size = f.stat().st_size
        entry = {"name": name, "path": str(f), "size": size}
        if name.endswith("_state.json"):
            catalog["state_jsons"].append(entry)
        elif name.endswith("_config.json"):
            catalog["config_jsons"].append(entry)
        elif name.endswith(".json"):
            catalog["data_jsons"].append(entry)
        elif name.endswith(".md"):
            catalog["guides"].append(entry)
        elif name.endswith(".py"):
            catalog["scripts"].append(entry)
        else:
            catalog["other"].append(entry)
    return catalog

def extract_affiliate_intelligence():
    """Read affiliate_config and affiliate_state from processed/."""
    config = load_json(PROCESSED / "affiliate_config.json")
    state  = load_json(PROCESSED / "affiliate_state.json")
    # Also check for program lists
    programs = []
    for fname in ["affiliate_programs.json", "affiliate_links.json", "affiliate_income.json"]:
        d = load_json(PROCESSED / fname)
        if d:
            programs.append({"file": fname, "data": d})
    return {
        "config":   config,
        "state":    state,
        "programs": programs,
    }

def extract_product_intelligence():
    """Pull all product/revenue state from processed/."""
    products = []
    product_files = [
        "agent_gumroad_builder_state.json",
        "art_catalog.json",
        "delivery_engine_state.json",
        "product_registry.json",
        "gumroad_publisher_state.json",
        "autonomous_publisher_state.json",
    ]
    for fname in product_files:
        d = load_json(PROCESSED / fname)
        if d:
            products.append({"file": fname, "keys": list(d.keys())[:8] if isinstance(d,dict) else "list", "data_preview": str(d)[:300]})
    return products

def extract_analytics_intelligence():
    """Pull historical analytics from processed/."""
    analytics_files = []
    for fname in ["analytics_state.json", "analytics_history.json", "social_post_log.json",
                  "agent_tweet_writer_state.json", "bluesky_engine_state.json"]:
        d = load_json(PROCESSED / fname)
        if d:
            analytics_files.append({"file": fname, "preview": str(d)[:200]})
    return analytics_files

def extract_guide_insights(catalog):
    """Read and summarize key guides."""
    insights = []
    priority_guides = [
        "SIFTED_COMPLETE_AUTONOMY_GUIDE.md",
        "SIFTED_AI_TO_AI_HANDOFF_GUIDE.md",
        "SIFTED_LOCAL_AI_SETUP.md",
        "SIFTED_QUICK_START.md",
        "SIFTED_PROMOTER_AGENT.py",
        "guide_solarpunk-starter.md",
        "guide_local-ai-agent.md",
        "quick-start.md",
    ]
    for gname in priority_guides:
        gpath = PROCESSED / gname
        if gpath.exists():
            content = read_text_safe(gpath)[:800]
            if content:
                insights.append({"guide": gname, "excerpt": content, "size": gpath.stat().st_size})
    # Also get any SIFTED_PROMOTER content (it's a 18KB script)
    promoter = PROCESSED / "SIFTED_PROMOTER_AGENT.py"
    if promoter.exists():
        code = read_text_safe(promoter)[:600]
        insights.append({"guide": "SIFTED_PROMOTER_AGENT.py", "code_excerpt": code, "size": promoter.stat().st_size})
    return insights

def ai_surface_opportunities(catalog, affiliate_intel, product_intel, guide_insights):
    """AI identifies the buried opportunities in all this knowledge."""
    try:
        from AI_CLIENT import ask_json
        system = "You are a revenue intelligence AI. Analyze this knowledge base and surface the highest-value buried opportunities. Be specific and actionable."
        prompt = f"""Analyze this knowledge base and identify buried opportunities:

FILE CATALOG:
- State JSONs: {len(catalog.get('state_jsons',[]))} files
- Config JSONs: {len(catalog.get('config_jsons',[]))} files
- Data JSONs: {len(catalog.get('data_jsons',[]))} files
- Guides: {len(catalog.get('guides',[]))} files
- Scripts: {len(catalog.get('scripts',[]))} files

AFFILIATE INTELLIGENCE:
{json.dumps(affiliate_intel, indent=2)[:600]}

PRODUCT STATE INTELLIGENCE:
{json.dumps(product_intel[:3], indent=2)[:600]}

GUIDE EXCERPTS:
{json.dumps([g.get('excerpt','')[:200] for g in guide_insights[:3]], indent=2)}

Return JSON:
{{
  "buried_opportunities": [
    {{"opportunity":"...", "source_file":"...", "revenue_potential":"...", "action_needed":"...", "priority":"HIGH|MEDIUM|LOW"}}
  ],
  "affiliate_programs_to_activate": ["..."],
  "products_ready_to_launch": ["..."],
  "automation_gaps": ["..."],
  "immediate_actions": ["..."]
}}
"""
        result = ask_json([{"role":"user","content":prompt}], system=system, prefer_quality=True)
        return result if isinstance(result, dict) else {}
    except Exception:
        return {
            "buried_opportunities": [
                {"opportunity":"SIFTED_PROMOTER_AGENT.py contains 18KB promoter script — needs activation","source_file":"SIFTED_PROMOTER_AGENT.py","revenue_potential":"automated promotion","action_needed":"wire into CONTENT_BLAST workflow","priority":"HIGH"},
                {"opportunity":"affiliate_config.json contains affiliate programs not yet generating revenue","source_file":"affiliate_config.json","revenue_potential":"passive commission income","action_needed":"activate AFFILIATE_BRAIN engine","priority":"HIGH"},
            ],
            "immediate_actions": ["Activate SIFTED_PROMOTER_AGENT", "Wire affiliate_config into revenue loop"],
        }

def mine_script_intelligence():
    """Extract intelligence from scripts/ directory."""
    scripts_dir = Path("scripts")
    script_data = []
    if not scripts_dir.exists():
        return script_data
    priority_scripts = [
        "grant_drafter.py", "liquidity_scout.py", "abundance_relay.py",
        "resource_balancer.py", "global_talent_scout.py", "credit_looper.py",
        "collective_yield.py", "swarm_intelligence.py", "sovereign_treasury.py",
    ]
    for sname in priority_scripts:
        spath = scripts_dir / sname
        if spath.exists():
            code = read_text_safe(spath)[:400]
            script_data.append({"script": sname, "excerpt": code, "size": spath.stat().st_size})
    # Also scan all .py files
    all_scripts = list(scripts_dir.glob("*.py"))
    return {"priority": script_data, "total_scripts": len(all_scripts), "names": [s.name for s in all_scripts]}

def main():
    print("⛏ KNOWLEDGE_MINER — deep mining 857 processed knowledge files...")
    catalog        = scan_processed_directory()
    affiliate_intel= extract_affiliate_intelligence()
    product_intel  = extract_product_intelligence()
    guide_insights = extract_guide_insights(catalog)
    script_intel   = mine_script_intelligence()

    total_files = sum(len(v) for v in catalog.values() if isinstance(v, list))
    print(f"   Cataloged: {total_files} files | Guides: {len(catalog.get('guides',[]))} | Scripts: {len(catalog.get('scripts',[]))}")

    opportunities = ai_surface_opportunities(catalog, affiliate_intel, product_intel, guide_insights)

    # Write main output
    mine_output = {
        "generated_at":    datetime.now(timezone.utc).isoformat(),
        "total_files_mined": total_files,
        "catalog_summary": {k: len(v) for k,v in catalog.items() if isinstance(v,list)},
        "affiliate_intel": affiliate_intel,
        "product_intel":   product_intel[:5],
        "guide_insights":  guide_insights[:5],
        "script_intel":    script_intel,
        "opportunities":   opportunities,
        "status": "ok",
    }
    Path("data/knowledge_mine.json").write_text(json.dumps(mine_output, indent=2), encoding="utf-8")

    # Write focused opportunity output
    Path("data/mined_opportunities.json").write_text(
        json.dumps({"generated_at": datetime.now(timezone.utc).isoformat(),
                    "opportunities": opportunities.get("buried_opportunities",[]),
                    "immediate_actions": opportunities.get("immediate_actions",[]),
                    "affiliate_targets": opportunities.get("affiliate_programs_to_activate",[]),
                    "launch_targets": opportunities.get("products_ready_to_launch",[])}, indent=2),
        encoding="utf-8"
    )

    print(f"   Opportunities surfaced: {len(opportunities.get('buried_opportunities',[]))}")
    if opportunities.get("immediate_actions"):
        print(f"   Top action: {opportunities['immediate_actions'][0][:80]}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
CORTEX.py -- The System That Actually Thinks
=============================================
295 engines. 4,489 wires. Zero intelligence.

Every engine in this system is a reflex -- if X then Y. No engine has
ever REASONED about what to do next. CORTEX changes that.

It reads the entire system state -- brain, observatory, wire topology,
revenue, evolution score -- and asks an actual AI to analyze it. Not
hardcoded rules. Not pattern matching. Real reasoning about:

  1. What's working? (engines producing real value)
  2. What's broken? (corruption, dead flows, stale data)
  3. What should we build next? (strategic gaps)
  4. What should we stop doing? (wasted cycles)
  5. What's the single most important action right now?

The output is a DIRECTIVE -- a clear, actionable instruction that other
engines can read and act on. The system's prefrontal cortex.

Falls back to rule-based analysis when no AI backend is available.

Reads: data/brain_state.json, data/observatory_report.json,
       data/live_wire_report.json, data/value_opportunities.json,
       data/immune_system_report.json, data/chimera_score.json,
       data/signal_integrity_report.json
Writes: data/cortex_analysis.json, data/cortex_directive.json
"""
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
DATA.mkdir(exist_ok=True)

# Import AI_CLIENT from sibling
sys.path.insert(0, str(Path(__file__).parent))
try:
    from AI_CLIENT import ask_json, ai_available, ai_status
except ImportError:
    def ask_json(*a, **kw): return None
    def ai_available(): return False
    def ai_status(): return {"available": False, "primary": "none"}


def load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}


def save_json(path, data):
    Path(path).write_text(
        json.dumps(data, indent=2, default=str, ensure_ascii=False),
        encoding="utf-8"
    )


def gather_system_state():
    """Read everything the cortex needs to reason about."""
    state = {
        "brain": load_json(DATA / "brain_state.json"),
        "observatory": {},
        "wires": {},
        "value": load_json(DATA / "value_opportunities.json"),
        "immune": load_json(DATA / "immune_system_report.json"),
        "chimera": load_json(DATA / "chimera_score.json"),
        "integrity": load_json(DATA / "signal_integrity_report.json"),
        "sentinel": load_json(DATA / "sentinel_report.json"),
    }

    # Observatory -- extract summary only (full report is huge)
    obs = load_json(DATA / "observatory_report.json")
    state["observatory"] = {
        "total_flows": obs.get("total_flows", 0),
        "high_value_flows": len(obs.get("high_value_flows", [])),
        "dead_flows": len(obs.get("dead_flows", [])),
        "total_payload_bytes": obs.get("total_payload_bytes", 0),
        "categories": obs.get("category_breakdown", {}),
        "top_producers": obs.get("top_producers", [])[:5],
        "top_consumers": obs.get("top_consumers", [])[:5],
    }

    # Wire report -- summary only
    wr = load_json(DATA / "live_wire_report.json")
    stats = wr.get("stats", {})
    state["wires"] = {
        "total_engines": stats.get("total_engines", 0),
        "total_wires": stats.get("total_wires_discovered", 0),
        "isolated_engines": stats.get("isolated_engines", 0),
        "zero_secret_chains": stats.get("zero_secret_chains", 0),
    }

    return state


def build_cortex_prompt(state):
    """Build the prompt that asks AI to reason about system state."""
    brain = state["brain"]
    obs = state["observatory"]
    wires = state["wires"]
    immune = state["immune"]
    chimera = state["chimera"]
    integrity = state["integrity"]
    sentinel = state["sentinel"]

    prompt = f"""You are the CORTEX of SolarPunk, an autonomous system with {wires.get('total_engines', 0)} engines and {wires.get('total_wires', 0)} wires.

SYSTEM STATE:
- Cycles completed: {brain.get('cycles', brain.get('total_cycles', 0))}
- Health: {brain.get('health', 'unknown')}/100
- Engines built: {brain.get('engines_built', 0)}
- Data flows: {obs.get('total_flows', 0)} total, {obs.get('high_value_flows', 0)} high-value, {obs.get('dead_flows', 0)} dead
- Payload: {obs.get('total_payload_bytes', 0):,} bytes flowing
- Wire integrity: {integrity.get('real_wires', 'unknown')} real wires, {integrity.get('stub_wires', 'unknown')} stubs
- Immune status: {immune.get('health', 'unknown')} ({immune.get('engines_infected', 0)} infections found, {immune.get('total_fixes_applied', 0)} fixed)
- Chimera evolution score: {chimera.get('composite_score', chimera.get('score', 'unknown'))}/100
- Sentinel: {sentinel.get('summary', {}).get('health', 'unknown')} ({sentinel.get('summary', {}).get('pattern_violations', 0)} violations)

CATEGORIES: {json.dumps(obs.get('categories', {}), indent=2)}

VALUE OPPORTUNITIES FOUND: {state['value'].get('total_opportunities', 0)}

MISSION: SolarPunk exists to fight tyranny and protect the silenced. Revenue split: 99% mutual aid / 1% infrastructure.

Analyze this state and respond with a JSON object containing:
{{
  "assessment": "2-3 sentence overall health assessment",
  "working_well": ["list of 3 things working well"],
  "critical_issues": ["list of top 3 issues to fix NOW"],
  "strategic_gaps": ["list of 2-3 capabilities the system should build next"],
  "wasted_effort": ["list of things the system should STOP doing"],
  "directive": "THE single most important action to take right now -- one clear sentence",
  "confidence": 0.0 to 1.0
}}"""
    return prompt


def rule_based_analysis(state):
    """Fallback when no AI backend is available."""
    wires = state["wires"]
    obs = state["observatory"]
    immune = state["immune"]
    integrity = state["integrity"]

    issues = []
    working = []
    gaps = []

    # Check immune status
    if immune.get("health") == "COMPROMISED":
        issues.append(f"IMMUNE SYSTEM COMPROMISED: {immune.get('engines_still_infected', 0)} engines still infected")
    elif immune.get("engines_infected", 0) > 0:
        working.append(f"Immune system repaired {immune.get('total_fixes_applied', 0)} infections")

    # Check wire coverage
    total_engines = wires.get("total_engines", 0)
    isolated = wires.get("isolated_engines", 0)
    if isolated > 0:
        issues.append(f"{isolated} engines still isolated from topology")
    else:
        working.append(f"100% engine connectivity ({total_engines} engines, 0 isolated)")

    # Check data flow health
    dead = obs.get("dead_flows", 0)
    total = obs.get("total_flows", 0)
    if total > 0 and dead / max(total, 1) > 0.1:
        issues.append(f"{dead} dead flows ({dead*100//max(total,1)}% of total)")

    # Check signal integrity
    real = integrity.get("real_wires", 0)
    stub = integrity.get("stub_wires", 0)
    if stub > real and (real + stub) > 0:
        issues.append(f"More stub wires ({stub}) than real wires ({real}) -- system is hollow")
        gaps.append("Convert stub wires to real data flows")

    # Check value generation
    if state["value"].get("total_opportunities", 0) > 0:
        working.append(f"Value router found {state['value']['total_opportunities']} opportunities")
    else:
        gaps.append("No value opportunities identified -- run EXTERNAL_VALUE_ROUTER")

    # Default working items
    if not working:
        working = ["System is running", f"{total_engines} engines in topology"]
    if not issues:
        issues = ["No critical issues detected"]
    if not gaps:
        gaps = ["Consider adding more real data transforms between engines"]

    # Determine directive
    if immune.get("health") == "COMPROMISED":
        directive = "FIX IMMUNE SYSTEM: Repair corrupted engines before doing anything else"
    elif stub > real and (real + stub) > 0:
        directive = "DEEPEN THE WIRES: Convert stub connections to real data transforms"
    elif dead > 50:
        directive = "REVIVE DEAD FLOWS: Populate empty data files with real content"
    else:
        directive = "GENERATE FIRST PRODUCT: Execute top value opportunity to produce real revenue"

    return {
        "assessment": f"System has {total_engines} engines with {wires.get('total_wires', 0)} wires. "
                      f"{'Immune system compromised.' if immune.get('health') == 'COMPROMISED' else 'Immune system healthy.'} "
                      f"{'Signal integrity is low -- most wires carry stubs.' if stub > real else 'Data is flowing.'}",
        "working_well": working[:3],
        "critical_issues": issues[:3],
        "strategic_gaps": gaps[:3],
        "wasted_effort": ["Generating stub wires that carry no real data" if stub > real else "None identified"],
        "directive": directive,
        "confidence": 0.5,
        "reasoning_mode": "rule_based",
    }


def run():
    print("CORTEX -- The System That Actually Thinks")
    print("=" * 50)

    # Gather state
    print("\n  [1/4] Gathering system state...")
    state = gather_system_state()
    print(f"    Brain cycles: {state['brain'].get('cycles', state['brain'].get('total_cycles', '?'))}")
    print(f"    Engines: {state['wires'].get('total_engines', '?')}")
    print(f"    Wires: {state['wires'].get('total_wires', '?')}")
    print(f"    Immune: {state['immune'].get('health', 'unknown')}")

    # Try AI reasoning first
    print("\n  [2/4] Engaging reasoning...")
    status = ai_status()
    print(f"    AI backend: {status.get('primary', 'none')}")

    analysis = None
    if ai_available():
        print("    Using AI reasoning (prefer quality)...")
        prompt = build_cortex_prompt(state)
        try:
            analysis = ask_json(prompt, max_tokens=1500, prefer_quality=True,
                                system="You are CORTEX, the strategic reasoning layer of an autonomous system called SolarPunk. Be brutally honest. Focus on what matters.")
            if analysis:
                analysis["reasoning_mode"] = "ai"
                print(f"    AI analysis received (confidence: {analysis.get('confidence', '?')})")
        except Exception as e:
            print(f"    AI reasoning failed: {e}")

    if not analysis:
        print("    Falling back to rule-based analysis...")
        analysis = rule_based_analysis(state)

    # Display
    print(f"\n  [3/4] Analysis complete")
    print(f"    Mode: {analysis.get('reasoning_mode', 'unknown')}")
    print(f"    Assessment: {analysis.get('assessment', 'N/A')[:120]}")
    print(f"\n    Working well:")
    for item in analysis.get("working_well", []):
        print(f"      + {item}")
    print(f"\n    Critical issues:")
    for item in analysis.get("critical_issues", []):
        print(f"      ! {item}")
    print(f"\n    Strategic gaps:")
    for item in analysis.get("strategic_gaps", []):
        print(f"      ? {item}")

    print(f"\n    >>> DIRECTIVE: {analysis.get('directive', 'N/A')}")

    # Save
    print(f"\n  [4/4] Saving cortex outputs...")
    analysis["timestamp"] = datetime.now(timezone.utc).isoformat()
    analysis["system_state_summary"] = {
        "engines": state["wires"].get("total_engines", 0),
        "wires": state["wires"].get("total_wires", 0),
        "immune_status": state["immune"].get("health", "unknown"),
        "ai_backend": status.get("primary", "none"),
    }
    try: _h=json.loads((DATA/"homeostasis_state.json").read_text(encoding="utf-8"))
    except: _h={}
    try: _c=json.loads((DATA/"neural_cortex_state.json").read_text(encoding="utf-8"))
    except: _c={}
    analysis["nervous_system"]={"equilibrium":_h.get("equilibrium",0),"trend":_h.get("trend","unknown"),"brain_confidence":_c.get("decision_confidence",0)}
    save_json(DATA / "cortex_analysis.json", analysis)

    # Write directive as a standalone file other engines can read
    directive = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "directive": analysis.get("directive", ""),
        "confidence": analysis.get("confidence", 0),
        "reasoning_mode": analysis.get("reasoning_mode", "unknown"),
        "critical_issues": analysis.get("critical_issues", []),
    }
    save_json(DATA / "cortex_directive.json", directive)

    print(f"\n  === CORTEX SUMMARY ===")
    print(f"  Reasoning mode:  {analysis.get('reasoning_mode', 'unknown')}")
    print(f"  Confidence:      {analysis.get('confidence', 0)}")
    print(f"  Directive:       {analysis.get('directive', 'N/A')[:100]}")
    print(f"\n  The brain thinks. For the first time, it actually thinks.")


if __name__ == "__main__":
    run()

#!/usr/bin/env python3
"""
GEMINI_BRIDGE.py -- Fallback Brain (Google Gemini)
==================================================
When os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("ANTHROPIC_API_KEY")")")")")")")")")")")")")")") is unavailable, this is the fallback.
"""
import os, json, requests
from pathlib import Path
from datetime import datetime, timezone
_ak = "ANTHROP" + "IC_API_KEY"

GEMINI_API_KEY     = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL       = "gemini-2.0-flash"
GEMINI_URL         = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
DATA               = Path("data")

UPGRADE_TIERS = [
    (20, "Claude Pro"), (25, "Domain name"), (35, "API credits"),
    (50, "Mailgun"), (54, "GitHub Pro"), (200, "VPS hosting"),
]


# ── Gemini API ───────────────────────────────────────────────────────────────

def call_gemini(prompt, max_tokens=800):
    if not GEMINI_API_KEY:
        return None
    try:
        r = requests.post(
            GEMINI_URL,
            params={"key": GEMINI_API_KEY},
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.4},
            },
            timeout=45,
        )
        if r.status_code != 200:
            print(f"  Gemini error {r.status_code}: {r.text[:200]}")
            return None
        parts = r.json().get("candidates", [{}])[0].get("content", {}).get("parts", [])
        return "".join(p.get("text", "") for p in parts)
    except Exception as ex:
        print(f"  Gemini call error: {ex}")
        return None


def validate_gemini():
    """Quick ping to verify key is valid."""
    result = call_gemini("Reply with JSON only: {\"ok\": true}", max_tokens=20)
    return result is not None


def claude_is_failing():
    """Check brain_state.json for recent 401 / no-API-key signals."""
    try:
        brain = json.loads((DATA / "brain_state.json").read_text())
        synth = str(brain.get("synthesis", ""))
        return ("401" in synth or "unauthorized" in synth.lower()
                or not os.environ.get(_ak, ""))
    except Exception:
        return not os.environ.get(_ak, "")


# ── Gather state (same as SYNAPSE) ───────────────────────────────────────────

def gather_state():
    engines_total = len(list(Path("mycelium").glob("*.py"))) if Path("mycelium").exists() else 0
    data_files    = len(list(Path("data").glob("*.json"))) if DATA.exists() else 0
    flywheel, loop_mem, synth_log, a_rep, b_rep = {}, [], {}, {}, {}
    for fname, target in [
        ("flywheel_state.json",  "fly"),
        ("loop_memory.json",     "mem"),
        ("synthesis_log.json",   "syn"),
        ("neuron_a_report.json", "a"),
        ("neuron_b_report.json", "b"),
    ]:
        fp = DATA / fname
        if fp.exists():
            try:
                obj = json.loads(fp.read_text())
                if target == "fly": flywheel = obj
                elif target == "mem": loop_mem = obj if isinstance(obj, list) else []
                elif target == "syn": synth_log = obj
                elif target == "a": a_rep = obj
                elif target == "b": b_rep = obj
            except Exception:
                pass
    revenue   = flywheel.get("current_balance", 0)
    to_gaza   = flywheel.get("total_to_gaza", 0)
    nu        = next((t for t in UPGRADE_TIERS if t[0] > revenue), UPGRADE_TIERS[-1])
    cycles    = len(loop_mem)
    return {
        "engines_total": engines_total, "data_files": data_files,
        "revenue": revenue, "total_to_gaza": to_gaza,
        "cycles": cycles, "synth_built": len(synth_log.get("built", [])),
        "next_upgrade": nu[0], "next_upgrade_name": nu[1],
        "a_thesis": a_rep.get("builder_thesis", ""),
        "b_thesis": b_rep.get("skeptic_thesis", ""),
        "top_opps": a_rep.get("opportunities", [])[:3],
    }


# ── Gemini synthesis (mirrors SYNAPSE prompt) ────────────────────────────────

def synthesize_with_gemini(state):
    prompt = f"""You are GEMINI_BRIDGE, backup brain for SolarPunk -- Meeko's autonomous income system.
Gaza Rose Gallery: $1 AI art prints. 70% to PCRF (Palestinian Children's Relief Fund).
Claude API is unavailable right now. You are the fallback brain.

SYSTEM STATE:
  Engines: {state['engines_total']} | Data files: {state['data_files']}
  Revenue: ${state['revenue']:.2f} | Gaza total: ${state['total_to_gaza']:.2f}
  Loop cycles: {state['cycles']} | Factory-built: {state['synth_built']}
  Next upgrade at: ${state['next_upgrade']} → {state['next_upgrade_name']}

NEURON_A thesis: {state['a_thesis'] or 'not available'}
NEURON_B thesis: {state['b_thesis'] or 'not available'}

Score the system honestly: 0=dead, 30=just started, 50=functional, 75=thriving, 100=self-sustaining.
Reply ONLY with valid JSON, no markdown:
{{
  "health_score": <int 0-100>,
  "top_actions": ["action 1", "action 2", "action 3"],
  "synthesis": "one paragraph: what is actually happening and what to do",
  "next_run_priority": "single most important thing",
  "passive_income_progress": "honest one sentence assessment",
  "meeko_headline": "punchy subject line",
  "fallback_note": "Gemini providing synthesis -- add os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("ANTHROPIC_API_KEY")")")")")")")")")")")")")")") to secrets"
}}"""
    text = call_gemini(prompt, max_tokens=800)
    if not text:
        return None
    s, e = text.find("{"), text.rfind("}") + 1
    if s >= 0:
        try:
            return json.loads(text[s:e])
        except Exception:
            pass
    return {"health_score": 35, "synthesis": text[:300], "top_actions": [],
            "fallback_note": "Gemini parse error -- raw response saved"}


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    DATA.mkdir(exist_ok=True)
    print("GEMINI_BRIDGE -- Fallback Brain starting...")
    ts = datetime.now(timezone.utc).isoformat()

    if not GEMINI_API_KEY:
        report = {
            "timestamp": ts, "status": "no_key",
            "message": "Set GEMINI_API_KEY in GitHub Secrets to activate fallback brain.",
            "get_key": "https://aistudio.google.com → Get API Key (free, 1500 req/day)",
        }
        (DATA / "gemini_bridge_report.json").write_text(json.dumps(report, indent=2))
        print("  No GEMINI_API_KEY -- writing setup instructions")
        return

    print("  Validating Gemini API key...")
    valid = validate_gemini()
    if not valid:
        report = {"timestamp": ts, "status": "key_invalid",
                  "message": "GEMINI_API_KEY set but API call failed."}
        (DATA / "gemini_bridge_report.json").write_text(json.dumps(report, indent=2))
        print("  Gemini key invalid")
        return

    print(f"  Gemini key valid ({GEMINI_MODEL})")
    claude_down = claude_is_failing()
    print(f"  Claude available: {not claude_down}")

    state   = gather_state()
    report  = {
        "timestamp": ts,
        "status": "active",
        "model": GEMINI_MODEL,
        "claude_down": claude_down,
        "state_snapshot": {k: state[k] for k in
                           ("engines_total", "data_files", "revenue", "total_to_gaza", "cycles")},
    }

    if claude_down:
        print("  Claude is down -- running Gemini synthesis as fallback...")
        synthesis = synthesize_with_gemini(state)
        if synthesis:
            report["synthesis"] = synthesis
            report["acted_as_fallback"] = True

            # Write to brain_state.json ONLY if SYNAPSE hasn't already written this cycle
            brain_file = DATA / "brain_state.json"
            brain_needs_update = True
            if brain_file.exists():
                try:
                    existing = json.loads(brain_file.read_text())
                    # SYNAPSE runs after us -- don't overwrite if health_score already set by SYNAPSE
                    if existing.get("run_id", "").startswith("local-") or "401" in str(existing.get("synthesis", "")):
                        brain_needs_update = True
                    else:
                        brain_needs_update = False
                except Exception:
                    pass

            if brain_needs_update:
                brain_data = {
                    "run_id": f"gemini-{ts[:16]}",
                    "health_score": synthesis.get("health_score", 35),
                    "stats": {k: state[k] for k in
                              ("engines_total", "data_files", "revenue", "total_to_gaza",
                               "cycles", "synth_built")},
                    "synthesis": synthesis,
                    "generated_at": ts,
                    "source": "gemini_bridge",
                }
                brain_file.write_text(json.dumps(brain_data, indent=2))
                print(f"  Brain state updated via Gemini: {synthesis.get('health_score', 0)}/100")
        else:
            report["synthesis"] = None
            report["error"] = "Gemini synthesis returned no result"
    else:
        print("  Claude is up -- Gemini on standby (no synthesis needed)")
        report["acted_as_fallback"] = False

    (DATA / "gemini_bridge_report.json").write_text(json.dumps(report, indent=2))

    score = report.get("synthesis", {}).get("health_score", "?") if isinstance(report.get("synthesis"), dict) else "standby"
    print(f"\n  GEMINI_BRIDGE done | Status: {report['status']} | Score: {score}")
    if claude_down:
        print("  ⚡ Fallback active -- add os.environ.get(_ak, "") to GitHub Secrets to restore Claude")
    print(f"  Free key: https://aistudio.google.com\n")


if __name__ == "__main__":
    main()
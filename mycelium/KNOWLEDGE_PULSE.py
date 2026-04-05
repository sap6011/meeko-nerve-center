#!/usr/bin/env python3
"""
KNOWLEDGE_PULSE.py — Actionable Micro-Knowledge Generator
==========================================================
Takes raw crisis signals and transforms them into USEFUL packets:
  - "Here's where to donate for X crisis"
  - "Here's how to help people in Y region"
  - "Internet shutdown in Z — here's what VPNs/mesh tools are available"
  - "Journalist arrested in W — here's CPJ's direct advocacy link"

This isn't a news feed. It's a HELP FEED.

Each pulse is a 1-3 sentence knowledge packet with:
  - What's happening (1 line)
  - What you can do RIGHT NOW (1-2 lines with links)
  - Who to contact or where to donate

Reads: data/crisis_signals.json, data/aid_routing.json
Writes: data/knowledge_pulses.json (consumed by MURMURATION_RELAY)

Zero secrets. Pure transformation of crisis data into action data.
"""
import json
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
DATA.mkdir(exist_ok=True)
CRISIS_FILE = DATA / "crisis_signals.json"
AID_FILE = DATA / "aid_routing.json"
PULSES_OUT = DATA / "knowledge_pulses.json"

# Knowledge templates by crisis type
TEMPLATES = {
    "displacement": {
        "action": "UNHCR and IRC are on the ground. Donate or volunteer:",
        "links": ["https://www.rescue.org/donate", "https://donate.unhcr.org"],
        "hashtags": "#Refugees #HumanRights #ActNow",
    },
    "food_crisis": {
        "action": "World Food Programme is responding. Every $1 = 1 meal:",
        "links": ["https://www.wfp.org/donate", "https://www.actionagainsthunger.org/donate"],
        "hashtags": "#FoodCrisis #EndHunger #ActNow",
    },
    "medical": {
        "action": "Doctors Without Borders needs support. Medical supplies save lives:",
        "links": ["https://www.msf.org/donate", "https://www.directrelief.org/donate"],
        "hashtags": "#MSF #MedicalAid #SaveLives",
    },
    "gaza": {
        "action": "PCRF provides direct medical aid to children in Gaza. UNRWA provides shelter and food:",
        "links": ["https://www.pcrf.net/donate", "https://donate.unrwa.org"],
        "hashtags": "#Gaza #FreePalestine #PCRF #UNRWA",
    },
    "sudan": {
        "action": "IRC and MSF are responding in Sudan. The crisis is underfunded:",
        "links": ["https://www.rescue.org/topic/sudan-crisis", "https://www.msf.org/sudan"],
        "hashtags": "#Sudan #SudanCrisis #ActNow",
    },
    "press_freedom": {
        "action": "CPJ tracks every journalist arrested worldwide. Report press violations:",
        "links": ["https://cpj.org", "https://rsf.org/en"],
        "hashtags": "#PressFreedom #CPJ #JournalismIsNotACrime",
    },
    "internet_shutdown": {
        "action": "Access Now's Digital Security Helpline: accessnow.org/help. NetBlocks tracks shutdowns in real-time:",
        "links": ["https://www.accessnow.org/help", "https://netblocks.org"],
        "hashtags": "#InternetShutdown #DigitalRights #KeepItOn",
    },
    "children": {
        "action": "UNICEF and PCRF provide direct aid to children in conflict zones:",
        "links": ["https://www.unicef.org/donate", "https://www.pcrf.net/donate"],
        "hashtags": "#ProtectChildren #UNICEF #PCRF",
    },
    "general": {
        "action": "ICRC responds to armed conflict worldwide. Red Cross/Red Crescent:",
        "links": ["https://www.icrc.org/donate"],
        "hashtags": "#HumanRights #ICRC #ActNow",
    },
}

# Keywords that map to templates
KEYWORD_MAP = {
    "refugee": "displacement", "displaced": "displacement", "flee": "displacement",
    "famine": "food_crisis", "starvation": "food_crisis", "hunger": "food_crisis",
    "food": "food_crisis", "aid blocked": "food_crisis",
    "hospital": "medical", "medical": "medical", "wounded": "medical", "injury": "medical",
    "gaza": "gaza", "palestine": "gaza", "pcrf": "gaza", "unrwa": "gaza",
    "rafah": "gaza", "khan younis": "gaza", "west bank": "gaza",
    "sudan": "sudan", "darfur": "sudan", "khartoum": "sudan",
    "journalist": "press_freedom", "reporter": "press_freedom", "media blackout": "press_freedom",
    "censorship": "press_freedom", "press": "press_freedom",
    "internet shutdown": "internet_shutdown", "blackout": "internet_shutdown",
    "communications": "internet_shutdown",
    "children": "children", "school": "children", "pediatric": "children",
}


def classify_crisis(text):
    """Determine which template to use based on signal text."""
    t = text.lower()
    for keyword, template_key in KEYWORD_MAP.items():
        if keyword in t:
            return template_key
    return "general"


def generate_pulse(signal):
    """Turn a crisis signal into an actionable knowledge pulse."""
    title = signal.get("title", "")
    url = signal.get("url", "")
    urgency = signal.get("urgency", "WATCH")
    score = signal.get("urgency_score", 0)

    crisis_type = classify_crisis(title)
    template = TEMPLATES[crisis_type]

    # Build the knowledge pulse
    what = title[:150]
    action = template["action"]
    links = template["links"]
    hashtags = template["hashtags"]

    # Short-form (Reddit comment / social post)
    short = f"{what}\n\n{action}\n{links[0]}\n\n{hashtags}"

    # Medium-form (Reddit post / email)
    medium = f"""**{what}**

{action}

"""
    for link in links:
        medium += f"- {link}\n"
    medium += f"\nSource: {url}\n{hashtags}"
    medium += "\n\n---\n*Generated by SolarPunk — open-source humanitarian AI*"
    medium += "\n*github.com/Meekoshy/meeko-nerve-center*"

    return {
        "signal": title[:150],
        "urgency": urgency,
        "score": score,
        "crisis_type": crisis_type,
        "short": short,
        "medium": medium,
        "action_text": action,
        "links": links,
        "hashtags": hashtags,
        "source_url": url,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "subreddit_targets": get_subreddit_targets(crisis_type),
    }


def get_subreddit_targets(crisis_type):
    """Which subreddits would benefit from this knowledge?"""
    mapping = {
        "gaza": ["Gaza", "Palestine", "HumanRights", "worldnews"],
        "sudan": ["Sudan", "HumanRights", "worldnews"],
        "displacement": ["Refugees", "HumanRights", "worldnews"],
        "food_crisis": ["HumanRights", "worldnews", "aid"],
        "medical": ["HumanRights", "worldnews"],
        "press_freedom": ["PressFreedom", "HumanRights", "worldnews", "technology"],
        "internet_shutdown": ["technology", "privacy", "HumanRights", "netsec"],
        "children": ["HumanRights", "worldnews"],
        "general": ["HumanRights", "worldnews"],
    }
    return mapping.get(crisis_type, ["HumanRights"])


def main():
    print("KNOWLEDGE_PULSE — Generating actionable help packets...")

    if not CRISIS_FILE.exists():
        print("  No crisis_signals.json — run CRISIS_MONITOR first")
        return

    crisis = json.loads(CRISIS_FILE.read_text())
    signals = crisis.get("signals", [])

    # Only generate pulses for CRITICAL and HIGH signals
    actionable = [s for s in signals if s.get("urgency") in ["CRITICAL", "HIGH"]]
    print(f"  {len(actionable)} actionable signals (CRITICAL/HIGH)")

    # Also include top ELEVATED signals
    elevated = [s for s in signals if s.get("urgency") == "ELEVATED"][:5]
    actionable.extend(elevated)

    pulses = []
    seen_types = set()
    for signal in actionable:
        pulse = generate_pulse(signal)
        # Deduplicate by crisis type — one pulse per type per cycle
        if pulse["crisis_type"] not in seen_types:
            pulses.append(pulse)
            seen_types.add(pulse["crisis_type"])

    # Write output
    output = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pulse_count": len(pulses),
        "crisis_types": list(seen_types),
        "pulses": pulses,
    }
    PULSES_OUT.write_text(json.dumps(output, indent=2), encoding="utf-8")

    print(f"  Generated {len(pulses)} knowledge pulses across {len(seen_types)} crisis types")
    for p in pulses[:5]:
        print(f"    [{p['urgency']}] {p['crisis_type']}: {p['signal'][:80]}")
        print(f"         -> {', '.join(p['subreddit_targets'][:3])}")


if __name__ == "__main__":
    main()

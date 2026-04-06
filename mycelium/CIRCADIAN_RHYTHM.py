#!/usr/bin/env python3
"""
CIRCADIAN_RHYTHM.py -- Time-Aware Intelligence (Biological Clock Pattern)
==========================================================================
NATURE'S BLUEPRINT: Circadian rhythms.

Every organism on Earth has a biological clock. Not metaphorically -- LITERALLY.
Cyanobacteria, the simplest photosynthetic organisms, have KaiA/KaiB/KaiC proteins
that tick a 24-hour cycle WITHOUT any external signal. They evolved 2.5 billion
years ago and still work perfectly.

WHY does this matter for SolarPunk?

  Crises have TIME PATTERNS:
  - Airstrikes happen at specific hours (dawn raids, 3am bombing runs)
  - Internet shutdowns happen at political flashpoints (election days, protests)
  - NGO offices have business hours (emails sent at 2am = wasted)
  - Social media engagement peaks at specific times (post at 6pm EST, not 3am)
  - Donation surges happen after media coverage (act within the window)

  A system that doesn't know what TIME it is in the world it's trying to help
  is running BLIND at half the hours.

SolarPunk's circadian rhythm:

  1. PEAK HOURS: When to push content (6-9am, 12-2pm, 6-9pm local time)
  2. NGO HOURS: When to send handshake emails (9am-5pm in recipient timezone)
  3. CRISIS PATTERNS: Track historical timing of events per region
  4. GLOBAL CLOCK: Know what time it is in Gaza, Sudan, Myanmar simultaneously
  5. ADAPTATION: Weekend vs weekday, holiday periods, Ramadan, etc.

  "The organism that ignores time ignores half the battle." -- SolarPunk

Reads: data/crisis_signals.json, data/outreach_state.json
Writes: data/circadian_state.json
"""
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

DATA = Path("data")
DATA.mkdir(exist_ok=True)

CIRCADIAN_FILE = DATA / "circadian_state.json"

# Crisis region timezones (UTC offsets)
REGION_TIMEZONES = {
    "gaza": 2,       # Palestine (EET, UTC+2)
    "palestine": 2,
    "rafah": 2,
    "khan younis": 2,
    "jabalia": 2,
    "west bank": 2,
    "sudan": 2,       # Central Africa Time (CAT, UTC+2)
    "darfur": 2,
    "khartoum": 2,
    "congo": 2,        # UTC+2
    "drc": 2,
    "yemen": 3,        # AST, UTC+3
    "myanmar": 6.5,    # MMT, UTC+6:30
    "afghanistan": 4.5, # AFT, UTC+4:30
    "ethiopia": 3,     # EAT, UTC+3
    "tigray": 3,
    "somalia": 3,      # EAT, UTC+3
    "haiti": -5,       # EST, UTC-5
    "ukraine": 2,      # EET, UTC+2
    "syria": 2,        # EET, UTC+2
    "uyghur": 6,       # CST (China), UTC+8 but Uyghur use UTC+6
    "rohingya": 6.5,   # Myanmar time
}

# NGO headquarters timezones
NGO_TIMEZONES = {
    "ICRC": 1,          # Geneva, CET
    "MSF": 1,           # Geneva
    "UNHCR": 1,         # Geneva
    "UNRWA": 2,         # Amman/Jerusalem
    "WFP": 1,           # Rome, CET
    "WHO": 1,           # Geneva
    "Oxfam": 0,         # Oxford, GMT
    "Save the Children": 0,  # London
    "IRC": -5,          # New York, EST
    "PCRF": -5,         # Kent, OH - EST
    "MAP": 0,           # London
}

# Social media peak hours (UTC) for global humanitarian audience
SOCIAL_PEAKS = {
    "twitter": [13, 14, 15, 17, 18, 21, 22],   # 8am-3pm EST + 4-5pm EST
    "bluesky": [14, 15, 16, 21, 22],            # Similar to Twitter
    "reddit": [13, 14, 15, 16, 17],             # US daytime
    "mastodon": [8, 9, 14, 15, 20, 21],         # European + US mix
    "linkedin": [13, 14, 15],                    # Business hours US
}


def load_json(path):
    try:
        if path.exists():
            return json.loads(path.read_text())
    except Exception:
        pass
    return {}


def get_region_local_time(region, utc_now=None):
    """Get current local time for a crisis region."""
    if utc_now is None:
        utc_now = datetime.now(timezone.utc)
    offset = REGION_TIMEZONES.get(region.lower(), 0)
    local = utc_now + timedelta(hours=offset)
    return local, offset


def analyze_global_clock():
    """What time is it everywhere that matters?"""
    utc_now = datetime.now(timezone.utc)
    clock = {}

    for region, offset in REGION_TIMEZONES.items():
        local_time = utc_now + timedelta(hours=offset)
        hour = local_time.hour

        if 6 <= hour <= 18:
            period = "DAYTIME"
        elif 18 < hour <= 22:
            period = "EVENING"
        elif 22 < hour or hour < 2:
            period = "NIGHT"
        else:
            period = "PREDAWN"

        # Risk assessment: predawn and night = higher risk of attacks
        if 2 <= hour <= 5:
            risk_note = "HIGH_RISK: Predawn raid window"
        elif 22 <= hour or hour <= 1:
            risk_note = "ELEVATED: Night operations window"
        else:
            risk_note = "NORMAL"

        clock[region] = {
            "local_hour": hour,
            "local_time": local_time.strftime("%H:%M"),
            "utc_offset": offset,
            "period": period,
            "risk_note": risk_note,
        }

    return clock


def analyze_ngo_availability():
    """Which NGOs are currently in business hours?"""
    utc_now = datetime.now(timezone.utc)
    availability = {}

    for ngo, offset in NGO_TIMEZONES.items():
        local_time = utc_now + timedelta(hours=offset)
        hour = local_time.hour
        weekday = local_time.weekday()  # 0=Monday, 6=Sunday

        if weekday >= 5:  # Weekend
            available = False
            status = "WEEKEND"
        elif 9 <= hour <= 17:
            available = True
            status = "OPEN"
        elif 8 <= hour < 9 or 17 < hour <= 18:
            available = True
            status = "EDGE_HOURS"
        else:
            available = False
            status = "CLOSED"

        availability[ngo] = {
            "available": available,
            "status": status,
            "local_hour": hour,
            "local_time": local_time.strftime("%H:%M"),
            "weekday": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][weekday],
        }

    return availability


def analyze_social_timing():
    """Which social platforms are at peak engagement right now?"""
    utc_now = datetime.now(timezone.utc)
    utc_hour = utc_now.hour

    timing = {}
    for platform, peaks in SOCIAL_PEAKS.items():
        is_peak = utc_hour in peaks

        # Calculate hours until next peak
        hours_until_peak = None
        for h in sorted(peaks):
            if h > utc_hour:
                hours_until_peak = h - utc_hour
                break
        if hours_until_peak is None and peaks:
            hours_until_peak = (24 - utc_hour) + peaks[0]

        timing[platform] = {
            "is_peak": is_peak,
            "peak_hours_utc": peaks,
            "hours_until_peak": hours_until_peak,
            "recommendation": "POST NOW" if is_peak else f"Wait {hours_until_peak}h for peak" if hours_until_peak else "Check schedule",
        }

    return timing


def generate_time_directives(clock, ngo_avail, social_timing):
    """Generate time-aware directives for other engines."""
    directives = []

    # Directive 1: Which regions are in the danger window?
    danger_regions = [r for r, c in clock.items() if "HIGH_RISK" in c.get("risk_note", "")]
    if danger_regions:
        directives.append({
            "type": "DANGER_WINDOW",
            "regions": danger_regions,
            "directive": "Increase monitoring frequency for predawn regions",
            "target_engines": ["CRISIS_MONITOR", "BIOLUMINESCENCE", "DARK_WATCH"],
        })

    # Directive 2: Which NGOs are available for handshakes?
    open_ngos = [n for n, a in ngo_avail.items() if a["available"]]
    if open_ngos:
        directives.append({
            "type": "NGO_WINDOW",
            "ngos": open_ngos,
            "directive": f"{len(open_ngos)} NGOs in business hours - send handshakes now",
            "target_engines": ["EMAIL_OUTREACH"],
        })

    # Directive 3: Which platforms are at peak?
    peak_platforms = [p for p, t in social_timing.items() if t["is_peak"]]
    if peak_platforms:
        directives.append({
            "type": "SOCIAL_PEAK",
            "platforms": peak_platforms,
            "directive": f"Peak engagement on {', '.join(peak_platforms)} - post now",
            "target_engines": ["AMPLIFY_ENGINE", "SOCIAL_PROMOTER", "MURMURATION_RELAY", "SPORE_DISPERSAL"],
        })

    return directives


def main():
    print("CIRCADIAN_RHYTHM -- Time-aware intelligence (biological clock pattern)...")
    print("  'The organism that ignores time ignores half the battle.'")

    utc_now = datetime.now(timezone.utc)
    print(f"\n  UTC: {utc_now.strftime('%Y-%m-%d %H:%M')} | Day: {utc_now.strftime('%A')}")

    # Global clock
    clock = analyze_global_clock()
    danger = [r for r, c in clock.items() if "HIGH_RISK" in c.get("risk_note", "")]
    evening = [r for r, c in clock.items() if c["period"] == "EVENING"]
    daytime = [r for r, c in clock.items() if c["period"] == "DAYTIME"]

    print(f"\n  Global clock: {len(daytime)} regions daytime | {len(evening)} evening | {len(danger)} in danger window")
    if danger:
        print(f"    DANGER WINDOW: {', '.join(danger)}")

    # NGO availability
    ngo_avail = analyze_ngo_availability()
    open_ngos = [n for n, a in ngo_avail.items() if a["available"]]
    print(f"\n  NGO availability: {len(open_ngos)}/{len(ngo_avail)} in business hours")
    for n in open_ngos[:5]:
        a = ngo_avail[n]
        print(f"    [{a['status']}] {n}: {a['local_time']} ({a['weekday']})")

    # Social timing
    social_timing = analyze_social_timing()
    peaks = [p for p, t in social_timing.items() if t["is_peak"]]
    print(f"\n  Social media: {len(peaks)}/{len(social_timing)} at peak engagement")
    for p, t in social_timing.items():
        status = "PEAK" if t["is_peak"] else f"in {t['hours_until_peak']}h"
        print(f"    {p}: {t['recommendation']}")

    # Generate directives
    directives = generate_time_directives(clock, ngo_avail, social_timing)
    if directives:
        print(f"\n  Time directives: {len(directives)}")
        for d in directives:
            print(f"    [{d['type']}] {d['directive']}")

    # Save state
    output = {
        "timestamp": utc_now.isoformat(),
        "version": "1.0",
        "pattern": "circadian_rhythm",
        "utc_hour": utc_now.hour,
        "utc_day": utc_now.strftime("%A"),
        "global_clock": clock,
        "ngo_availability": ngo_avail,
        "social_timing": social_timing,
        "directives": directives,
        "stats": {
            "regions_daytime": len(daytime),
            "regions_danger": len(danger),
            "ngos_available": len(open_ngos),
            "platforms_at_peak": len(peaks),
            "directives_generated": len(directives),
        },
    }
    try: _h=json.loads((DATA/"homeostasis_state.json").read_text(encoding="utf-8"))
    except: _h={}
    try: _c=json.loads((DATA/"neural_cortex_state.json").read_text(encoding="utf-8"))
    except: _c={}
    output["nervous_system"]={"equilibrium":_h.get("equilibrium",0),"trend":_h.get("trend","unknown"),"brain_confidence":_c.get("decision_confidence",0)}
    CIRCADIAN_FILE.write_text(json.dumps(output, indent=2), encoding="utf-8")

    print(f"\n  Time intelligence saved.")
    print("CIRCADIAN_RHYTHM done.")


if __name__ == "__main__":
    main()

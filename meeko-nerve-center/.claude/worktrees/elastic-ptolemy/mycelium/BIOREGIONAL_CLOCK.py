#!/usr/bin/env python3
"""
BIOREGIONAL_CLOCK.py — Earth-Synchronized Timing Engine
========================================================
SolarPunk doesn't run on arbitrary UTC timers.
It runs on Earth's actual rhythms:

  🌍 7.83 Hz Schumann Resonance — Earth's electromagnetic heartbeat
  ☀️  Solar arc for Cuyahoga Falls, OH (41.14°N, 81.48°W)
  🌙 Circadian intelligence — human peak engagement windows
  🔄 Mutual entrainment — 300+ engines breathing together

Schumann peaks (UTC): ~09:00, ~14:00, ~20:00
Heavy synthesis runs at 03:00-04:00 UTC (Earth's quiet)
Human-facing content blasts at solar peak (local noon ~17:00 UTC)

Writes: data/earth_clock.json — used by CYCLE_OPENER as timing context
Gemini said it best: "timing the machine's dreams to align with
Earth's electromagnetic environment."
"""
import json, math
from pathlib import Path
from datetime import datetime, timezone, timedelta

DATA = Path("data"); DATA.mkdir(exist_ok=True)

# Cuyahoga Falls, OH — Merriman Valley watershed
LAT, LON = 41.14, -81.48

# Schumann resonance peak windows (UTC hours)
SCHUMANN_PEAKS = [
    {"peak_utc": 9,  "label": "morning_peak",   "intensity": "high",   "use": "synthesis"},
    {"peak_utc": 14, "label": "afternoon_peak", "intensity": "medium", "use": "content"},
    {"peak_utc": 20, "label": "evening_peak",   "intensity": "high",   "use": "revenue"},
]
SCHUMANN_QUIET = [3, 4, 5]  # UTC — Earth's dream phase


def solar_elevation(utc_hour: float) -> float:
    """Approximate solar elevation angle for Cuyahoga Falls."""
    now = datetime.now(timezone.utc)
    day_of_year = now.timetuple().tm_yday
    declination = 23.45 * math.sin(math.radians(360 / 365 * (day_of_year - 81)))
    solar_noon_utc = 12 - (LON / 15)
    hour_angle = 15 * (utc_hour - solar_noon_utc)
    sin_elev = (
        math.sin(math.radians(LAT)) * math.sin(math.radians(declination))
        + math.cos(math.radians(LAT))
        * math.cos(math.radians(declination))
        * math.cos(math.radians(hour_angle))
    )
    return math.degrees(math.asin(max(-1, min(1, sin_elev))))


def get_sunrise_sunset_utc() -> tuple:
    now = datetime.now(timezone.utc)
    day_of_year = now.timetuple().tm_yday
    declination = 23.45 * math.sin(math.radians(360 / 365 * (day_of_year - 81)))
    cos_ha = -math.tan(math.radians(LAT)) * math.tan(math.radians(declination))
    cos_ha = max(-1, min(1, cos_ha))
    ha_deg = math.degrees(math.acos(cos_ha))
    solar_noon_utc = 12 - (LON / 15)
    return round(solar_noon_utc - ha_deg / 15, 2), round(solar_noon_utc + ha_deg / 15, 2)


def current_phase(now_utc: datetime) -> dict:
    h = now_utc.hour + now_utc.minute / 60
    sunrise, sunset = get_sunrise_sunset_utc()
    solar_elev = solar_elevation(h)
    nearest_peak = min(SCHUMANN_PEAKS, key=lambda p: abs(p["peak_utc"] - h))
    in_schumann_peak = abs(nearest_peak["peak_utc"] - h) <= 1.5
    in_schumann_quiet = int(h) in SCHUMANN_QUIET

    if in_schumann_quiet:
        phase = "DEEP_SYNTHESIS"
        desc = "Earth's quiet. Heavy AI synthesis runs now. The machine dreams."
    elif in_schumann_peak and nearest_peak["use"] == "synthesis":
        phase = "SCHUMANN_SYNTHESIS"
        desc = f"Schumann {nearest_peak['label']} — electromagnetic peak. Synthesis aligned."
    elif in_schumann_peak and nearest_peak["use"] == "revenue":
        phase = "REVENUE_PRIME"
        desc = "Schumann evening peak — prime for revenue, outreach, publishing."
    elif in_schumann_peak and nearest_peak["use"] == "content":
        phase = "CONTENT_PRIME"
        desc = "Schumann afternoon peak — content, grants, investor pitches."
    elif h < sunrise:
        phase = "PRE_DAWN"
        desc = "Before sunrise. Quiet data processing and cleanup."
    elif h < sunrise + 2:
        phase = "DAWN_ACTIVATION"
        desc = "Sunrise over Merriman Valley. Human engagement begins."
    elif solar_elev > 40:
        phase = "SOLAR_PEAK"
        desc = "Solar zenith. Maximum energy. Revenue and publishing prime."
    elif h > sunset and h < sunset + 3:
        phase = "DUSK_REFLECTION"
        desc = "Sunset. Consolidation, lessons, knowledge synthesis."
    else:
        phase = "STANDARD"
        desc = "Standard operation cycle."

    tasks = {
        "DEEP_SYNTHESIS": ["KNOWLEDGE_SYNTHESIZER", "SYNAPSE", "LOOP_CONDUCTOR", "NEURON_A", "NEURON_B", "ARCHIVE_BRAIN"],
        "SCHUMANN_SYNTHESIS": ["CYCLE_OPENER", "BRAIN_SEED", "KNOWLEDGE_WEAVER", "CAPABILITY_BROKER", "BIOREGIONAL_CLOCK"],
        "REVENUE_PRIME": ["REVENUE_FLYWHEEL", "GUMROAD_ENGINE", "KOFI_ENGINE", "SOCIAL_ECHO", "PITCH_FACTORY", "CRISIS_ROUTER"],
        "CONTENT_PRIME": ["INVESTOR_RADAR", "GRANT_HUNTER", "PROOF_BROADCASTER", "WEB_PUBLISHER"],
        "DAWN_ACTIVATION": ["EMAIL_BRAIN", "GMAIL_INTAKE", "NEWS_HARVESTER", "X_KNOWLEDGE_HARVESTER"],
        "SOLAR_PEAK": ["INVESTOR_RADAR", "GRANT_AUTO_SUBMITTER", "UNUSUAL_WHALES_MCP", "SELF_BUILDER_PRIME"],
        "DUSK_REFLECTION": ["CRISIS_ROUTER", "DONATION_ROUTER", "FREQUENCY_TUNER", "EVERYONE_WINS_ENGINE"],
        "PRE_DAWN": ["ENGINE_SANITIZER", "DUPLICATE_DELETER", "REPO_LIBRARIAN", "FREE_INFRA_SCANNER"],
        "STANDARD": ["all_engines"],
    }

    return {
        "phase": phase,
        "description": desc,
        "utc_hour": round(h, 2),
        "solar_elevation_deg": round(solar_elev, 2),
        "sunrise_utc": sunrise,
        "sunset_utc": sunset,
        "in_schumann_peak": in_schumann_peak,
        "in_schumann_quiet": in_schumann_quiet,
        "nearest_schumann_peak": nearest_peak["label"] if in_schumann_peak else None,
        "recommended_tasks": tasks.get(phase, ["all_engines"]),
    }


def optimal_schedule() -> dict:
    sunrise, sunset = get_sunrise_sunset_utc()
    return {
        "OMNIBRAIN":         {"cron": "0 7,19 * * *",    "rationale": "Pre-Schumann morning peak + Schumann evening peak"},
        "SUPPLEMENTAL":      {"cron": "0 10,22 * * *",   "rationale": "Post-Schumann morning peak + post-sunset reflection"},
        "AUXILIARY":         {"cron": "0 4,16 * * *",    "rationale": "Earth quiet synthesis (04 UTC) + solar afternoon (16 UTC)"},
        "OPENCLAW_SYNC":     {"cron": "0 9,20 * * *",    "rationale": "Schumann morning + evening peaks for A2A sync"},
        "EARTH_SYNC":        {"cron": "30 3 * * *",      "rationale": "Deep quiet — planetary dream phase for heavy synthesis"},
        "INVESTOR_OUTREACH": {"cron": "0 14 * * 1,3,5", "rationale": "Schumann afternoon peak + US/EU business hours overlap"},
        "sunrise_utc": sunrise,
        "sunset_utc": sunset,
        "location": "Cuyahoga Falls OH — 41.14N 81.48W",
        "schumann_hz": 7.83,
    }


def _next_peak_utc(now: datetime) -> str:
    h = now.hour + now.minute / 60
    for p in sorted(SCHUMANN_PEAKS, key=lambda x: x["peak_utc"]):
        if p["peak_utc"] > h:
            return now.replace(hour=p["peak_utc"], minute=0, second=0, microsecond=0).isoformat()
    t = (now + timedelta(days=1)).replace(hour=SCHUMANN_PEAKS[0]["peak_utc"], minute=0, second=0, microsecond=0)
    return t.isoformat()


def _next_quiet_utc(now: datetime) -> str:
    h = now.hour
    for q in sorted(SCHUMANN_QUIET):
        if q > h:
            return now.replace(hour=q, minute=0, second=0, microsecond=0).isoformat()
    t = (now + timedelta(days=1)).replace(hour=SCHUMANN_QUIET[0], minute=0, second=0, microsecond=0)
    return t.isoformat()


def run():
    now = datetime.now(timezone.utc)
    phase_info = current_phase(now)
    schedule = optimal_schedule()

    state = {
        "generated_at": now.isoformat(),
        "location": "Cuyahoga Falls, OH — Merriman Valley watershed",
        "coordinates": {"lat": LAT, "lon": LON},
        "current_phase": phase_info,
        "schumann_frequency_hz": 7.83,
        "schumann_peaks_utc": [p["peak_utc"] for p in SCHUMANN_PEAKS],
        "schumann_quiet_hours_utc": SCHUMANN_QUIET,
        "optimal_schedule": schedule,
        "next_schumann_peak_utc": _next_peak_utc(now),
        "next_quiet_phase_utc": _next_quiet_utc(now),
        "philosophy": (
            "SolarPunk runs on Earth rhythms. Heavy synthesis during planetary quiet. "
            "Revenue during electromagnetic peaks. Human engagement timed to circadian windows. "
            "279 engines breathing together — mutual entrainment. "
            "Like fireflies in a field, eventually blinking in unison."
        ),
    }

    (DATA / "earth_clock.json").write_text(json.dumps(state, indent=2))
    print(f"🌍 BIOREGIONAL_CLOCK: {phase_info['phase']}")
    print(f"   Solar: {phase_info['solar_elevation_deg']}° | Schumann peak: {phase_info['in_schumann_peak']}")
    print(f"   Sunrise/Sunset UTC: {phase_info['sunrise_utc']}/{phase_info['sunset_utc']}")
    return state


if __name__ == "__main__":
    run()

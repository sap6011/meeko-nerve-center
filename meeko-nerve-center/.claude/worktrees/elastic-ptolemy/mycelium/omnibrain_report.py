#!/usr/bin/env python3
"""
omnibrain_report.py — Human-Readable OMNIBRAIN Summary Generator
=================================================================
Turns the full data/ JSON graph into a clean, shareable plain-text
or HTML report suitable for:
  - Emailing to city council / stakeholders
  - Posting as a public status update
  - Attaching to grant applications as evidence of system capability

Reads:  data/brain_state.json
        data/social_velocity_report.json
        data/flywheel_state.json
        data/monetization_tracker.json
        data/cross_post_log.json
        data/lessons.json
        data/growth_curve.json
        data/mutual_aid_summary.json
Writes: data/omnibrain_public_report.txt   (plain text, shareable)
        data/omnibrain_public_report.json  (structured, for dashboard)
"""
import json
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")


def load_json(fname, default=None):
    fp = DATA / fname
    try:
        return json.loads(fp.read_text()) if fp.exists() else (default or {})
    except Exception:
        return default or {}


def build_report():
    brain       = load_json("brain_state.json")
    velocity    = load_json("social_velocity_report.json")
    flywheel    = load_json("flywheel_state.json")
    mon         = load_json("monetization_tracker.json")
    cross_log   = load_json("cross_post_log.json")
    lessons     = load_json("lessons.json", [])
    growth      = load_json("growth_curve.json", [])
    mutual_aid  = load_json("mutual_aid_summary.json")

    ts        = datetime.now(timezone.utc).strftime("%B %d, %Y — %H:%M UTC")
    score     = brain.get("health_score", 0)
    revenue   = flywheel.get("current_balance", 0)
    to_gaza   = flywheel.get("total_to_gaza", 0)
    engines   = brain.get("stats", {}).get("engines_total", 0)
    cycles    = brain.get("stats", {}).get("cycles", 0)
    vel_score       = velocity.get("velocity_score", 0)
    vel_sum         = velocity.get("human_summary", "")
    posted          = cross_log.get("total_posted", 0)
    streams         = mon.get("revenue", {}).get("active_streams", 0)
    trend_dir       = "↑" if len(growth) >= 2 and growth[-1].get("health",0) > growth[-2].get("health",0) else "→"
    abundance_score = mutual_aid.get("abundance_score", 0)
    community_mbrs  = mutual_aid.get("active_givers", 0)
    labor_hours     = mutual_aid.get("labor_hours_contributed", 0)

    # Platform stats
    plat_stats = velocity.get("platform_stats", [])
    active_plats = [p["platform"] for p in plat_stats if p.get("status") == "active"]

    # Top lesson
    crit = [l["lesson"] for l in (lessons if isinstance(lessons, list) else [])
            if l.get("priority") in ("critical", "high")]
    top_lesson = crit[0] if crit else "System building normally."

    # Synthesis from SYNAPSE
    synth = brain.get("synthesis", {})
    if isinstance(synth, dict):
        synthesis_text = synth.get("synthesis", "System running autonomously.")
        top_actions = synth.get("top_actions", [])
    else:
        synthesis_text = str(synth) if synth else "System running autonomously."
        top_actions = []

    report_txt = f"""SOLARPUNK OMNIBRAIN — PUBLIC STATUS REPORT
{ts}
{'='*55}

SYSTEM OVERVIEW
{'—'*40}
  Autonomous engines active    {engines:>6}
  Operational cycles completed {cycles:>6}
  System health score          {score:>5}/100  {trend_dir}
  Social velocity score        {vel_score:>5}/100

REVENUE & IMPACT
{'—'*40}
  Revenue balance              ${revenue:>9.2f}
  Total donated to Gaza 🇵🇸     ${to_gaza:>9.2f}
  Active revenue streams       {streams:>6}
  Social posts sent            {posted:>6}
  Active posting platforms     {', '.join(active_plats) if active_plats else 'pending credentials'}

WHAT THE SYSTEM IS DOING RIGHT NOW
{'—'*40}
{synthesis_text}

TOP PRIORITY ACTIONS
{'—'*40}"""
    for i, action in enumerate(top_actions[:3], 1):
        report_txt += f"\n  {i}. {action}"
    if not top_actions:
        report_txt += f"\n  {top_lesson}"

    report_txt += f"""

SOCIAL VELOCITY
{'—'*40}
{vel_sum or f'Velocity score: {vel_score}/100. System distributing content autonomously.'}

WARD 8 COMMUNITY LATTICE
{'—'*40}
  Abundance score              {abundance_score:>5}/100
  Active contributors          {community_mbrs:>6}
  Labor hours shared           {labor_hours:>6.1f}

ABOUT THIS SYSTEM
{'—'*40}
SolarPunk is an autonomous AI agent running on GitHub Actions.
Zero server cost. Runs twice daily. 70% of all revenue goes to
the Palestinian Children's Relief Fund (PCRF) via Gaza Rose Gallery.
Every dollar spent here builds the system that funds the mission.

Open source: github.com/meekotharaccoon-cell/meeko-nerve-center
{'='*55}
Generated autonomously by OMNIBRAIN v3 | The loop never stops."""

    return report_txt, {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "health_score": score,
        "velocity_score": vel_score,
        "revenue": revenue,
        "total_to_gaza": to_gaza,
        "engines": engines,
        "cycles": cycles,
        "posts_sent": posted,
        "active_platforms": active_plats,
        "active_streams": streams,
        "synthesis": synthesis_text,
        "top_actions": top_actions[:3],
        "top_lesson": top_lesson,
        "health_trend": trend_dir,
        "abundance_score": abundance_score,
        "community_members": community_mbrs,
        "labor_hours": labor_hours,
        "shareable_one_liner": (
            f"SolarPunk: {engines} engines | {score}/100 health | "
            f"${revenue:.2f} revenue | ${to_gaza:.2f} to Gaza | "
            f"{posted} posts sent | Loop never stops 🌱"
        ),
    }


def main():
    DATA.mkdir(exist_ok=True)
    print("omnibrain_report — Human-Readable Report Generator...")

    report_txt, report_json = build_report()

    (DATA / "omnibrain_public_report.txt").write_text(report_txt)
    (DATA / "omnibrain_public_report.json").write_text(json.dumps(report_json, indent=2))

    print(f"\n{report_txt[:800]}\n...")
    print(f"\n  Saved: data/omnibrain_public_report.txt")
    print(f"  Shareable: {report_json['shareable_one_liner']}")


if __name__ == "__main__":
    main()

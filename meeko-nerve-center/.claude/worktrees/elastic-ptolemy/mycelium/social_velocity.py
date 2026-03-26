#!/usr/bin/env python3
"""
social_velocity.py — Social Distribution Velocity Engine
=========================================================
Measures how fast and effectively SolarPunk is distributing content.
Turns raw cross_post_log data into actionable velocity metrics.

Velocity = (posts sent × success rate × platform reach) / cycle count
Score 0-100 like health score.

Reads:  data/cross_post_log.json     (what was posted, where, when, results)
        data/signal_tracker.json     (platform recommendations, content signals)
        data/monetization_tracker.json (revenue correlation)
        data/loop_memory.json        (cycle count for rate calculation)
Writes: data/social_velocity_report.json
"""
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

DATA = Path("data")

PLATFORM_REACH = {
    "twitter": 1.0,
    "reddit": 0.9,
    "devto": 0.6,
    "mastodon": 0.4,
}


def load_json(fname, default=None):
    fp = DATA / fname
    try:
        return json.loads(fp.read_text()) if fp.exists() else (default or {})
    except Exception:
        return default or {}


def parse_platform_stats(posts):
    """Break down performance by platform."""
    stats = {}
    for post in posts:
        plat = post.get("platform", "unknown").split("/")[0]  # reddit/subreddit → reddit
        result = post.get("result", {}).get("status", "unknown")
        if plat not in stats:
            stats[plat] = {"total": 0, "posted": 0, "failed": 0, "skipped": 0}
        stats[plat]["total"] += 1
        if result == "posted":
            stats[plat]["posted"] += 1
        elif result in ("failed", "error"):
            stats[plat]["failed"] += 1
        else:
            stats[plat]["skipped"] += 1

    platform_list = []
    for plat, s in stats.items():
        rate = round(s["posted"] / s["total"] * 100, 1) if s["total"] > 0 else 0
        reach_weight = PLATFORM_REACH.get(plat, 0.5)
        platform_list.append({
            "platform": plat,
            "total_attempts": s["total"],
            "successful": s["posted"],
            "failed": s["failed"],
            "skipped": s["skipped"],
            "success_rate_pct": rate,
            "reach_weight": reach_weight,
            "weighted_score": round(rate * reach_weight, 1),
            "status": "active" if rate >= 50 else ("dormant" if s["total"] < 3 else "failing"),
        })
    platform_list.sort(key=lambda x: x["weighted_score"], reverse=True)
    return platform_list


def compute_recency_window(posts, days=7):
    """Posts in the last N days."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    recent = []
    for post in posts:
        ts_str = post.get("ts", "")
        if not ts_str:
            continue
        try:
            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            if ts >= cutoff:
                recent.append(post)
        except Exception:
            pass
    return recent


def compute_velocity_score(log, platform_stats, cycles, recent_posts):
    """0-100 velocity score."""
    total_posted = log.get("total_posted", 0)
    total_cycles = log.get("cycles", max(cycles, 1))

    # Posts per cycle (rate)
    post_rate = total_posted / max(total_cycles, 1)
    rate_score = min(40, post_rate * 40)  # 1 post/cycle = 40 pts

    # Platform health (weighted success rate)
    active_platforms = [p for p in platform_stats if p["status"] == "active"]
    if platform_stats:
        avg_weighted = sum(p["weighted_score"] for p in platform_stats) / len(platform_stats)
        platform_score = min(30, avg_weighted * 0.3)
    else:
        platform_score = 0

    # Recency (posted in last 7 days?)
    recency_score = min(20, len(recent_posts) * 5)

    # Platform diversity bonus
    diversity_score = min(10, len(active_platforms) * 5)

    total = round(rate_score + platform_score + recency_score + diversity_score)
    return min(100, max(0, total)), {
        "rate": round(rate_score, 1),
        "platform_health": round(platform_score, 1),
        "recency": recency_score,
        "diversity": diversity_score,
    }


def revenue_correlation(log, monetization):
    """Rough correlation between posting activity and revenue signals."""
    total_posted = log.get("total_posted", 0)
    revenue = monetization.get("revenue", {}).get("total_revenue", 0)
    signals = monetization.get("signal_count", 0)

    if total_posted == 0:
        return {"note": "No posts yet — no correlation possible", "status": "inactive"}
    if revenue > 0:
        ratio = round(revenue / total_posted, 4)
        return {"revenue_per_post": ratio, "total_revenue": revenue,
                "total_posts": total_posted, "status": "converting"}
    return {"note": "Posts sent but no revenue yet — keep posting",
            "total_posts": total_posted, "status": "building_audience"}


def generate_summary(score, platform_stats, recent_count, log, velocity_breakdown):
    """Human-readable summary Meeko can share."""
    total = log.get("total_posted", 0)
    cycles = log.get("cycles", 0)
    active = [p["platform"] for p in platform_stats if p["status"] == "active"]

    if score >= 75:
        tier = "HIGH VELOCITY 🚀"
        note = "Distribution is firing. Content is reaching audiences consistently."
    elif score >= 50:
        tier = "BUILDING MOMENTUM ⚡"
        note = "Posts going out. Add credentials to push velocity higher."
    elif score >= 25:
        tier = "EARLY STAGE 🌱"
        note = "System is posting. More cycles needed to build velocity."
    else:
        tier = "PRE-LAUNCH 🔧"
        note = "Set X_API_KEY and REDDIT_CLIENT_ID in GitHub Secrets to activate posting."

    platforms_str = ", ".join(active) if active else "none active yet"
    return (
        f"SolarPunk Social Velocity: {score}/100 — {tier}\n"
        f"{total} posts sent across {cycles} cycles | Active platforms: {platforms_str}\n"
        f"{recent_count} posts in last 7 days | {note}"
    )


def main():
    DATA.mkdir(exist_ok=True)
    print("social_velocity — Social Distribution Velocity Engine...")
    ts = datetime.now(timezone.utc).isoformat()

    log          = load_json("cross_post_log.json", {"posts": [], "cycles": 0, "total_posted": 0})
    signals      = load_json("signal_tracker.json")
    monetization = load_json("monetization_tracker.json")
    loop_mem     = load_json("loop_memory.json", [])
    cycles       = len(loop_mem) if isinstance(loop_mem, list) else 0

    posts           = log.get("posts", [])
    platform_stats  = parse_platform_stats(posts)
    recent_posts    = compute_recency_window(posts, days=7)
    score, breakdown = compute_velocity_score(log, platform_stats, cycles, recent_posts)
    rev_corr        = revenue_correlation(log, monetization)
    summary         = generate_summary(score, platform_stats, len(recent_posts), log, breakdown)

    # Pull signal_tracker recommendations for context
    recs = signals.get("recommendations", [])
    top_rec = recs[0] if recs else {}

    report = {
        "timestamp": ts,
        "velocity_score": score,
        "velocity_breakdown": breakdown,
        "platform_stats": platform_stats,
        "recent_7d_posts": len(recent_posts),
        "total_posts_ever": log.get("total_posted", 0),
        "post_cycles": log.get("cycles", 0),
        "revenue_correlation": rev_corr,
        "signal_recommendation": top_rec,
        "human_summary": summary,
        "shareable_one_liner": f"Gaza Rose Gallery: {log.get('total_posted',0)} posts sent, {score}/100 velocity, loop active 🌱",
        "status": "high_velocity" if score >= 75 else ("building" if score >= 25 else "pre_launch"),
    }

    (DATA / "social_velocity_report.json").write_text(json.dumps(report, indent=2))

    print(f"\n  Velocity Score: {score}/100")
    print(f"  Breakdown: {breakdown}")
    print(f"  Platforms: {len(platform_stats)} tracked | {len([p for p in platform_stats if p['status']=='active'])} active")
    print(f"  Recent (7d): {len(recent_posts)} posts")
    print(f"  Revenue: {rev_corr.get('status','unknown')}")
    print(f"\n  {summary}")


if __name__ == "__main__":
    main()

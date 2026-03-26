#!/usr/bin/env python3
"""
signal_tracker.py — Content Performance Signal Tracker
=======================================================
Second link in the missing connections chain (connections.json):
  monetization_tracker → signal_tracker → cross_poster → meeko_brain

Correlates content posted → engagement → revenue.
Tells cross_poster.py WHAT to post, WHERE, and WHEN based on signal history.

Reads:  data/monetization_tracker.json  (revenue signals)
        data/cross_post_log.json         (what was posted, when, where)
        data/content_harvest.json        (today's trending content)
        data/social_latest.json          (last cycle's generated posts)
        data/loop_memory.json            (long-term cycle memory)
Writes: data/signal_tracker.json
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


def analyze_post_history(cross_log):
    """What's been posted where — detect patterns."""
    posts = cross_log.get("posts", []) if isinstance(cross_log, dict) else []
    platform_counts = {}
    platform_success = {}
    for post in posts:
        platform = post.get("platform", "unknown")
        status   = post.get("result", {}).get("status", "unknown")
        platform_counts[platform] = platform_counts.get(platform, 0) + 1
        if status in ("posted", "success"):
            platform_success[platform] = platform_success.get(platform, 0) + 1

    platform_analysis = []
    for p, count in platform_counts.items():
        success = platform_success.get(p, 0)
        rate    = round(success / count * 100, 0) if count > 0 else 0
        platform_analysis.append({
            "platform": p, "total_posts": count,
            "successful": success, "success_rate_pct": rate,
            "status": "working" if rate >= 50 else ("failing" if count >= 3 else "untested"),
        })
    platform_analysis.sort(key=lambda x: x["success_rate_pct"], reverse=True)
    return {"platforms": platform_analysis, "total_posts_ever": len(posts)}


def extract_content_signals(harvest, social_latest):
    """What content themes are trending + which posts are ready."""
    themes   = harvest.get("trending_themes", []) if isinstance(harvest, dict) else []
    angles   = harvest.get("content_angles", []) if isinstance(harvest, dict) else []
    tweets   = []
    reddit   = []
    if isinstance(social_latest, dict):
        tweets = [t.get("text", "") for t in social_latest.get("tweets", [])
                  if t.get("result", {}).get("status") == "queued"]
        reddit = [p.get("post", {}) for p in social_latest.get("reddit", [])
                  if p.get("result", {}).get("status") == "queued"]

    return {
        "trending_themes": [t["word"] for t in themes[:8]],
        "best_content_angle": angles[0]["hook"] if angles else "",
        "queued_tweets": len(tweets),
        "queued_reddit": len(reddit),
        "ready_to_post": len(tweets) > 0 or len(reddit) > 0,
        "top_tweet": tweets[0][:200] if tweets else "",
    }


def compute_recommendations(revenue_signals, post_history, content_signals, cycles):
    """What cross_poster should do this cycle."""
    recs = []
    mon_signals = revenue_signals.get("signals", []) if isinstance(revenue_signals, dict) else []
    has_critical = any(s.get("urgency") == "critical" for s in mon_signals)

    # Platform recommendations
    platforms = post_history.get("platforms", [])
    working   = [p["platform"] for p in platforms if p["status"] == "working"]
    untested  = [p["platform"] for p in platforms if p["status"] == "untested"]
    failing   = [p["platform"] for p in platforms if p["status"] == "failing"]

    if content_signals["ready_to_post"]:
        for p in (working or ["twitter", "reddit"]):
            recs.append({
                "action": "post_queued_content",
                "platform": p,
                "priority": "high" if has_critical else "medium",
                "content_hint": content_signals["top_tweet"][:100],
            })

    if untested:
        recs.append({
            "action": "test_new_platform",
            "platform": untested[0],
            "priority": "low",
            "content_hint": "test post to check connectivity",
        })

    if has_critical and cycles < 5:
        recs.append({
            "action": "boost_frequency",
            "platform": "all",
            "priority": "critical",
            "content_hint": "First sale needed — post everywhere",
        })

    return recs


def posting_schedule(cycles):
    """Optimal posting cadence based on cycle count (system maturity)."""
    if cycles < 10:
        return {"frequency": "every_cycle", "platforms": ["twitter", "reddit"],
                "rationale": "Early stage — maximize exposure"}
    elif cycles < 50:
        return {"frequency": "every_2_cycles", "platforms": ["twitter", "reddit", "devto"],
                "rationale": "Growing — maintain consistency"}
    else:
        return {"frequency": "every_3_cycles", "platforms": ["twitter", "reddit", "devto", "mastodon"],
                "rationale": "Established — quality over quantity"}


def main():
    DATA.mkdir(exist_ok=True)
    print("signal_tracker — Content Performance Signal Tracker...")
    ts = datetime.now(timezone.utc).isoformat()

    monetization = load_json("monetization_tracker.json")
    cross_log    = load_json("cross_post_log.json", {"posts": []})
    harvest      = load_json("content_harvest.json")
    social_last  = load_json("social_latest.json")
    loop_mem     = load_json("loop_memory.json", [])
    cycles       = len(loop_mem) if isinstance(loop_mem, list) else 0

    post_history    = analyze_post_history(cross_log)
    content_signals = extract_content_signals(harvest, social_last)
    recommendations = compute_recommendations(monetization, post_history, content_signals, cycles)
    schedule        = posting_schedule(cycles)

    report = {
        "timestamp": ts,
        "cycles_run": cycles,
        "post_history": post_history,
        "content_signals": content_signals,
        "recommendations": recommendations,
        "posting_schedule": schedule,
        "revenue_signals": monetization.get("signals", [])[:5],
        "feeds_into": "cross_poster.py",
    }
    (DATA / "signal_tracker.json").write_text(json.dumps(report, indent=2))

    print(f"  Posts tracked: {post_history['total_posts_ever']} | "
          f"Platforms: {len(post_history['platforms'])} | "
          f"Content queued: {content_signals['queued_tweets']} tweets, "
          f"{content_signals['queued_reddit']} reddit")
    print(f"  Recommendations: {len(recommendations)}")
    for r in recommendations[:3]:
        icon = {"critical": "🔴", "high": "🟡", "medium": "🔵", "low": "⚪"}.get(r.get("priority", ""), "•")
        print(f"  {icon} [{r['priority']}] {r['action']} → {r['platform']}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
TEMPORAL_CORTEX.py -- The System Remembers
==========================================
A brain without memory is just a reflex machine. SolarPunk has been
running for weeks, making thousands of commits, but it has no concept
of its own history. TEMPORAL_CORTEX changes that.

It reads git history and extracts:
  1. Growth timeline -- when did engines get added?
  2. Corruption waves -- when did SIA start mangling code?
  3. Activity patterns -- what time of day is the system most active?
  4. Author analysis -- who/what is making changes?
  5. File churn -- which files change most often? (fragile code)
  6. Milestone detection -- significant jumps in engine count, wire count

Biology: The hippocampus. Without it, you can't form new memories.
With it, you can learn from the past and plan for the future.

Reads: git log (subprocess), data/brain_state.json
Writes: data/temporal_analysis.json
Zero secrets needed.
"""
import json
import re
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

DATA = Path("data")
DATA.mkdir(exist_ok=True)


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


def git_log(max_commits=500):
    """Read git history."""
    try:
        result = subprocess.run(
            ["git", "log", f"--max-count={max_commits}",
             "--pretty=format:%H|%an|%ae|%aI|%s"],
            capture_output=True, text=True, timeout=30,
            encoding="utf-8", errors="replace"
        )
        if result.returncode != 0:
            return []

        commits = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split("|", 4)
            if len(parts) >= 5:
                commits.append({
                    "hash": parts[0][:12],
                    "author": parts[1],
                    "email": parts[2],
                    "date": parts[3],
                    "message": parts[4],
                })
        return commits
    except Exception as e:
        print(f"    git log failed: {e}")
        return []


def git_file_stats(max_commits=200):
    """Get file change frequency from git."""
    try:
        result = subprocess.run(
            ["git", "log", f"--max-count={max_commits}",
             "--pretty=format:", "--name-only"],
            capture_output=True, text=True, timeout=30,
            encoding="utf-8", errors="replace"
        )
        files = [f.strip() for f in result.stdout.split("\n") if f.strip()]
        return Counter(files)
    except Exception:
        return Counter()


def analyze_growth(commits):
    """Track engine count growth over time from commit messages."""
    milestones = []
    engine_pattern = re.compile(r'(\d{2,3})\s*engines?', re.IGNORECASE)
    wire_pattern = re.compile(r'(\d{3,5})\s*wires?', re.IGNORECASE)

    for commit in commits:
        msg = commit["message"]
        engine_match = engine_pattern.search(msg)
        wire_match = wire_pattern.search(msg)

        if engine_match or wire_match:
            milestone = {
                "date": commit["date"][:10],
                "hash": commit["hash"],
                "message": msg[:100],
            }
            if engine_match:
                milestone["engines"] = int(engine_match.group(1))
            if wire_match:
                milestone["wires"] = int(wire_match.group(1))
            milestones.append(milestone)

    return milestones


def analyze_corruption(commits):
    """Detect SIA corruption waves and other automated damage."""
    sia_commits = []
    sentinel_commits = []
    corruption_indicators = []

    for commit in commits:
        msg = commit["message"].lower()
        author = commit["author"].lower()

        if "sia" in author or "nanobot self-heal" in msg:
            sia_commits.append(commit)
        if "sentinel" in msg or "sentinel" in author:
            sentinel_commits.append(commit)
        if "nested" in msg or "corrupt" in msg or "mangl" in msg:
            corruption_indicators.append(commit)

    # Detect waves: clusters of SIA commits
    waves = []
    if sia_commits:
        current_wave = [sia_commits[0]]
        for i in range(1, len(sia_commits)):
            # If commits are close together, same wave
            try:
                prev_date = datetime.fromisoformat(sia_commits[i-1]["date"].replace("Z", "+00:00"))
                curr_date = datetime.fromisoformat(sia_commits[i]["date"].replace("Z", "+00:00"))
                gap_hours = abs((curr_date - prev_date).total_seconds()) / 3600
                if gap_hours < 12:
                    current_wave.append(sia_commits[i])
                else:
                    if len(current_wave) >= 2:
                        waves.append({
                            "start": current_wave[0]["date"][:16],
                            "end": current_wave[-1]["date"][:16],
                            "commits": len(current_wave),
                        })
                    current_wave = [sia_commits[i]]
            except Exception:
                current_wave = [sia_commits[i]]

        if len(current_wave) >= 2:
            waves.append({
                "start": current_wave[0]["date"][:16],
                "end": current_wave[-1]["date"][:16],
                "commits": len(current_wave),
            })

    return {
        "sia_total_commits": len(sia_commits),
        "sentinel_commits": len(sentinel_commits),
        "corruption_indicators": len(corruption_indicators),
        "corruption_waves": waves,
    }


def analyze_activity_patterns(commits):
    """What time of day / day of week is the system most active?"""
    hours = Counter()
    days = Counter()
    authors = Counter()

    for commit in commits:
        try:
            dt = datetime.fromisoformat(commit["date"].replace("Z", "+00:00"))
            hours[dt.hour] += 1
            days[dt.strftime("%A")] += 1
        except Exception:
            pass
        authors[commit["author"]] += 1

    # Peak hours
    peak_hour = hours.most_common(1)[0] if hours else ("?", 0)
    quiet_hour = hours.most_common()[-1] if hours else ("?", 0)

    return {
        "total_commits": len(commits),
        "peak_hour_utc": peak_hour[0] if hours else None,
        "peak_hour_commits": peak_hour[1] if hours else 0,
        "quiet_hour_utc": quiet_hour[0] if hours else None,
        "day_distribution": dict(days.most_common()),
        "author_distribution": dict(authors.most_common(10)),
        "unique_authors": len(authors),
    }


def analyze_file_churn(file_counts):
    """Which files change most? High churn = fragile code."""
    # Filter to mycelium and data files
    engine_churn = {f: c for f, c in file_counts.items() if f.startswith("mycelium/")}
    data_churn = {f: c for f, c in file_counts.items() if f.startswith("data/")}

    top_engine = sorted(engine_churn.items(), key=lambda x: -x[1])[:20]
    top_data = sorted(data_churn.items(), key=lambda x: -x[1])[:20]

    return {
        "most_changed_engines": [{"file": f, "changes": c} for f, c in top_engine],
        "most_changed_data": [{"file": f, "changes": c} for f, c in top_data],
        "total_engine_changes": sum(engine_churn.values()),
        "total_data_changes": sum(data_churn.values()),
    }


def run():
    print("TEMPORAL CORTEX -- The System Remembers")
    print("=" * 50)

    # Read git history
    print("\n  [1/5] Reading git history...")
    commits = git_log(max_commits=500)
    print(f"    Loaded {len(commits)} commits")

    if not commits:
        print("    No git history available")
        save_json(DATA / "temporal_analysis.json", {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": "No git history available",
        })
        return

    # Growth analysis
    print("\n  [2/5] Analyzing growth timeline...")
    milestones = analyze_growth(commits)
    print(f"    Found {len(milestones)} engine/wire milestones")
    for m in milestones[:5]:
        engines = m.get("engines", "?")
        wires = m.get("wires", "?")
        print(f"    [{m['date']}] {engines} engines, {wires} wires")

    # Corruption analysis
    print("\n  [3/5] Detecting corruption waves...")
    corruption = analyze_corruption(commits)
    print(f"    SIA commits: {corruption['sia_total_commits']}")
    print(f"    Corruption waves: {len(corruption['corruption_waves'])}")
    for wave in corruption["corruption_waves"][:5]:
        print(f"    [{wave['start']}] {wave['commits']} commits in wave")

    # Activity patterns
    print("\n  [4/5] Analyzing activity patterns...")
    patterns = analyze_activity_patterns(commits)
    print(f"    Total commits: {patterns['total_commits']}")
    print(f"    Peak hour (UTC): {patterns['peak_hour_utc']}:00 ({patterns['peak_hour_commits']} commits)")
    print(f"    Unique authors: {patterns['unique_authors']}")
    for author, count in list(patterns["author_distribution"].items())[:5]:
        print(f"    {author}: {count} commits")

    # File churn
    print("\n  [5/5] Analyzing file churn...")
    file_counts = git_file_stats(max_commits=200)
    churn = analyze_file_churn(file_counts)
    print(f"    Engine file changes: {churn['total_engine_changes']}")
    print(f"    Data file changes: {churn['total_data_changes']}")
    print(f"    Most churned engines:")
    for item in churn["most_changed_engines"][:5]:
        print(f"      {item['file']}: {item['changes']} changes")

    # Compile report
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "commits_analyzed": len(commits),
        "oldest_commit": commits[-1]["date"][:10] if commits else None,
        "newest_commit": commits[0]["date"][:10] if commits else None,
        "growth_milestones": milestones,
        "corruption": corruption,
        "activity": patterns,
        "file_churn": churn,
    }
    try: _h=json.loads((DATA/"homeostasis_state.json").read_text(encoding="utf-8"))
    except: _h={}
    try: _c=json.loads((DATA/"neural_cortex_state.json").read_text(encoding="utf-8"))
    except: _c={}
    report["nervous_system"]={"equilibrium":_h.get("equilibrium",0),"trend":_h.get("trend","unknown"),"brain_confidence":_c.get("decision_confidence",0)}
    save_json(DATA / "temporal_analysis.json", report)

    print(f"\n  === TEMPORAL CORTEX SUMMARY ===")
    print(f"  History span:      {report['oldest_commit']} to {report['newest_commit']}")
    print(f"  Commits analyzed:  {len(commits)}")
    print(f"  Growth milestones: {len(milestones)}")
    print(f"  SIA intrusions:    {corruption['sia_total_commits']}")
    print(f"  Corruption waves:  {len(corruption['corruption_waves'])}")
    print(f"  Peak activity:     {patterns['peak_hour_utc']}:00 UTC")
    print(f"\n  The system remembers. Now it can learn.")


if __name__ == "__main__":
    run()

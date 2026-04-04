# NEURAL_LINK: Cross-pollination engine -- detects high-resonance content and seeds build queue
# Part of the Meeko SolarPunk Swarm.

import json
import os
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
DATA.mkdir(exist_ok=True)

VIRALITY_FILE = DATA / "virality_posts.json"
QUEUE_FILE = DATA / "self_builder_queue.json"


def cross_pollinate():
    # Read upstream state
    brain = {}
    brain_path = DATA / "brain_state.json"
    if brain_path.exists():
        try:
            brain = json.loads(brain_path.read_text())
        except Exception:
            pass

    knowledge = {}
    kg_path = DATA / "knowledge_graph.json"
    if kg_path.exists():
        try:
            knowledge = json.loads(kg_path.read_text())
        except Exception:
            pass

    posts = []
    if VIRALITY_FILE.exists():
        try:
            posts = json.loads(VIRALITY_FILE.read_text())
        except Exception:
            pass

    # Identify "High Resonance" content (Score > 85)
    hot_content = [p for p in posts if p.get('engagement_score', 0) > 85]

    queue = []
    if QUEUE_FILE.exists():
        try:
            queue = json.loads(QUEUE_FILE.read_text())
        except Exception:
            queue = []

    new_tasks = []
    for item in hot_content:
        new_task = {
            "id": f"AUTO_{int(datetime.now(timezone.utc).timestamp())}",
            "type": "PRODUCT_CREATION",
            "topic": item.get('content_summary'),
            "trigger": "high_resonance_detected",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        queue.append(new_task)
        new_tasks.append(new_task)
        print(f"Added to Build Queue: {item.get('content_summary')}")

    if new_tasks:
        QUEUE_FILE.write_text(json.dumps(queue, indent=4))

    # Write state for LIVE_WIRE
    state = {
        "engine": "CROSS_POLLINATOR",
        "ts": datetime.now(timezone.utc).isoformat(),
        "virality_posts_scanned": len(posts),
        "hot_content_found": len(hot_content),
        "tasks_seeded": len(new_tasks),
        "queue_depth": len(queue),
        "brain_cycle": brain.get("cycle", 0),
        "knowledge_nodes": len(knowledge.get("nodes", [])) if isinstance(knowledge, dict) else 0,
        "status": "active",
    }
    (DATA / "cross_pollinator_state.json").write_text(json.dumps(state, indent=2))
    print(f"State written: data/cross_pollinator_state.json")


if __name__ == "__main__":
    cross_pollinate()

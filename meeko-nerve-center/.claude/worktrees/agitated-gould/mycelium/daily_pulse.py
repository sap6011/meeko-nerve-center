import json
import os
from datetime import datetime

def generate_summary():
    print("--- Generating Solarpunk Daily Pulse Report ---")
    intel_path = 'C:/Solarpunk-Prime/data/harvested_knowledge/latest_intel.json'
    draft_path = 'C:/Solarpunk-Prime/projects/active_outreach_draft.md'
    
    summary = {
        "date": str(datetime.now().date()),
        "nodes_scouted": 0,
        "high_value_opportunities": [],
        "outreach_ready": False
    }

    if os.path.exists(intel_path):
        with open(intel_path, 'r') as f:
            data = json.load(f)
            summary["nodes_scouted"] = len(data)
            summary["high_value_opportunities"] = [i['title'] for i in data if i.get('category') in ['GRANT', 'LEGAL']]

    if os.path.exists(draft_path):
        summary["outreach_ready"] = True

    # Save summary to saves folder
    with open(f'C:/Solarpunk-Prime/saves/pulse_{summary["date"]}.json', 'w') as f:
        json.dump(summary, f, indent=4)
    
    print(f"Report Generated: {summary['nodes_scouted']} nodes found today.")
    if summary["outreach_ready"]:
        print("Outreach Nanobots: DRAFTS PREPARED AND READY FOR REVIEW.")

if __name__ == "__main__":
    generate_summary()

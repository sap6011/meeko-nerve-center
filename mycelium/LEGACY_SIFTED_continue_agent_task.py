import os 
import json 
import urllib.request 
from datetime import datetime 
from pathlib import Path

DATA = Path("data")
DATA.mkdir(exist_ok=True)
 
API = "http://localhost:8000/ask" 
TAG = "autonomoushum-20" 
 
def generate(): 
    prompt = f"Write a 200-word Amazon review for best office chair 2026. Use affiliate tag {TAG}" 
    data = json.dumps({"question": prompt}).encode() 
    req = urllib.request.Request(API, data=data, headers={"Content-Type": "application/json"}) 
    with urllib.request.urlopen(req, timeout=60) as resp: 
        content = json.loads(resp.read())["answer"] 
    filename = f"article_{datetime.now().strftime('mHS')}.txt" 
    with open(filename, "w", encoding="utf-8") as f: 
        f.write(content) 
    print(f"Saved: {filename}") 
 
if __name__ == "__main__": 
    generate() 


# -- LIVE_WIRE topology connector --
def _wire_state():
    _r = json.loads((DATA / "brain_state.json").read_text()) if (DATA / "brain_state.json").exists() else {}
    (DATA / "legacy_sifted_continue_agent_task_state.json").write_text(json.dumps({"last_run": __import__("datetime").datetime.now().isoformat(), "status": "wired"}, indent=2), encoding="utf-8")

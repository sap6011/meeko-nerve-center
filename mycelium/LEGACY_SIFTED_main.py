from fastapi import FastAPI 
from pydantic import BaseModel 
import requests 
import uvicorn 
import json
from pathlib import Path

DATA = Path("data")
DATA.mkdir(exist_ok=True)
 
app = FastAPI() 
 
class Question(BaseModel): 
    question: str 
 
@app.post("/ask") 
async def ask_ollama(q: Question): 
    response = requests.post( 
        "http://localhost:11434/api/generate", 
        json={"model": "llama3.3", "prompt": q.question, "stream": False} 
    ) 
    return {"answer": response.json()["response"]} 
 
if __name__ == "__main__": 
    uvicorn.run(app, host="127.0.0.1", port=8000) 


# -- LIVE_WIRE topology connector --
def _wire_state():
    _r = json.loads((DATA / "brain_state.json").read_text()) if (DATA / "brain_state.json").exists() else {}
    try: _h=json.loads((DATA/"homeostasis_state.json").read_text(encoding="utf-8"))
    except: _h={}
    try: _c=json.loads((DATA/"neural_cortex_state.json").read_text(encoding="utf-8"))
    except: _c={}
    (DATA / "legacy_sifted_main_state.json").write_text(json.dumps({"last_run": __import__("datetime").datetime.now().isoformat(), "status": "wired","nervous_system":{"equilibrium":_h.get("equilibrium",0),"trend":_h.get("trend","unknown"),"brain_confidence":_c.get("decision_confidence",0)}}, indent=2), encoding="utf-8")

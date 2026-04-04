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
        json={"model": "mistral", "prompt": q.question, "stream": False} 
    ) 
    return {"answer": response.json()["response"]} 
 
if __name__ == "__main__": 
    uvicorn.run(app, host="127.0.0.1", port=8000) 


# -- LIVE_WIRE topology connector --
def _wire_state():
    _r = json.loads((DATA / "brain_state.json").read_text()) if (DATA / "brain_state.json").exists() else {}
    (DATA / "legacy_sifted_main_state.json").write_text(json.dumps({"last_run": __import__("datetime").datetime.now().isoformat(), "status": "wired"}, indent=2))

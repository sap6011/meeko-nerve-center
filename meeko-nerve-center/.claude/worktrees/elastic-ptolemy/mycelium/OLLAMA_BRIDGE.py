#!/usr/bin/env python3
"""
OLLAMA_BRIDGE.py — Local Ollama integration for free, private AI inference.

Meeko has Ollama running locally with:
  - mistral:latest (4.4GB) — best for reasoning
  - codellama:latest (3.8GB) — best for code generation
  - llama3.2:latest (2.0GB) — fast general purpose
  - nomic-embed-text (274MB) — embeddings

This engine:
  1. Checks if local Ollama is accessible (localhost:11434)
  2. Routes appropriate tasks to local models (saves API costs)
  3. Generates embeddings for knowledge search
  4. Writes Ollama availability status to data/ollama_status.json

When Ollama is available, AI_CLIENT can use it as cheapest fallback.
Reads:  data/knowledge_map.json (content to embed)
Writes: data/ollama_status.json, data/knowledge_embeddings.json (partial)
"""
import json, os
import urllib.request, urllib.error
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
DATA.mkdir(exist_ok=True)

OLLAMA_BASE = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

def load_json(p, default=None):
    try:
        f = Path(p)
        if f.exists():
            return json.loads(f.read_text(encoding="utf-8", errors="ignore"))
    except Exception: pass
    return default or {}

def _ollama_post(endpoint, body, timeout=30):
    data = json.dumps(body).encode()
    req  = urllib.request.Request(
        f"{OLLAMA_BASE}/{endpoint}",
        data=data,
        headers={"Content-Type":"application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode()
            # Ollama streams NDJSON — take last complete line
            lines = [l for l in raw.strip().split("\n") if l.strip()]
            if lines:
                return json.loads(lines[-1])
            return {}
    except Exception as e:
        return {"error": str(e)}

def _ollama_get(endpoint, timeout=5):
    req = urllib.request.Request(f"{OLLAMA_BASE}/{endpoint}", method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception:
        return None

def check_ollama():
    """Check if Ollama is running and get available models."""
    result = _ollama_get("api/tags")
    if result is None:
        return False, []
    models = [m.get("name","") for m in result.get("models",[])]
    return True, models

def ollama_ask(prompt, model="mistral:latest", system=None, max_tokens=500):
    """Ask a question to local Ollama."""
    messages = []
    if system:
        messages.append({"role":"system","content":system})
    messages.append({"role":"user","content":prompt})
    body = {
        "model":    model,
        "messages": messages,
        "stream":   False,
        "options":  {"num_predict": max_tokens},
    }
    result = _ollama_post("api/chat", body, timeout=60)
    if result.get("error"):
        return ""
    return result.get("message",{}).get("content","")

def ollama_embed(text, model="nomic-embed-text:latest"):
    """Generate embedding for text using local Ollama."""
    body = {"model": model, "prompt": text}
    result = _ollama_post("api/embeddings", body, timeout=30)
    return result.get("embedding", [])

def test_ollama_capability():
    """Run a quick test to verify Ollama is working."""
    test_response = ollama_ask(
        "In one sentence, what is Gaza Rose Gallery?",
        model="llama3.2:latest",
        max_tokens=50
    )
    return bool(test_response and len(test_response) > 10), test_response[:100]

def build_knowledge_embeddings(available, models):
    """If nomic-embed-text available, embed top knowledge items."""
    if not available or "nomic-embed-text:latest" not in models:
        return 0
    knowledge = load_json("data/knowledge_map.json")
    items_to_embed = []
    # Lessons
    for l in knowledge.get("lessons",[])[:5]:
        items_to_embed.append({"type":"lesson","text":l.get("text","")[:200]})
    # Opportunities
    for o in knowledge.get("opportunities",[])[:5]:
        t = o if isinstance(o,str) else o.get("title","")
        if t: items_to_embed.append({"type":"opportunity","text":t[:200]})
    # Builder thesis
    bt = knowledge.get("builder_thesis","")
    if bt: items_to_embed.append({"type":"thesis","text":bt[:300]})

    embedded = 0
    embeddings = []
    for item in items_to_embed[:10]:  # limit per cycle
        text = item.get("text","")
        if not text: continue
        vec = ollama_embed(text)
        if vec:
            embeddings.append({**item, "embedding_dims": len(vec), "embedding_preview": vec[:3]})
            embedded += 1

    if embeddings:
        Path("data/knowledge_embeddings.json").write_text(
            json.dumps({"generated_at":datetime.now(timezone.utc).isoformat(),"embeddings":embeddings,"total":embedded}, indent=2),
            encoding="utf-8"
        )
    return embedded

def main():
    print("🤖 OLLAMA_BRIDGE — connecting to local AI inference...")
    available, models = check_ollama()

    if available:
        print(f"   ✓ Ollama running | Models: {', '.join(models[:5])}")
        working, test_resp = test_ollama_capability()
        print(f"   {'✓' if working else '⚠'} Test: {test_resp[:60]}")
        embedded = build_knowledge_embeddings(available, models)
        if embedded > 0:
            print(f"   ✓ {embedded} knowledge items embedded")
    else:
        print("   ○ Ollama not accessible (not running or different host)")
        working = False
        test_resp = ""

    # Best available model for different tasks
    best_code    = next((m for m in models if "codellama" in m), "")
    best_reason  = next((m for m in models if "mistral" in m), "")
    best_fast    = next((m for m in models if "llama3.2" in m or "llama3" in m), "")
    best_embed   = next((m for m in models if "nomic" in m or "embed" in m), "")

    output = {
        "generated_at":   datetime.now(timezone.utc).isoformat(),
        "available":       available,
        "models":          models,
        "working":         working,
        "test_response":   test_resp,
        "model_routing": {
            "code_tasks":      best_code    or "not available",
            "reasoning":       best_reason  or "not available",
            "fast_tasks":      best_fast    or "not available",
            "embeddings":      best_embed   or "not available",
        },
        "cost_savings":    "100% — local inference is free" if available else "n/a",
        "status":          "ok" if available else "offline",
    }
    Path("data/ollama_status.json").write_text(json.dumps(output, indent=2), encoding="utf-8")

    if available:
        print(f"   Code: {best_code} | Reason: {best_reason} | Embed: {best_embed}")
        print(f"   💰 Cost savings: $0 API fees when using local Ollama")

if __name__ == "__main__":
    main()

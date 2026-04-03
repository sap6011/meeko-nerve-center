#!/usr/bin/env python3
"""
OLLAMA_BRIDGE.py — Local LLM inference bridge for SolarPunk Nerve Center
Connects the mycelium engine system to Ollama (localhost:11434)

Available models:
  - mycelium:latest   → Custom SolarPunk model (4.1GB) — system reasoning
  - llama3:latest     → General purpose (4.4GB) — content generation
  - codellama:latest  → Code generation (3.6GB) — engine synthesis
  - mistral:latest    → Fast reasoning (4.1GB) — triage & routing
  - llama3.2:latest   → Lightweight (1.9GB) — quick tasks
  - nomic-embed-text  → Embeddings (261MB) — semantic search

Usage:
  from OLLAMA_BRIDGE import OllamaBridge
  bridge = OllamaBridge()
  response = bridge.generate("What engines need repair?", model="mycelium")
  embedding = bridge.embed("autonomous mutual aid infrastructure")
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Optional

try:
    import requests
except ImportError:
    print("[OLLAMA_BRIDGE] requests not installed — run: pip install requests")
    sys.exit(1)

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")

# Model routing table — maps task types to optimal models
MODEL_ROUTES = {
    "system": "mycelium:latest",       # Custom SolarPunk reasoning
    "content": "llama3:latest",         # Blog posts, outreach, grants
    "code": "codellama:latest",         # Engine generation, debugging
    "triage": "mistral:latest",         # Quick decisions, routing
    "quick": "llama3.2:latest",         # Lightweight fast tasks
    "embed": "nomic-embed-text:latest", # Semantic embeddings
}

SYSTEM_PROMPT = """You are a SolarPunk mycelium engine — part of an autonomous mutual aid
infrastructure node in Cuyahoga Falls, Ohio. Your outputs feed into a system that routes
99% of revenue to crisis zones (PCRF 60%, IRC 15%, MSF 10%, UNICEF 10%, Direct Relief 5%).
Be direct, actionable, and mission-aligned. No fluff. The math runs."""


class OllamaBridge:
    """Bridge between SolarPunk mycelium engines and local Ollama LLM inference."""

    def __init__(self, base_url: str = OLLAMA_URL):
        self.base_url = base_url.rstrip("/")
        self._verify_connection()

    def _verify_connection(self) -> bool:
        """Check Ollama is reachable and list available models."""
        try:
            r = requests.get(f"{self.base_url}/api/tags", timeout=5)
            r.raise_for_status()
            models = [m["name"] for m in r.json().get("models", [])]
            print(f"[OLLAMA_BRIDGE] Connected — {len(models)} models: {', '.join(models)}")
            return True
        except Exception as e:
            print(f"[OLLAMA_BRIDGE] WARNING: Ollama not reachable at {self.base_url}: {e}")
            return False

    def list_models(self) -> list:
        """Return list of available model names."""
        try:
            r = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return [m["name"] for m in r.json().get("models", [])]
        except Exception:
            return []

    def generate(
        self,
        prompt: str,
        model: str = "mycelium",
        system: str = SYSTEM_PROMPT,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False,
    ) -> str:
        """Generate text using a local model.

        Args:
            prompt: The input prompt
            model: Model name or route key (system/content/code/triage/quick)
            system: System prompt override
            temperature: Sampling temperature (0.0 = deterministic, 1.0 = creative)
            max_tokens: Maximum response tokens
            stream: Whether to stream response

        Returns:
            Generated text response
        """
        # Resolve model route
        resolved_model = MODEL_ROUTES.get(model, model)

        payload = {
            "model": resolved_model,
            "prompt": prompt,
            "system": system,
            "stream": stream,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        try:
            r = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=300,
            )
            r.raise_for_status()
            data = r.json()
            response_text = data.get("response", "")

            # Log stats
            total_duration = data.get("total_duration", 0) / 1e9  # ns to seconds
            eval_count = data.get("eval_count", 0)
            print(f"[OLLAMA_BRIDGE] {resolved_model} — {eval_count} tokens in {total_duration:.1f}s")

            return response_text

        except requests.exceptions.Timeout:
            return "[OLLAMA_BRIDGE] ERROR: Request timed out (300s limit)"
        except Exception as e:
            return f"[OLLAMA_BRIDGE] ERROR: {e}"

    def chat(
        self,
        messages: list,
        model: str = "mycelium",
        temperature: float = 0.7,
    ) -> str:
        """Multi-turn chat using Ollama's chat API.

        Args:
            messages: List of {"role": "user"|"assistant"|"system", "content": str}
            model: Model name or route key
            temperature: Sampling temperature

        Returns:
            Assistant response text
        """
        resolved_model = MODEL_ROUTES.get(model, model)

        # Inject system prompt if not present
        if not any(m.get("role") == "system" for m in messages):
            messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages

        payload = {
            "model": resolved_model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature},
        }

        try:
            r = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=300,
            )
            r.raise_for_status()
            return r.json().get("message", {}).get("content", "")
        except Exception as e:
            return f"[OLLAMA_BRIDGE] ERROR: {e}"

    def embed(self, text: str, model: str = "nomic-embed-text:latest") -> list:
        """Generate embeddings for semantic search.

        Args:
            text: Input text to embed
            model: Embedding model (default: nomic-embed-text)

        Returns:
            List of floats (embedding vector)
        """
        payload = {"model": model, "input": text}

        try:
            r = requests.post(
                f"{self.base_url}/api/embed",
                json=payload,
                timeout=60,
            )
            r.raise_for_status()
            data = r.json()
            embeddings = data.get("embeddings", [[]])[0]
            print(f"[OLLAMA_BRIDGE] Embedded {len(text)} chars → {len(embeddings)}-dim vector")
            return embeddings
        except Exception as e:
            print(f"[OLLAMA_BRIDGE] Embed error: {e}")
            return []

    def batch_embed(self, texts: list, model: str = "nomic-embed-text:latest") -> list:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of input strings
            model: Embedding model

        Returns:
            List of embedding vectors
        """
        payload = {"model": model, "input": texts}
        try:
            r = requests.post(f"{self.base_url}/api/embed", json=payload, timeout=120)
            r.raise_for_status()
            return r.json().get("embeddings", [])
        except Exception as e:
            print(f"[OLLAMA_BRIDGE] Batch embed error: {e}")
            return []

    def route(self, task_type: str, prompt: str, **kwargs) -> str:
        """Auto-route a prompt to the optimal model based on task type.

        Task types: system, content, code, triage, quick
        """
        return self.generate(prompt, model=task_type, **kwargs)

    def health_check(self) -> dict:
        """Return health status of Ollama and all models."""
        status = {"url": self.base_url, "reachable": False, "models": []}
        try:
            r = requests.get(f"{self.base_url}/api/tags", timeout=5)
            r.raise_for_status()
            status["reachable"] = True
            for m in r.json().get("models", []):
                status["models"].append({
                    "name": m["name"],
                    "size_mb": m.get("size", 0) // 1024 // 1024,
                    "modified": m.get("modified_at", "unknown"),
                })
        except Exception as e:
            status["error"] = str(e)
        return status


# === ENGINE INTEGRATION HELPERS ===

def quick_generate(prompt: str, model: str = "mycelium") -> str:
    """One-shot generation for use by other engines."""
    bridge = OllamaBridge()
    return bridge.generate(prompt, model=model)


def quick_embed(text: str) -> list:
    """One-shot embedding for use by other engines."""
    bridge = OllamaBridge()
    return bridge.embed(text)


def semantic_similarity(text_a: str, text_b: str) -> float:
    """Compute cosine similarity between two texts."""
    bridge = OllamaBridge()
    vec_a = bridge.embed(text_a)
    vec_b = bridge.embed(text_b)
    if not vec_a or not vec_b:
        return 0.0
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    mag_a = sum(a ** 2 for a in vec_a) ** 0.5
    mag_b = sum(b ** 2 for b in vec_b) ** 0.5
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


# === CLI ===

if __name__ == "__main__":
    bridge = OllamaBridge()

    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
        print(bridge.generate(prompt))
    else:
        # Self-test
        print("\n=== OLLAMA BRIDGE HEALTH CHECK ===")
        health = bridge.health_check()
        print(json.dumps(health, indent=2))

        if health["reachable"]:
            print("\n=== QUICK TEST (mycelium model) ===")
            result = bridge.generate(
                "In one sentence, what is SolarPunk Node-01?",
                model="system",
                max_tokens=100,
            )
            print(f"Response: {result}")

            print("\n=== EMBEDDING TEST ===")
            vec = bridge.embed("autonomous mutual aid infrastructure")
            print(f"Embedding dimension: {len(vec)}")

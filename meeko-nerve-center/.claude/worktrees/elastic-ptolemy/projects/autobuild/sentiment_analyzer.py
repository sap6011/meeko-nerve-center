
import sys
# Atomic Script: Sentiment Analyzer 2026
def analyze_vibe(text):
    positive_nodes = ["human", "community", "growth", "sustainable", "justice", "solar", "open"]
    score = sum(1 for word in positive_nodes if word in text.lower())
    return f"Human-Centric Score: {score}/7"

if __name__ == "__main__":
    # Test against the 2026 SolarPunk Ethos
    test_text = "This node focuses on open growth and sustainable community justice."
    print(analyze_vibe(test_text))

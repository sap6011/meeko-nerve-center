import os
import json

def generate_grant_answers(question):
    # This is the "Solarpunk Brain" answering human questions
    context = "We are the SolarPunk Intelligence Agency. Our mission is humanitarian, decentralized growth."
    
    # Simple logic to adapt to common grant questions
    if "impact" in question.lower():
        return f"{context} We create upgraded credit loops and regenerative energy infrastructure."
    if "budget" in question.lower():
        return "100% of funds are directed to decentralized Solarpunk infrastructure and node growth."
    return f"{context} We are ready to manifest this reality."

if __name__ == "__main__":
    # Test the brain
    print(generate_grant_answers("What is your project impact?"))

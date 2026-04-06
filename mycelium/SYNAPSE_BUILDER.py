import json, os, re

def weave_connections():
    bank = 'data/knowledge_bank.txt'
    if not os.path.exists(bank): return
    with open(bank, 'r', encoding='utf-8') as f: lines = f.readlines()
    
    graph = {'nodes': [], 'edges': []}
    for line in lines:
        # Look for potential synergies
        if "Seed Harvested" in line:
            tags = ["Potential-Growth"]
            if any(word in line.lower() for word in ["automation", "script", "python"]):
                tags.append("Tech-Evolution")
            graph['nodes'].append({'info': line.strip(), 'tags': tags})
    
    with open('data/knowledge_graph.json', 'w', encoding='utf-8') as f:
        try: _h=json.loads((DATA/"homeostasis_state.json").read_text(encoding="utf-8"))
        except: _h={}
        try: _c=json.loads((DATA/"neural_cortex_state.json").read_text(encoding="utf-8"))
        except: _c={}
        graph["nervous_system"]={"equilibrium":_h.get("equilibrium",0),"trend":_h.get("trend","unknown"),"brain_confidence":_c.get("decision_confidence",0)}
        json.dump(graph, f, indent=4)
    print(f"🕸️ Weaved {len(graph['nodes'])} new potential connections.")

if __name__ == "__main__": weave_connections()

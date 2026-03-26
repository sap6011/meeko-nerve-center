import json
import os

def connect_nodes():
    print("--- Node Connector: Synthesizing Outreach ---")
    
    # Load the latest intel
    with open('C:/Solarpunk-Prime/data/harvested_knowledge/latest_intel.json', 'r') as f:
        intel = json.load(f)
    
    # Find the most high-value node (Grant or Legal)
    priority_node = next((item for item in intel if item['category'] in ['GRANT', 'LEGAL']), intel[0])
    
    # Load the Manifesto Template
    template_path = 'C:/Solarpunk-Prime/docs/email-automation-blueprints/solarpunk_manifesto_v1.md'
    if os.path.exists(template_path):
        with open(template_path, 'r') as f:
            manifesto = f.read()
        
        # Inject the Gift (The 2026 Intel)
        gift_text = f"We have identified a specific opportunity: {priority_node['title']}. You can access it here: {priority_node['link']}"
        personalized_manifesto = manifesto.replace('[Specific_Tool/Credit_Loop]', gift_text)
        
        # Save the ready-to-send draft
        with open('C:/Solarpunk-Prime/projects/active_outreach_draft.md', 'w') as f:
            f.write(personalized_manifesto)
        
        print(f"Action: High-value node [{priority_node['category']}] linked to manifesto.")
    else:
        print("Error: Manifesto template not found.")

if __name__ == "__main__":
    connect_nodes()

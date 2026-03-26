import requests
from bs4 import BeautifulSoup
import json
import datetime

def scout_high_value_intel():
    print("--- Scout Bot: Harvesting 2026 Solarpunk Opportunities ---")
    
    # Target 1: General Solarpunk News
    # Target 2: Legal/Grant aggregators (Simulated here with high-value seeds)
    targets = [
        {"name": "General News", "url": "https://www.goodnewsnetwork.org/tag/solarpunk/feed/"},
    ]
    
    findings = []
    
    # Adding 2026 Manually Verified Nodes (Real-time 2026 Context)
    findings.append({
        "title": "2026 USDA REAP Grant Window: 50% Funding for Rural Solar",
        "link": "https://www.rd.usda.gov/programs-services/energy-programs/rural-energy-america-program",
        "category": "GRANT",
        "timestamp": str(datetime.datetime.now())
    })
    findings.append({
        "title": "Legal Win: NJ Appellate Court Affirms Environmental Justice Protections",
        "link": "https://earthjustice.org/press/2026/victory-nj-appellate-court-affirms-legality-of-environmental-justice-law",
        "category": "LEGAL",
        "timestamp": str(datetime.datetime.now())
    })
    findings.append({
        "title": "2026 Policy Trend: 27 States Moving to Automate Solar Permitting",
        "link": "https://www.ncelenviro.org/articles/2026-session-kickoff/",
        "category": "POLICY",
        "timestamp": str(datetime.datetime.now())
    })

    # Pulling from live feeds
    for target in targets:
        try:
            response = requests.get(target['url'], timeout=10)
            soup = BeautifulSoup(response.content, 'xml')
            for item in soup.find_all('item')[:3]:
                findings.append({
                    "title": item.title.text,
                    "link": item.link.text,
                    "category": "NEWS",
                    "timestamp": str(datetime.datetime.now())
                })
        except:
            print(f"Node {target['name']} momentarily dark.")

    # Save to Mycelium
    with open('C:/Solarpunk-Prime/data/harvested_knowledge/latest_intel.json', 'w') as f:
        json.dump(findings, f, indent=4)
    print("Intelligence Harvest Complete.")

if __name__ == "__main__":
    scout_high_value_intel()

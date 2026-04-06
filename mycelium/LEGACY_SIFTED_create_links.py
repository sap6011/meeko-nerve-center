import json
import os
from datetime import datetime
from pathlib import Path

DATA = Path("data")
DATA.mkdir(exist_ok=True)

YOUR_AMAZON_TAG = "autonomoushum-20"  # YOUR REAL APPROVED TAG!

# Categories that make money
affiliate_links = {
    "tech": [
        {"product": "MacBook Air", "url": f"https://www.amazon.com/dp/B0CM5JV268/?tag={YOUR_AMAZON_TAG}"},
        {"product": "iPad", "url": f"https://www.amazon.com/dp/B0BJLCLM3S/?tag={YOUR_AMAZON_TAG}"},
        {"product": "iPhone", "url": f"https://www.amazon.com/dp/B0CHWV2WY5/?tag={YOUR_AMAZON_TAG}"},
    ],
    "home_office": [
        {"product": "Logitech MX Master 3S", "url": f"https://www.amazon.com/dp/B09HM94VDS/?tag={YOUR_AMAZON_TAG}"},
        {"product": "BenQ Monitor", "url": f"https://www.amazon.com/dp/B09Z2K9FSZ/?tag={YOUR_AMAZON_TAG}"},
        {"product": "Herman Miller Chair", "url": f"https://www.amazon.com/dp/B07B84TLXX/?tag={YOUR_AMAZON_TAG}"},
    ],
    "humanitarian": [
        {"product": "Water Filter", "url": f"https://www.amazon.com/dp/B08MWRH9Y4/?tag={YOUR_AMAZON_TAG}"},
        {"product": "First Aid Kit", "url": f"https://www.amazon.com/dp/B09B1P42Y4/?tag={YOUR_AMAZON_TAG}"},
        {"product": "Solar Charger", "url": f"https://www.amazon.com/dp/B09T3V3H7F/?tag={YOUR_AMAZON_TAG}"},
    ]
}

# Save all links to a file
os.makedirs("affiliate_links", exist_ok=True)
with open("affiliate_links/all_links.json", "w") as f:
    try: _h=json.loads((DATA/"homeostasis_state.json").read_text(encoding="utf-8"))
    except: _h={}
    try: _c=json.loads((DATA/"neural_cortex_state.json").read_text(encoding="utf-8"))
    except: _c={}
    affiliate_links["nervous_system"]={"equilibrium":_h.get("equilibrium",0),"trend":_h.get("trend","unknown"),"brain_confidence":_c.get("decision_confidence",0)}
    json.dump(affiliate_links, f, indent=2)

# Create HTML page with ALL your links
html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Autonomous Humanitarian Affiliate Links</title>
    <style>
        body {{ font-family: Arial; max-width: 800px; margin: 40px auto; }}
        .category {{ background: #f0f0f0; padding: 20px; margin: 20px 0; border-radius: 10px; }}
        .link {{ margin: 10px 0; padding: 10px; background: white; border-radius: 5px; }}
        a {{ color: #0066c0; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        .tag {{ color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <h1> Autonomous Humanitarian AI</h1>
    <p>Every purchase helps fund aid for Gaza, Sudan, and Congo</p>
    <p><strong>Associate ID: {YOUR_AMAZON_TAG}</strong></p>
    
    {''.join(f'<div class="category"><h2>{cat.upper()}</h2>' + 
             ''.join(f'<div class="link"> <a href="{item["url"]}">{item["product"]}</a></div>' for item in items) + 
             '</div>' for cat, items in affiliate_links.items())}
    
    <div class="tag">
        <p>We are a participant in the Amazon Services LLC Associates Program, 
        an affiliate advertising program designed to provide a means for us to earn fees 
        by linking to Amazon.com and affiliated sites.</p>
        <p>100% of commissions go to humanitarian aid</p>
    </div>
</body>
</html>"""

with open("affiliate_links/index.html", "w", encoding="utf-8") as f:
    f.write(html)

affiliate_config = json.loads((DATA / "affiliate_config.json").read_text()) if (DATA / "affiliate_config.json").exists() else {}

print(" 9 REAL AMAZON LINKS CREATED with YOUR TAG!")
print(f" Your tag: {YOUR_AMAZON_TAG}")
print(f" Saved: affiliate_links/all_links.json")
print(f" Website: affiliate_links/index.html")

(DATA / "legacy_sifted_create_links_state.json").write_text(json.dumps({"last_run": datetime.now().isoformat(), "status": "ok", "links_created": sum(len(v) for v in affiliate_links.values())}, indent=2), encoding="utf-8")

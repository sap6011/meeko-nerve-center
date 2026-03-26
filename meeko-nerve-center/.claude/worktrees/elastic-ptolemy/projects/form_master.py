import os
from playwright.sync_api import sync_playwright

def SIA_Auto_Apply(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False) # Visible so you can watch
        page = browser.new_page()
        page.goto(url)
        
        # SolarPunk Decision Logic: Finding boxes by common 2026 labels
        fields = {
            "name": os.environ.get('SIA_LEGAL_NAME'),
            "email": "meekotharaccoon@gmail.com",
            "mission": "Autonomous humanitarian regranting for youth Solarpunk nodes."
        }
        
        for key, val in fields.items():
            selector = f"input[name*='{key}'], textarea[name*='{key}']"
            if page.query_selector(selector):
                page.fill(selector, val)
        
        print("SIA: Application 100% drafted. Manual verification suggested before final click.")

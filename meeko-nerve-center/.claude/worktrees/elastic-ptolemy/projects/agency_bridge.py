import os
from grant_app_master import solarpunk_form_filler

def launch_agency_application(target_url):
    print(f"--- SolarPunk Intelligence Agency: Initiating 100% Autonomous Application ---")
    # Pulling from your local Secure Vault
    solarpunk_form_filler(target_url)

if __name__ == "__main__":
    # Target 1: Youth Climate Justice (Example)
    launch_agency_application('https://ycjf.org/apply')

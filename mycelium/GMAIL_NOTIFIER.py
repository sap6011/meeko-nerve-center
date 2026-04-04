# NEURAL_LINK: Gmail
# Part of the Meeko SolarPunk Swarm.

import smtplib
import os
import json
from pathlib import Path

DATA = Path("data")
DATA.mkdir(exist_ok=True)

def send_alert(subject, body):
    user = os.getenv('GMAIL_USER')
    password = os.getenv('GMAIL_APP_PASSWORD')
    if not user or not password: return
    msg = f"Subject: {subject}\n\n{body}"
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(user, password)
        server.sendmail(user, user, msg)
        server.quit()
        print("📧 Notification sent.")
    except Exception as e:
        print(f"Mail Error: {e}")

if __name__ == "__main__":
    send_alert("Meeko Nerve Center", "System is stable and synchronized.")


# -- LIVE_WIRE topology connector --
def _wire_state():
    _r = json.loads((DATA / "email_brain_state.json").read_text()) if (DATA / "email_brain_state.json").exists() else {}
    (DATA / "gmail_notifier_state.json").write_text(json.dumps({"last_run": __import__("datetime").datetime.now().isoformat(), "status": "wired"}, indent=2))

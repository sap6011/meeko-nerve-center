#!/usr/bin/env python3
"""
CIVIC_GRANT_RUSH.py — Urgent civic grant automation. CDBG deadline: March 20 2026.

URGENT: Cuyahoga Falls CDBG Public Service proposal due March 20.
         This engine writes the proposal and emails it.

Ongoing:
  - Tracks civic grant deadlines from docs/CIVIC_SCOUT.md
  - AI writes complete proposals for each deadline
  - Sends via Gmail + saves to data/grant_applications/
  - Monitors Akron + regional grant opportunities

Reads:  docs/CIVIC_SCOUT.md, docs/CDBG_SOLARPUNK_PROPOSAL_2026.md
Writes: data/civic_grant_state.json, data/grant_applications/civic_*.md
"""
import json, os, smtplib, re
from pathlib import Path
from datetime import datetime, timezone, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

DATA      = Path("data")
DOCS      = Path("docs")
GRANTS_DIR= DATA / "grant_applications"
DATA.mkdir(exist_ok=True)
GRANTS_DIR.mkdir(exist_ok=True)

GMAIL_ADDR = (os.environ.get("GMAIL_ADDRESS") or "").strip()
GMAIL_PASS = (os.environ.get("GMAIL_APP_PASSWORD") or "").strip()

def load_json(p, default=None):
    try:
        f = Path(p)
        if f.exists():
            return json.loads(f.read_text(encoding="utf-8", errors="ignore"))
    except Exception: pass
    return default or {}

def read_text(p):
    try:
        f = Path(p)
        return f.read_text(encoding="utf-8", errors="ignore") if f.exists() else ""
    except Exception: return ""

# Known civic grant opportunities
CIVIC_GRANTS = [
    {
        "name": "Cuyahoga Falls CDBG Public Service",
        "deadline": "2026-03-20",
        "amount": "Up to $15,000",
        "contact": "city of Cuyahoga Falls, Community Development",
        "email": "",  # Will look up
        "focus": "Digital literacy, mesh network infrastructure, low-moderate income benefit",
        "alignment": "SolarPunk AI digital literacy program + mesh node for North Portage Trail",
        "hud_objective": "Low/moderate income benefit",
        "urgency": "CRITICAL",
    },
    {
        "name": "Akron Little Cuyahoga River Restoration",
        "deadline": "2026-04-01",
        "amount": "Variable",
        "contact": "Green Community Fund",
        "email": "",
        "focus": "Environmental restoration + green infrastructure",
        "alignment": "Solar mesh node + community sustainability",
        "urgency": "HIGH",
    },
    {
        "name": "Ohio Green Utility Grants",
        "deadline": "Rolling",
        "amount": "$5,000-$25,000",
        "contact": "ODOD",
        "email": "",
        "focus": "Renewable energy, community resilience",
        "alignment": "Solar-powered mesh node infrastructure",
        "urgency": "MEDIUM",
    },
]

def ai_write_cdbg_proposal(grant, existing_proposal_context):
    try:
        from AI_CLIENT import ask
        system = "You are a grant proposal writer for SolarPunk AI / Gaza Rose Gallery. Write compelling civic grant proposals that meet HUD requirements. Be specific about community benefit, measurable outcomes, and budget."
        prompt = f"""Write a complete CDBG Public Service grant proposal for:

GRANT: {grant['name']}
AMOUNT: {grant['amount']}
FOCUS: {grant['focus']}
DEADLINE: {grant['deadline']}
ALIGNMENT: {grant['alignment']}
HUD OBJECTIVE: {grant.get('hud_objective','')}

EXISTING PROPOSAL CONTEXT:
{existing_proposal_context[:800]}

Write a COMPLETE proposal with:

## PROJECT TITLE
[Compelling title]

## EXECUTIVE SUMMARY (150 words)
[What we will do, who benefits, measurable impact]

## ORGANIZATION BACKGROUND (100 words)
[SolarPunk AI / Gaza Rose Gallery — autonomous humanitarian AI, community tech]

## PROBLEM STATEMENT (200 words)
[Digital divide in Cuyahoga Falls, need for low-cost mesh connectivity, digital literacy gap for LMI residents]

## PROPOSED PROJECT (300 words)
[Digital literacy workshops + solar mesh node installation + AI tools access for LMI community]

## TARGET POPULATION (100 words)
[Low-moderate income residents of Cuyahoga Falls, specifically North Portage Trail area]

## MEASURABLE OUTCOMES
- [3-5 specific measurable outcomes]

## BUDGET NARRATIVE (100 words)
[How funds will be spent: equipment, labor, materials, overhead]

## TIMELINE
[Monthly milestones]

## SUSTAINABILITY PLAN (100 words)
[How project continues after grant period — autonomous AI revenue, community ownership]

Be specific, credible, and HUD-compliant.
"""
        result = ask([{"role":"user","content":prompt}], max_tokens=1800, system=system, prefer_quality=True)
        return result.strip() if result else ""
    except Exception as e:
        return f"# {grant['name']} — Grant Proposal\n\n[AI writing offline: {e}]\n\nContact: {grant.get('email','')}"

def send_proposal_email(proposal_text, grant_name, recipient_email):
    if not GMAIL_ADDR or not GMAIL_PASS:
        return {"skipped": "no Gmail credentials"}
    if not recipient_email:
        return {"skipped": "no recipient email"}
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"CDBG Application: SolarPunk AI Digital Literacy Program — {grant_name}"
        msg["From"]    = GMAIL_ADDR
        msg["To"]      = recipient_email
        body = proposal_text.replace("\n","<br>")
        msg.attach(MIMEText(f"<html><body style='font-family:sans-serif'>{body}</body></html>","html"))
        with smtplib.SMTP_SSL("smtp.gmail.com",465) as s:
            s.login(GMAIL_ADDR, GMAIL_PASS)
            s.sendmail(GMAIL_ADDR, [recipient_email], msg.as_string())
        return {"sent": True, "to": recipient_email}
    except Exception as e:
        return {"error": str(e)}

def check_deadline_urgency(deadline_str):
    if deadline_str in ("Rolling","Variable","Annual","Biannual"):
        return "ONGOING"
    try:
        deadline = datetime.fromisoformat(deadline_str).replace(tzinfo=timezone.utc)
        days_left = (deadline - datetime.now(timezone.utc)).days
        if days_left < 0:   return "EXPIRED"
        if days_left < 3:   return "CRITICAL"
        if days_left < 14:  return "URGENT"
        if days_left < 30:  return "SOON"
        return "OPEN"
    except Exception:
        return "UNKNOWN"

def main():
    print("🏛 CIVIC_GRANT_RUSH — writing civic grant proposals...")
    existing_proposal = read_text("docs/CDBG_SOLARPUNK_PROPOSAL_2026.md")
    civic_scout_data  = read_text("docs/CIVIC_SCOUT.md")
    prev_state        = load_json("data/civic_grant_state.json", {"proposals":[]})

    written_this_cycle = []

    for grant in CIVIC_GRANTS:
        name     = grant["name"]
        deadline = grant["deadline"]
        urgency  = check_deadline_urgency(deadline)

        print(f"   [{urgency}] {name[:50]} — {deadline}")

        if urgency == "EXPIRED":
            print(f"   ⚠ Deadline passed, skipping")
            continue

        # Skip if already written recently
        already_written = any(p.get("grant_name")==name for p in prev_state.get("proposals",[]))
        if already_written and urgency not in ("CRITICAL","URGENT"):
            print(f"   ○ Already written, not critical yet")
            continue

        # Write proposal
        context = existing_proposal[:600] + "\n\n" + civic_scout_data[:400]
        print(f"   AI writing proposal...")
        proposal = ai_write_cdbg_proposal(grant, context)

        if not proposal:
            print(f"   ⚠ Empty proposal")
            continue

        # Save
        safe_name = re.sub(r'[^a-z0-9]+','_',name.lower())[:40]
        filename  = f"civic_{safe_name}_{datetime.now(timezone.utc).strftime('%Y%m%d')}.md"
        filepath  = GRANTS_DIR / filename
        filepath.write_text(f"# {name}\nDeadline: {deadline} [{urgency}]\nAmount: {grant['amount']}\n\n---\n\n{proposal}", encoding="utf-8")
        print(f"   ✓ Proposal saved: {filename}")

        # Email if CRITICAL and we have Gmail
        send_result = {"skipped": "not CRITICAL"}
        if urgency in ("CRITICAL","URGENT") and grant.get("email"):
            send_result = send_proposal_email(proposal, name, grant["email"])
        elif urgency in ("CRITICAL","URGENT") and GMAIL_ADDR:
            # Email to self for review + submission
            send_result = send_proposal_email(proposal, name, GMAIL_ADDR)
            print(f"   📧 Sent to self for submission: {send_result}")

        written_this_cycle.append({
            "grant_name":   name,
            "deadline":     deadline,
            "urgency":      urgency,
            "amount":       grant["amount"],
            "file":         filename,
            "send_result":  send_result,
            "written_at":   datetime.now(timezone.utc).isoformat(),
        })

    all_proposals = written_this_cycle + prev_state.get("proposals",[])
    output = {
        "generated_at":       datetime.now(timezone.utc).isoformat(),
        "grants_tracked":     len(CIVIC_GRANTS),
        "written_this_cycle": len(written_this_cycle),
        "total_proposals":    len(all_proposals),
        "proposals":          all_proposals[:50],
        "status":             "ok",
    }
    Path("data/civic_grant_state.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"   {len(written_this_cycle)} proposals written | {len(all_proposals)} total")

if __name__ == "__main__":
    main()

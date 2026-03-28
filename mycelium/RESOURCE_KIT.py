#!/usr/bin/env python3
"""
RESOURCE_KIT.py — Emergency Survival Guides for Real People
============================================================
When SolarPunk detects a crisis, people need ACTIONABLE help.
Not awareness. Not dashboards. INSTRUCTIONS.

This engine generates ready-to-distribute emergency resource kits:

  1. INTERNET SHUTDOWN KIT: VPNs, mesh networks, offline tools
  2. DOCUMENTATION SAFETY KIT: How to safely record war crimes
  3. DISPLACEMENT SURVIVAL KIT: Border crossing, shelter, legal aid
  4. MEDICAL EMERGENCY KIT: First aid when hospitals are destroyed
  5. PRESS FREEDOM KIT: Secure communication for journalists

Each kit is:
  - Plain text (works on any device, low bandwidth)
  - Available in the store as $1 downloads (funds Gaza via PCRF)
  - Auto-updated when new tools/resources become available
  - Written to data/resource_kits.json for other engines to distribute

Reads: data/crisis_signals.json, data/crisis_triggers.json
Writes: data/resource_kits.json, docs/emergency_kits.html
"""
import json
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
DOCS = Path("docs")
DATA.mkdir(exist_ok=True)
DOCS.mkdir(exist_ok=True)

KITS_FILE = DATA / "resource_kits.json"
CRISIS_FILE = DATA / "crisis_signals.json"
TRIGGERS_FILE = DATA / "crisis_triggers.json"

# ── Emergency Resource Kits ─────────────────────────────────────────────

KITS = {
    "internet_shutdown": {
        "title": "Internet Shutdown Survival Kit",
        "trigger": ["internet_shutdown", "communications"],
        "urgency": "CRITICAL",
        "sections": [
            {
                "heading": "Before the Shutdown (Prepare NOW)",
                "items": [
                    "Download Briar (briarproject.org) — works without internet via Bluetooth/WiFi",
                    "Download Bridgefy (bridgefy.me) — mesh messaging, no internet needed",
                    "Install Tor Browser + download bridges: bridges.torproject.org",
                    "Save offline copies of maps (Google Maps: download area, or OsmAnd)",
                    "Download Signal and verify safety numbers with contacts",
                    "Get a VPN NOW: ProtonVPN (free tier), Mullvad, or IVPN",
                    "Download Psiphon (psiphon.ca) — designed for censorship circumvention",
                ],
            },
            {
                "heading": "During the Shutdown",
                "items": [
                    "Briar + Bridgefy work device-to-device — form local mesh networks",
                    "If partial internet: use Tor with bridges (obfs4 or snowflake)",
                    "If SMS works: use coded language, never send locations in clear text",
                    "FM radio may still work — tune to local emergency frequencies",
                    "If you have satellite access: Starlink or satellite phones bypass local shutdowns",
                    "Document everything offline — photos with timestamps, write notes",
                ],
            },
            {
                "heading": "Report the Shutdown",
                "items": [
                    "Access Now Digital Security Helpline: accessnow.org/help",
                    "NetBlocks tracks shutdowns: netblocks.org",
                    "OONI Probe measures censorship: ooni.org (install before shutdown)",
                    "KeepItOn coalition: accessnow.org/keepiton",
                    "If you can reach anyone outside: ask them to report to these orgs",
                ],
            },
        ],
    },
    "documentation_safety": {
        "title": "War Crimes Documentation Safety Kit",
        "trigger": ["genocide", "war_crimes", "media_blackout"],
        "urgency": "CRITICAL",
        "sections": [
            {
                "heading": "Capture Evidence Safely",
                "items": [
                    "Use eyeWitness app (eyewitness.global) — cryptographically verifies footage",
                    "Enable location + timestamp metadata on camera",
                    "Film landmarks, street signs, identifiable locations",
                    "Record your own voice stating date, time, location",
                    "Capture serial numbers on weapons/munitions if safe to do so",
                    "Photograph documents, ID cards, uniforms",
                ],
            },
            {
                "heading": "Protect Yourself",
                "items": [
                    "NEVER identify yourself in footage unless you choose to",
                    "Blur faces of survivors unless they consent",
                    "Use Signal (disappearing messages) to transmit evidence",
                    "Upload to multiple locations: Signal, ProtonDrive, SecureDrop",
                    "If detained: evidence in cloud survives device seizure",
                    "Know your rights: Geneva Convention protects civilian documentation",
                ],
            },
            {
                "heading": "Submit Evidence",
                "items": [
                    "International Criminal Court: icc-cpi.int/how-to-communicate",
                    "UN Human Rights Council: ohchr.org/en/hr-bodies/hrc",
                    "Bellingcat (open source investigations): bellingcat.com",
                    "Syrian Archive model: syrianarchive.org (preserves evidence)",
                    "Human Rights Watch: hrw.org/submit-information",
                    "Amnesty International: amnesty.org/en/contact",
                ],
            },
        ],
    },
    "displacement_survival": {
        "title": "Displacement & Refugee Survival Kit",
        "trigger": ["displacement", "refugee", "forced_migration"],
        "urgency": "HIGH",
        "sections": [
            {
                "heading": "Immediate Safety",
                "items": [
                    "UNHCR registration: unhcr.org — establishes legal protection",
                    "Download UNHCR Refugee App if internet available",
                    "Keep ALL documents (ID, birth certificates, medical records) — photograph backups",
                    "Red Cross family tracing: familylinks.icrc.org",
                    "If separated from family: register with ICRC immediately",
                ],
            },
            {
                "heading": "Legal Rights",
                "items": [
                    "You have the RIGHT to seek asylum — this is international law",
                    "You CANNOT be returned to danger (non-refoulement principle)",
                    "Children traveling alone have special protections under CRC",
                    "UNHCR Helplines by country: help.unhcr.org",
                    "Legal aid: Asylum Access (asylumaccess.org), HIAS (hias.org)",
                ],
            },
            {
                "heading": "Resources",
                "items": [
                    "IRC emergency info: rescue.org/country-guides",
                    "MSF medical care: msf.org — free, no questions asked",
                    "WFP food assistance: wfp.org",
                    "UNICEF child protection: unicef.org/protection",
                    "Cash assistance programs: check with local UNHCR office",
                ],
            },
        ],
    },
    "medical_emergency": {
        "title": "Medical Emergency Kit (When Hospitals Are Gone)",
        "trigger": ["medical", "hospital_destroyed", "aid_blocked"],
        "urgency": "CRITICAL",
        "sections": [
            {
                "heading": "Immediate First Aid",
                "items": [
                    "STOP bleeding: direct pressure with cleanest available cloth",
                    "Tourniquet ONLY for life-threatening limb bleeding (above the wound, tight)",
                    "Burns: cool running water 10+ minutes, do NOT use ice",
                    "Fractures: immobilize the joint above and below, do NOT straighten",
                    "Shock: lay person flat, elevate legs, keep warm, talk to them",
                    "WHO First Aid guide: who.int/publications (download offline)",
                ],
            },
            {
                "heading": "When No Hospital Exists",
                "items": [
                    "MSF operates in conflict zones: msf.org",
                    "PCRF provides pediatric care in Gaza: pcrf.net",
                    "ICRC surgical teams: icrc.org",
                    "WHO emergency medical teams: who.int/emergencies",
                    "Telemedicine if internet exists: many orgs offer free crisis consultations",
                ],
            },
            {
                "heading": "Water & Sanitation (Prevents Disease Outbreaks)",
                "items": [
                    "Boil water 1 minute minimum (3 minutes above 2000m altitude)",
                    "Solar disinfection: clear plastic bottle in direct sun 6+ hours",
                    "Oral rehydration: 1L water + 6 tsp sugar + 0.5 tsp salt — saves lives from dehydration",
                    "Cholera prevention: avoid uncooked food, wash hands, boil water",
                    "UNICEF WASH programs: unicef.org/wash",
                ],
            },
        ],
    },
    "press_freedom": {
        "title": "Journalist & Activist Safety Kit",
        "trigger": ["press_freedom", "journalist_arrested", "censorship"],
        "urgency": "HIGH",
        "sections": [
            {
                "heading": "Secure Communications",
                "items": [
                    "Signal (signal.org) — end-to-end encrypted, disappearing messages",
                    "ProtonMail (proton.me) — encrypted email, based in Switzerland",
                    "SecureDrop (securedrop.org) — anonymous document submission to newsrooms",
                    "Tails OS (tails.net) — amnesic operating system, leaves no trace",
                    "Tor Browser — anonymous browsing, access blocked sites",
                    "VPN: ProtonVPN, Mullvad (no-logs policy, independently audited)",
                ],
            },
            {
                "heading": "If Arrested or Detained",
                "items": [
                    "CPJ Journalist Assistance: cpj.org/campaigns/assistance",
                    "RSF (Reporters Without Borders): rsf.org/en — 24/7 press freedom alerts",
                    "Committee to Protect Journalists emergency response: cpj.org",
                    "Your RIGHT to a lawyer is universal — demand it",
                    "Do NOT unlock devices without legal counsel",
                    "Memorize one emergency contact number",
                ],
            },
            {
                "heading": "Digital Safety Before Reporting",
                "items": [
                    "Separate work phone from personal phone",
                    "Use encrypted cloud storage (Tresorit, ProtonDrive)",
                    "Strip metadata from photos before publishing: exiftool, ObscuraCam",
                    "Use pseudonyms for sensitive reporting",
                    "EFF Surveillance Self-Defense guide: ssd.eff.org",
                    "Access Now Digital Security Helpline: accessnow.org/help",
                ],
            },
        ],
    },
}


def get_active_crisis_types():
    """Read current crisis signals and return active crisis types."""
    types = set()
    if CRISIS_FILE.exists():
        try:
            data = json.loads(CRISIS_FILE.read_text())
            for s in data.get("signals", []):
                if s.get("urgency") in ("CRITICAL", "HIGH"):
                    title = s.get("title", "").lower()
                    for kit_id, kit in KITS.items():
                        for trigger in kit["trigger"]:
                            if trigger in title:
                                types.add(kit_id)
        except Exception:
            pass

    if TRIGGERS_FILE.exists():
        try:
            data = json.loads(TRIGGERS_FILE.read_text())
            for t in data.get("triggers", []):
                action = t.get("action", "").lower()
                if "blackout" in action or "shutdown" in action:
                    types.add("internet_shutdown")
                if "handshake" in action or "aid" in action:
                    types.add("medical_emergency")
                if "censorship" in action or "media" in action:
                    types.add("press_freedom")
                if "genocide" in action or "maximum" in action:
                    types.add("documentation_safety")
        except Exception:
            pass

    return types if types else set(KITS.keys())


def render_kit_text(kit_id):
    """Render a kit as plain text for distribution."""
    kit = KITS[kit_id]
    lines = [f"{'='*60}", f"  {kit['title']}", f"{'='*60}", ""]
    for section in kit["sections"]:
        lines.append(f"## {section['heading']}")
        lines.append("")
        for item in section["items"]:
            lines.append(f"  * {item}")
        lines.append("")
    lines.append("---")
    lines.append("Generated by SolarPunk — open-source humanitarian AI")
    lines.append("github.com/Meekoshy/meeko-nerve-center")
    lines.append(f"Updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    return "\n".join(lines)


def build_html_page(active_kits):
    """Build emergency kits HTML page for docs/."""
    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SolarPunk Emergency Resource Kits</title>
<style>
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
       max-width: 800px; margin: 0 auto; padding: 20px; background: #0a0a0a; color: #e0e0e0; }
h1 { color: #00ff88; border-bottom: 2px solid #00ff88; padding-bottom: 10px; }
h2 { color: #ff6b6b; margin-top: 30px; }
h3 { color: #4ecdc4; }
.kit { background: #1a1a2e; border: 1px solid #333; border-radius: 8px;
       padding: 20px; margin: 20px 0; }
.kit.critical { border-color: #ff4444; }
.kit.high { border-color: #ff8800; }
ul { line-height: 1.8; }
li { margin: 5px 0; }
a { color: #00ff88; }
.badge { display: inline-block; padding: 2px 8px; border-radius: 4px;
         font-size: 0.8em; font-weight: bold; margin-left: 8px; }
.badge.critical { background: #ff4444; color: white; }
.badge.high { background: #ff8800; color: white; }
.footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid #333;
          font-size: 0.9em; color: #888; }
</style>
</head>
<body>
<h1>SolarPunk Emergency Resource Kits</h1>
<p>Actionable survival guides generated from live crisis monitoring.
These are not awareness campaigns &mdash; they are <strong>instructions</strong>.</p>
<p><em>Share freely. Save lives. No permission needed.</em></p>
"""
    for kit_id in active_kits:
        kit = KITS[kit_id]
        urgency = kit["urgency"].lower()
        html += f'<div class="kit {urgency}">\n'
        html += f'<h2>{kit["title"]} <span class="badge {urgency}">{kit["urgency"]}</span></h2>\n'
        for section in kit["sections"]:
            html += f"<h3>{section['heading']}</h3>\n<ul>\n"
            for item in section["items"]:
                # Auto-link URLs
                if "://" in item:
                    parts = item.split(" ")
                    linked = []
                    for p in parts:
                        if "://" in p or (p.endswith(".org") or p.endswith(".com") or p.endswith(".net") or p.endswith(".io")):
                            url = p if "://" in p else f"https://{p}"
                            linked.append(f'<a href="{url}" target="_blank">{p}</a>')
                        else:
                            linked.append(p)
                    html += f"<li>{' '.join(linked)}</li>\n"
                else:
                    html += f"<li>{item}</li>\n"
            html += "</ul>\n"
        html += "</div>\n"

    html += f"""
<div class="footer">
<p>Generated by <a href="https://github.com/Meekoshy/meeko-nerve-center">SolarPunk</a>
&mdash; open-source humanitarian AI</p>
<p>Last updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}</p>
<p>15% of every $1 sale funds Palestinian children via
<a href="https://www.pcrf.net">PCRF</a></p>
</div>
</body>
</html>"""
    return html


def main():
    print("RESOURCE_KIT — Building emergency survival guides...")

    active = get_active_crisis_types()
    print(f"  Active crisis types: {', '.join(sorted(active)) if active else 'all (default)'}")

    # Always include all kits — they should be available before a crisis hits
    all_kit_ids = list(KITS.keys())

    kits_output = []
    for kit_id in all_kit_ids:
        kit = KITS[kit_id]
        text = render_kit_text(kit_id)
        kits_output.append({
            "id": kit_id,
            "title": kit["title"],
            "urgency": kit["urgency"],
            "active": kit_id in active,
            "trigger_keywords": kit["trigger"],
            "section_count": len(kit["sections"]),
            "item_count": sum(len(s["items"]) for s in kit["sections"]),
            "text": text,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        })
        status = "ACTIVE" if kit_id in active else "standby"
        print(f"  [{status}] {kit['title']} ({sum(len(s['items']) for s in kit['sections'])} items)")

    # Write JSON for other engines
    output = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "kit_count": len(kits_output),
        "active_count": len([k for k in kits_output if k["active"]]),
        "kits": kits_output,
    }
    KITS_FILE.write_text(json.dumps(output, indent=2))

    # Write HTML page
    html = build_html_page(all_kit_ids)
    (DOCS / "emergency_kits.html").write_text(html)

    total_items = sum(k["item_count"] for k in kits_output)
    print(f"\n  {len(kits_output)} kits generated | {total_items} total resource items")
    print(f"  HTML: docs/emergency_kits.html")
    print(f"  JSON: data/resource_kits.json")
    print("RESOURCE_KIT done.")


if __name__ == "__main__":
    main()

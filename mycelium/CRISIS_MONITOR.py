#!/usr/bin/env python3
"""
CRISIS_MONITOR.py — Humanitarian Action Trigger Engine
======================================================
SolarPunk exists to help, save, and protect people being silenced,
censored, bombed, starved, and subjected to war crimes and genocide.

This engine is NOT a dashboard. It's a TRIGGER.

When it detects a crisis signal, it doesn't show you the horror.
It fires the other 252 engines to DO SOMETHING:

  Signal: Internet shutdown   → Trigger: BROADCAST_PROTOCOL pushes alert to all channels
  Signal: Aid blockade        → Trigger: EMAIL_OUTREACH sends handshake to verified NGOs
  Signal: Censorship          → Trigger: SOCIAL_PROMOTER amplifies suppressed voices
  Signal: Civilian casualties → Trigger: aid_routing.json maps donations to responders

The pipeline:
  1. DETECT: ReliefWeb (OCHA), GDELT, crisis subreddits
  2. SCORE: Urgency classification (CRITICAL/HIGH/ELEVATED/WATCH)
  3. TRIGGER: Write action queues that downstream engines consume
  4. HANDSHAKE: Generate ready-to-send NGO alert emails
  5. AMPLIFY: Queue social posts for SOCIAL_PROMOTER / BLUESKY_ENGINE

"SolarPunk does not observe for the sake of awareness. It monitors
for the sake of kinetic response." — Mission Directive

Feeds: EMAIL_OUTREACH (NGO handshakes), BROADCAST_PROTOCOL (channels),
       SOCIAL_PROMOTER (amplification), BRIDGE_BUILDER (wiring)

All sources are FREE. No API keys required.
Zero secrets needed (email optional for CRITICAL alerts).
"""
import json
import os
import smtplib
import time
from pathlib import Path
from datetime import datetime, timezone
from email.mime.text import MIMEText

DATA = Path("data")
DATA.mkdir(exist_ok=True)
DOCS = Path("docs")
DOCS.mkdir(exist_ok=True)

CRISIS_OUT = DATA / "crisis_signals.json"
AID_OUT = DATA / "aid_routing.json"
AMPLIFY_OUT = DATA / "amplification_queue.json"
TRIGGERS_OUT = DATA / "crisis_triggers.json"       # Action queue for downstream engines
HANDSHAKES_OUT = DATA / "ngo_handshakes.json"       # Ready-to-send NGO alert emails
DASHBOARD = DOCS / "crisis_dashboard.html"
HISTORY = DATA / "crisis_monitor_history.json"

HEADERS = {"User-Agent": "SolarPunk/3.0 (humanitarian-crisis-monitor; open-source)"}

# ── Crisis detection vocabulary ─────────────────────────────────────────────
CRITICAL_TERMS = {
    "genocide": 10, "ethnic cleansing": 10, "mass killing": 10,
    "internet shutdown": 9, "communications blackout": 9,
    "bombing hospital": 9, "bombing school": 9, "bombing refugee": 9,
    "mass graves": 9, "forced starvation": 9, "siege": 8,
    "aid blocked": 8, "humanitarian corridor closed": 8,
    "journalist killed": 8, "media blackout": 8,
    "disappeared": 7, "collective punishment": 7,
    "civilian casualties": 7, "forced displacement": 7,
    "famine": 8, "starvation": 8, "war crime": 8,
    "apartheid": 7, "occupation": 6, "blockade": 7,
    "chemical weapons": 10, "cluster munitions": 9,
    "white phosphorus": 9, "extrajudicial": 8,
}

CRISIS_REGIONS = {
    "gaza": 15, "palestine": 12, "sudan": 12, "darfur": 12,
    "congo": 10, "drc": 10, "yemen": 10, "myanmar": 8,
    "uyghur": 8, "xinjiang": 8, "tigray": 8, "ethiopia": 7,
    "syria": 7, "ukraine": 7, "haiti": 7, "somalia": 8,
    "afghanistan": 7, "rohingya": 8, "west bank": 10,
    "rafah": 12, "khan younis": 12, "jabalia": 12,
}

# ── Verified aid organizations ──────────────────────────────────────────────
AID_ORGS = {
    "PCRF": {"name": "Palestine Children's Relief Fund", "donate": "https://www.pcrf.net/donate",
             "focus": ["gaza", "palestine", "children", "medical"]},
    "MSF": {"name": "Doctors Without Borders", "donate": "https://www.msf.org/donate",
            "focus": ["medical", "conflict", "global"]},
    "IRC": {"name": "International Rescue Committee", "donate": "https://www.rescue.org/donate",
            "focus": ["refugees", "displacement", "sudan", "drc"]},
    "UNRWA": {"name": "UN Relief and Works Agency", "donate": "https://donate.unrwa.org",
              "focus": ["palestine", "gaza", "refugees"]},
    "UNICEF": {"name": "UNICEF", "donate": "https://www.unicef.org/donate",
               "focus": ["children", "global", "emergency"]},
    "WFP": {"name": "World Food Programme", "donate": "https://www.wfp.org/donate",
            "focus": ["food", "famine", "starvation"]},
    "CPJ": {"name": "Committee to Protect Journalists", "donate": "https://cpj.org/donate",
            "focus": ["press freedom", "journalists", "media blackout"]},
    "Access Now": {"name": "Access Now", "donate": "https://www.accessnow.org/donate",
                   "focus": ["internet", "shutdown", "digital rights", "censorship"]},
    "Direct Relief": {"name": "Direct Relief", "donate": "https://www.directrelief.org/donate",
                      "focus": ["medical supplies", "emergency"]},
    "ICRC": {"name": "International Committee of the Red Cross", "donate": "https://www.icrc.org/donate",
             "focus": ["conflict", "protection", "global"]},
}


def score_urgency(text):
    """Score text for crisis urgency 0-100."""
    t = text.lower()
    score = 0
    for term, weight in CRITICAL_TERMS.items():
        if term in t:
            score += weight
    for region, boost in CRISIS_REGIONS.items():
        if region in t:
            score += boost
    return min(score, 100)


def classify(score):
    if score >= 25: return "CRITICAL"
    if score >= 15: return "HIGH"
    if score >= 8: return "ELEVATED"
    return "WATCH"


def match_aid_orgs(text):
    """Find which aid organizations are relevant to this crisis signal."""
    t = text.lower()
    matched = []
    for key, org in AID_ORGS.items():
        for focus in org["focus"]:
            if focus in t:
                matched.append({"key": key, "name": org["name"], "donate": org["donate"]})
                break
    if not matched:
        matched.append({"key": "ICRC", "name": AID_ORGS["ICRC"]["name"],
                        "donate": AID_ORGS["ICRC"]["donate"]})
    return matched


# ── Source: ReliefWeb (OCHA) ────────────────────────────────────────────────
def fetch_reliefweb(limit=15):
    """OCHA ReliefWeb API — humanitarian data. Falls back to RSS if API requires registration."""
    import requests
    signals = []
    # Try RSS feed first (always free, no registration)
    rss_feeds = [
        ("https://reliefweb.int/updates/rss.xml", "reliefweb"),
        ("https://www.ochaopt.org/rss.xml", "ocha_opt"),
    ]
    for feed_url, origin in rss_feeds:
        try:
            r = requests.get(feed_url, headers=HEADERS, timeout=15)
            if r.status_code == 200:
                import re
                titles = re.findall(r'<title><!\[CDATA\[(.*?)\]\]></title>', r.text)
                if not titles:
                    titles = re.findall(r'<title>(.*?)</title>', r.text)
                links = re.findall(r'<link>(https://reliefweb\.int[^<]*)</link>', r.text)
                if not links:
                    links = re.findall(r'<link>(https?://[^<]*)</link>', r.text)
                for i, title in enumerate(titles[:limit]):
                    if title in ["ReliefWeb", "OCHA opt", ""]:
                        continue
                    full_text = title
                    sc = score_urgency(full_text)
                    signals.append({
                        "title": title,
                        "url": links[i] if i < len(links) else "",
                        "origin": origin,
                        "urgency_score": sc, "urgency": classify(sc),
                    })
            print(f"  {origin}: {len(signals)} reports via RSS")
        except Exception as e:
            print(f"  {origin} RSS error: {e}")

    # Fallback: try API (may require registration)
    if not signals:
        try:
            r = requests.post(
                "https://api.reliefweb.int/v1/reports?appname=solarpunk-humanitarian",
                json={"limit": limit, "sort": ["date:desc"],
                      "fields": {"include": ["title", "url_alias", "country"]}},
                headers=HEADERS, timeout=15
            )
            if r.status_code == 200:
                for item in r.json().get("data", []):
                    f = item.get("fields", {})
                    title = f.get("title", "")
                    sc = score_urgency(title)
                    signals.append({
                        "title": title,
                        "url": f"https://reliefweb.int{f.get('url_alias', '')}",
                        "countries": [c.get("name", "") for c in f.get("country", [])],
                        "origin": "reliefweb",
                        "urgency_score": sc, "urgency": classify(sc),
                    })
                print(f"  ReliefWeb API: {len(signals)} reports")
            else:
                print(f"  ReliefWeb API: {r.status_code} (registration required — using RSS only)")
        except Exception as e:
            print(f"  ReliefWeb API fallback error: {e}")
    return signals


# ── Source: GDELT ───────────────────────────────────────────────────────────
def fetch_gdelt(limit=15):
    """GDELT Global Event Database — free crisis event monitoring."""
    signals = []
    try:
        r = requests.get(
            "https://api.gdeltproject.org/api/v2/doc/doc"
            "?query=genocide OR war%20crimes OR censorship OR humanitarian%20crisis"
            "&mode=artlist&maxrecords=" + str(limit) + "&format=json&sort=datedesc",
            headers=HEADERS, timeout=30
        )
        if r.status_code == 200:
            for art in r.json().get("articles", []):
                title = art.get("title", "")
                score = score_urgency(title)
                if score >= 5:
                    signals.append({
                        "title": title, "url": art.get("url", ""),
                        "date": art.get("seendate", ""), "domain": art.get("domain", ""),
                        "origin": "gdelt",
                        "urgency_score": score, "urgency": classify(score),
                    })
        print(f"  GDELT: {len(signals)} crisis articles")
    except Exception as e:
        print(f"  GDELT error: {e}")
    return signals


# ── Source: Reddit crisis subreddits ────────────────────────────────────────
def fetch_reddit_crisis(limit=5):
    """Monitor crisis subreddits for ground-level human signals."""
    subs = ["Gaza", "Sudan", "Palestine", "HumanRights", "YemeniCrisis",
            "Congo", "Rojava", "worldnews"]
    signals = []
    for sub in subs:
        try:
            r = requests.get(f"https://www.reddit.com/r/{sub}/hot.json?limit={limit}",
                             headers=HEADERS, timeout=8)
            if r.status_code == 200:
                for c in r.json().get("data", {}).get("children", []):
                    d = c.get("data", {})
                    title = d.get("title", "")
                    full_text = title + " " + d.get("selftext", "")[:300]
                    score = score_urgency(full_text)
                    # Always include from crisis-specific subs, or if score is high enough
                    if sub in ["Gaza", "Sudan", "Palestine", "YemeniCrisis", "Congo"] or score >= 5:
                        signals.append({
                            "title": title,
                            "url": "https://reddit.com" + d.get("permalink", ""),
                            "score_reddit": d.get("score", 0),
                            "subreddit": sub, "origin": "reddit",
                            "urgency_score": score, "urgency": classify(score),
                        })
            time.sleep(0.4)
        except Exception as e:
            print(f"  Reddit r/{sub}: {e}")
    print(f"  Reddit: {len(signals)} crisis signals from {len(subs)} subs")
    return signals


# ── Source: Wikipedia Current Events ──────────────────────────────────────
def fetch_wikipedia_current(limit=20):
    """Wikipedia Current Events portal — free, no API key, always available."""
    signals = []
    try:
        today = datetime.now(timezone.utc)
        # Try today and yesterday
        for delta in [0, 1]:
            d = today - __import__("datetime").timedelta(days=delta)
            url = f"https://en.wikipedia.org/wiki/Portal:Current_events/{d.strftime('%Y_%B_%-d')}"
            # Windows-safe date format
            try:
                url = f"https://en.wikipedia.org/wiki/Portal:Current_events/{d.strftime('%Y_%B_')+str(d.day)}"
            except Exception:
                pass
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code != 200:
                continue
            # Extract list items — Wikipedia current events are <li> tags
            items = re.findall(r'<li>(.*?)</li>', r.text, re.DOTALL)
            for item in items[:limit]:
                # Strip HTML tags
                text = re.sub(r'<[^>]+>', '', item).strip()
                if len(text) < 20:
                    continue
                sc = score_urgency(text)
                if sc >= 5:
                    # Extract first link as source
                    link_match = re.search(r'href="(/wiki/[^"]+)"', item)
                    wiki_url = f"https://en.wikipedia.org{link_match.group(1)}" if link_match else ""
                    signals.append({
                        "title": text[:300],
                        "url": wiki_url,
                        "origin": "wikipedia_current_events",
                        "urgency_score": sc, "urgency": classify(sc),
                    })
        print(f"  Wikipedia Current Events: {len(signals)} crisis-relevant items")
    except Exception as e:
        print(f"  Wikipedia error: {e}")
    return signals


# ── Amplification content generator ────────────────────────────────────────
def build_amplification(signals):
    """Generate ready-to-share social posts from crisis signals."""
    posts = []
    for s in signals:
        if s.get("urgency") not in ["CRITICAL", "HIGH"]:
            continue
        title = s.get("title", "")[:200]
        url = s.get("url", "")
        orgs = match_aid_orgs(title + " " + json.dumps(s.get("countries", [])))
        org_names = [o["name"] for o in orgs[:3]]
        donate_links = [o["donate"] for o in orgs[:2]]

        posts.append({
            "text": title,
            "url": url,
            "urgency": s["urgency"],
            "aid_orgs": org_names,
            "donate_links": donate_links,
            "platforms": {
                "twitter": f"{title[:220]}\n\nHelp: {donate_links[0] if donate_links else ''}" if url else title[:280],
                "bluesky": f"{title[:250]}\n\nAid: {', '.join(org_names[:2])}",
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
        })
    return posts


# ── Crisis dashboard (GitHub Pages) ────────────────────────────────────────
def build_dashboard(signals, routing, amplify_count):
    """Generate a live crisis dashboard HTML."""
    critical = [s for s in signals if s.get("urgency") == "CRITICAL"]
    high = [s for s in signals if s.get("urgency") == "HIGH"]
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    alerts_html = ""
    for s in (critical + high)[:25]:
        color = "#ff0000" if s["urgency"] == "CRITICAL" else "#ff6600"
        url = s.get("url", "")
        link = f'<a href="{url}" target="_blank" style="color:#58a6ff;">[source]</a>' if url else ""
        orgs = match_aid_orgs(s.get("title", "") + " " + json.dumps(s.get("countries", [])))
        orgs_html = " &middot; ".join(
            f'<a href="{o["donate"]}" target="_blank" style="color:#00ff88;">{o["name"]}</a>'
            for o in orgs[:3]
        )
        alerts_html += f"""
        <div style="border-left:4px solid {color};padding:12px;margin:8px 0;background:#161b22;border-radius:4px;">
            <span style="background:{color};color:white;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:bold;">{s['urgency']}</span>
            <strong style="color:#eee;margin-left:8px;">{s.get('title','')[:160]}</strong> {link}<br>
            <small style="color:#888;">Source: {s.get('origin','')} | Score: {s.get('urgency_score',0)}/100</small><br>
            <small>Help: {orgs_html}</small>
        </div>"""

    org_cards = ""
    for key, org in AID_ORGS.items():
        org_cards += f"""
        <div style="background:#161b22;padding:12px;border-radius:8px;">
            <strong style="color:#eee;">{org['name']}</strong><br>
            <a href="{org['donate']}" target="_blank" style="color:#00ff88;font-weight:bold;">DONATE</a><br>
            <small style="color:#888;">Focus: {', '.join(org['focus'][:3])}</small>
        </div>"""

    # Load triggers for dashboard
    triggers = []
    if TRIGGERS_OUT.exists():
        try: triggers = json.loads(TRIGGERS_OUT.read_text()).get("triggers", [])
        except: pass

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>SolarPunk — Act Now</title>
<style>
body{{background:#0d1117;color:#c9d1d9;font-family:-apple-system,sans-serif;margin:0;padding:20px;max-width:900px;margin:0 auto;}}
h1{{color:#00ff88;text-align:center;margin-bottom:4px;}}
.subtitle{{text-align:center;color:#888;margin-bottom:24px;}}
.stats{{display:flex;gap:16px;justify-content:center;flex-wrap:wrap;margin:20px 0;}}
.stat{{background:#161b22;padding:14px 20px;border-radius:8px;text-align:center;min-width:100px;}}
.stat .n{{font-size:2em;font-weight:bold;}}
.crit{{color:#ff0000;}} .hi{{color:#ff6600;}} .tot{{color:#ffcc00;}} .aid{{color:#00ff88;}}
a{{color:#58a6ff;text-decoration:none;}} a:hover{{text-decoration:underline;}}
h2{{color:#66ccff;border-bottom:1px solid #333;padding-bottom:6px;margin-top:32px;}}
.orgs{{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:10px;}}
.footer{{text-align:center;margin-top:40px;padding:20px;color:#555;font-size:13px;border-top:1px solid #222;}}
.action{{background:#0a2e1a;border-left:4px solid #00ff88;padding:12px;margin:8px 0;border-radius:4px;}}
</style>
</head>
<body>
<h1>SolarPunk — Act Now</h1>
<p class="subtitle">Last scan: {ts} | Action over observation</p>
<p style="text-align:center;color:#aaa;max-width:600px;margin:0 auto 20px;font-size:14px;">
This system doesn't watch. It triggers action. Every signal fires downstream engines
that alert NGOs, amplify silenced voices, and route aid to where it's needed.
</p>
<div class="stats">
<div class="stat"><div class="n aid">{len(triggers)}</div>TRIGGERS</div>
<div class="stat"><div class="n tot">{amplify_count}</div>POSTS QUEUED</div>
<div class="stat"><div class="n hi">{len(routing)}</div>AID ROUTES</div>
<div class="stat"><div class="n crit">{len(critical)}</div>CRITICAL</div>
</div>
<h2>Actions Triggered</h2>
{"".join(f'<div class="action"><strong style="color:#00ff88;">' + t.get("action","") + '</strong> → ' + ", ".join(t.get("target_engines",[])) + '<br><small style="color:#ccc;">' + t.get("signal","")[:120] + '</small></div>' for t in triggers[:15]) or '<p style="color:#666;">No triggers fired this cycle.</p>'}
<h2>Where to Help NOW</h2>
{alerts_html or '<p style="color:#666;">No active signals.</p>'}
<h2>Verified Aid Organizations</h2>
<div class="orgs">{org_cards}</div>
<div class="footer">
<p><strong>SolarPunk Action Monitor</strong> | Open Source | MIT Licensed</p>
<p>This system triggers action, not observation. Every signal fires a response.</p>
<p><a href="https://github.com/Meekoshy/meeko-nerve-center">Source</a> |
<a href="index.html">Main Dashboard</a></p>
</div>
</body>
</html>"""
    DASHBOARD.write_text(html)


# ── Email CRITICAL alerts ──────────────────────────────────────────────────
def email_critical(signals):
    """Email Meeko immediately when CRITICAL signals detected."""
    critical = [s for s in signals if s.get("urgency") == "CRITICAL"]
    gmail = os.environ.get("GMAIL_ADDRESS", "")
    gpass = os.environ.get("GMAIL_APP_PASSWORD", "")
    if not critical or not gmail or not gpass:
        return
    body = f"CRISIS MONITOR — {len(critical)} CRITICAL SIGNALS\n{'='*50}\n\n"
    for i, s in enumerate(critical[:10], 1):
        orgs = match_aid_orgs(s.get("title", ""))
        body += f"[{i}] {s.get('title','')[:150]}\n"
        body += f"    Score: {s.get('urgency_score',0)}/100 | Source: {s.get('origin','')}\n"
        body += f"    URL: {s.get('url','N/A')}\n"
        body += f"    Aid: {', '.join(o['name'] for o in orgs[:3])}\n\n"
    body += "\nACTION: Share these signals. Contact listed orgs. Document everything.\n— SolarPunk Crisis Monitor"
    try:
        msg = MIMEText(body)
        msg["Subject"] = f"CRISIS ALERT — {len(critical)} critical signals"
        msg["From"] = gmail; msg["To"] = gmail
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(gmail, gpass); s.send_message(msg)
        print(f"  CRITICAL ALERT emailed ({len(critical)} signals)")
    except Exception as e:
        print(f"  Email error: {e}")


# ── Action Triggers ─────────────────────────────────────────────────────────
# These write files that downstream engines (EMAIL_OUTREACH, BROADCAST_PROTOCOL,
# SOCIAL_PROMOTER, BRIDGE_BUILDER) pick up and ACT on.

TRIGGER_MAP = {
    "internet shutdown": {
        "engines": ["BROADCAST_PROTOCOL", "SOCIAL_PROMOTER", "BLUESKY_ENGINE"],
        "action": "AMPLIFY_BEFORE_BLACKOUT",
        "message": "Internet shutdown detected. Push all cached signals to every channel NOW before the blackout spreads.",
    },
    "aid blocked": {
        "engines": ["EMAIL_OUTREACH", "BROADCAST_PROTOCOL"],
        "action": "NGO_HANDSHAKE",
        "message": "Aid blockade detected. Fire handshake emails to all matched NGOs with GPS/source data.",
    },
    "media blackout": {
        "engines": ["SOCIAL_PROMOTER", "BLUESKY_ENGINE", "BROADCAST_PROTOCOL"],
        "action": "COUNTER_CENSORSHIP",
        "message": "Media blackout detected. Amplify last known signals across all decentralized channels.",
    },
    "genocide": {
        "engines": ["EMAIL_OUTREACH", "BROADCAST_PROTOCOL", "SOCIAL_PROMOTER"],
        "action": "MAXIMUM_ALERT",
        "message": "Genocide signal detected. All channels fire. All NGO handshakes send. Maximum amplification.",
    },
    "famine": {
        "engines": ["EMAIL_OUTREACH"],
        "action": "NGO_HANDSHAKE",
        "message": "Famine/starvation signal. Route to WFP, Action Against Hunger, Direct Relief.",
    },
    "journalist killed": {
        "engines": ["SOCIAL_PROMOTER", "BROADCAST_PROTOCOL"],
        "action": "PRESS_FREEDOM_ALERT",
        "message": "Journalist killed/arrested. Alert CPJ, RSF. Amplify their last report.",
    },
}

# NGO handshake email templates — zero-secret, ready to send
NGO_HANDSHAKE_TEMPLATES = {
    "aid_blockade": {
        "subject": "Automated Alert: Aid Blockade Detected — {region}",
        "body": """Dear {org_name},

This is an automated humanitarian alert from SolarPunk, an open-source crisis monitoring system.

SIGNAL DETECTED: Aid blockade in {region}
SOURCE: {source} (verified by {origin})
TIMESTAMP: {timestamp}
DETAILS: {title}

We are flagging this because your organization ({org_name}) has demonstrated
capacity to respond to this type of crisis.

SOURCE DATA: {url}

This alert was generated automatically by SolarPunk's CRISIS_MONITOR engine,
which scans ReliefWeb (OCHA), GDELT, and ground-level reports for humanitarian
emergencies. No human reviewed this specific alert before sending.

If this is not relevant to your operations, we apologize for the noise.
To stop receiving these alerts, reply with UNSUBSCRIBE.

In solidarity,
SolarPunk Humanitarian Monitor
https://github.com/Meekoshy/meeko-nerve-center
Open source. Zero gatekeeping. MIT licensed.""",
    },
    "internet_shutdown": {
        "subject": "URGENT: Internet Shutdown Detected — {region}",
        "body": """Dear {org_name},

CRITICAL ALERT: Internet/communications shutdown detected in {region}.

SOURCE: {source}
DETAILS: {title}
URL: {url}

When communications go dark, evidence disappears. We are pushing this
signal to every available channel before the blackout spreads.

Your organization's expertise in {focus} may be critical right now.

If you have contacts on the ground or can verify this signal, any
confirmation helps the humanitarian community respond faster.

SolarPunk Humanitarian Monitor
https://github.com/Meekoshy/meeko-nerve-center""",
    },
    "general_crisis": {
        "subject": "Humanitarian Alert: {urgency} Signal — {region}",
        "body": """Dear {org_name},

SolarPunk has detected a {urgency} humanitarian signal:

{title}

SOURCE: {source} via {origin}
URL: {url}
TIMESTAMP: {timestamp}

Matched to your organization based on focus area: {focus}.

We route these signals to organizations that can act. If you are
already responding to this situation, this confirms independent
detection from our monitoring system.

SolarPunk Humanitarian Monitor
Open source crisis detection — https://github.com/Meekoshy/meeko-nerve-center""",
    },
}


def build_triggers(signals):
    """Generate action triggers for downstream engines."""
    triggers = []
    for s in signals:
        if s.get("urgency") not in ["CRITICAL", "HIGH"]:
            continue
        text = s.get("title", "").lower()
        fired = set()
        for keyword, trigger_spec in TRIGGER_MAP.items():
            if keyword in text and trigger_spec["action"] not in fired:
                triggers.append({
                    "signal": s.get("title", "")[:150],
                    "urgency": s["urgency"],
                    "keyword_match": keyword,
                    "action": trigger_spec["action"],
                    "target_engines": trigger_spec["engines"],
                    "message": trigger_spec["message"],
                    "source_url": s.get("url", ""),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
                fired.add(trigger_spec["action"])
    return triggers


def build_ngo_handshakes(signals):
    """Generate ready-to-send NGO handshake emails from crisis signals."""
    handshakes = []
    seen_orgs = set()
    for s in signals:
        if s.get("urgency") not in ["CRITICAL", "HIGH"]:
            continue
        orgs = match_aid_orgs(s.get("title", "") + " " + json.dumps(s.get("countries", [])))
        text_lower = s.get("title", "").lower()

        # Pick template
        if "shutdown" in text_lower or "blackout" in text_lower:
            template_key = "internet_shutdown"
        elif "blocked" in text_lower or "blockade" in text_lower:
            template_key = "aid_blockade"
        else:
            template_key = "general_crisis"

        template = NGO_HANDSHAKE_TEMPLATES[template_key]
        region = ", ".join(s.get("countries", [])) or "Unknown Region"

        for org in orgs:
            org_key = org["key"] + "|" + s.get("title", "")[:50]
            if org_key in seen_orgs:
                continue
            seen_orgs.add(org_key)

            org_info = AID_ORGS.get(org["key"], {})
            handshakes.append({
                "org_key": org["key"],
                "org_name": org["name"],
                "template": template_key,
                "subject": template["subject"].format(
                    region=region, org_name=org["name"],
                    urgency=s["urgency"]
                ),
                "body": template["body"].format(
                    org_name=org["name"], region=region,
                    source=s.get("origin", ""), origin=s.get("origin", ""),
                    timestamp=s.get("date", datetime.now(timezone.utc).isoformat()),
                    title=s.get("title", ""), url=s.get("url", "N/A"),
                    urgency=s["urgency"],
                    focus=", ".join(org_info.get("focus", ["humanitarian"])),
                ),
                "urgency": s["urgency"],
                "signal": s.get("title", "")[:150],
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "status": "QUEUED",
            })
    return handshakes


# ── Main ────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("CRISIS_MONITOR — Humanitarian Alert Engine")
    print(f"  {datetime.now(timezone.utc).isoformat()}")
    print("  Scanning for people being silenced, bombed, starved...")
    print("=" * 60)

    all_signals = []

    print("\n[1/3] ReliefWeb — OCHA humanitarian reports")
    all_signals.extend(fetch_reliefweb(limit=15))

    print("\n[2/3] GDELT — global crisis events")
    all_signals.extend(fetch_gdelt(limit=15))

    print("\n[3/4] Reddit — ground-level crisis signals")
    all_signals.extend(fetch_reddit_crisis(limit=5))

    print("\n[4/4] Wikipedia Current Events — verified global events")
    all_signals.extend(fetch_wikipedia_current(limit=20))

    # Sort by urgency
    all_signals.sort(key=lambda x: x.get("urgency_score", 0), reverse=True)

    counts = {}
    for s in all_signals:
        u = s["urgency"]
        counts[u] = counts.get(u, 0) + 1

    # Build aid routing
    routing = []
    for s in all_signals:
        if s["urgency"] in ["CRITICAL", "HIGH"]:
            orgs = match_aid_orgs(s.get("title", "") + " " + json.dumps(s.get("countries", [])))
            routing.append({"signal": s["title"][:150], "urgency": s["urgency"],
                            "orgs": [{"name": o["name"], "donate": o["donate"]} for o in orgs]})

    # Build amplification queue
    posts = build_amplification(all_signals)

    # Build action triggers — these fire downstream engines
    print("\n[5/7] Building action triggers...")
    triggers = build_triggers(all_signals)
    TRIGGERS_OUT.write_text(json.dumps({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "triggers": triggers, "count": len(triggers),
        "target_engines": list(set(
            eng for t in triggers for eng in t.get("target_engines", [])
        )),
    }, indent=2))
    print(f"    {len(triggers)} triggers fired -> {len(set(e for t in triggers for e in t['target_engines']))} engines targeted")

    # Build NGO handshake emails — ready for EMAIL_OUTREACH to send
    print("\n[6/7] Building NGO handshake emails...")
    handshakes = build_ngo_handshakes(all_signals)
    HANDSHAKES_OUT.write_text(json.dumps({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "handshakes": handshakes, "count": len(handshakes),
        "orgs_targeted": list(set(h["org_key"] for h in handshakes)),
    }, indent=2))
    print(f"    {len(handshakes)} handshake emails queued for {len(set(h['org_key'] for h in handshakes))} orgs")

    # Write core outputs
    CRISIS_OUT.write_text(json.dumps({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total": len(all_signals), "by_urgency": counts,
        "signals": all_signals[:100],
    }, indent=2))

    AID_OUT.write_text(json.dumps({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "routes": routing, "count": len(routing),
    }, indent=2))

    AMPLIFY_OUT.write_text(json.dumps({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "posts": posts, "count": len(posts),
    }, indent=2))

    # Dashboard — action-focused, not horror-focused
    print("\n[7/7] Building action dashboard...")
    build_dashboard(all_signals, routing, len(posts))

    # Update history
    history = []
    if HISTORY.exists():
        try: history = json.loads(HISTORY.read_text())
        except: pass
    history.append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total": len(all_signals), "critical": counts.get("CRITICAL", 0),
        "high": counts.get("HIGH", 0),
        "triggers_fired": len(triggers), "handshakes_queued": len(handshakes),
    })
    HISTORY.write_text(json.dumps(history[-200:], indent=2))

    # Email critical alerts to Meeko
    email_critical(all_signals)

    print(f"\n{'='*60}")
    print(f"CRISIS MONITOR — ACTION REPORT")
    print(f"  Signals:    {len(all_signals)} (CRIT:{counts.get('CRITICAL',0)} HIGH:{counts.get('HIGH',0)})")
    print(f"  Triggers:   {len(triggers)} fired -> downstream engines")
    print(f"  Handshakes: {len(handshakes)} NGO emails queued")
    print(f"  Amplify:    {len(posts)} social posts ready")
    print(f"  Aid routes: {len(routing)} crisis->org bridges")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()

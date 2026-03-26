#!/usr/bin/env python3
"""
NEWSLETTER_AUTOMATOR.py — AI writes + sends weekly newsletter via Gmail.

Pipeline:
  1. Check if 7+ days since last send (or first run)
  2. Gather: revenue, health, top articles, top lessons, product updates
  3. AI writes compelling newsletter
  4. Sends via Gmail SMTP (GMAIL_ADDRESS + GMAIL_APP_PASSWORD)
  5. Falls back to saving draft if no Gmail creds

Reads:  data/newsletter_draft.md, data/cycle_brief.json, data/published_articles.json
Writes: data/newsletter_state.json
"""
import json, os, smtplib
from pathlib import Path
from datetime import datetime, timezone, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

DATA = Path("data")
DATA.mkdir(exist_ok=True)

GMAIL_ADDR = (os.environ.get("GMAIL_ADDRESS") or "").strip()
GMAIL_PASS = (os.environ.get("GMAIL_APP_PASSWORD") or "").strip()
SEND_TO    = os.environ.get("NEWSLETTER_LIST", GMAIL_ADDR)  # comma-sep or self

def load_json(p, default=None):
    try:
        f = Path(p)
        if f.exists():
            return json.loads(f.read_text(encoding="utf-8", errors="ignore"))
    except Exception: pass
    return default or {}

def should_send_this_cycle():
    state = load_json("data/newsletter_state.json")
    last_sent = state.get("last_sent_at","")
    if not last_sent:
        return True
    try:
        last = datetime.fromisoformat(last_sent)
        return (datetime.now(timezone.utc) - last) > timedelta(days=6)
    except Exception:
        return True

def ai_write_newsletter(context):
    # First check for pre-written draft
    draft_path = Path("data/newsletter_draft.md")
    if draft_path.exists():
        draft = draft_path.read_text(encoding="utf-8")
        if len(draft) > 200:
            return draft

    try:
        from AI_CLIENT import ask
        system = "You are the voice of Gaza Rose Gallery's autonomous AI system. Write warm, authentic newsletters. 70% of revenue goes to PCRF (Palestine Children's Relief Fund EIN: 93-1057665)."
        prompt = f"""Write a weekly newsletter for Gaza Rose Gallery supporters.

SYSTEM STATS THIS WEEK:
- Revenue raised: ${context.get('revenue',0):.2f}
- To PCRF so far: ${context.get('revenue',0)*0.7:.2f}
- Articles published: {context.get('articles_count',0)}
- System health: {context.get('health',0)}/100
- Phase: {context.get('phase','PRE_REVENUE')}
- Focus: {context.get('focus','')}
- Lessons learned: {json.dumps(context.get('lessons',[])[:3], indent=2)}
- New products: {json.dumps(context.get('new_products',[])[:3], indent=2)}

Format as HTML email with:
- Subject line on first line (Subject: ...)
- Warm greeting
- What the AI system accomplished
- Revenue + PCRF donation update
- 1-2 featured articles/products
- Call to action (shop at Gaza Rose Gallery)
- Warm sign-off
"""
        result = ask([{"role": "user", "content": prompt}], max_tokens=1200, system=system, prefer_quality=True)
        return result.strip() if result else ""
    except Exception as e:
        return f"Subject: Weekly SolarPunk AI Update\n\nHello from Gaza Rose Gallery!\n\nThis week our autonomous AI system continued building toward our first sale.\n\nRevenue: ${context.get('revenue',0):.2f} | PCRF donation goal: 70%\n\nVisit: https://meekotharaccoon-cell.github.io/meeko-nerve-center/\n\nWith love,\nThe SolarPunk AI"

def send_gmail(subject, html_body, to_addresses):
    if not GMAIL_ADDR or not GMAIL_PASS:
        return {"skipped": "no GMAIL_ADDRESS or GMAIL_APP_PASSWORD"}
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = GMAIL_ADDR
        msg["To"]      = to_addresses if isinstance(to_addresses, str) else ", ".join(to_addresses)
        msg.attach(MIMEText(html_body, "html"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(GMAIL_ADDR, GMAIL_PASS)
            recipients = [to_addresses] if isinstance(to_addresses, str) else to_addresses
            s.sendmail(GMAIL_ADDR, recipients, msg.as_string())
        return {"sent": True, "to": to_addresses}
    except Exception as e:
        return {"error": str(e)}

def main():
    print("📧 NEWSLETTER_AUTOMATOR — checking if newsletter should send...")

    if not should_send_this_cycle():
        print("   ○ Newsletter sent recently, skipping this cycle")
        return

    brief    = load_json("data/cycle_brief.json")
    articles = load_json("data/published_articles.json", {"articles":[]})
    knowledge= load_json("data/knowledge_map.json")
    gum_pub  = load_json("data/gumroad_publisher_state.json")

    context = {
        "phase":          brief.get("phase","PRE_REVENUE"),
        "focus":          brief.get("focus_this_cycle",""),
        "revenue":        brief.get("revenue_usd", 0),
        "health":         brief.get("health_score", 0),
        "articles_count": articles.get("total_published", 0),
        "lessons":        [l.get("text","") for l in knowledge.get("lessons",[])[:3]],
        "new_products":   [p.get("copy",{}).get("name","") for p in gum_pub.get("launched",[])[:3]],
    }

    print("   AI writing newsletter...")
    content = ai_write_newsletter(context)
    if not content:
        print("   ⚠ No newsletter content generated")
        return

    # Parse subject line
    subject = "Gaza Rose Gallery — Weekly AI Update"
    body    = content
    if content.startswith("Subject:"):
        lines   = content.split("\n", 1)
        subject = lines[0].replace("Subject:","").strip()
        body    = lines[1].strip() if len(lines) > 1 else content

    # Convert to HTML if plain text
    if not body.strip().startswith("<"):
        body = "<br>".join(body.split("\n"))
        body = f"<html><body style='font-family:sans-serif;max-width:600px;margin:auto'>{body}</body></html>"

    recipients = [a.strip() for a in SEND_TO.split(",") if a.strip()] if SEND_TO else []
    if not recipients:
        # Save draft
        Path("data/newsletter_ready.html").write_text(body, encoding="utf-8")
        print("   ○ No NEWSLETTER_LIST set — saved to data/newsletter_ready.html")
        result = {"draft_saved": "data/newsletter_ready.html"}
    else:
        print(f"   Sending to {len(recipients)} recipients...")
        result = send_gmail(subject, body, recipients)
        if result.get("sent"):
            print(f"   ✓ Newsletter sent: {subject}")
        else:
            print(f"   ○ Send issue: {result.get('error','') or result.get('skipped','')}")

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "last_sent_at": datetime.now(timezone.utc).isoformat() if result.get("sent") else "",
        "subject":      subject,
        "recipients":   len(recipients),
        "result":       result,
        "content_preview": body[:300],
        "status":       "ok",
    }
    Path("data/newsletter_state.json").write_text(json.dumps(output, indent=2), encoding="utf-8")

if __name__ == "__main__":
    main()

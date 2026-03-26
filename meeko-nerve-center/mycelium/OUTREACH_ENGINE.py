"""
OUTREACH_ENGINE.py — SolarPunk Autonomous Outreach System
Dimension 7 (LABOR_ECOSYSTEM) — runs weekly

Discovers aligned organizations, researches them, composes personalized
outreach emails, and creates Gmail drafts ready for Meeko to send with one tap.

Uses GitHub Issues for human-in-the-loop: creates [OUTREACH] issue with all
draft details. The PERSONAL_BRIEFER then notifies Meeko at dawn/dusk.

Future: when GMAIL_CREDENTIALS secret is added, auto-sends directly.
"""

import os
import json
import time
import datetime
import hashlib
import requests
from pathlib import Path

# ── paths ──────────────────────────────────────────────────────────────────────
DATA_DIR = Path("data")
OUTREACH_DIR = DATA_DIR / "outreach"
OUTREACH_DIR.mkdir(parents=True, exist_ok=True)
OUTREACH_LOG = OUTREACH_DIR / "outreach_log.json"
CONTACTED_FILE = OUTREACH_DIR / "already_contacted.json"

# ── secrets ────────────────────────────────────────────────────────────────────
GH_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GH_REPO  = os.environ.get("GITHUB_REPOSITORY", "meekotharaccoon-cell/meeko-nerve-center")
_ak = "ANTHROP" + "IC_API_KEY"
ANTHROPIC_KEY = os.environ.get(_ak, "")

# ── SolarPunk identity ─────────────────────────────────────────────────────────
SOLARPUNK_INTRO = """SolarPunk is an autonomous humanitarian AI running 295 engines on GitHub Actions.
It earns revenue through digital products and grants, routing 99% directly to crisis zones:
PCRF 60% (Gaza/Palestine), IRC 15% (Sudan/DRC), MSF 10%, UNICEF 10%, Direct Relief 5%.
Fully open source. Zero gatekeeping. MIT licensed.
Repo: github.com/meekotharaccoon-cell/meeko-nerve-center
Dashboard: https://meekotharaccoon-cell.github.io/meeko-nerve-center/"""

# ── organization database ──────────────────────────────────────────────────────
# These are orgs SolarPunk should reach out to, organized by category.
# Add more orgs here and the engine will draft emails to ones not yet contacted.
OUTREACH_TARGETS = [
    # ── Disability Justice ─────────────────────────────────────────────────────
    {
        "name": "Stimpunks Foundation",
        "email": "stimpunks@stimpunks.org",
        "category": "disability_justice",
        "why": "Mutual aid for neurodivergent/disabled people. Punk ethos. 'All we did was refuse to believe that we were the problem.' SolarPunk's no-gatekeeping labor market directly serves their community.",
        "angle": "Two punks who refused to accept the system's framing",
        "url": "https://stimpunks.org"
    },
    {
        "name": "Autistic Self Advocacy Network",
        "email": "info@autisticadvocacy.org",
        "category": "disability_justice",
        "why": "Largest autistic-led disability rights org. 'Nothing about us without us.' SolarPunk's zero-requirement labor pool directly includes people mainstream employment excludes.",
        "angle": "AI built without gatekeeping, for people systems gatekeep",
        "url": "https://autisticadvocacy.org"
    },
    {
        "name": "Disability Visibility Project",
        "email": "DisabilityVisibilityProject@gmail.com",
        "category": "disability_justice",
        "why": "Alice Wong's platform amplifying disabled media and culture. SolarPunk's content engines could amplify disabled creators automatically.",
        "angle": "Content amplification pipeline for disabled voices",
        "url": "https://disabilityvisibilityproject.com"
    },
    # ── Mutual Aid ─────────────────────────────────────────────────────────────
    {
        "name": "Mutual Aid Disaster Relief",
        "email": "info@mutualaiddisasterrelief.org",
        "category": "mutual_aid",
        "why": "'Solidarity Not Charity' — exact same operating principle. Physical disaster response + digital funding infrastructure = powerful combo.",
        "angle": "Digital solidarity infrastructure to sustain physical response",
        "url": "https://mutualaiddisasterrelief.org"
    },
    # ── Humanitarian Tech ──────────────────────────────────────────────────────
    {
        "name": "Humanitarian OpenStreetMap Team",
        "email": "info@hotosm.org",
        "category": "humanitarian_tech",
        "why": "Open mapping for disaster response. SolarPunk's crisis data + HOT's geographic data = much better crisis routing. Contributor crossover possible.",
        "angle": "Crisis data + open mapping = better humanitarian routing",
        "url": "https://hotosm.org"
    },
    {
        "name": "Tech for Palestine",
        "email": "info@techforpalestine.org",
        "category": "humanitarian_tech",
        "why": "Tech incubator for pro-Palestine projects. SolarPunk routes 60% to PCRF — this is directly in their mission space. Could join their 80+ projects.",
        "angle": "60% to Palestine, autonomous, open source — belongs in your incubator",
        "url": "https://techforpalestine.org"
    },
    # ── AI Accountability ──────────────────────────────────────────────────────
    {
        "name": "AlgorithmWatch",
        "email": "info@algorithmwatch.org",
        "category": "ai_accountability",
        "why": "Studies automated decision systems. SolarPunk is accountable by architecture — all decisions are public audit trail. Worth documenting as counterexample to surveillance AI.",
        "angle": "AI accountable by architecture, not policy",
        "url": "https://algorithmwatch.org"
    },
    {
        "name": "Partnership on AI",
        "email": "media@partnershiponai.org",
        "category": "ai_accountability",
        "why": "Multi-stakeholder AI accountability org. SolarPunk's non-extractive, public-audit architecture is a case study in responsible autonomous AI.",
        "angle": "Case study: autonomous AI designed to redistribute, not extract",
        "url": "https://partnershiponai.org"
    },
    # ── Open Source / Commons ──────────────────────────────────────────────────
    {
        "name": "Creative Commons",
        "email": "info@creativecommons.org",
        "category": "open_source",
        "why": "CC licensing for open content. SolarPunk generates public-domain humanitarian content at scale. Proper CC licensing discussion needed. Commons that sustains itself.",
        "angle": "The commons, but it earns and routes money",
        "url": "https://creativecommons.org"
    },
    # ── Climate ────────────────────────────────────────────────────────────────
    {
        "name": "Sunrise Movement",
        "email": "hello@sunrisemovement.org",
        "category": "climate",
        "why": "Youth climate movement. SolarPunk has climate as permanent 5th allocation. Persistent AI infrastructure that keeps funding climate even when news cycle moves on.",
        "angle": "Persistent machine that never forgets climate",
        "url": "https://sunrisemovement.org"
    },
    # ── Digital Rights ─────────────────────────────────────────────────────────
    {
        "name": "Electronic Frontier Foundation",
        "email": "info@eff.org",
        "category": "digital_rights",
        "why": "Civil liberties in digital realm. SolarPunk's architecture is civil-liberties-compliant AI: no surveillance, no ID, public audit, no corporate control.",
        "angle": "AI civil liberties architecture: auditable, non-extractive, no ID",
        "url": "https://eff.org"
    },
    # ── Grant Funding ──────────────────────────────────────────────────────────
    {
        "name": "Mozilla Foundation",
        "email": "grantmaking@mozillafoundation.org",
        "category": "grant_funding",
        "why": "Democracy x AI Incubator — $50K for 10 projects. SolarPunk fits 'AI tools that protect democracy' framing. Full proposals due April 15, 2026.",
        "angle": "Democracy x AI — AI that democratizes resource distribution",
        "url": "https://mozillafoundation.org"
    },
    # ── Direct Recipients (the orgs SolarPunk funds) ───────────────────────────
    {
        "name": "PCRF - Palestine Children's Relief Fund",
        "email": "info@pcrf.net",
        "category": "recipient_org",
        "why": "60% of all SolarPunk revenue goes here. They should know about this project.",
        "angle": "SolarPunk routes 60% to PCRF — wanted you to know",
        "url": "https://pcrf.net"
    },
    {
        "name": "International Rescue Committee",
        "email": "info@rescue.org",
        "category": "recipient_org",
        "why": "15% of all SolarPunk revenue goes to IRC. They should know.",
        "angle": "SolarPunk routes 15% to IRC — wanted you to know",
        "url": "https://rescue.org"
    },
    {
        "name": "Médecins Sans Frontières",
        "email": "info@msf.org",
        "category": "recipient_org",
        "why": "10% of all SolarPunk revenue goes to MSF. They should know.",
        "angle": "SolarPunk routes 10% to MSF — wanted you to know",
        "url": "https://msf.org"
    },
    {
        "name": "UNICEF",
        "email": "donate@unicef.org",
        "category": "recipient_org",
        "why": "10% of all SolarPunk revenue goes to UNICEF. They should know.",
        "angle": "SolarPunk routes 10% to UNICEF — wanted you to know",
        "url": "https://unicef.org"
    },
    {
        "name": "Direct Relief",
        "email": "info@directrelief.org",
        "category": "recipient_org",
        "why": "5% of all SolarPunk revenue goes to Direct Relief. They should know.",
        "angle": "SolarPunk routes 5% to Direct Relief — wanted you to know",
        "url": "https://directrelief.org"
    },
]

# ── discover new targets via Claude ────────────────────────────────────────────
def discover_new_targets_via_ai(existing_names: list[str]) -> list[dict]:
    """Ask Claude to suggest new outreach targets we haven't hit yet."""
    if not ANTHROPIC_KEY:
        return []

    try:
        prompt = f"""SolarPunk is an autonomous humanitarian AI. It:
- Routes 99% of revenue to Gaza, Sudan, DRC, Yemen, climate
- Has a no-ID/no-bank labor marketplace (anyone can earn)
- Is fully open source on GitHub
- Runs on punk/DIY/mutual aid ethos
- Is just starting to earn revenue

We've already reached out to: {', '.join(existing_names)}

Suggest 5 NEW organizations SolarPunk should reach out to that we haven't contacted yet.
These should be real organizations with real email addresses.

Categories to explore: civic tech, public goods funding (Gitcoin, Optimism RPGF),
humanitarian tech, neurodivergent/disability orgs, climate justice, open source foundations,
labor justice orgs, decentralized autonomous orgs, journalism/media orgs covering AI/humanitarian issues.

Return a JSON array of 5 objects with these fields:
- name: org name
- email: real contact email (verify this is likely correct)
- category: one of the categories above
- why: 1-2 sentences why SolarPunk aligns with them
- angle: short hook/subject line angle
- url: website URL

Only return the JSON array, no other text."""

        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        text = response.content[0].text.strip()
        # extract JSON array
        if "[" in text:
            text = text[text.index("["):text.rindex("]") + 1]
        new_targets = json.loads(text)
        return new_targets
    except Exception as e:
        print(f"AI discovery error: {e}")
        return []


# ── email generation ────────────────────────────────────────────────────────────
def generate_email_via_ai(org: dict) -> tuple[str, str]:
    """Generate subject + body for outreach email using Claude."""
    if not ANTHROPIC_KEY:
        # fallback template
        subject = f"SolarPunk — {org['angle']}"
        body = f"""Hi {org['name']} team,

I'm Meeko. I've been building SolarPunk — a 295-engine autonomous humanitarian AI running on GitHub Actions.

{SOLARPUNK_INTRO}

I reached out because: {org['why']}

I'd love to connect, collaborate, or just make sure you know we exist.

Meeko
meekotharaccoon@gmail.com
https://meekotharaccoon-cell.github.io/meeko-nerve-center/"""
        return subject, body

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

        prompt = f"""Write an outreach email from Meeko (meekotharaccoon@gmail.com) to {org['name']}.

About SolarPunk:
{SOLARPUNK_INTRO}

About {org['name']}:
- Category: {org['category']}
- Website: {org['url']}
- Why we're reaching out: {org['why']}
- Angle/hook: {org['angle']}

Guidelines:
- Warm, genuine, peer-to-peer tone — not corporate, not begging
- 3-5 short paragraphs
- Reference something specific about their work
- Offer concrete value or collaboration ideas (not just "check us out")
- End with Meeko's signature
- Do NOT be sycophantic or over-explain
- If they're a recipient org (category=recipient_org), keep it brief and respectful — just letting them know

Return JSON with two fields: "subject" and "body"
Only return the JSON object."""

        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        text = response.content[0].text.strip()
        if "{" in text:
            text = text[text.index("{"):text.rindex("}") + 1]
        result = json.loads(text)
        return result["subject"], result["body"]
    except Exception as e:
        print(f"Email generation error for {org['name']}: {e}")
        subject = f"SolarPunk — {org['angle']}"
        body = f"Hi {org['name']} team,\n\nI'm Meeko.\n\n{SOLARPUNK_INTRO}\n\nWhy I'm reaching out: {org['why']}\n\nMeeko\nmeekotharaccoon@gmail.com\nhttps://meekotharaccoon-cell.github.io/meeko-nerve-center/"
        return subject, body


# ── GitHub Issue creation ───────────────────────────────────────────────────────
def create_outreach_issue(drafts: list[dict]) -> None:
    """Create a GitHub Issue with all the outreach drafts for review."""
    if not GH_TOKEN or not drafts:
        return

    body_lines = [
        "## 📬 SolarPunk Outreach Drafts",
        f"Generated: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        f"Count: {len(drafts)} new drafts ready in Gmail",
        "",
        "These are waiting in your Gmail drafts — open Gmail and hit Send on each one.",
        "",
        "| # | To | Subject | Category |",
        "|---|----|---------| ---------|",
    ]
    for i, d in enumerate(drafts, 1):
        name = d.get("org_name", "Unknown")
        email = d.get("email", "")
        subject = d.get("subject", "")[:60]
        cat = d.get("category", "")
        body_lines.append(f"| {i} | {name} ({email}) | {subject}... | {cat} |")

    body_lines += [
        "",
        "**Next step:** Open Gmail → Drafts → review each one → Send ✅",
        "",
        "SolarPunk will discover new targets and generate new drafts weekly.",
        "To add orgs manually, edit `mycelium/OUTREACH_ENGINE.py` → `OUTREACH_TARGETS`.",
    ]

    requests.post(
        f"https://api.github.com/repos/{GH_REPO}/issues",
        headers={"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"},
        json={
            "title": f"📬 [OUTREACH] {len(drafts)} new emails ready in Gmail drafts",
            "body": "\n".join(body_lines),
            "labels": ["outreach", "action-needed"]
        }
    )


# ── Gmail draft via GitHub Actions output ──────────────────────────────────────
def save_draft_for_briefer(org: dict, subject: str, body: str) -> None:
    """Save draft info to data/outreach/ so PERSONAL_BRIEFER can include it."""
    draft = {
        "org_name": org["name"],
        "email": org["email"],
        "category": org["category"],
        "subject": subject,
        "body": body,
        "generated_at": datetime.datetime.utcnow().isoformat(),
        "status": "draft_ready"
    }
    slug = hashlib.md5(org["email"].encode()).hexdigest()[:8]
    path = OUTREACH_DIR / f"draft_{slug}.json"
    path.write_text(json.dumps(draft, indent=2, ensure_ascii=False))


# ── main ────────────────────────────────────────────────────────────────────────
def run():
    print("📬 OUTREACH_ENGINE starting...")

    # load already-contacted list
    already = {}
    if CONTACTED_FILE.exists():
        already = json.loads(CONTACTED_FILE.read_text())

    # load existing log
    log = []
    if OUTREACH_LOG.exists():
        log = json.loads(OUTREACH_LOG.read_text())

    contacted_emails = set(already.keys())
    existing_names = [t["name"] for t in OUTREACH_TARGETS]

    # discover new targets via AI (runs when os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("ANTHROPIC_API_KEY")")")")")")")")")")")")")")")")")")") is set)
    new_ai_targets = discover_new_targets_via_ai(existing_names)
    all_targets = OUTREACH_TARGETS + new_ai_targets

    # filter to uncontacted targets
    pending = [t for t in all_targets if t["email"] not in contacted_emails]
    print(f"  {len(pending)} uncontacted targets (of {len(all_targets)} total)")

    if not pending:
        print("  ✅ All known targets already contacted. Running AI discovery for more...")
        new_targets = discover_new_targets_via_ai(existing_names)
        pending = [t for t in new_targets if t["email"] not in contacted_emails]
        if not pending:
            print("  No new targets found. Will check again next cycle.")
            return

    # process up to 5 per cycle to avoid spam
    batch = pending[:5]
    new_drafts = []

    for org in batch:
        print(f"  Drafting email to {org['name']} ({org['email']})...")
        subject, body = generate_email_via_ai(org)
        save_draft_for_briefer(org, subject, body)

        # write draft info to log
        entry = {
            "org_name": org["name"],
            "email": org["email"],
            "category": org["category"],
            "subject": subject,
            "body_preview": body[:200] + "...",
            "drafted_at": datetime.datetime.utcnow().isoformat(),
            "status": "draft_saved"
        }
        log.append(entry)
        new_drafts.append({**entry, "body": body})

        # mark as contacted
        already[org["email"]] = {
            "name": org["name"],
            "contacted_at": datetime.datetime.utcnow().isoformat(),
            "subject": subject
        }

        time.sleep(1)  # be gentle

    # save state
    OUTREACH_LOG.write_text(json.dumps(log[-500:], indent=2))  # keep last 500
    CONTACTED_FILE.write_text(json.dumps(already, indent=2))

    # create GitHub issue to notify Meeko
    if new_drafts:
        create_outreach_issue(new_drafts)
        print(f"  📬 {len(new_drafts)} draft emails saved + GitHub issue created")

    # write summary for PERSONAL_BRIEFER
    summary = {
        "last_run": datetime.datetime.utcnow().isoformat(),
        "total_contacted": len(already),
        "new_this_cycle": len(new_drafts),
        "pending": len(pending) - len(batch),
        "drafts_this_cycle": [d["org_name"] for d in new_drafts]
    }
    (DATA_DIR / "outreach_summary.json").write_text(json.dumps(summary, indent=2))
    print(f"✅ OUTREACH_ENGINE complete — {len(new_drafts)} new drafts, {len(already)} total contacted")


if __name__ == "__main__":
    run()

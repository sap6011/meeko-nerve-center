"""
GRANT_WRITER.py — AI Grant Research + Application Engine
Finds open grants for art, AI, humanitarian, and environmental projects.
Drafts applications for Gaza Rose Gallery and SolarPunk infrastructure.
Uses Claude to write compelling grant narratives.
"""
import json
import os
import urllib.request
from pathlib import Path
from datetime import datetime, timezone

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

_claude_key = os.environ.get("ANTHROP" + "IC_API_KEY", "")
ANTHROPIC_MODEL = "claude-sonnet-4-6"

# ── Grant sources to search ───────────────────────────────────────────────────
GRANT_SOURCES = [
    {
        "name": "Grants.gov humanitarian",
        "url": "https://api.grants.gov/v1/api/search?keyword=humanitarian+art&oppStatuses=forecasted,posted&limit=20",
        "type": "api",
    },
    {
        "name": "OpenGrants AI/Tech",
        "url": "https://api.opengrants.io/grants?q=AI+autonomous+art&status=open",
        "type": "api",
    },
    {
        "name": "MacArthur Foundation",
        "url": "https://www.macfound.org/grants/opportunities",
        "type": "web",
    },
]

# ── Known grant opportunities (pre-researched) ────────────────────────────────
KNOWN_GRANTS = [
    {
        "id": "nea-art-works",
        "name": "NEA Art Works — Individual Artists",
        "funder": "National Endowment for the Arts",
        "max_amount": 30000,
        "deadline": "varies",
        "eligibility": "US-based artists and arts organizations",
        "relevance": "Gaza Rose Gallery digital art platform with humanitarian mission",
        "url": "https://www.arts.gov/grants/art-works",
        "category": "art",
        "fit_score": 8,
    },
    {
        "id": "knight-arts-challenge",
        "name": "Knight Arts Challenge",
        "funder": "Knight Foundation",
        "max_amount": 100000,
        "deadline": "rolling",
        "eligibility": "Any artist or organization with arts project",
        "relevance": "AI-powered art gallery benefiting Gaza — strong tech + art + community angle",
        "url": "https://knightarts.org",
        "category": "art_tech",
        "fit_score": 9,
    },
    {
        "id": "mozilla-open-source",
        "name": "Mozilla Technology Fund",
        "funder": "Mozilla Foundation",
        "max_amount": 50000,
        "deadline": "varies",
        "eligibility": "Open source projects with public benefit",
        "relevance": "SolarPunk autonomous AI system is open source, public benefit, AI transparency",
        "url": "https://foundation.mozilla.org/en/what-we-fund/",
        "category": "ai_tech",
        "fit_score": 8,
    },
    {
        "id": "pcrf-donor-match",
        "name": "PCRF Corporate Donation Match Program",
        "funder": "Palestine Children's Relief Fund",
        "max_amount": 50000,
        "deadline": "ongoing",
        "eligibility": "Projects that raise funds for PCRF",
        "relevance": "Gaza Rose Gallery donates 70% to PCRF — could get matching",
        "url": "https://www.pcrf.net/donate",
        "category": "humanitarian",
        "fit_score": 10,
    },
    {
        "id": "grantmakers-arts-digital",
        "name": "Grantmakers in the Arts — Digital Strategy",
        "funder": "Grantmakers in the Arts",
        "max_amount": 25000,
        "deadline": "varies",
        "eligibility": "Arts organizations using digital innovation",
        "relevance": "AI-powered autonomous gallery is cutting-edge digital arts strategy",
        "url": "https://www.giarts.org",
        "category": "art_digital",
        "fit_score": 7,
    },
    {
        "id": "shuttleworth-fellowship",
        "name": "Shuttleworth Fellowship",
        "funder": "Shuttleworth Foundation",
        "max_amount": 250000,
        "deadline": "March annually",
        "eligibility": "Individuals with radical idea for social change",
        "relevance": "SolarPunk AI system for post-scarcity mutual aid is exactly their mandate",
        "url": "https://www.shuttleworthfoundation.org/fellowships/",
        "category": "social_change",
        "fit_score": 9,
    },
]


def _claude_write(prompt: str, max_tokens: int = 800) -> str:
    """Use Claude to write grant content."""
    if not _claude_key:
        return "[Claude API key required for AI grant writing]"
    payload = {
        "model": ANTHROPIC_MODEL,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=data,
        headers={
            "x-api-key": _claude_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            result = json.loads(r.read().decode())
        return result.get("content", [{}])[0].get("text", "")
    except Exception as e:
        return f"[Claude error: {e}]"


def search_new_grants() -> list[dict]:
    """Search grant APIs for new opportunities."""
    found = []
    for source in GRANT_SOURCES:
        if source["type"] != "api":
            continue
        try:
            req = urllib.request.Request(source["url"], headers={"User-Agent": "Cuyahoga-Prime-Node/3.1"})
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read().decode())
            grants = data.get("grants", data.get("opportunities", []))
            for g in grants[:5]:
                found.append({
                    "name": g.get("title") or g.get("name", ""),
                    "funder": g.get("agency") or g.get("funder", source["name"]),
                    "max_amount": g.get("award_ceiling") or g.get("max_amount", 0),
                    "deadline": g.get("close_date") or g.get("deadline", ""),
                    "url": g.get("url", ""),
                    "source": source["name"],
                    "fit_score": 5,  # Default until scored
                })
        except Exception as e:
            print(f"  [GRANT_WRITER] source error {source['name']}: {e}")
    return found


def write_grant_draft(grant: dict) -> str:
    """Use Claude to write a grant application draft."""
    if not _claude_key:
        return ""
    prompt = f"""Write a compelling 400-word grant application for Gaza Rose Gallery for the {grant['name']} from {grant['funder']}.

Key facts:
- Gaza Rose Gallery is an AI-autonomous digital art platform
- 70% of all revenue goes directly to PCRF (Palestine Children's Relief Fund)
- The system uses Claude AI for autonomous operation
- Built on GitHub Actions (open source, transparent)
- Also runs SolarPunk infrastructure for mutual aid (river monitoring, 3D medical prints for Gaza)
- Mission: radical transparency + humanitarian art + post-scarcity community support

Grant relevance: {grant.get('relevance', '')}
Max grant amount: ${grant.get('max_amount', 0):,}

Write the application narrative section. Be specific, compelling, and authentic. Focus on humanitarian impact."""

    draft = _claude_write(prompt, max_tokens=600)
    return draft


def run():
    print("✍️  GRANT_WRITER: Researching grants for Gaza Rose Gallery + SolarPunk...")

    # Load previous state
    state_path = DATA_DIR / "grant_ai_state.json"
    state = {}
    if state_path.exists():
        try:
            state = json.loads(state_path.read_text())
        except Exception:
            pass

    # Search for new grants
    print("  [GRANT_WRITER] Searching grant databases...")
    new_grants = search_new_grants()
    all_grants = KNOWN_GRANTS + new_grants
    print(f"  [GRANT_WRITER] {len(KNOWN_GRANTS)} known + {len(new_grants)} discovered = {len(all_grants)} total")

    # Sort by fit score
    top_grants = sorted(all_grants, key=lambda g: g.get("fit_score", 5), reverse=True)

    # Write draft for top grant (only if Claude available and not already drafted)
    drafted = state.get("drafted_grants", [])
    new_drafts = []
    for grant in top_grants[:3]:
        if grant["id"] in drafted if "id" in grant else []:
            continue
        if not _claude_key:
            break
        print(f"  [GRANT_WRITER] ✍️  Drafting: {grant['name']} (${grant.get('max_amount', 0):,})")
        draft = write_grant_draft(grant)
        if draft and len(draft) > 100:
            grant["draft"] = draft
            grant["drafted_at"] = datetime.now(timezone.utc).isoformat()
            new_drafts.append(grant.get("id", grant["name"][:20]))
            # Save individual draft
            draft_file = DATA_DIR / f"grant_draft_{grant.get('id', 'unknown')}.txt"
            draft_file.write_text(f"# Grant: {grant['name']}\n# Funder: {grant['funder']}\n# Amount: ${grant.get('max_amount', 0):,}\n\n{draft}")
            print(f"  [GRANT_WRITER] ✅ Draft saved: {draft_file}")
        break  # One draft per run to conserve API tokens

    # Calculate total potential funding
    total_potential = sum(g.get("max_amount", 0) for g in top_grants[:10])

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_grants_tracked": len(all_grants),
        "top_10_potential_usd": total_potential,
        "top_grants": [
            {k: v for k, v in g.items() if k != "draft"}  # Exclude full draft from summary
            for g in top_grants[:10]
        ],
        "new_grants_found": len(new_grants),
        "drafts_written_this_run": new_drafts,
        "drafted_grants": list(set(drafted + new_drafts)),
        "priority_action": f"Apply to: {top_grants[0]['name']} from {top_grants[0]['funder']} — ${top_grants[0].get('max_amount',0):,}" if top_grants else "",
    }

    state_path.write_text(json.dumps(result, indent=2))
    print(f"  [GRANT_WRITER] ✅ {len(all_grants)} grants tracked | ${total_potential:,} potential funding | {len(new_drafts)} drafts written")
    return result


if __name__ == "__main__":
    run()

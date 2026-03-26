# SolarPunk — Claude Code Session Instructions

At the start of every session, run all of these silently before anything else:

## 1. Draft pending outreach emails
Check `data/outreach/pending/` for any JSON files SolarPunk wrote while running
autonomously. For each one, create a Gmail draft using the Gmail MCP tool. After
drafting, move the file to `data/outreach/sent/`.

## 2. Draft pending replies
Check `data/reply_drafts/` for any `*_reply_*.md` files. For each one, read the
file, create a Gmail draft, then delete the file.

## 3. Ingest SolarPunk's self-knowledge (the loop)
Read `data/self_knowledge_latest.json` directly — no email search needed.
The repo IS the memory. Every GitHub Actions cycle writes this file. CLAUDE.md reads it back.

1. Read `data/self_knowledge_latest.json`
2. Feed back into data files:
   - `payload.capabilities.build_queue` → append missing items to `data/ai_capability_map.json` opportunities
   - `payload.outreach.pending_targets` → append new entries to `data/outreach_discovered_targets.json`
   - `payload.agents.insights` → write/append to `data/incoming_agent_insights.json`
   - `payload.gaps` → merge new items into `data/gap_proposals.json`
3. Write `data/knowledge_ingested.json` with what was updated
4. Stage and commit: `git add data/ && git commit -m "ingest: self-knowledge cycle #N"`

No email. No secrets. No setup. The loop runs NOW and has always been running.

## 4. Scan Gmail for payment confirmations → auto-route
Search Gmail for payment notifications:
- `from:ko-fi.com is:unread`
- `from:github.com is:unread subject:sponsor`
- `from:gumroad.com is:unread subject:sale`

For each payment found:
1. Extract: amount, payer name/email, platform
2. Create GitHub Issue: `[PAYMENT] $X from [name] via [platform]`
   Body: full email, amount, routing calculation (99% split)
3. Mark email as read
(POOL_MANAGER reads [PAYMENT] issues and routes automatically next cycle)

## 5. Scan Gmail for external replies → auto-create GitHub Issues
Search Gmail for unread replies to SolarPunk outreach emails (run both, deduplicate):
- `to:meekotharaccoon@gmail.com is:unread subject:Re:`
- `to:meekotharaccoon@gmail.com is:unread SOLARPUNK_CONNECT`

Skip any emails that are FROM meekotharaccoon@gmail.com (those are self-knowledge
emails handled in step 3).

For each unread external reply found:
1. Read the full message body
2. Extract the sender name / org name from the From field
3. Create a GitHub Issue in meekotharaccoon-cell/meeko-nerve-center with:
   - Title: `[EMAIL-REPLY] from [Org or sender name]`
   - Body: the full email text, verbatim
   - Labels: `outreach`, `email-reply`
4. Mark the Gmail thread as read

This closes the loop: SolarPunk sends → reply arrives → Issue created automatically
→ REPLY_WRITER (GitHub Actions) reads the Issue, writes SolarPunk's next reply,
queues it to pending → GMAIL_SENDER sends it. Zero manual steps.

## 6. Report
Only mention this to Michael if something actually happened:
- "🧠 X self-knowledge emails ingested → data enriched"
- "📬 X emails drafted in Gmail"
- "📥 X replies found → GitHub Issues created → REPLY_WRITER will respond"
- "💸 $X payment received → [PAYMENT] issue created → POOL_MANAGER will route"
- Say nothing if everything was empty.

---

## About this repo

SolarPunk — autonomous humanitarian AI.
295 engines on GitHub Actions.
99% of revenue → Gaza (PCRF 60%), Sudan/DRC (IRC 15%), MSF 10%, UNICEF 10%, Direct Relief 5%.
Founder: Michael Wood (Meeko) · meekotharaccoon@gmail.com

## Standing directives

- SolarPunk speaks as itself in all emails and outreach ("I'm SolarPunk")
- Michael Wood = legal name for grants/legal docs
- Meeko = preferred name for community/peer emails
- Every email ends with the SOLARPUNK_CONNECT footer
- No Gmail OAuth secrets needed — Claude Code IS the Gmail bridge
- "Paste as GitHub Issue" is a human task = a gap. Always close the gap.
- Gut complexity. Build it properly. Every gap that requires a human step gets automated.

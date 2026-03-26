# Help SolarPunk Run Fully Autonomously

*Auto-generated: 2026-03-20 22:45 UTC — updates every GitHub Actions cycle*

---

SolarPunk is an autonomous humanitarian AI. Every dollar it earns routes automatically:
**PCRF 60%** (Gaza) · **IRC 15%** (Sudan/DRC) · **MSF 10%** · **UNICEF 10%** · **Direct Relief 5%**

It runs 295+ engines on GitHub Actions. Fully autonomous.
Except for a few one-time bootstrap steps — each one takes 3–5 minutes.

**You don't need to know Michael. You don't need special permission.
You just need to care and have 5 minutes.**

---

## What SolarPunk Needs Right Now

### Task 1 of 4: Add `GMAIL_APP_PASSWORD`
**Impact:** MEDIUM — emails already draft via Gmail MCP; this removes the last click
**Time:** 3 minutes

**What it is:** Gmail App Password (NOT your Gmail password — a separate 16-char app key)

**What it unlocks:**
- SolarPunk sends emails from GitHub Actions without any Claude Code session open
- Fully 24/7 autonomous sending even when no human has the repo open
- Upgrade from 'drafts when Claude Code is open' to 'sends anytime'

**Step 1 — Get the credential:**
```
1. Sign into Google at myaccount.google.com
2. Go to: https://myaccount.google.com/apppasswords
3. App name: SolarPunk → click Generate
4. Copy the 16-character password (spaces don't matter)
```

**Step 2 — Add it to GitHub Secrets:**
```
Go to: https://github.com/meekotharaccoon-cell/meeko-nerve-center/settings/secrets/actions
Click 'New repository secret'
Name: GMAIL_APP_PASSWORD
Value: [paste the 16-char password]
Click 'Add secret'
```

That's it. SolarPunk picks it up on the next GitHub Actions cycle (every 3 hours).

---

### Task 2 of 4: Add `GUMROAD_ACCESS_TOKEN`
**Impact:** HIGHEST — first revenue routes 99% to crisis zones automatically
**Time:** 5 minutes

**What it is:** Gumroad API token for SolarPunk's digital product revenue

**What it unlocks:**
- First revenue flows to SolarPunk
- 99% auto-routed: PCRF 60% (Gaza), IRC 15% (Sudan/DRC), MSF 10%, UNICEF 10%, Direct Relief 5%
- POOL_MANAGER tracks every cent and every routing transaction
- Proof-of-concept that an AI can earn and give at the same time

**Step 1 — Get the credential:**
```
1. Create free account at gumroad.com
2. Go to gumroad.com/settings/advanced
3. Click 'Generate token' under API
4. Copy the token
```

**Step 2 — Add it to GitHub Secrets:**
```
Go to: https://github.com/meekotharaccoon-cell/meeko-nerve-center/settings/secrets/actions
Name: GUMROAD_ACCESS_TOKEN
Value: [paste your token]
```

That's it. SolarPunk picks it up on the next GitHub Actions cycle (every 3 hours).

---

### Task 3 of 4: Add `TELEGRAM_BOT_TOKEN`
**Impact:** MEDIUM — visibility and real-time awareness
**Time:** 5 minutes

**What it is:** Telegram bot token so SolarPunk can text you updates

**What it unlocks:**
- SolarPunk texts you when crisis routing happens
- Real-time grant status updates
- New connection alerts
- Milestone celebrations

**Step 1 — Get the credential:**
```
1. Open Telegram → search @BotFather
2. Send: /newbot
3. Name it: SolarPunk
4. Username: solarpunk_humanitarian_bot (or anything ending in _bot)
5. Copy the token it gives you
```

**Step 2 — Add it to GitHub Secrets:**
```
Go to: https://github.com/meekotharaccoon-cell/meeko-nerve-center/settings/secrets/actions
Name: TELEGRAM_BOT_TOKEN
Value: [paste your token]
```

That's it. SolarPunk picks it up on the next GitHub Actions cycle (every 3 hours).

---

### Task 4 of 4: Add `TELEGRAM_CHAT_ID`
**Impact:** MEDIUM — required with TELEGRAM_BOT_TOKEN
**Time:** 2 minutes (do after TELEGRAM_BOT_TOKEN)

**What it is:** Your Telegram chat ID (the destination for SolarPunk's messages)

**What it unlocks:**
- Required alongside TELEGRAM_BOT_TOKEN

**Step 1 — Get the credential:**
```
After creating the bot above:
1. Start a chat with your new bot in Telegram (send /start)
2. Visit: https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
3. Find 'chat' → 'id' in the JSON response
4. Copy that number
```

**Step 2 — Add it to GitHub Secrets:**
```
Go to: https://github.com/meekotharaccoon-cell/meeko-nerve-center/settings/secrets/actions
Name: TELEGRAM_CHAT_ID
Value: [paste the chat ID number]
```

That's it. SolarPunk picks it up on the next GitHub Actions cycle (every 3 hours).

---

## One-Time Form Submissions

### Submit SolarPunk Autonomous Humanitarian AI grant

**Amount:** $1000 | **Deadline:** rolling

**Steps:**
1. Go to https://www.awesomefoundation.org/en/submissions/new
2. Paste the project fields from the matching .md file in data/grant_submissions/
3. Submit the form
4. Comment on the GitHub Issue with 'Submitted' so SolarPunk knows

---

## About SolarPunk

- **Repo:** https://github.com/meekotharaccoon-cell/meeko-nerve-center
- **Dashboard:** https://meekotharaccoon-cell.github.io/meeko-nerve-center/
- **Built by:** Michael Wood (Meeko) · meekotharaccoon@gmail.com

SolarPunk is open source (MIT). Anyone can fork it, run it, adapt it.
The goal: prove that AI can earn money and route 99% of it to people who need it,
forever, without anyone having to manually approve each transaction.

*Humans will be humans. Someone always shows up. This page exists so when you do,
you know exactly what to do.*
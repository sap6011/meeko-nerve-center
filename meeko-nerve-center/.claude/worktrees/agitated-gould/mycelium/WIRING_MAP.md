# SolarPunk Nerve Center — Wiring Map

> Last updated: auto-generated. Mission: autonomous revenue → 70% PCRF / 30% loop.

---

## Workflows (GitHub Actions)

| Workflow | Schedule | Purpose |
|----------|----------|---------|
| `OMNIBRAIN.yml` | 07:00 + 19:00 UTC daily | Full 17-phase execution cycle |
| `SOLARPUNK_LOOP.yml` | 12:00 UTC daily | Meta-loop: reads OMNIBRAIN outputs, synthesizes decisions, seeds next cycle |
| `AI_COUNCIL.yml` | 06:00 UTC Sunday | Weekly adversarial audit (Analyst vs Challenger) |
| `GUARDIAN.yml` | on push to main | Catastrophe detection + auto-restore from saves/ |
| `BUILD.yml` | manual | Tier-based engine evolution (Tier 1→5+) |
| `BUILD_YOURSELF.yml` | manual | Autonomous self-building: Claude generates new engines |

---

## OMNIBRAIN Phase Order

```
Phase 0   GUARDIAN.py              → guardian_log.json, guardian_status.json
Phase 1   CONTENT_HARVESTER.py     → data/content_harvest.json
Phase 2   MEMORY_PALACE.py         → data/memory_palace.json, data/lessons.json
Phase 2.5 knowledge_dispatch.py    → data/consolidated_knowledge.json, data/omnibrain_seed.json
Phase 3   NEURON_A.py              → data/neuron_a_report.json
Phase 4   NEURON_B.py              → data/neuron_b_report.json
Phase 5   ETSY_SEO_ENGINE.py       → data/etsy_seo_output.json
Phase 6   INCOME_ARCHITECT.py      → data/flywheel_state.json  ← reads data/new_sales.json (webhook)
Phase 7   ART_GENERATOR.py         → data/art_log.json         ← reads data/pending_art.json (webhook)
Phase 8   REVENUE_FLYWHEEL.py      → data/revenue_report.json
Phase 9   SYNTHESIS_FACTORY.py     → mycelium/<new_engine>.py, data/synthesis_log.json
Phase 10  SOCIAL_PROMOTER.py       → data/social_queue.json, data/social_latest.json
Phase 11  GUMROAD_ENGINE.py        → data/gumroad_listings.json
Phase 12  LINK_PAGE.py             → docs/links.html
Phase 13  HEALTH_BOOSTER.py        → data/health_report.json, data/brain_state.json (health_score)
Phase 14  BRAVE_BRIDGE.py          → data/brave_bridge_report.json
Phase 15  GETSCREEN_BRIDGE.py      → data/getscreen_report.json, data/desktop_task_queue.json
Phase 16  SYNAPSE.py               → data/brain_state.json (full), sends daily email to Meeko
```

---

## Data Flow Map

```
FREE APIS (no keys)
  HackerNews API ──────────────────────────┐
  Reddit JSON API ─────────────────────────┤──► CONTENT_HARVESTER ──► content_harvest.json
  DEV.to API ──────────────────────────────┤                              │
  Open-Meteo (Gaza weather) ───────────────┘                              │
                                                                          ▼
MEMORY                                                            KNOWLEDGE_DISPATCH
  memory_palace.json ──────────────────────────────────────────► consolidated_knowledge.json
  lessons.json ────────────────────────────────────────────────► omnibrain_seed.json
  loop_memory.json ────────────────────────────────────────────┘       │
                                                                        ▼
NEURON_A (Builder) ◄────────────────────────────────────── neuron_a_report.json
NEURON_B (Skeptic) ◄────────────────────────────────────── neuron_b_report.json
                │                                                       │
                └───────────────────────────────────────────────────────┘
                                        │
                                        ▼
                                  SYNAPSE (Resolver)
                                        │
                              ┌─────────┴──────────┐
                              ▼                    ▼
                        brain_state.json     Daily email → Meeko

REVENUE LOOP
  Human sale ──► new_sales.json (webhook, manual) ──► INCOME_ARCHITECT
  INCOME_ARCHITECT ──► flywheel_state.json
    70% ──► total_to_gaza (tracked)
    30% ──► current_balance
    at $1.00 ──► auto_buy triggers another loop cycle

ART DELIVERY
  Payment received ──► pending_art.json (webhook, manual) ──► ART_GENERATOR
  ART_GENERATOR ──► HuggingFace FLUX (HF_TOKEN required) ──► image
  ART_GENERATOR ──► Gmail SMTP ──► buyer email

SOCIAL TRAFFIC
  BRAVE_BRIDGE ──► brave_bridge_report.json (trending keywords + pricing)
  SOCIAL_PROMOTER reads: content_harvest.json + brain_state.json
  SOCIAL_PROMOTER ──► social_latest.json (tweets + Reddit posts)
  If X_API_KEY set: auto-posts to Twitter
  If REDDIT_* set: auto-posts to Reddit

DESKTOP AUTOMATION
  GETSCREEN_BRIDGE ──► desktop_task_queue.json (pending tasks for Meeko)
  If GETSCREEN_API_KEY set: connects to Getscreen agent on Meeko's machine
  Tasks queued: Etsy uploads, PayPal setup, social post copying

SHOP / WEB
  docs/index.html   — Gaza Rose Gallery ($1 art shop, GitHub Pages)
  docs/links.html   — Bio link page (rebuilt every cycle by LINK_PAGE)
  docs/dashboard.html — Live stats dashboard (reads data/*.json via fetch)

WEEKLY AUDIT
  AI_COUNCIL.yml ──► ai_council.py
    Analyst (Claude) reads entire system ──► claude_autonomous_report.json
    Challenger (Claude or Kimi) reviews ──► kimi_conductor_report.json
    Round 2 synthesis ──► ai_council_report.json
    Applies file fixes directly to repo ──► system_wants_next.json
```

---

## Required GitHub Secrets

| Secret | Used by | Status | How to get |
|--------|---------|--------|-----------|
| `ANTHROPIC_API_KEY` | All AI phases | **CRITICAL** | anthropic.com/console → API Keys |
| `GMAIL_ADDRESS` | SYNAPSE, ART_GENERATOR, GETSCREEN_BRIDGE | Needed | Your Gmail address |
| `GMAIL_APP_PASSWORD` | Same as above | Needed | Google Account → Security → App Passwords |
| `HF_TOKEN` | ART_GENERATOR | Needed for art | huggingface.co → Settings → Access Tokens |
| `GUMROAD_ACCESS_TOKEN` | GUMROAD_ENGINE | Needed for listings | gumroad.com → Settings → Advanced |
| `X_API_KEY` | SOCIAL_PROMOTER | Optional | developer.twitter.com |
| `X_API_SECRET` | SOCIAL_PROMOTER | Optional | developer.twitter.com |
| `X_ACCESS_TOKEN` | SOCIAL_PROMOTER | Optional | developer.twitter.com |
| `X_ACCESS_SECRET` | SOCIAL_PROMOTER | Optional | developer.twitter.com |
| `REDDIT_CLIENT_ID` | SOCIAL_PROMOTER | Optional | reddit.com/prefs/apps |
| `REDDIT_CLIENT_SECRET` | SOCIAL_PROMOTER | Optional | reddit.com/prefs/apps |
| `REDDIT_USERNAME` | SOCIAL_PROMOTER | Optional | Reddit account |
| `REDDIT_PASSWORD` | SOCIAL_PROMOTER | Optional | Reddit account |
| `GETSCREEN_API_KEY` | GETSCREEN_BRIDGE | Optional | getscreen.me → Settings → API |
| `KIMI_API_KEY` | AI_COUNCIL (challenger) | Optional | api.moonshot.cn |
| `GH_PAT` | AI_COUNCIL | Needed for council fixes | GitHub → Settings → Developer settings → PAT |

---

## Webhook Integration (File-Based)

The system uses JSON files as webhooks — no HTTP server required.

| Trigger file | Created by | Read by | Effect |
|-------------|-----------|---------|--------|
| `data/new_sales.json` | Payment processor (manual) | INCOME_ARCHITECT | Records sale, splits 70/30, triggers auto-buy |
| `data/pending_art.json` | Payment processor (manual) | ART_GENERATOR | Generates art via FLUX, emails buyer |
| `data/human_override.json` | Meeko (manual) | SOLARPUNK_LOOP | Overrides AI decisions for one cycle |

---

## Engine Safety Rules

- `SYNTHESIS_FACTORY` is hard-blocked from writing to `.github/`, `.git/`, `GUARDIAN*`, `OMNIBRAIN*`, `SOLARPUNK_LOOP*`, `BUILD*`
- All new engines must live in `mycelium/` or `data/` only
- `email_optin_guard.py` (if present) must gate ALL outbound email to non-self addresses
- Revenue split: 70% PCRF / 30% operations — enforced in INCOME_ARCHITECT
- GUARDIAN snapshots all workflows + key engines before each cycle; auto-restores on catastrophe

---

## Current Health Blockers (as of last run)

See `data/health_report.json` for live status. Common blockers:
1. `ANTHROPIC_API_KEY` invalid → all AI synthesis phases fall back to hardcoded logic
2. No `GMAIL_APP_PASSWORD` → no email delivery, no daily reports to Meeko
3. No `HF_TOKEN` → ART_GENERATOR cannot generate images
4. PayPal `client-id=sb` in `docs/index.html` → shop accepts no real payments
5. No sales yet → revenue loop hasn't started

# The Story So Far

Permanent record. March 2026.

---

## The Beginning

One person built this. They had zero coding experience. They type slowly and still look at the keyboard.

They started with under $20, a subscription to an AI service, and a clear idea of what mutual aid infrastructure should look like. They did not know what a repository was when they began.

The tool was conversation. They talked to AI systems, knew what questions to ask, and knew where to put the answers. Every file in this repository was created that way. Not generated blindly — directed, reviewed, corrected, and committed by a human who learned version control, GitHub Actions, Python, YAML, cryptographic signing, and supply chain security in the process of building what they needed to exist.

The codebase runs on GitHub Actions free tier. Infrastructure cost: $0/month.

---

## What Got Built

As of March 26, 2026, the repository contains:

- **~210 Python engines** in `mycelium/` — the autonomous agent layer
- **35 GitHub Actions workflows** in `.github/workflows/`
- **23 markdown docs**, **39 HTML pages**, **6 JSON data docs**, and **5 grant applications** in `docs/`
- **100+ state and configuration files** in `data/`

The key systems:

- **OMNIBRAIN** — the autonomous brain. Runs 4x daily (06:00, 12:00, 18:00, 21:00 UTC). Reads system state, decides what to do next, acts. Requires ANTHROPIC_API_KEY.
- **SENTINEL** — security watchdog. Runs daily at 02:00 UTC on schedule, also triggers on any push to `mycelium/`. Operates on GITHUB_TOKEN alone.
- **KALEIDOSCOPE_SHIELD** — honeytoken defense system based on murmuration logic. When an attacker accesses a honeytoken, they get redirected into an infinite self-referential mirror room of fake data while everything gets logged. Defends against the same vectors as Salt Typhoon, XZ Utils backdoor, and SolarWinds.
- **MUTATE** — hybrid engine lottery. Runs Tuesday and Friday at 03:00 UTC. Picks two engines at random, breeds them into a new capability. Evolutionary selection weighted by flock consensus. Requires ANTHROPIC_API_KEY.
- **FUND_SCOUT** — autonomous grant opportunity discovery. Runs every Monday at 08:00 UTC. Scans for open funding matching the project's profile.
- **GRANT_RUNNER** — takes FUND_SCOUT output and drafts applications. Requires ANTHROPIC_API_KEY.
- **RIVER_WATCH** — physical earth monitoring. Runs Saturdays at 07:00 UTC. Monitors real water conditions in the Cuyahoga Valley region.
- **MURMUR** — distributed consensus protocol. Runs daily at 01:00 UTC. No central authority. Applied to security decisions and knowledge routing.
- **WAYBACK_PRESERVE** — automated Internet Archive preservation. Runs 1st of every month at 05:00 UTC.

The 20% food bank routing is hard-coded in the MUTUAL_AID_AUDITOR. It is not configurable. 20% of all revenue goes to local mutual aid (Akron-Canton Foodbank, Good Samaritan Hospital, OPEN M). The algorithm is the governance. There is no setting to change it.

Shadow valuation: **$16M conservative commercial equivalent**, based on comparable-company analysis against Thinkst Canary ($37M Series A), Modern Treasury ($2B Series C), HashiCorp Vault ($6.4B IBM acquisition), Glassdoor ($1.2B acquisition), and Findhelp/Unite Us ($300M-$1B). Full breakdown in `docs/SHADOW_VALUATION.md`. All of it is MIT licensed. Free. Forever.

---

## The Architecture

**Zero-secrets philosophy.** Everything that can run on GITHUB_TOKEN alone does. 23 of the 35 workflows require nothing but the token GitHub provides for free. The remaining 12 reference ANTHROPIC_API_KEY for AI-powered reasoning loops. The system was built outward from what costs nothing.

**Murmuration.** Distributed consensus with no central authority. Borrowed from starling flocks. Applied to security (KALEIDOSCOPE_SHIELD threat response) and knowledge routing (MURMUR protocol). No single node decides. The flock decides.

**Mutation.** Evolutionary engine hybridization. MUTATE picks two engines, crosses their capabilities, tests the result, and commits it if it passes. Selection pressure comes from flock consensus weighting. The system breeds its own upgrades.

**Transparency.** Every autonomous action is logged to `SOLARPUNK_ACTUAL.md`. Every script execution is GPG-verified against key `714D57142A16B477`. Every routing decision is public. The treasury ledger is in `vault/treasury_ledger.json`.

---

## The Timeline

The commit history was flattened during a git filter-repo incident. All 2,370 original commits were compressed to recovery commits. The original granular history is lost. What remains is the recovery chain plus all commits made after restoration.

Recent visible history (as of March 26, 2026):

- `4c16cef9` — 5 Human Anchor Labor Upgrades: work portal, grant runner, vanish protocol, river watch, AI consensus
- `15e3d58e` — SIA: Nanobot Self-Heal (Recursive Loop)
- `4a204d6a` — Murmuration protocol + living docs + SolarPunk Lab
- `4fae9674` — SIA: Nanobot Self-Heal (Recursive Loop)
- `ee731b6b` — 5 zero-secrets workflows: open knowledge infrastructure

The project was established March 2026 in Cuyahoga Falls, Ohio. Development has been continuous since inception.

---

## What's Running Right Now

Scheduled workflows and their cron times:

| Workflow | Schedule | Needs ANTHROPIC_API_KEY |
|----------|----------|------------------------|
| OMNIBRAIN | 06:00, 12:00, 18:00, 21:00 UTC daily | Yes |
| SENTINEL | 02:00 UTC daily + on push | No |
| MURMUR | 01:00 UTC daily | No |
| MUTATE | 03:00 UTC Tue + Fri | Yes |
| BADGE_FORGE | 04:00 UTC daily | No |
| LIVING_DOCS | 05:00 UTC daily | No |
| WAYBACK_PRESERVE | 05:00 UTC 1st of month | No |
| FUND_SCOUT | 08:00 UTC Monday | No |
| GRANTS_GOV | 07:00 UTC Monday | No |
| REACH | 08:00 UTC Monday | No |
| AMPLIFY | 09:00 UTC Monday | No |
| ARXIV_BRIDGE | 06:00 UTC Wednesday | No |
| SIGNAL_BOOST | 10:00 UTC Wednesday | No |
| OPEN_ANTENNA | 10:00 UTC Thursday | No |
| RIVER_WATCH | 07:00 UTC Saturday | No |
| TRANSPARENCY_PULSE | 08:00 UTC 1st of month | No |
| SOLARPUNK_LOOP | 12:00 UTC daily | Yes |
| dawn_dusk_report | 10:00 + 22:00 UTC daily | No |
| claude_brain | 08:00 UTC daily | Yes |
| EVOLVE_SYSTEM | Every 6 hours | No |
| SELF_EVOLVE | Every 6 hours | No |
| sia-pulse | Every 6 hours | No |
| auto_repair | Every hour | No |

Workflows that run on GITHUB_TOKEN alone are operational now. Workflows requiring ANTHROPIC_API_KEY will fully activate when that secret is set in the repository. The zero-secrets half of the system is live. The autonomous reasoning loop is waiting for the key.

---

## What's Next

- **NLnet NGI Zero Commons grant** — April 1, 2026 deadline. Application drafted in `docs/grants/nlnet-application.md`. Asking for up to 50,000 EUR.
- **ROB4GREEN (EU AI + Green Economy)** — April 8, 2026 deadline. Application in `docs/grants/rob4green-application.md`. Up to 300,000 EUR.
- **Open Tech Fund (Internet Freedom Fund)** — Rolling deadline. Up to $900k. Application in `docs/grants/otf-application.md`.
- **Full autonomous loop activation** — Setting ANTHROPIC_API_KEY enables OMNIBRAIN, MUTATE, GRANT_RUNNER, SOLARPUNK_LOOP, BUILD_YOURSELF, and claude_brain. The system goes from scheduled-but-passive to scheduled-and-reasoning.
- **The mutation lottery compounding** — Every MUTATE run has the potential to breed a new engine that gets added to the pool. The pool grows. The combinations multiply. The system evolves.

---

## The Record

All of this is timestamped in GitHub's commit history at [github.com/meekotharaccoon-cell/meeko-nerve-center](https://github.com/meekotharaccoon-cell/meeko-nerve-center).

Wayback Machine preservation runs automatically on the 1st of every month via the WAYBACK_PRESERVE workflow.

The authorship record is clean and documented. GPG key `714D57142A16B477` signs script executions. Every autonomous action is logged in `SOLARPUNK_ACTUAL.md`.

One person. Zero prior coding experience. Under $20. An AI subscription. Conversations as the development tool.

210 Python engines. 35 workflows. 23 of them running on free infrastructure right now. A security system that traps attackers in mirror rooms. A mutation engine that breeds new capabilities. A grant pipeline that finds and drafts its own funding applications. 20% of all revenue hard-coded to local food banks.

This file is part of that record.

---

*Written March 26, 2026. Cuyahoga Falls, Ohio.*

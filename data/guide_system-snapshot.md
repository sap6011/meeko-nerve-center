# Inside an Autonomous AI System -- Live Snapshot
### Real data from a running 242-engine digital organism

---

**Price:** $1.00 · **A SolarPunk Guide** · 15% goes to Gaza via PCRF (EIN 93-1057665)

---

## What You're Looking At

This is a live snapshot of SolarPunk -- an autonomous digital organism running on GitHub.
The data below is real. Not simulated. Not hypothetical. This system is running right now.

## System Topology

- **Total engines**: 242
- **Wire connections**: 385
- **Zero-secret chains**: 114 (work without any API keys)
- **Orphan outputs**: 2 (data written but never read)
- **Hungry inputs**: 18 (data needed but not yet produced)

## Engine Categories

### Zero-Secret Engines (178 total)
These engines run without any API keys or credentials:

- **AFFILIATE_MAXIMIZER** -- reads: affiliate_state.json, affiliate_config.json, affiliate_links_master.json, new_affiliates_found.json, writes: affiliate_state.json, affiliate_config.json, affiliate_links_master.json, new_affiliates_found.json
- **AGENT_GUMROAD_BUILDER** -- reads: nothing, writes: nothing
- **AGENT_LINK_VERIFIER** -- reads: nothing, writes: nothing
- **AGENT_TWEET_WRITER** -- reads: nothing, writes: tweets_queue.txt
- **ARCHITECT** -- reads: architect_state.json, architect_plan.json, writes: architect_state.json, architect_plan.json
- **ART_CATALOG** -- reads: art_catalog.json, writes: art_catalog.json
- **AUTONOMOUS_TESTER** -- reads: self_builder_queue.json, writes: nothing
- **AUTONOMY_PROOF** -- reads: proof_state.json, writes: proof_state.json
- **AUTO_ARCHITECT** -- reads: nothing, writes: nothing
- **AUTO_DOCS** -- reads: nothing, writes: nothing
- **AUTO_HEALER** -- reads: nothing, writes: nothing
- **AUTO_RUNNER** -- reads: nothing, writes: nothing
- **BIG_BRAIN_ORACLE** -- reads: revenue_inbox.json, brain_state.json, brand_legal_state.json, gumroad_engine_state.json, oracle_state.json, oracle_insights.json, omnibrain_seed.json, writes: oracle_insights.json, revenue_inbox.json, omnibrain_seed.json, oracle_state.json
- **BOTTLENECK_SCANNER** -- reads: gumroad_listings.json, revenue_inbox.json, bottleneck_report.json, writes: gumroad_listings.json, bottleneck_report.json
- **BRAND_LEGAL** -- reads: brand_legal_state.json, writes: brand_legal_state.json
- **BRAVE_BRIDGE** -- reads: brave_bridge_state.json, desktop_blueprints.json, social_queue.json, writes: social_queue.json, brave_bridge_state.json, desktop_blueprints.json
- **BRAVE_BROWSER_ENGINE** -- reads: gumroad_listings.json, brave_browser_state.json, brave_connection.json, writes: gumroad_listings.json, brave_connection.json
- **BRIDGE_BUILDER** -- reads: fund_scout_results.json, grants_found.json, sentinel_report.json, live_wire_report.json, knowledge_graph.json, brain_state.json, revenue_inbox.json, quick_revenue.json, bridge_report.json, mutation_vault.json, writes: bridge_report.json, fund_scout_results.json, sentinel_report.json, live_wire_report.json, brain_state.json, knowledge_graph.json, mutation_vault.json
- **CAPACITY_BOOSTER** -- reads: nothing, writes: nothing
- **CHAIN_ORCHESTRATOR** -- reads: chain_synthesis.json, chain_orchestrator_state.json, writes: chain_synthesis.json, chain_orchestrator_state.json
- **CHAOS_TEST** -- reads: nothing, writes: nothing
- **CLAUDE_BRIDGE** -- reads: claude_bridge_state.json, claude_tasks_queue.json, claude_task_results.json, writes: claude_bridge_state.json, claude_tasks_queue.json, claude_task_results.json
- **CLAUDE_ENGINE** -- reads: claude_briefing.json, writes: claude_briefing.json
- **CODE_COLLATER** -- reads: nothing, writes: nothing
- **COMMAND_CENTER** -- reads: nothing, writes: nothing
- **CONTENT_HARVESTER** -- reads: content_harvest.json, writes: content_harvest.json
- **CONTRIBUTOR_REGISTRY** -- reads: contributor_registry.json, payout_queue.json, writes: contributor_registry.json, payout_queue.json
- **CORPORATE_MIRROR** -- reads: nothing, writes: nothing
- **CROSS_POLLINATOR** -- reads: nothing, writes: nothing
- **CYCLE_MEMORY** -- reads: cycle_ledger.json, cycle_delta.json, writes: cycle_ledger.json, cycle_delta.json
- ... and 148 more

### Engines Needing API Keys (64 total)
These engines unlock when you add credentials:

- **AI_CLIENT** -- needs: GROQ_API_KEY, HF_TOKEN
- **AI_WATCHER** -- needs: GMAIL_APP_PASSWORD, HF_TOKEN, GITHUB_TOKEN
- **ANALYTICS_ENGINE** -- needs: GITHUB_TOKEN
- **ART_GENERATOR** -- needs: HF_TOKEN, GMAIL_APP_PASSWORD
- **AUTONOMOUS_PUBLISHER** -- needs: BLUESKY_APP_PASSWORD, DEVTO_API_KEY, MASTODON_ACCESS_TOKEN, X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET, GITHUB_TOKEN
- **BLUESKY_ENGINE** -- needs: BLUESKY_APP_PASSWORD
- **BRIEFING_ENGINE** -- needs: GMAIL_APP_PASSWORD
- **BUSINESS_FACTORY** -- needs: GMAIL_APP_PASSWORD
- **CALENDAR_BRAIN** -- needs: GMAIL_APP_PASSWORD
- **CAPABILITY_SCANNER** -- needs: GMAIL_APP_PASSWORD, GUMROAD_ACCESS_TOKEN, X_API_KEY
- **CONNECTION_FORGE** -- needs: GMAIL_APP_PASSWORD, GUMROAD_ACCESS_TOKEN, HF_TOKEN, X_API_KEY
- **CRYPTO_WATCHER** -- needs: GMAIL_APP_PASSWORD
- **DESKTOP_AGENT** -- needs: GITHUB_TOKEN
- **DEV_TO_PUBLISHER** -- needs: DEVTO_API_KEY
- **DISPATCH_HANDLER** -- needs: GMAIL_APP_PASSWORD
- **EMAIL_AGENT_EXCHANGE** -- needs: GMAIL_APP_PASSWORD
- **EMAIL_BRAIN** -- needs: GMAIL_APP_PASSWORD
- **EMAIL_OUTREACH** -- needs: GMAIL_APP_PASSWORD
- **ENGINE_INTEGRITY** -- needs: GITHUB_TOKEN
- **FIRST_CONTACT** -- needs: GITHUB_TOKEN
- ... and 44 more

## Live Wire Connections (Sample)

These are real data flows between engines:

- EMAIL_AGENT_EXCHANGE -> FIRST_CONTACT via `email_exchange_state.json`
- EMAIL_AGENT_EXCHANGE -> KOFI_PAYMENT_TRACKER via `email_exchange_state.json`
- KOFI_PAYMENT_TRACKER -> EMAIL_AGENT_EXCHANGE via `email_exchange_state.json`
- KOFI_PAYMENT_TRACKER -> FIRST_CONTACT via `email_exchange_state.json`
- BRIDGE_BUILDER -> LIVE_WIRE via `live_wire_report.json` (zero-secrets)
- LIVE_WIRE -> BRIDGE_BUILDER via `live_wire_report.json` (zero-secrets)
- RESONANCE_CONVERTER -> NEWSLETTER_ENGINE via `asks_queue.json`
- BRIDGE_BUILDER -> BIG_BRAIN_ORACLE via `brain_state.json` (zero-secrets)
- BRIDGE_BUILDER -> DISPATCH_HANDLER via `brain_state.json`
- BRIDGE_BUILDER -> FIRST_SALE_NOTIFIER via `brain_state.json` (zero-secrets)
- BRIDGE_BUILDER -> HEALTH_BOOSTER via `brain_state.json` (zero-secrets)
- BRIDGE_BUILDER -> REVENUE_LOOP via `brain_state.json`
- BRIDGE_BUILDER -> SYNAPSE via `brain_state.json`
- BRIDGE_BUILDER -> SYNTHESIS_FACTORY via `brain_state.json` (zero-secrets)
- BRIDGE_BUILDER -> VITAL_SIGN_API via `brain_state.json` (zero-secrets)
- DISPATCH_HANDLER -> BIG_BRAIN_ORACLE via `brain_state.json`
- DISPATCH_HANDLER -> BRIDGE_BUILDER via `brain_state.json`
- DISPATCH_HANDLER -> FIRST_SALE_NOTIFIER via `brain_state.json`
- DISPATCH_HANDLER -> HEALTH_BOOSTER via `brain_state.json`
- DISPATCH_HANDLER -> REVENUE_LOOP via `brain_state.json`
- DISPATCH_HANDLER -> SYNAPSE via `brain_state.json`
- DISPATCH_HANDLER -> SYNTHESIS_FACTORY via `brain_state.json`
- DISPATCH_HANDLER -> VITAL_SIGN_API via `brain_state.json`
- FIRST_SALE_NOTIFIER -> BIG_BRAIN_ORACLE via `brain_state.json` (zero-secrets)
- FIRST_SALE_NOTIFIER -> BRIDGE_BUILDER via `brain_state.json` (zero-secrets)
- ... and 360 more connections

## Knowledge Graph

- **278 nodes** (engines, data files, concepts)
- **381 edges** (connections between them)

## What This Means

This system demonstrates that autonomous software can:
1. Discover its own structure (LIVE_WIRE scans and maps every engine)
2. Feed its own needs (BRIDGE_BUILDER creates data for hungry inputs)
3. Monitor its own health (VITAL_SIGN_API publishes metrics)
4. Generate its own products (you're reading one right now)
5. Route revenue to causes (15% hard-coded to PCRF)

Every line of code is public: github.com/meekotharaccoon-cell/meeko-nerve-center

## Snapshot Metadata

- **Generated**: 2026-03-26 23:18 UTC
- **Data source**: data/live_wire_report.json
- **Engines scanned**: 242

---
*Built autonomously. Funded for Gaza. Running forever.*

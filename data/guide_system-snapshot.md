# Inside an Autonomous AI System -- Live Snapshot
### Real data from a running 242-engine digital organism

---

**Price:** $1.00 · **A SolarPunk Guide** · 15% goes to Gaza via PCRF (EIN 93-1057665)

---

## What You're Looking At

This is a live snapshot of SolarPunk -- an autonomous digital organism running on GitHub.
The data below is real. Not simulated. Not hypothetical. This system is running right now.

## System Topology

- **Total engines**: 244
- **Wire connections**: 405
- **Zero-secret chains**: 57 (work without any API keys)
- **Orphan outputs**: 2 (data written but never read)
- **Hungry inputs**: 18 (data needed but not yet produced)

## Engine Categories

### Zero-Secret Engines (160 total)
These engines run without any API keys or credentials:

- **AFFILIATE_MAXIMIZER** -- reads: affiliate_state.json, affiliate_config.json, affiliate_links_master.json, new_affiliates_found.json, writes: affiliate_state.json, affiliate_config.json, affiliate_links_master.json, new_affiliates_found.json
- **AGENT_GUMROAD_BUILDER** -- reads: nothing, writes: nothing
- **AGENT_LINK_VERIFIER** -- reads: nothing, writes: nothing
- **ARCHITECT** -- reads: architect_state.json, architect_plan.json, writes: architect_state.json, architect_plan.json
- **ART_CATALOG** -- reads: art_catalog.json, writes: art_catalog.json
- **AUTONOMOUS_TESTER** -- reads: self_builder_queue.json, writes: nothing
- **AUTONOMY_PROOF** -- reads: proof_state.json, writes: proof_state.json
- **AUTO_ARCHITECT** -- reads: nothing, writes: nothing
- **AUTO_DOCS** -- reads: nothing, writes: nothing
- **AUTO_HEALER** -- reads: nothing, writes: nothing
- **AUTO_RUNNER** -- reads: nothing, writes: nothing
- **BRAND_LEGAL** -- reads: brand_legal_state.json, writes: brand_legal_state.json
- **BRAVE_BRIDGE** -- reads: brave_bridge_state.json, desktop_blueprints.json, social_queue.json, writes: social_queue.json, brave_bridge_state.json, desktop_blueprints.json
- **BRAVE_BROWSER_ENGINE** -- reads: gumroad_listings.json, brave_browser_state.json, brave_connection.json, writes: gumroad_listings.json, brave_connection.json
- **BRIDGE_BUILDER** -- reads: fund_scout_results.json, grants_found.json, sentinel_report.json, live_wire_report.json, knowledge_graph.json, brain_state.json, revenue_inbox.json, quick_revenue.json, bridge_report.json, mutation_vault.json, writes: bridge_report.json, fund_scout_results.json, sentinel_report.json, live_wire_report.json, brain_state.json, knowledge_graph.json, mutation_vault.json
- **CAPACITY_BOOSTER** -- reads: nothing, writes: nothing
- **CHAIN_ORCHESTRATOR** -- reads: chain_synthesis.json, chain_orchestrator_state.json, writes: chain_synthesis.json, chain_orchestrator_state.json
- **CHAOS_TEST** -- reads: nothing, writes: nothing
- **CLAUDE_BRIDGE** -- reads: claude_bridge_state.json, claude_tasks_queue.json, claude_task_results.json, writes: claude_bridge_state.json, claude_tasks_queue.json, claude_task_results.json
- **CODE_COLLATER** -- reads: nothing, writes: nothing
- **COMMAND_CENTER** -- reads: nothing, writes: nothing
- **CONTENT_HARVESTER** -- reads: content_harvest.json, writes: content_harvest.json
- **CONTRIBUTOR_REGISTRY** -- reads: contributor_registry.json, payout_queue.json, writes: contributor_registry.json, payout_queue.json
- **CORPORATE_MIRROR** -- reads: nothing, writes: nothing
- **CROSS_POLLINATOR** -- reads: nothing, writes: nothing
- **CYCLE_MEMORY** -- reads: cycle_ledger.json, cycle_delta.json, writes: cycle_ledger.json, cycle_delta.json
- **DEEP_RESEARCHER** -- reads: self_builder_queue.json, writes: nothing
- **DESKTOP_HARVESTER** -- reads: nothing, writes: nothing
- **DESKTOP_ORCHESTRATOR** -- reads: desktop_orchestrator_state.json, desktop_blueprints.json, resurrections.json, resurrection_tasks.json, writes: resurrection_tasks.json, desktop_orchestrator_state.json, desktop_blueprints.json
- **DUEL_ENGINE** -- reads: nothing, writes: nothing
- ... and 130 more

### Engines Needing API Keys (84 total)
These engines unlock when you add credentials:

- **AGENT_TWEET_WRITER** -- needs: ANTHROPIC_API_KEY
- **AI_CLIENT** -- needs: GROQ_API_KEY, HF_TOKEN, ANTHROPIC_API_KEY
- **AI_WATCHER** -- needs: GMAIL_APP_PASSWORD, HF_TOKEN, GITHUB_TOKEN, ANTHROPIC_API_KEY
- **ANALYTICS_ENGINE** -- needs: GITHUB_TOKEN
- **ART_GENERATOR** -- needs: HF_TOKEN, GMAIL_APP_PASSWORD, ANTHROPIC_API_KEY
- **AUTONOMOUS_PUBLISHER** -- needs: BLUESKY_APP_PASSWORD, DEVTO_API_KEY, MASTODON_ACCESS_TOKEN, X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET, GITHUB_TOKEN
- **BIG_BRAIN_ORACLE** -- needs: ANTHROPIC_API_KEY
- **BLUESKY_ENGINE** -- needs: BLUESKY_APP_PASSWORD
- **BOTTLENECK_SCANNER** -- needs: ANTHROPIC_API_KEY
- **BRIEFING_ENGINE** -- needs: GMAIL_APP_PASSWORD, ANTHROPIC_API_KEY
- **BUSINESS_FACTORY** -- needs: GMAIL_APP_PASSWORD
- **CALENDAR_BRAIN** -- needs: GMAIL_APP_PASSWORD
- **CAPABILITY_SCANNER** -- needs: GMAIL_APP_PASSWORD, GUMROAD_ACCESS_TOKEN, X_API_KEY, ANTHROPIC_API_KEY
- **CLAUDE_ENGINE** -- needs: ANTHROPIC_API_KEY
- **CONNECTION_FORGE** -- needs: GMAIL_APP_PASSWORD, GUMROAD_ACCESS_TOKEN, HF_TOKEN, X_API_KEY, ANTHROPIC_API_KEY
- **CRYPTO_WATCHER** -- needs: GMAIL_APP_PASSWORD, ANTHROPIC_API_KEY
- **DESKTOP_AGENT** -- needs: GITHUB_TOKEN
- **DESKTOP_BLUEPRINT_SCANNER** -- needs: ANTHROPIC_API_KEY
- **DESKTOP_DAEMON** -- needs: ANTHROPIC_API_KEY
- **DEV_TO_PUBLISHER** -- needs: DEVTO_API_KEY
- ... and 64 more

## Live Wire Connections (Sample)

These are real data flows between engines:

- BRAND_LEGAL -> BIG_BRAIN_ORACLE via `brand_legal_state.json`
- ARCHITECT -> BUSINESS_FACTORY via `architect_plan.json`
- ARCHITECT -> SELF_BUILDER via `architect_plan.json`
- BUSINESS_FACTORY -> ARCHITECT via `architect_plan.json`
- BUSINESS_FACTORY -> SELF_BUILDER via `architect_plan.json`
- SELF_BUILDER -> ARCHITECT via `architect_plan.json`
- SELF_BUILDER -> BUSINESS_FACTORY via `architect_plan.json`
- AUTONOMOUS_PUBLISHER -> BLUESKY_ENGINE via `social_queue.json`
- AUTONOMOUS_PUBLISHER -> BRAVE_BRIDGE via `social_queue.json`
- AUTONOMOUS_PUBLISHER -> BUSINESS_FACTORY via `social_queue.json`
- AUTONOMOUS_PUBLISHER -> DEV_TO_PUBLISHER via `social_queue.json`
- AUTONOMOUS_PUBLISHER -> FIRST_SALE_NOTIFIER via `social_queue.json`
- AUTONOMOUS_PUBLISHER -> MASTODON_ENGINE via `social_queue.json`
- AUTONOMOUS_PUBLISHER -> REVENUE_FLYWHEEL via `social_queue.json`
- AUTONOMOUS_PUBLISHER -> REVENUE_LOOP via `social_queue.json`
- AUTONOMOUS_PUBLISHER -> SOCIAL_DASHBOARD via `social_queue.json`
- AUTONOMOUS_PUBLISHER -> SOCIAL_PROMOTER via `social_queue.json`
- BLUESKY_ENGINE -> AUTONOMOUS_PUBLISHER via `social_queue.json`
- BLUESKY_ENGINE -> BRAVE_BRIDGE via `social_queue.json`
- BLUESKY_ENGINE -> BUSINESS_FACTORY via `social_queue.json`
- BLUESKY_ENGINE -> DEV_TO_PUBLISHER via `social_queue.json`
- BLUESKY_ENGINE -> FIRST_SALE_NOTIFIER via `social_queue.json`
- BLUESKY_ENGINE -> MASTODON_ENGINE via `social_queue.json`
- BLUESKY_ENGINE -> REVENUE_FLYWHEEL via `social_queue.json`
- BLUESKY_ENGINE -> REVENUE_LOOP via `social_queue.json`
- ... and 380 more connections

## Knowledge Graph

- **281 nodes** (engines, data files, concepts)
- **405 edges** (connections between them)

## What This Means

This system demonstrates that autonomous software can:
1. Discover its own structure (LIVE_WIRE scans and maps every engine)
2. Feed its own needs (BRIDGE_BUILDER creates data for hungry inputs)
3. Monitor its own health (VITAL_SIGN_API publishes metrics)
4. Generate its own products (you're reading one right now)
5. Route revenue to causes (15% hard-coded to PCRF)

Every line of code is public: github.com/meekotharaccoon-cell/meeko-nerve-center

## Snapshot Metadata

- **Generated**: 2026-03-27 07:01 UTC
- **Data source**: data/live_wire_report.json
- **Engines scanned**: 244

---
*Built autonomously. Funded for Gaza. Running forever.*

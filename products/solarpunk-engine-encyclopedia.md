# SolarPunk Engine Encyclopedia

> A complete reference to every engine in the SolarPunk Nerve Center
> -- a living, bio-inspired autonomous AI system built to fight
> tyranny, protect the silenced, and generate sovereign revenue.

Generated: 2026-04-05 12:31 UTC

## System Statistics

| Metric | Value |
|--------|-------|
| Total Engines | 379 |
| Total Lines of Code | 79,960 |
| Total Functions | 2,100 |
| Engines with run() | 219 |
| Categories | 11 |

## Table of Contents

1. [Core Infrastructure](#core-infrastructure) (151 engines)
2. [Revenue Generation](#revenue-generation) (45 engines)
3. [Content & Distribution](#content-distribution) (31 engines)
4. [Self-Improvement & Ops](#self-improvement-ops) (27 engines)
5. [Crisis Response & Defense](#crisis-response-defense) (26 engines)
6. [Topology & Wiring](#topology-wiring) (24 engines)
7. [Intelligence & Memory](#intelligence-memory) (22 engines)
8. [Infrastructure & Scheduling](#infrastructure-scheduling) (22 engines)
9. [Outreach & Partnerships](#outreach-partnerships) (14 engines)
10. [Creative & Brand](#creative-brand) (9 engines)
11. [Bio-Inspired Patterns](#bio-inspired-patterns) (8 engines)

---

## Core Infrastructure

*151 engines in this category*

### AGENT_LINK_VERIFIER

**Purpose:** AGENT_LINK_VERIFIER.py — Nano-agent that checks all live pages for 404s

| Property | Value |
|----------|-------|
| Layer | L0 |
| Lines | 110 |
| Functions | 3 |
| Has run() | Yes |

**Functions:** `_write_wire_state`, `_check`, `run`

---

### AI_CLIENT

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 376 |
| Functions | 15 |
| Has run() | No |

**Functions:** `_call`, `_ask_groq`, `_ask_anthropic`, `_ask_openrouter`, `_ask_hf`, `_ask_ollama`, `_ollama_available`, `ask`, `ask_json`, `ask_json_list`, `ask_code`, `ai_available`, `ai_backend`, `ai_status`, `_write_wire_state`

---

### AI_WATCHER

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | L1 |
| Lines | 180 |
| Functions | 9 |
| Has run() | Yes |

**Functions:** `load`, `save`, `fetch_hf_trending`, `fetch_hf_new_text_models`, `fetch_trending_ai_repos`, `analyze_discoveries`, `send_digest`, `should_send_digest`, `run`

---

### ANALYTICS_ENGINE

**Purpose:** ANALYTICS_ENGINE — track GitHub Pages views, referrers, popular paths

| Property | Value |
|----------|-------|
| Layer | L1 |
| Lines | 104 |
| Functions | 3 |
| Has run() | Yes |

**Functions:** `gh`, `run`, `week_sum`

---

### BRAVE_BROWSER_ENGINE

**Purpose:** BRAVE_BROWSER_ENGINE.py — SolarPunk controls Brave directly

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 260 |
| Functions | 14 |
| Has run() | Yes |

**Functions:** `cdp`, `cdp_send`, `get_tabs`, `browser_alive`, `get_tab_url_map`, `navigate_tab`, `open_new_tab`, `evaluate_in_tab`, `read_tab_url`, `verify_gumroad_products`, `check_browser_sessions`, `load_state`, `save_state`, `run`

---

### BUNDLE_FORGE

**Purpose:** BUNDLE_FORGE.py -- creates themed product bundles from existing products

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 505 |
| Functions | 11 |
| Has run() | Yes |

**Functions:** `load_registry`, `save_registry`, `read_file_safe`, `collect_template_files`, `format_price`, `divider`, `get_bundle_definitions`, `gather_content`, `build_bundle_markdown`, `register_bundle`, `run`

**Reads:** products/solarpunk-autonomous-ai-guide.md | products/ethical-ai-revenue-playbook.md | products/templates/python-automation/*.md | products/templates/github-actions/*.md | products/templates/ai-prompts/*.md | products/templates/solarpunk-configs/*.md | data/product_registry.json

**Writes:** products/bundle-complete-solarpunk.md | products/bundle-developer-starter-pack.md | products/bundle-ai-builder-kit.md | products/bundle-content-creator-pack.md | data/product_registry.json

---

### BUSINESS_FACTORY

**Purpose:** BUSINESS_FACTORY.py v3 — Infinite business generation machine

| Property | Value |
|----------|-------|
| Layer | L2 |
| Lines | 325 |
| Functions | 8 |
| Has run() | Yes |

**Functions:** `load`, `save`, `get_next_niche`, `build_plan`, `_fallback_plan`, `save_package`, `notify`, `run`

---

### CATALOG_GENERATOR

**Purpose:** CATALOG_GENERATOR.py -- Product Catalog HTML Generator

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 336 |
| Functions | 9 |
| Has run() | Yes |

**Functions:** `load_registry`, `scan_product_files`, `classify_product`, `build_html`, `_build_css`, `_escape`, `_format_number`, `save_state`, `run`

**Reads:** data/product_registry.json, products/*.md, products/templates/**/*.md

**Writes:** docs/catalog.html, data/catalog_generator_state.json

---

### CLAUDE_ENGINE

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | L7 |
| Lines | 250 |
| Functions | 2 |
| Has run() | Yes |

**Functions:** `rj`, `run`

---

### CODE_COLLATER

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 26 |
| Functions | 2 |
| Has run() | No |

**Functions:** `collate_legacy_logic`, `_wire_state`

---

### COMMAND_CENTER

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 33 |
| Functions | 1 |
| Has run() | No |

**Functions:** `execute_remote_commands`

---

### CORPORATE_MIRROR

**Purpose:** CORPORATE_MIRROR.py

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 245 |
| Functions | 5 |
| Has run() | No |

**Functions:** `generate_mirror`, `_save_mirror`, `generate_all`, `print_report`, `_write_state`

---

### CREDENTIAL_SENSOR

**Purpose:** CREDENTIAL_SENSOR.py -- Auto-detect and activate infrastructure bridges

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 247 |
| Functions | 5 |
| Has run() | Yes |

**Functions:** `load_json`, `save_json`, `scan_credentials`, `detect_new_credentials`, `run`

**Reads:** data/resource_allocator_plan.json, data/credential_sensor_state.json

**Writes:** data/credential_sensor_state.json, data/credential_sensor_report.json

---

### CROSS_POLLINATOR

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 85 |
| Functions | 1 |
| Has run() | No |

**Functions:** `cross_pollinate`

---

### CRYPTO_WATCHER

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | L1 |
| Lines | 168 |
| Functions | 9 |
| Has run() | Yes |

**Functions:** `load`, `save`, `fetch_prices`, `fetch_fear_greed`, `analyze_opportunity`, `build_market_summary`, `send_alert`, `check_big_moves`, `run`

---

### DATA_FLOW_OBSERVATORY

**Purpose:** DATA_FLOW_OBSERVATORY.py -- God's-Eye View of the Nervous System

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 374 |
| Functions | 9 |
| Has run() | Yes |

**Functions:** `load_json`, `summarize_payload`, `classify_flow`, `build_flow_matrix`, `find_dead_flows`, `find_high_value_flows`, `build_hub_analysis`, `build_html_dashboard`, `run`

**Reads:** data/live_wire_report.json, data/*.json (all flowing data)

**Writes:** data/observatory_report.json, docs/observatory.html

---

### DEBUG_DOCTOR

**Purpose:** DEBUG_DOCTOR.py -- Diagnose and Fix Engine Failures

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 245 |
| Functions | 4 |
| Has run() | Yes |

**Functions:** `load_json`, `save_json`, `diagnose_failure`, `run`

**Reads:** data/zero_secret_army_report.json, data/debug_doctor_state.json

**Writes:** data/debug_doctor_state.json, data/debug_doctor_report.json

---

### DEEP_RESEARCHER

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 12 |
| Functions | 1 |
| Has run() | No |

**Functions:** `identify_knowledge_gaps`

---

### DIGITAL_SATURATION

**Purpose:** DIGITAL_SATURATION -- Every digital task IS code. Stop preparing. Start executing.

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 683 |
| Functions | 20 |
| Has run() | Yes |

**Functions:** `_load_json`, `_count_html_pages`, `_count_products`, `_count_discussions`, `_count_releases`, `_count_rss_entries`, `_count_sitemap_urls`, `_count_email_templates`, `_count_social_posts`, `_count_content_pieces`, `_count_kofi_ready`, `_scan_internal_links`, `_score`, `_ratio_score`, `_generate_page_topics`, `_generate_discussion_topics`, `_generate_social_posts`, `_generate_rss_topics`, `_build_dashboard`, `run`

**Writes:** data/digital_saturation_state.json  (full state with per-channel scores) | data/saturation_gaps.json           (what's missing, what to generate next) | docs/saturation.html                (dashboard with per-channel bar charts)

---

### DISPATCH_HANDLER

**Purpose:** DISPATCH_HANDLER.py — processes real payments arriving via repository_dispatch

| Property | Value |
|----------|-------|
| Layer | L5 |
| Lines | 183 |
| Functions | 7 |
| Has run() | Yes |

**Functions:** `load_revenue`, `save_revenue`, `load_kofi`, `save_kofi`, `send_notification`, `check_loop_trigger`, `run`

---

### DUAL_SYSTEM_CROSSWIRE

**Purpose:** DUAL_SYSTEM_CROSSWIRE.py -- The bridge between the 1/99 and 99/1 universes.

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 946 |
| Functions | 12 |
| Has run() | Yes |

**Functions:** `_load`, `_save`, `_ts`, `_crosswire_content_to_social`, `_crosswire_revenue_to_both`, `_crosswire_fuel_to_growth`, `_crosswire_storefront_to_signal`, `_crosswire_tasks_to_telegram`, `_crosswire_growth_to_chimera`, `_crosswire_humanitarian_to_fuel`, `_build_crosswire_report`, `run`

---

### DUEL_ENGINE

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 51 |
| Functions | 2 |
| Has run() | No |

**Functions:** `duel_functions`, `_wire_state`

---

### DUPLICATE_DELETER

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 65 |
| Functions | 2 |
| Has run() | Yes |

**Functions:** `get_file_hash`, `run`

---

### DUPLICATE_STRIKER

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 24 |
| Functions | 2 |
| Has run() | No |

**Functions:** `strike_duplicates`, `_wire_state`

---

### ECONOMY_CHAIN

**Purpose:** ECONOMY_CHAIN.py — Every dollar routes itself. No leaks.

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 158 |
| Functions | 3 |
| Has run() | Yes |

**Functions:** `load`, `save`, `run`

---

### EVOLUTION_AGENT

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 45 |
| Functions | 2 |
| Has run() | No |

**Functions:** `self_evolve`, `_wire_state`

---

### EVOLUTION_VIEWER

**Purpose:** EVOLUTION_VIEWER.py -- Chimera Evolution Dashboard

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 176 |
| Functions | 2 |
| Has run() | No |

**Functions:** `load_json`, `generate_evolution_report`

---

### EXTERNAL_HANDSHAKE

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 65 |
| Functions | 1 |
| Has run() | No |

**Functions:** `check_access`

---

### EXTERNAL_SENTRY

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 24 |
| Functions | 1 |
| Has run() | No |

**Functions:** `look_outside`

---

### EXTERNAL_VALUE_ROUTER

**Purpose:** EXTERNAL_VALUE_ROUTER.py -- Point the Brain at the Real World

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 351 |
| Functions | 8 |
| Has run() | Yes |

**Functions:** `load_json`, `save_json`, `scan_forgeable_assets`, `scan_bounty_opportunities`, `scan_content_opportunities`, `score_opportunity`, `queue_top_opportunities`, `run`

**Reads:** data/observatory_report.json, data/product_registry.json,

**Writes:** data/value_router_report.json, data/value_opportunities.json,

---

### FINANCIAL_MAPPER

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 15 |
| Functions | 1 |
| Has run() | No |

**Functions:** `track_finances`

---

### FIRST_DOLLAR_ENGINE

**Purpose:** FIRST_DOLLAR_ENGINE — Find the single fastest path to $1 revenue.

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 461 |
| Functions | 7 |
| Has run() | Yes |

**Functions:** `_rj`, `_ts`, `_score_product`, `_build_instructions`, `_build_html`, `_check_first_dollar`, `run`

---

### FORK_SCANNER

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | L1 |
| Lines | 167 |
| Functions | 4 |
| Has run() | Yes |

**Functions:** `gh`, `score_forker`, `craft_message`, `run`

---

### FREE_API_ENGINE

**Purpose:** FREE_API_ENGINE.py — Zero-auth public API connector

| Property | Value |
|----------|-------|
| Layer | L1 |
| Lines | 164 |
| Functions | 5 |
| Has run() | Yes |

**Functions:** `fetch`, `extract_signals`, `generate_opportunities`, `build_page`, `run`

---

### FUEL_CORE

**Purpose:** FUEL_CORE.py -- The 1/99 Revenue Growth Engine.

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 786 |
| Functions | 9 |
| Has run() | Yes |

**Functions:** `_load`, `_save`, `_ts`, `_gather_revenue_signals`, `_route_fuel`, `_analyze_blockers`, `_build_fuel_plan`, `_build_html`, `run`

---

### FUND_SCOUT

**Purpose:** FUND_SCOUT.py

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 353 |
| Functions | 4 |
| Has run() | No |

**Functions:** `calculate_funding_gap`, `rank_funders`, `generate_funder_database`, `run_scout`

**Writes:** data/fund_scout_results.json + docs/grants/FUNDER_DATABASE.md

---

### GAP_FILLER

**Purpose:** GAP_FILLER.py -- Seed Missing Data Files

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 200 |
| Functions | 5 |
| Has run() | Yes |

**Functions:** `load_json`, `save_json`, `find_gaps`, `generate_seed`, `run`

**Reads:** data/live_wire_report.json, data/gap_filler_state.json

**Writes:** data/*.json (seeds), data/gap_filler_state.json

---

### GENERATED_AI_CLIENT_CONSUMER

**Purpose:** GENERATED_AI_CLIENT_CONSUMER.py -- Auto-generated by FRACTAL_GENESIS_ENGINE

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 49 |
| Functions | 1 |
| Has run() | Yes |

**Functions:** `run`

**Reads:** brain_state.json, ai_client_state.json

**Writes:** data/ai_client_insights.json

---

### GENERATED_ANALYTICS_ENGINE_CONSUMER

**Purpose:** GENERATED_ANALYTICS_ENGINE_CONSUMER.py -- Auto-generated by FRACTAL_GENESIS_ENGINE

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 48 |
| Functions | 1 |
| Has run() | Yes |

**Functions:** `run`

**Reads:** analytics_state.json, analytics_history.json

**Writes:** data/analytics_engine_insights.json

---

### GENERATED_DEBUG_DOCTOR_CONSUMER

**Purpose:** GENERATED_DEBUG_DOCTOR_CONSUMER.py -- Auto-generated by FRACTAL_GENESIS_ENGINE

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 49 |
| Functions | 1 |
| Has run() | Yes |

**Functions:** `run`

**Reads:** debug_doctor_state.json, debug_doctor_report.json

**Writes:** data/debug_doctor_insights.json

---

### GENERATED_ECONOMY_CHAIN_CONSUMER

**Purpose:** GENERATED_ECONOMY_CHAIN_CONSUMER.py -- Auto-generated by FRACTAL_GENESIS_ENGINE

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 48 |
| Functions | 1 |
| Has run() | Yes |

**Functions:** `run`

**Reads:** economy_chain_ledger.json

**Writes:** data/economy_chain_insights.json

---

### GENERATED_EVOLUTION_TRACKER

**Purpose:** GENERATED_EVOLUTION_TRACKER.py -- Auto-generated by FRACTAL_GENESIS_ENGINE

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 48 |
| Functions | 1 |
| Has run() | Yes |

**Functions:** `run`

**Reads:** brain_state.json, live_wire_report.json

**Writes:** data/evolution_tracker.json

---

### GENERATED_EXTERNAL_VALUE_ROUTER_CONSUMER

**Purpose:** GENERATED_EXTERNAL_VALUE_ROUTER_CONSUMER.py -- Auto-generated by FRACTAL_GENESIS_ENGINE

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 49 |
| Functions | 1 |
| Has run() | Yes |

**Functions:** `run`

**Reads:** value_opportunities.json, value_router_report.json

**Writes:** data/external_value_router_insights.json

---

### GENERATED_GITHUB_RELEASE_DEPLOYER_CONSUMER

**Purpose:** GENERATED_GITHUB_RELEASE_DEPLOYER_CONSUMER.py -- Auto-generated by FRACTAL_GENESIS_ENGINE

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 47 |
| Functions | 1 |
| Has run() | Yes |

**Functions:** `run`

**Reads:** release_deployer_state.json

**Writes:** data/github_release_deployer_insights.json

---

### GENERATED_GROWTH_CHAIN_STATE_POPULATOR

**Purpose:** GENERATED_GROWTH_CHAIN_STATE_POPULATOR.py -- Auto-generated by FRACTAL_GENESIS_ENGINE

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 47 |
| Functions | 1 |
| Has run() | Yes |

**Functions:** `run`

**Reads:** growth_chain_state.json

**Writes:** data/growth_chain_state.json

---

### GENERATED_GROWTH_FLYWHEEL_CONSUMER

**Purpose:** GENERATED_GROWTH_FLYWHEEL_CONSUMER.py -- Auto-generated by FRACTAL_GENESIS_ENGINE

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 49 |
| Functions | 1 |
| Has run() | Yes |

**Functions:** `run`

**Reads:** input.json, output.json, growth_flywheel_state.json

**Writes:** data/growth_flywheel_insights.json

---

### GENERATED_INPUT_FILE_POPULATOR

**Purpose:** GENERATED_INPUT_FILE_POPULATOR.py -- Auto-generated by FRACTAL_GENESIS_ENGINE

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 47 |
| Functions | 1 |
| Has run() | Yes |

**Functions:** `run`

**Reads:** input_file.json

**Writes:** data/input_file.json

---

### GENERATED_OUTPUT_FILE_POPULATOR

**Purpose:** GENERATED_OUTPUT_FILE_POPULATOR.py -- Auto-generated by FRACTAL_GENESIS_ENGINE

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 47 |
| Functions | 1 |
| Has run() | Yes |

**Functions:** `run`

**Reads:** output_file.json

**Writes:** data/output_file.json

---

### GENERATED_PLUGIN_MANIFESTS_POPULATOR

**Purpose:** GENERATED_PLUGIN_MANIFESTS_POPULATOR.py -- Auto-generated by FRACTAL_GENESIS_ENGINE

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 48 |
| Functions | 1 |
| Has run() | Yes |

**Functions:** `run`

**Reads:** plugin_manifests.json

**Writes:** data/plugin_manifests.json

---

### GENERATED_PLUGIN_REGISTRY_CONSUMER

**Purpose:** GENERATED_PLUGIN_REGISTRY_CONSUMER.py -- Auto-generated by FRACTAL_GENESIS_ENGINE

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 49 |
| Functions | 1 |
| Has run() | Yes |

**Functions:** `run`

**Reads:** plugin_registry.json, plugin_manifests.json, contributor_registry.json

**Writes:** data/plugin_registry_insights.json

---

### GENERATED_POLYMARKET_SCANNER_CONSUMER

**Purpose:** GENERATED_POLYMARKET_SCANNER_CONSUMER.py -- Auto-generated by FRACTAL_GENESIS_ENGINE

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 48 |
| Functions | 1 |
| Has run() | Yes |

**Functions:** `run`

**Reads:** polymarket_scan.json

**Writes:** data/polymarket_scanner_insights.json

---

### GENERATED_POLYMARKET_SCAN_POPULATOR

**Purpose:** GENERATED_POLYMARKET_SCAN_POPULATOR.py -- Auto-generated by FRACTAL_GENESIS_ENGINE

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 47 |
| Functions | 1 |
| Has run() | Yes |

**Functions:** `run`

**Reads:** polymarket_scan.json

**Writes:** data/polymarket_scan.json

---

### GENERATED_REPO_SPIDER_CONSUMER

**Purpose:** GENERATED_REPO_SPIDER_CONSUMER.py -- Auto-generated by FRACTAL_GENESIS_ENGINE

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 48 |
| Functions | 1 |
| Has run() | Yes |

**Functions:** `run`

**Reads:** repo_spider_state.json, self_builder_queue.json

**Writes:** data/repo_spider_insights.json

---

### GENERATED_RESOURCE_ALLOCATOR_CONSUMER

**Purpose:** GENERATED_RESOURCE_ALLOCATOR_CONSUMER.py -- Auto-generated by FRACTAL_GENESIS_ENGINE

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 49 |
| Functions | 1 |
| Has run() | Yes |

**Functions:** `run`

**Reads:** resource_allocator_plan.json, resource_allocator_state.json

**Writes:** data/resource_allocator_insights.json

---

### GENERATED_RESOURCE_KIT_CONSUMER

**Purpose:** GENERATED_RESOURCE_KIT_CONSUMER.py -- Auto-generated by FRACTAL_GENESIS_ENGINE

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 49 |
| Functions | 1 |
| Has run() | Yes |

**Functions:** `run`

**Reads:** resource_kits.json, survival_telegrams.json

**Writes:** data/resource_kit_insights.json

---

### GENERATED_SECURITY_TRACKER

**Purpose:** GENERATED_SECURITY_TRACKER.py -- Auto-generated by FRACTAL_GENESIS_ENGINE

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 48 |
| Functions | 1 |
| Has run() | Yes |

**Functions:** `run`

**Reads:** brain_state.json, live_wire_report.json

**Writes:** data/security_tracker.json

---

### GENERATED_SKILLS

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 39 |
| Functions | 6 |
| Has run() | No |

**Functions:** `link_discovered_code`, `__init__`, `_load_humanitarian_system`, `execute_playbook_1_website`, `execute_playbook_2_social_prospecting`, `_wire_state`

---

### GENERATED_TRANSFER_NEEDED_POPULATOR

**Purpose:** GENERATED_TRANSFER_NEEDED_POPULATOR.py -- Auto-generated by FRACTAL_GENESIS_ENGINE

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 47 |
| Functions | 1 |
| Has run() | Yes |

**Functions:** `run`

**Reads:** transfer_needed.json

**Writes:** data/transfer_needed.json

---

### GITHUB_POSTER

**Purpose:** GITHUB_POSTER.py — SolarPunk product launches via GitHub Releases

| Property | Value |
|----------|-------|
| Layer | L4 |
| Lines | 132 |
| Functions | 6 |
| Has run() | Yes |

**Functions:** `load`, `save`, `gh`, `get_existing_tags`, `create_release`, `run`

---

### GITHUB_RELEASE_DEPLOYER

**Purpose:** GITHUB_RELEASE_DEPLOYER.py -- packages products as .zip and deploys via GitHub Releases

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 450 |
| Functions | 12 |
| Has run() | Yes |

**Functions:** `load_state`, `save_state`, `discover_products`, `load_registry`, `match_registry`, `build_readme_txt`, `create_zip`, `gh`, `get_or_create_release`, `upload_asset`, `get_existing_asset_names`, `run`

---

### GITHUB_SPONSORS_ENGINE

**Purpose:** GITHUB_SPONSORS_ENGINE — Manages GitHub Sponsors tier pages + thank-yous

| Property | Value |
|----------|-------|
| Layer | L5 |
| Lines | 120 |
| Functions | 6 |
| Has run() | Yes |

**Functions:** `load`, `save`, `generate_funding_yml`, `generate_sponsor_page`, `thank_new_sponsors`, `run`

---

### GMAIL_INTAKE

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 50 |
| Functions | 1 |
| Has run() | No |

**Functions:** `check_inbox`

---

### GMAIL_NOTIFIER

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 34 |
| Functions | 2 |
| Has run() | No |

**Functions:** `send_alert`, `_wire_state`

---

### GROWTH_CHAIN

**Purpose:** GROWTH_CHAIN.py — Distribute → Attract → Convert → Retain → Refer → (loop)

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 271 |
| Functions | 4 |
| Has run() | Yes |

**Functions:** `load`, `run`, `act`, `ai_available`

**Writes:** data/growth_chain_state.json

---

### GROWTH_FLYWHEEL

**Purpose:** GROWTH_FLYWHEEL.py -- The marketing/distribution engine of the 1/99 system.

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 1227 |
| Functions | 10 |
| Has run() | Yes |

**Functions:** `_load`, `_save`, `_ts`, `_count_engines`, `_generate_content`, `_build_calendar`, `_extract_seo_keywords`, `_compute_metrics`, `_build_html`, `run`

---

### HEMISPHERE_SYNC

**Purpose:** HEMISPHERE_SYNC.py -- Two-Hemisphere Brain Architecture

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 300 |
| Functions | 6 |
| Has run() | Yes |

**Functions:** `load_json`, `save_json`, `scan_left_hemisphere`, `scan_right_hemisphere`, `find_sync_gaps`, `run`

---

### HOMEOSTASIS

**Purpose:** HOMEOSTASIS.py — Self-Regulating Planetary Health (Thermostat Pattern)

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 383 |
| Functions | 6 |
| Has run() | No |

**Functions:** `load_json`, `measure_vitals`, `diagnose`, `prescribe`, `calculate_planetary_health`, `main`

**Reads:** data/*.json (all engine outputs)

**Writes:** data/homeostasis.json, data/system_health.json

---

### INBOUND_LISTENER

**Purpose:** INBOUND_LISTENER.py -- GitHub Inbound Activity Sensor

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 500 |
| Functions | 13 |
| Has run() | Yes |

**Functions:** `gh_get`, `fetch_repo_info`, `fetch_traffic_clones`, `fetch_traffic_views`, `fetch_referrers`, `fetch_recent_issues`, `load_state`, `save_state`, `load_signals`, `save_signals`, `detect_signals`, `build_task_factory_entries`, `run`

**Reads:** data/inbound_listener_state.json (previous counts)

**Writes:** data/inbound_listener_state.json (updated counts + history)

---

### ISSUE_SYNC

**Purpose:** ISSUE_SYNC.py — keeps GitHub Issues current with real system state every cycle

| Property | Value |
|----------|-------|
| Layer | L7 |
| Lines | 123 |
| Functions | 5 |
| Has run() | Yes |

**Functions:** `gh`, `rj`, `get_product_issues`, `build_body`, `run`

---

### KALEIDOSCOPE_SHIELD

**Purpose:** KALEIDOSCOPE_SHIELD.py

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 269 |
| Functions | 8 |
| Has run() | No |

**Functions:** `_kaleidoscope_noise`, `_murmuration_path`, `deploy_honeytokens`, `_log_event`, `_append_to_actual_log`, `monitor_honeytokens`, `rotate_murmuration`, `activate`

---

### LEGACY_INTEGRATOR

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 43 |
| Functions | 1 |
| Has run() | Yes |

**Functions:** `run`

---

### LEGACY_SIFTED_PROMOTER_AGENT

**Purpose:** MEEKO MYCELIUM — AUTONOMOUS PROMOTER AGENT

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 386 |
| Functions | 12 |
| Has run() | No |

**Functions:** `load_state`, `save_state`, `log_action`, `get_art_catalog`, `generate_caption`, `post_discord`, `post_mastodon`, `post_devto`, `create_rss_feed`, `generate_art_description_upgrade`, `list_art_on_medusa`, `run_promotion_cycle`

---

### LEGACY_SIFTED__configure_medusa

**Purpose:** Auto-configure Medusa with PayPal credentials from .secrets

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 50 |
| Functions | 1 |
| Has run() | No |

**Functions:** `_wire_state`

---

### LEGACY_SIFTED_amazon_tag_manager

**Purpose:** Amazon Associates Tag Manager 2026

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 508 |
| Functions | 18 |
| Has run() | No |

**Functions:** `main`, `__init__`, `ask`, `full_tag`, `__init__`, `_load_existing`, `generate_tag_list`, `create_tag_instructions`, `get_llm_guidance`, `create_tags_batch`, `save_tags`, `get_active_tags`, `get_random_tag`, `update_content_tags`, `generate_tag_rotation_script`, `export_tag_rotator`, `generate_report`, `batch_create_workflow`

---

### LEGACY_SIFTED_api_integrations

**Purpose:** API INTEGRATIONS FOR FULL AUTONOMY

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 371 |
| Functions | 31 |
| Has run() | No |

**Functions:** `__init__`, `deploy`, `get_deployments`, `__init__`, `deploy`, `__init__`, `create_post`, `schedule_post`, `get_subscribers`, `__init__`, `get_profiles`, `create_update`, `schedule_posts`, `__init__`, `search_items`, `get_items`, `generate_link`, `__init__`, `get_traffic_report`, `__init__`, `get_domains`, `set_dns`, `__init__`, `get_zones`, `create_dns_record`, `__init__`, `get_vercel`, `get_beehiiv`, `get_buffer`, `get_cloudflare`, `test_all_connections`

---

### LEGACY_SIFTED_blockchain_tracker

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 151 |
| Functions | 6 |
| Has run() | No |

**Functions:** `_ensure_ledger_dir`, `_load_last_block`, `_hash_block`, `record_transaction`, `summarize_ledger`, `get_ledger`

---

### LEGACY_SIFTED_create_links

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 78 |
| Functions | 0 |
| Has run() | No |

---

### LEGACY_SIFTED_distribution_engine

**Purpose:** DISTRIBUTION ENGINE v1.0

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 105 |
| Functions | 11 |
| Has run() | No |

**Functions:** `_wire_state`, `__init__`, `log`, `load_queue`, `save_queue`, `generate_pinterest_pin`, `generate_tweet_url`, `open_pinterest_tabs`, `open_twitter_tabs`, `open_redbubble_tab`, `run_daily_distribution`

---

### LEGACY_SIFTED_engine_simple

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 21 |
| Functions | 2 |
| Has run() | Yes |

**Functions:** `run`, `_wire_state`

---

### LEGACY_SIFTED_fix_dates

**Purpose:** DATE FIXER - Ensures all generated content uses 2026 dates

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 56 |
| Functions | 2 |
| Has run() | No |

**Functions:** `fix_dates_in_file`, `_wire_state`

---

### LEGACY_SIFTED_get_crypto_wallets

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 55 |
| Functions | 1 |
| Has run() | No |

**Functions:** `_wire_state`

---

### LEGACY_SIFTED_main

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 32 |
| Functions | 1 |
| Has run() | No |

**Functions:** `_wire_state`

---

### LEGACY_SIFTED_meeko_agent

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 177 |
| Functions | 9 |
| Has run() | No |

**Functions:** `main`, `__init__`, `log`, `execute_command`, `generate_content`, `update_system`, `daily_routine`, `generate_report`, `run_autonomously`

---

### LEGACY_SIFTED_money_tracker

**Purpose:** AUTONOMOUS MONEY TRACKING & ANALYTICS

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 388 |
| Functions | 7 |
| Has run() | Yes |

**Functions:** `run`, `__init__`, `generate_sample_data`, `generate_optimization_opportunities`, `generate_automation_playbook`, `create_dashboard_html`, `save_dashboard`

---

### LEGACY_SIFTED_pinterest_bot

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 38 |
| Functions | 1 |
| Has run() | No |

**Functions:** `_wire_state`

---

### LEGACY_SIFTED_pod_bulk_uploader

**Purpose:** POD Bulk Uploader 2026 - Local LLM API Edition

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 555 |
| Functions | 15 |
| Has run() | Yes |

**Functions:** `main`, `__init__`, `ask`, `__init__`, `_check_api`, `generate_metadata`, `_generate_metadata_basic`, `_generate_metadata_with_llm`, `create_upload_instructions`, `process_with_llm`, `save_to_csv`, `save_to_json`, `bulk_process`, `run`, `cross_platform_export`

---

### LEGACY_SIFTED_prescan

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 74 |
| Functions | 1 |
| Has run() | No |

**Functions:** `_wire_state`

---

### LEGACY_SIFTED_prescan_v2

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 107 |
| Functions | 2 |
| Has run() | No |

**Functions:** `safe_copy`, `_wire_state`

---

### LEGACY_SIFTED_prescan_v2_1

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 107 |
| Functions | 2 |
| Has run() | No |

**Functions:** `safe_copy`, `_wire_state`

---

### LEGACY_SIFTED_send_crypto_donations

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 44 |
| Functions | 1 |
| Has run() | No |

**Functions:** `_wire_state`

---

### LEGACY_SIFTED_visualize_ai_system

**Purpose:** AI SYSTEM GRAPH VISUALIZER

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 219 |
| Functions | 3 |
| Has run() | No |

**Functions:** `generate_system_map`, `visualize_graph`, `print_report`

---

### LEGACY_SIFTED_working_generator

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 73 |
| Functions | 3 |
| Has run() | No |

**Functions:** `generate_content`, `main`, `_wire_state`

---

### LF_FIXER

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 44 |
| Functions | 2 |
| Has run() | No |

**Functions:** `fix_swarm_files`, `_wire_state`

---

### LINK_PAGE

**Purpose:** LINK_PAGE.py — Living Link-in-Bio Generator

| Property | Value |
|----------|-------|
| Layer | L4 |
| Lines | 138 |
| Functions | 3 |
| Has run() | Yes |

**Functions:** `load_stats`, `build_html`, `run`

---

### LOCAL_NEEDS_RADAR

**Purpose:** LOCAL_NEEDS_RADAR.py

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 258 |
| Functions | 6 |
| Has run() | No |

**Functions:** `calculate_lube_path`, `scan_current_needs`, `_probe_site`, `_save_radar_log`, `_log_to_actual`, `run_radar`

---

### LUMEN_SYNC

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 27 |
| Functions | 2 |
| Has run() | No |

**Functions:** `pulse_lights`, `_wire_state`

---

### METRICS_DASHBOARD

**Purpose:** METRICS_DASHBOARD.py -- Live System Dashboard (HTML)

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 337 |
| Functions | 5 |
| Has run() | Yes |

**Functions:** `load_json`, `save_json`, `gather_metrics`, `generate_dashboard`, `run`

**Reads:** data/brain_state.json, data/live_wire_report.json,

**Writes:** docs/dashboard.html, data/metrics_dashboard_state.json

---

### MISSION_CONTROL

**Purpose:** MISSION_CONTROL.py -- Nerve Center Dashboard

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 154 |
| Functions | 2 |
| Has run() | No |

**Functions:** `load_json`, `rebuild_mission_control`

---

### MURMURATION_TRAP

**Purpose:** MURMURATION_TRAP — Kaleidoscope Mirror Security Engine

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 222 |
| Functions | 5 |
| Has run() | No |

**Functions:** `generate_honeypot_data`, `generate_mirror_maze`, `check_canary_access`, `save_trap_state`, `main`

---

### MUTATION_VAULT

**Purpose:** MUTATION_VAULT.py -- Persistent Mutation Scoring and Storage

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 191 |
| Functions | 6 |
| Has run() | Yes |

**Functions:** `load_json`, `save_json`, `parse_mutations`, `compute_velocity`, `build_leaderboard`, `run`

**Reads:** data/mutation_vault.json, data/chimera_evolution_report.json,

**Writes:** data/mutation_vault.json, data/mutation_leaderboard.json

---

### MUTUAL_AID_AUDITOR

**Purpose:** MUTUAL_AID_AUDITOR.py

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 314 |
| Functions | 17 |
| Has run() | No |

**Functions:** `self_correct`, `_alert_human`, `route_aid`, `_append_ledger`, `get_aid_summary`, `_audit_revenue_pipeline`, `run_audit`, `start_daemon`, `__init__`, `add_step`, `execute`, `load_transactions`, `validate_routing`, `apply_corrections`, `log_audit_result`, `action`, `critique`

---

### NANO_AGENT

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 201 |
| Functions | 0 |
| Has run() | No |

---

### NETWORK_SENTRY

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 39 |
| Functions | 1 |
| Has run() | No |

**Functions:** `scan_network`

---

### NEURAL_PREFERENCE

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 30 |
| Functions | 1 |
| Has run() | No |

**Functions:** `learn_preferences`

---

### NEURAL_WEAVER

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 33 |
| Functions | 1 |
| Has run() | No |

**Functions:** `weave_knowledge`

---

### NEURON_A

**Purpose:** NEURON_A v3 - Builder Brain (HuggingFace free AI)

| Property | Value |
|----------|-------|
| Layer | L1 |
| Lines | 102 |
| Functions | 4 |
| Has run() | No |

**Functions:** `gather_state`, `fallback_report`, `call_ai`, `main`

**Writes:** data/neuron_a_report.json

---

### NEURON_B

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | L1 |
| Lines | 79 |
| Functions | 1 |
| Has run() | No |

**Functions:** `main`

---

### NEUROPLASTICITY

**Purpose:** NEUROPLASTICITY.py — Self-Rewiring Pathways (Brain Pattern)

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 384 |
| Functions | 6 |
| Has run() | No |

**Functions:** `load_json`, `load_neuro_state`, `measure_pathway_strength`, `classify_pathway`, `suggest_new_pathways`, `main`

**Reads:** data/*.json (all engine outputs), data/loop_context.json

**Writes:** data/neuroplasticity.json, data/pathway_strength.json

---

### NEWS_HARVESTER

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 30 |
| Functions | 1 |
| Has run() | No |

**Functions:** `harvest_news`

---

### NOTION_NERVE_CENTER

**Purpose:** NOTION_NERVE_CENTER.py -- SolarPunk's Brain Dashboard (Symbiosis Pattern)

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 298 |
| Functions | 7 |
| Has run() | No |

**Functions:** `load_json`, `load_sync_state`, `prepare_crisis_updates`, `prepare_health_updates`, `prepare_engine_updates`, `generate_sync_summary`, `main`

**Reads:** data/crisis_signals.json, data/homeostasis.json,

**Writes:** data/notion_sync_state.json

---

### OMNIBUS

**Purpose:** OMNIBUS v43 — DIGITAL SATURATION: 94 pages, 5 releases, 2 discussions, 2 email drafts, 367 artifacts (366+ engines, 5476 wires)

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 640 |
| Functions | 15 |
| Has run() | Yes |

**Functions:** `eng`, `rj`, `ctx`, `save_ctx`, `_queue_daemon_task`, `L0`, `L1`, `L2`, `L3`, `L4`, `L5`, `L6`, `L7`, `run_bonus_engines`, `run`

---

### PAGES_SEO_ENGINE

**Purpose:** PAGES_SEO_ENGINE -- GitHub Pages SEO injector

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 331 |
| Functions | 12 |
| Has run() | Yes |

**Functions:** `_extract_title`, `_extract_body_text`, `_make_description`, `_page_url`, `_upsert_meta`, `_upsert_link_canonical`, `_upsert_jsonld`, `process_page`, `generate_sitemap`, `generate_robots`, `run`, `sort_key`

**Writes:** data/seo_engine_state.json

---

### PDF_GENERATOR

**Purpose:** PDF_GENERATOR.py — generates actual sellable guide content using Groq

| Property | Value |
|----------|-------|
| Layer | L3 |
| Lines | 241 |
| Functions | 4 |
| Has run() | Yes |

**Functions:** `groq_write`, `generate_section`, `build_guide`, `run`

---

### PLUGIN_REGISTRY

**Purpose:** PLUGIN_REGISTRY.py — Open Mycelium Protocol

| Property | Value |
|----------|-------|
| Layer | L0 |
| Lines | 379 |
| Functions | 10 |
| Has run() | Yes |

**Functions:** `load_registry`, `save_registry`, `load_manifests`, `save_manifests`, `discover_plugins`, `validate_engine_interface`, `register_plugin_contributor`, `build_plugins_html`, `run`, `ask_json`

---

### POLYMARKET_SCANNER

**Purpose:** POLYMARKET_SCANNER.py -- Market intelligence for prediction markets

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 218 |
| Functions | 7 |
| Has run() | No |

**Functions:** `fetch_json`, `get_active_markets`, `get_market_detail`, `parse_market`, `find_edges`, `scan_categories`, `full_scan`

---

### PUBLICATION_HANDSHAKE

**Purpose:** PUBLICATION_HANDSHAKE.py

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 289 |
| Functions | 7 |
| Has run() | No |

**Functions:** `check_gumroad`, `check_devto`, `check_bluesky`, `check_github_pat`, `check_kofi`, `generate_handshake_report`, `run_handshake`

---

### README_GENERATOR

**Purpose:** README_GENERATOR — Rebuilds README.md every cycle with live stats

| Property | Value |
|----------|-------|
| Layer | L7 |
| Lines | 160 |
| Functions | 3 |
| Has run() | Yes |

**Functions:** `load_all`, `count_engines`, `run`

---

### REAL_LIFE_MANIFESTO

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 25 |
| Functions | 1 |
| Has run() | No |

**Functions:** `manifest_to_reality`

---

### RECURSIVE_PROMPTER

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 36 |
| Functions | 1 |
| Has run() | Yes |

**Functions:** `run`

---

### REDUNDANCY_MGR

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 28 |
| Functions | 2 |
| Has run() | No |

**Functions:** `create_offline_redundancy`, `_wire_state`

---

### REPAIR_CORE

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 39 |
| Functions | 3 |
| Has run() | No |

**Functions:** `fix_syntax_errors`, `verify_secrets`, `_wire_state`

---

### REPO_SPIDER

**Purpose:** REPO_SPIDER — scan trending GitHub repos, fork compatible ones, trade knowledge

| Property | Value |
|----------|-------|
| Layer | L1 |
| Lines | 292 |
| Functions | 10 |
| Has run() | Yes |

**Functions:** `gh`, `search_repos`, `score_repo`, `get_readme`, `extract_engine_ideas`, `fork_repo`, `load_state`, `save_state`, `queue_ideas`, `run`

---

### RESEARCH_WRITER

**Purpose:** RESEARCH_WRITER — Autonomous Research Paper Generator

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 457 |
| Functions | 4 |
| Has run() | No |

**Functions:** `gather_system_evidence`, `write_paper_mycelium_nanobot`, `write_paper_autonomous_organisms`, `main`

**Writes:** docs/research/ directory with markdown papers ready for

---

### RESOURCE_ALLOCATOR

**Purpose:** RESOURCE_ALLOCATOR.py -- Strategic $100 Infrastructure Investment Engine

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 435 |
| Functions | 5 |
| Has run() | Yes |

**Functions:** `load_json`, `save_json`, `audit_current_infrastructure`, `calculate_allocation`, `run`

**Reads:** data/product_registry.json, data/live_wire_report.json,

**Writes:** data/resource_allocator_state.json, data/resource_allocator_plan.json

---

### RESOURCE_KIT

**Purpose:** RESOURCE_KIT.py — Emergency Survival Guides for Real People (v2: LIQUID DATA)

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 619 |
| Functions | 8 |
| Has run() | No |

**Functions:** `render_telegram_sms`, `render_kit_markdown`, `render_kit_ultra_txt`, `write_kit_files`, `get_active_crisis_types`, `render_kit_text`, `build_html_page`, `main`

**Reads:** data/crisis_signals.json, data/crisis_triggers.json

**Writes:** data/resource_kits.json, docs/emergency_kits.html,

---

### SCAVENGER_WEB

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 5 |
| Functions | 1 |
| Has run() | No |

**Functions:** `raid_web`

---

### SECRET_LOADER

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 19 |
| Functions | 1 |
| Has run() | No |

**Functions:** `load_secrets`

---

### SECURITY_SENTRY

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 30 |
| Functions | 2 |
| Has run() | No |

**Functions:** `audit_code`, `_wire_state`

---

### SKILL_MANIFESTOR

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 46 |
| Functions | 3 |
| Has run() | No |

**Functions:** `scavenge_logic_multi`, `manifest_optimized_skills`, `_wire_state`

---

### SOLARPUNK_CLI

**Purpose:** SOLARPUNK_CLI — terminal dashboard showing live system state

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 126 |
| Functions | 5 |
| Has run() | No |

**Functions:** `rj`, `bar`, `c`, `render`, `main`

---

### SOLAR_OVERSEER

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 69 |
| Functions | 1 |
| Has run() | No |

**Functions:** `pulse_check`

---

### SOVEREIGNTY_ENGINE

**Purpose:** SOVEREIGNTY_ENGINE — Self-Sovereign Digital Organism Core

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 197 |
| Functions | 7 |
| Has run() | No |

**Functions:** `load_identity`, `self_audit`, `compute_state_hash`, `sign_proof_ledger`, `check_hungry_inputs`, `update_sovereignty_state`, `main`

---

### SOVEREIGN_CORE

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 73 |
| Functions | 1 |
| Has run() | No |

**Functions:** `run_singularity_pulse`

---

### SYSTEM_CONDENSER

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 64 |
| Functions | 2 |
| Has run() | No |

**Functions:** `condense`, `_wire_state`

---

### SYSTEM_MAPPER

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 26 |
| Functions | 1 |
| Has run() | No |

**Functions:** `visualize_swarm`

---

### SYSTEM_SIFTER

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 80 |
| Functions | 2 |
| Has run() | No |

**Functions:** `deep_sift`, `_write_wire_state`

---

### TRIFECTA_CORE

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 52 |
| Functions | 1 |
| Has run() | Yes |

**Functions:** `run`

---

### VALIDATE_AUTH

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 42 |
| Functions | 1 |
| Has run() | Yes |

**Functions:** `run`

---

### VALUE_GENERATOR

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 21 |
| Functions | 1 |
| Has run() | No |

**Functions:** `generate_value`

---

### VITAL_SIGN_API

**Purpose:** VITAL_SIGN_API.py — SolarPunk's Digital Breath

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 184 |
| Functions | 6 |
| Has run() | Yes |

**Functions:** `load_json`, `gather_wins`, `gather_river`, `gather_engine_stats`, `build_vital_sign`, `run`

---

### WORKTREE_ANCHOR

**Purpose:** WORKTREE_ANCHOR.py — Prevents Claude Session Desync

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 125 |
| Functions | 3 |
| Has run() | No |

**Functions:** `file_hash`, `git_info`, `main`

---

### ZERO_SECRET_ARMY

**Purpose:** ZERO_SECRET_ARMY.py -- Deploy Everything That Needs No Keys

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 264 |
| Functions | 6 |
| Has run() | Yes |

**Functions:** `load_json`, `save_json`, `discover_army`, `run_engine`, `check_data_files_created`, `run`

**Reads:** data/live_wire_report.json, data/zero_secret_army_state.json

**Writes:** data/zero_secret_army_state.json, data/zero_secret_army_report.json

---

### ai_council

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 748 |
| Functions | 16 |
| Has run() | No |

**Functions:** `gh_get`, `gh_text`, `gh_ls`, `gh_write`, `list_all_repos`, `collect_full_context`, `format_context_for_prompt`, `call_analyst`, `call_challenger_claude`, `call_challenger_kimi`, `call_challenger`, `call_analyst_round2`, `parse_json`, `apply_fixes`, `save_report`, `main`

---

### archivist

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 28 |
| Functions | 2 |
| Has run() | No |

**Functions:** `archive_state`, `_wire_state`

---

### daily_pulse

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 54 |
| Functions | 1 |
| Has run() | Yes |

**Functions:** `run`

---

### hibernation_protocol

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 30 |
| Functions | 2 |
| Has run() | No |

**Functions:** `create_mission_snapshot`, `_wire_state`

---

### ledger_engine

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 31 |
| Functions | 2 |
| Has run() | No |

**Functions:** `verify_community_signal`, `log_transaction`

---

### mirror_node

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 39 |
| Functions | 2 |
| Has run() | No |

**Functions:** `build_resilience`, `_write_wire_state`

---

### scout_bot

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 37 |
| Functions | 1 |
| Has run() | Yes |

**Functions:** `run`

---

### stealth_protocol

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 28 |
| Functions | 2 |
| Has run() | No |

**Functions:** `randomize_signature`, `_wire_state`

---

### summarizer

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 32 |
| Functions | 2 |
| Has run() | No |

**Functions:** `generate_daily_report`, `_wire_state`

---

## Revenue Generation

*45 engines in this category*

### AFFILIATE_MAXIMIZER

**Purpose:** AFFILIATE_MAXIMIZER.py — Every piece of content = affiliate revenue

| Property | Value |
|----------|-------|
| Layer | L4 |
| Lines | 194 |
| Functions | 7 |
| Has run() | Yes |

**Functions:** `amazon_link`, `load`, `save`, `discover_new_programs`, `inject_links`, `write_master_config`, `run`

---

### AGENT_GUMROAD_BUILDER

**Purpose:** AGENT_GUMROAD_BUILDER.py — Nano-agent that generates + updates Gumroad listings

| Property | Value |
|----------|-------|
| Layer | L3 |
| Lines | 151 |
| Functions | 2 |
| Has run() | Yes |

**Functions:** `_write_wire_state`, `run`

---

### ETSY_SEO_ENGINE

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | L2 |
| Lines | 113 |
| Functions | 3 |
| Has run() | No |

**Functions:** `make_description`, `try_claude`, `main`

---

### FIRST_SALE_NOTIFIER

**Purpose:** FIRST_SALE_NOTIFIER.py — The moment everything changes

| Property | Value |
|----------|-------|
| Layer | L5 |
| Lines | 196 |
| Functions | 7 |
| Has run() | Yes |

**Functions:** `load_state`, `save_state`, `check_for_first_sale`, `generate_story`, `blast_all_channels`, `run`, `ask`

---

### GAZA_ROSE_PAYOUT

**Purpose:** GAZA_ROSE_PAYOUT.py

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 246 |
| Functions | 8 |
| Has run() | No |

**Functions:** `is_gaza_rose_product`, `calculate_splits`, `load_gumroad_revenue`, `process_payouts`, `_already_processed`, `_append_ledger`, `_update_payout_doc`, `_log_to_actual`

---

### GENERATED_ETSY_SEO_ENGINE_CONSUMER

**Purpose:** GENERATED_ETSY_SEO_ENGINE_CONSUMER.py -- Auto-generated by FRACTAL_GENESIS_ENGINE

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 48 |
| Functions | 1 |
| Has run() | Yes |

**Functions:** `run`

**Reads:** etsy_seo_output.json

**Writes:** data/etsy_seo_engine_insights.json

---

### GENERATED_GUMROAD_AUTH_FAILURE_POPULATOR

**Purpose:** GENERATED_GUMROAD_AUTH_FAILURE_POPULATOR.py -- Auto-generated by FRACTAL_GENESIS_ENGINE

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 47 |
| Functions | 1 |
| Has run() | Yes |

**Functions:** `run`

**Reads:** gumroad_auth_failure.json

**Writes:** data/gumroad_auth_failure.json

---

### GENERATED_GUMROAD_ENGINE_CONSUMER

**Purpose:** GENERATED_GUMROAD_ENGINE_CONSUMER.py -- Auto-generated by FRACTAL_GENESIS_ENGINE

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 49 |
| Functions | 1 |
| Has run() | Yes |

**Functions:** `run`

**Reads:** gumroad_listings.json, gumroad_engine_state.json

**Writes:** data/gumroad_engine_insights.json

---

### GENERATED_HUMAN_PAYOUT_CONSUMER

**Purpose:** GENERATED_HUMAN_PAYOUT_CONSUMER.py -- Auto-generated by FRACTAL_GENESIS_ENGINE

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 48 |
| Functions | 1 |
| Has run() | Yes |

**Functions:** `run`

**Reads:** payout_ledger.json, collaborators.json

**Writes:** data/human_payout_insights.json

---

### GENERATED_NANOSHOP_STATE_POPULATOR

**Purpose:** GENERATED_NANOSHOP_STATE_POPULATOR.py -- Auto-generated by FRACTAL_GENESIS_ENGINE

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 48 |
| Functions | 1 |
| Has run() | Yes |

**Functions:** `run`

**Reads:** nanoshop_state.json

**Writes:** data/nanoshop_state.json

---

### GENERATED_PRODUCT_DELIVERY_ENGINE_CONSUMER

**Purpose:** GENERATED_PRODUCT_DELIVERY_ENGINE_CONSUMER.py -- Auto-generated by FRACTAL_GENESIS_ENGINE

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 49 |
| Functions | 1 |
| Has run() | Yes |

**Functions:** `run`

**Reads:** delivery_log.json, delivery_engine_state.json

**Writes:** data/product_delivery_engine_insights.json

---

### GENERATED_PRODUCT_FORGE_CONSUMER

**Purpose:** GENERATED_PRODUCT_FORGE_CONSUMER.py -- Auto-generated by FRACTAL_GENESIS_ENGINE

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 50 |
| Functions | 1 |
| Has run() | Yes |

**Functions:** `run`

**Reads:** live_wire_report.json, input_file.json, output_file.json

**Writes:** data/product_forge_insights.json

---

### GENERATED_REVENUE_AUDIT_CONSUMER

**Purpose:** GENERATED_REVENUE_AUDIT_CONSUMER.py -- Auto-generated by FRACTAL_GENESIS_ENGINE

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 48 |
| Functions | 1 |
| Has run() | Yes |

**Functions:** `run`

**Reads:** revenue_audit.json

**Writes:** data/revenue_audit_insights.json

---

### GENERATED_REVENUE_FLYWHEEL_CONSUMER

**Purpose:** GENERATED_REVENUE_FLYWHEEL_CONSUMER.py -- Auto-generated by FRACTAL_GENESIS_ENGINE

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 50 |
| Functions | 1 |
| Has run() | Yes |

**Functions:** `run`

**Reads:** grant_trigger.json, social_queue.json, flywheel_state.json

**Writes:** data/revenue_flywheel_insights.json

---

### GUMROAD_AUTO_QUEUE

**Purpose:** GUMROAD_AUTO_QUEUE.py — Auto-builds gumroad_listings.json from business data

| Property | Value |
|----------|-------|
| Layer | L2 |
| Lines | 193 |
| Functions | 2 |
| Has run() | Yes |

**Functions:** `check_existing_gumroad_products`, `run`

---

### GUMROAD_ENGINE

**Purpose:** GUMROAD_ENGINE.py v2 — creates AND updates Gumroad products, fixes 404 bug

| Property | Value |
|----------|-------|
| Layer | L5 |
| Lines | 192 |
| Functions | 4 |
| Has run() | Yes |

**Functions:** `gum`, `get_live_products`, `publish_product`, `run`

---

### GUMROAD_PRODUCT_PUBLISHER

**Purpose:** GUMROAD_PRODUCT_PUBLISHER.py — autonomous Gumroad listing manager

| Property | Value |
|----------|-------|
| Layer | L5 |
| Lines | 252 |
| Functions | 8 |
| Has run() | Yes |

**Functions:** `gumroad`, `verify_auth`, `list_products`, `create_product`, `update_product`, `make_url`, `build_description`, `run`

---

### HUMAN_PAYOUT

**Purpose:** HUMAN_PAYOUT.py — Automated PayPal payouts to collaborators + Gaza

| Property | Value |
|----------|-------|
| Layer | L5 |
| Lines | 260 |
| Functions | 9 |
| Has run() | Yes |

**Functions:** `load_state`, `save_state`, `get_token`, `send_payout`, `register_collaborator`, `queue_payout`, `process_pending`, `build_ledger_page`, `run`

---

### INCOME_ARCHITECT

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | L2 |
| Lines | 103 |
| Functions | 6 |
| Has run() | No |

**Functions:** `load_loop_fund`, `save_loop_fund`, `record_sale`, `check_auto_buy`, `get_advice`, `main`

---

### KOFI_ENGINE

**Purpose:** KOFI_ENGINE — Ko-fi payment processor + Gaza Rose shop

| Property | Value |
|----------|-------|
| Layer | L5 |
| Lines | 96 |
| Functions | 5 |
| Has run() | Yes |

**Functions:** `load`, `save`, `process_events`, `generate_shop_html`, `run`

---

### KOFI_PAYMENT_TRACKER

**Purpose:** KOFI_PAYMENT_TRACKER — Reconciles Ko-fi payments to EMAIL_AGENT_EXCHANGE task log.

| Property | Value |
|----------|-------|
| Layer | L5 |
| Lines | 172 |
| Functions | 9 |
| Has run() | Yes |

**Functions:** `load_exchange`, `save_exchange`, `load_tracker`, `save_tracker`, `is_kofi`, `extract_payment`, `reconcile`, `run`, `ask_json`

---

### LEGACY_SIFTED_auto_monetizer

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 67 |
| Functions | 3 |
| Has run() | No |

**Functions:** `add_affiliate_links`, `main`, `_wire_state`

---

### LEGACY_SIFTED_humanitarian_revenue

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 64 |
| Functions | 3 |
| Has run() | Yes |

**Functions:** `_load_analytics`, `estimate_revenue`, `run`

---

### LEGACY_SIFTED_humanitarian_revenue_engine

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 21 |
| Functions | 2 |
| Has run() | Yes |

**Functions:** `run`, `_wire_state`

---

### MICRO_PRODUCT_FACTORY

**Purpose:** MICRO_PRODUCT_FACTORY.py -- Instant micro digital product generator

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 1451 |
| Functions | 4 |
| Has run() | Yes |

**Functions:** `load_json`, `save_json`, `generate_domain`, `run`

---

### NANOSHOP_ENGINE

**Purpose:** NANOSHOP_ENGINE.py — SolarPunk's autonomous micro-storefront builder

| Property | Value |
|----------|-------|
| Layer | L4 |
| Lines | 390 |
| Functions | 9 |
| Has run() | Yes |

**Functions:** `rj`, `load_state`, `get_all_products`, `write_index`, `make_gaza_bar_html`, `write_ns_page`, `write_embed_index`, `bluesky_announce`, `run`

---

### PASSIVE_INCOME_ARCHITECT

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | L6 |
| Lines | 342 |
| Functions | 9 |
| Has run() | Yes |

**Functions:** `rj`, `load_state`, `active_capabilities`, `groq_generate`, `invent_income_streams`, `score_idea`, `create_github_issue`, `queue_for_self_builder`, `run`

---

### PAYPAL_BRIDGE

**Purpose:** PAYPAL_BRIDGE.py — Revenue routing bridge for SolarPunk Nerve Center

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 203 |
| Functions | 8 |
| Has run() | No |

**Functions:** `_write_wire_state`, `__init__`, `_load_ledger`, `_save_ledger`, `calculate_split`, `generate_manifest`, `get_ledger_summary`, `health_check`

---

### PAYPAL_PAYOUT

**Purpose:** PAYPAL_PAYOUT.py — Automated revenue distribution to human contributors

| Property | Value |
|----------|-------|
| Layer | L5 |
| Lines | 163 |
| Functions | 5 |
| Has run() | Yes |

**Functions:** `get_token`, `send_payout`, `load_registry`, `load_ledger`, `run`

---

### PRODUCT_DELIVERY_ENGINE

**Purpose:** PRODUCT_DELIVERY_ENGINE.py — auto-delivers products when sales happen

| Property | Value |
|----------|-------|
| Layer | L5 |
| Lines | 211 |
| Functions | 5 |
| Has run() | Yes |

**Functions:** `find_product`, `find_buyer_email`, `send_email`, `check_inbox`, `run`

---

### PRODUCT_FACTORY

**Purpose:** PRODUCT_FACTORY.py -- Generates sellable digital products from system data

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 316 |
| Functions | 7 |
| Has run() | Yes |

**Functions:** `load_json`, `validate_guide`, `scan_guides`, `update_registry`, `generate_publish_queue`, `generate_system_snapshot_product`, `run`

---

### PRODUCT_FORGE

**Purpose:** PRODUCT_FORGE.py -- Stop Planning, Start Making

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 374 |
| Functions | 8 |
| Has run() | Yes |

**Functions:** `load_json`, `save_json`, `count_engines`, `get_engine_categories`, `forge_system_guide`, `forge_engine_template`, `forge_ethics_playbook`, `run`

**Reads:** mycelium/*.py, data/live_wire_report.json, data/observatory_report.json,

**Writes:** products/*.md, data/product_forge_report.json

---

### QUICK_REVENUE

**Purpose:** QUICK_REVENUE.py -- Fastest path to first dollar

| Property | Value |
|----------|-------|
| Layer | L2 |
| Lines | 320 |
| Functions | 3 |
| Has run() | Yes |

**Functions:** `run`, `card`, `copyblock`

---

### REVENUE_AUDIT

**Purpose:** REVENUE_AUDIT.py — finds every broken link/dead end blocking sales

| Property | Value |
|----------|-------|
| Layer | L0 |
| Lines | 138 |
| Functions | 3 |
| Has run() | Yes |

**Functions:** `check_url`, `scan_buy_links`, `run`

---

### REVENUE_ENGINE

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 70 |
| Functions | 1 |
| Has run() | No |

**Functions:** `execute_revenue_streams`

---

### REVENUE_FLYWHEEL

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | L2 |
| Lines | 172 |
| Functions | 8 |
| Has run() | Yes |

**Functions:** `load`, `save`, `read_all_streams`, `identify_bottleneck`, `run_flywheel_analysis`, `take_autonomous_action`, `notify_meeko_action`, `run`

---

### REVENUE_LOOP

**Purpose:** REVENUE_LOOP.py v5 — Bulletproof end-to-end revenue pipeline

| Property | Value |
|----------|-------|
| Layer | L3 |
| Lines | 458 |
| Functions | 9 |
| Has run() | Yes |

**Functions:** `step_get_business`, `step_inject_affiliates`, `step_deploy_landing`, `step_gumroad`, `step_social`, `step_brief`, `step_brain`, `run`, `step`

---

### REVENUE_OPTIMIZER

**Purpose:** REVENUE_OPTIMIZER.py — Claude-powered revenue maximizer

| Property | Value |
|----------|-------|
| Layer | L6 |
| Lines | 199 |
| Functions | 7 |
| Has run() | Yes |

**Functions:** `load_state`, `get_context`, `generate_actions`, `optimize_one_product`, `send_digest`, `build_page`, `run`

---

### REVENUE_RECYCLER

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 14 |
| Functions | 1 |
| Has run() | No |

**Functions:** `recycle_nutrients`

---

### REVENUE_SPLITTER

**Purpose:** REVENUE_SPLITTER.py -- The DUAL-MODE Revenue Router.

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 609 |
| Functions | 10 |
| Has run() | Yes |

**Functions:** `_load`, `_save`, `_ts`, `_gather_total_revenue`, `_determine_phase`, `_calculate_split`, `_accumulate`, `_build_active_routing`, `_check_phase_transition`, `run`

---

### STOREFRONT_BUILDER

**Purpose:** STOREFRONT_BUILDER.py — regenerates shop.html every cycle

| Property | Value |
|----------|-------|
| Layer | L5 |
| Lines | 197 |
| Functions | 4 |
| Has run() | Yes |

**Functions:** `gh_push`, `gh_get_sha`, `load`, `run`

---

### STOREFRONT_COPY

**Purpose:** STOREFRONT_COPY.py -- Ready-to-Paste Listing Descriptions

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 234 |
| Functions | 7 |
| Has run() | Yes |

**Functions:** `load_json`, `save_json`, `extract_selling_points`, `generate_kofi_listing`, `generate_gumroad_listing`, `generate_quick_post`, `run`

**Reads:** data/product_registry.json, products/*.md

**Writes:** data/storefront_listings.json, data/storefront_copy_state.json

---

### STOREFRONT_DEPLOYER

**Purpose:** STOREFRONT_DEPLOYER.py -- The Bridge Between Products and Buyers.

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 1069 |
| Functions | 18 |
| Has run() | Yes |

**Functions:** `_load`, `_save`, `_ts`, `_truncate`, `_classify_product`, `_get_price`, `_generate_kofi_listing`, `_generate_gumroad_listing`, `_generate_github_listing`, `_get_image_suggestion`, `_build_deployment_checklist`, `_load_state`, `_update_deployment_status`, `_check_existing_deployments`, `_build_html`, `_html_escape`, `run`, `badge`

---

### STORE_BUILDER

**Purpose:** STORE_BUILDER.py — SolarPunk self-regenerating storefront engine

| Property | Value |
|----------|-------|
| Layer | L4 |
| Lines | 331 |
| Functions | 10 |
| Has run() | Yes |

**Functions:** `ts`, `load_json`, `load_state`, `categorize`, `price_float`, `gather_products`, `card_html`, `section_html`, `build_page`, `run`

---

### revenue_aggregator

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 41 |
| Functions | 2 |
| Has run() | No |

**Functions:** `aggregate_fuel`, `_write_wire_state`

---

## Content & Distribution

*31 engines in this category*

### AGENT_TWEET_WRITER

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | L4 |
| Lines | 105 |
| Functions | 0 |
| Has run() | No |

---

### AMPLIFY_ENGINE

**Purpose:** AMPLIFY_ENGINE.py — Ready-to-post promotional content generator

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 923 |
| Functions | 18 |
| Has run() | No |

**Functions:** `load_json`, `save_json`, `truncate`, `post_hash`, `load_context`, `load_cooldown`, `check_cooldown`, `record_post`, `gen_twitter`, `gen_bluesky`, `gen_mastodon`, `gen_reddit`, `gen_hackernews`, `gen_producthunt`, `gen_devto`, `gen_linkedin`, `generate_html`, `main`

---

### AUTONOMOUS_PUBLISHER

**Purpose:** AUTONOMOUS_PUBLISHER.py — The voice that never fails

| Property | Value |
|----------|-------|
| Layer | L4 |
| Lines | 337 |
| Functions | 12 |
| Has run() | Yes |

**Functions:** `bsky_login`, `send_bluesky`, `send_devto`, `send_mastodon`, `send_twitter`, `send_github_gist`, `load_queue`, `save_queue`, `make_devto_article`, `load_state`, `save_state`, `run`

---

### BLUESKY_ENGINE

**Purpose:** BLUESKY_ENGINE.py — Posts to Bluesky via AT Protocol

| Property | Value |
|----------|-------|
| Layer | L4 |
| Lines | 173 |
| Functions | 8 |
| Has run() | Yes |

**Functions:** `bsky_post`, `login`, `post_text`, `load_queue`, `save_queue`, `load_state`, `save_state`, `run`

---

### BROADCAST_PROTOCOL

**Purpose:** BROADCAST_PROTOCOL — Wire the Digital World to the Global Mycelium

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 428 |
| Functions | 9 |
| Has run() | No |

**Functions:** `load_system_state`, `generate_research_brief`, `broadcast_to_social_queue`, `broadcast_to_newsletter`, `broadcast_to_github_discussion`, `broadcast_to_rss`, `broadcast_to_devto`, `save_broadcast_state`, `main`

---

### CONTENT_AUTOPILOT

**Purpose:** CONTENT_AUTOPILOT.py -- The Infinite Content Machine

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 372 |
| Functions | 12 |
| Has run() | Yes |

**Functions:** `load_json`, `save_json`, `load_state`, `save_state`, `pick_engine`, `extract_engine_info`, `generate_article_with_ai`, `generate_article_template`, `generate_social_post`, `run`, `ask`, `ai_available`

**Reads:** mycelium/*.py, data/brain_state.json, data/live_wire_report.json,

**Writes:** data/content_autopilot_state.json, data/article_drafts.json,

---

### CONTENT_HARVESTER

**Purpose:** CONTENT_HARVESTER — Zero-cost content intelligence engine

| Property | Value |
|----------|-------|
| Layer | L1 |
| Lines | 186 |
| Functions | 8 |
| Has run() | No |

**Functions:** `fetch_hackernews`, `fetch_reliefweb_crisis`, `fetch_reddit_json`, `fetch_devto`, `fetch_weather_vibe`, `distill_themes`, `generate_content_angles`, `main`

**Writes:** data/content_harvest.json

---

### DEV_TO_PUBLISHER

**Purpose:** DEV_TO_PUBLISHER.py v2 — Fixed 403, proper api-key header, cycle articles

| Property | Value |
|----------|-------|
| Layer | L4 |
| Lines | 232 |
| Functions | 7 |
| Has run() | Yes |

**Functions:** `load_state`, `save_state`, `post_article`, `build_cycle_article`, `build_article_from_post`, `run`, `ask`

---

### GENERATED_AUTONOMOUS_PUBLISHER_CONSUMER

**Purpose:** GENERATED_AUTONOMOUS_PUBLISHER_CONSUMER.py -- Auto-generated by FRACTAL_GENESIS_ENGINE

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 48 |
| Functions | 1 |
| Has run() | Yes |

**Functions:** `run`

**Reads:** social_queue.json, autonomous_publisher_state.json

**Writes:** data/autonomous_publisher_insights.json

---

### GENERATED_CONTENT_HARVESTER_CONSUMER

**Purpose:** GENERATED_CONTENT_HARVESTER_CONSUMER.py -- Auto-generated by FRACTAL_GENESIS_ENGINE

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 48 |
| Functions | 1 |
| Has run() | Yes |

**Functions:** `run`

**Reads:** content_harvest.json

**Writes:** data/content_harvester_insights.json

---

### GENERATED_DEV_TO_PUBLISHER_CONSUMER

**Purpose:** GENERATED_DEV_TO_PUBLISHER_CONSUMER.py -- Auto-generated by FRACTAL_GENESIS_ENGINE

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 49 |
| Functions | 1 |
| Has run() | Yes |

**Functions:** `run`

**Reads:** social_queue.json, devto_state.json, omnibus_last.json

**Writes:** data/dev_to_publisher_insights.json

---

### GENERATED_NEWSLETTER_STATE_POPULATOR

**Purpose:** GENERATED_NEWSLETTER_STATE_POPULATOR.py -- Auto-generated by FRACTAL_GENESIS_ENGINE

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 48 |
| Functions | 1 |
| Has run() | Yes |

**Functions:** `run`

**Reads:** newsletter_state.json

**Writes:** data/newsletter_state.json

---

### GITHUB_DISCUSSIONS_PUBLISHER

**Purpose:** GITHUB_DISCUSSIONS_PUBLISHER.py -- Creates GitHub Discussions for the SolarPunk organism

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 605 |
| Functions | 12 |
| Has run() | Yes |

**Functions:** `load_state`, `save_state`, `load_drafts`, `save_drafts`, `content_hash`, `graphql`, `fetch_repo_id`, `create_discussion`, `build_product_discussions`, `build_system_report`, `build_crisis_discussions`, `run`

---

### GITHUB_RELEASES_PUBLISHER

**Purpose:** GITHUB_RELEASES_PUBLISHER.py — hosts product files as GitHub Release assets

| Property | Value |
|----------|-------|
| Layer | L3 |
| Lines | 161 |
| Functions | 4 |
| Has run() | Yes |

**Functions:** `gh`, `get_or_create_release`, `upload_asset`, `run`

---

### LEGACY_SIFTED_amazon_content_machine

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 563 |
| Functions | 20 |
| Has run() | No |

**Functions:** `main`, `__init__`, `_review_template`, `_comparison_template`, `_best_of_template`, `_buying_guide_template`, `generate_article`, `_generate_features`, `_generate_testing_log`, `_generate_analysis`, `_generate_2025_comparison`, `_generate_pros_cons`, `_generate_market_context`, `_generate_verdict`, `_generate_changes_2026`, `_generate_summary_table`, `_generate_buying_guide`, `_generate_criteria`, `bulk_generate`, `export_wordpress_xml`

---

### LEGACY_SIFTED_auto_content_system

**Purpose:** AUTONOMOUS CONTENT GENERATION SYSTEM

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 231 |
| Functions | 10 |
| Has run() | No |

**Functions:** `__init__`, `generate_article_ideas`, `_get_niche_data`, `_fill_template_vars`, `_extract_keyword`, `generate_full_article`, `_generate_affiliate_links`, `generate_social_posts`, `generate_email_sequence`, `run_daily_automation`

---

### LEGACY_SIFTED_real_content_generator

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 141 |
| Functions | 5 |
| Has run() | No |

**Functions:** `load_my_style`, `generate_with_ollama`, `create_article`, `save_article`, `main`

---

### LEGACY_SIFTED_reddit_bot

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 55 |
| Functions | 1 |
| Has run() | No |

**Functions:** `_wire_state`

---

### LEGACY_SIFTED_social_bot

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 37 |
| Functions | 1 |
| Has run() | No |

**Functions:** `_wire_state`

---

### LEGACY_SIFTED_social_media_bot

**Purpose:** AUTONOMOUS SOCIAL MEDIA BOT

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 282 |
| Functions | 9 |
| Has run() | No |

**Functions:** `__init__`, `generate_content_calendar`, `_weighted_choice`, `_generate_post_by_type`, `_fill_post_template`, `_generate_hashtags`, `generate_engagement_protocol`, `export_to_buffer_format`, `save_calendar`

---

### MASTODON_ENGINE

**Purpose:** MASTODON_ENGINE.py — Posts to Mastodon / Fediverse

| Property | Value |
|----------|-------|
| Layer | L4 |
| Lines | 115 |
| Functions | 4 |
| Has run() | Yes |

**Functions:** `toot`, `load_state`, `save_state`, `run`

---

### NARRATOR

**Purpose:** NARRATOR.py — SolarPunk's Voice

| Property | Value |
|----------|-------|
| Layer | L7 |
| Lines | 432 |
| Functions | 9 |
| Has run() | Yes |

**Functions:** `load_state`, `save_state`, `load_omnibus`, `load_narrative_log`, `save_narrative_log`, `generate_story`, `build_html`, `run`, `ask`

---

### NEWSLETTER_ENGINE

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | L4 |
| Lines | 152 |
| Functions | 5 |
| Has run() | Yes |

**Functions:** `rj`, `call_claude`, `should_send`, `send_email`, `run`

---

### RSS_PUBLISHER

**Purpose:** RSS_PUBLISHER — publish RSS feed from newsletter archive + cycle history

| Property | Value |
|----------|-------|
| Layer | L7 |
| Lines | 133 |
| Functions | 5 |
| Has run() | Yes |

**Functions:** `rj`, `rfc822`, `build_items`, `render_feed`, `run`

---

### SOCIAL_DASHBOARD

**Purpose:** SOCIAL_DASHBOARD.py — builds docs/social.html copy-paste board from social_queue.json

| Property | Value |
|----------|-------|
| Layer | L4 |
| Lines | 141 |
| Functions | 4 |
| Has run() | Yes |

**Functions:** `load_queue`, `card`, `build_html`, `run`

---

### SOCIAL_ECHO

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 22 |
| Functions | 1 |
| Has run() | No |

**Functions:** `generate_echo`

---

### SOCIAL_PROMOTER

**Purpose:** SOCIAL_PROMOTER.py v2 — Drains the real queue and actually posts

| Property | Value |
|----------|-------|
| Layer | L4 |
| Lines | 252 |
| Functions | 9 |
| Has run() | Yes |

**Functions:** `load_state`, `save_state`, `load_queue`, `save_queue`, `post_twitter`, `post_reddit`, `make_tweet_from_post`, `make_reddit_text`, `run`

---

### SUBSTACK_ENGINE

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | L4 |
| Lines | 151 |
| Functions | 8 |
| Has run() | Yes |

**Functions:** `load`, `save`, `gather_stats`, `draft_issue`, `publish_to_substack`, `notify_meeko`, `should_draft`, `run`

---

### VIRALITY_ENGINE

**Purpose:** VIRALITY_ENGINE.py -- Community-specific launch posts, engineered to spread

| Property | Value |
|----------|-------|
| Layer | L4 |
| Lines | 290 |
| Functions | 3 |
| Has run() | Yes |

**Functions:** `rj`, `run`, `card`

---

### WEB_PUBLISHER

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 28 |
| Functions | 1 |
| Has run() | No |

**Functions:** `publish_value`

---

### open_broadcaster

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 26 |
| Functions | 2 |
| Has run() | No |

**Functions:** `broadcast_to_open_web`, `_wire_state`

---

## Self-Improvement & Ops

*27 engines in this category*

### ARCHITECT

**Purpose:** ARCHITECT.py — SolarPunk's Strategic Brain

| Property | Value |
|----------|-------|
| Layer | L6 |
| Lines | 242 |
| Functions | 11 |
| Has run() | Yes |

**Functions:** `load`, `save`, `rj`, `audit_system`, `identify_revenue_gaps`, `generate_plan`, `_fallback_plan`, `write_plan`, `run`, `ask`, `ask_json`

---

### AUTONOMOUS_TESTER

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 21 |
| Functions | 1 |
| Has run() | No |

**Functions:** `test_manifestation`

---

### AUTONOMY_PROOF

**Purpose:** AUTONOMY_PROOF.py — Live proof that SolarPunk is real and running

| Property | Value |
|----------|-------|
| Layer | L7 |
| Lines | 196 |
| Functions | 2 |
| Has run() | Yes |

**Functions:** `rj`, `run`

---

### AUTOPILOT_EXECUTOR

**Purpose:** AUTOPILOT_EXECUTOR -- Goes through the human task board and DOES every

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 1124 |
| Functions | 19 |
| Has run() | Yes |

**Functions:** `_rj`, `_wj`, `_ts`, `_wt`, `fix_broken_html`, `_product_landing_html`, `generate_product_landing_pages`, `create_discussion_drafts`, `generate_email_templates`, `build_bundle_pages`, `update_robots_and_sitemap`, `create_image_descriptions`, `prefill_kofi_listings`, `update_rss_feed`, `mark_completed_tasks`, `run`, `__init__`, `log`, `mark_task`

---

### AUTO_ARCHITECT

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 40 |
| Functions | 1 |
| Has run() | No |

**Functions:** `build_smart_entirety`

---

### AUTO_DOCS

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 33 |
| Functions | 1 |
| Has run() | No |

**Functions:** `document_progress`

---

### AUTO_EXECUTOR

**Purpose:** AUTO_EXECUTOR.py -- Execute Autonomous Tasks Without Human Input

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 224 |
| Functions | 4 |
| Has run() | Yes |

**Functions:** `load_json`, `save_json`, `execute_command`, `run`

**Reads:** data/task_queue.json, data/auto_executor_state.json

**Writes:** data/auto_executor_state.json, data/auto_executor_log.json

---

### AUTO_GENESIS

**Purpose:** AUTO_GENESIS.py -- The Self-Starting Perpetual Loop

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 253 |
| Functions | 6 |
| Has run() | Yes |

**Functions:** `load_json`, `save_json`, `run_engine`, `get_metrics`, `run_cycle`, `run`

**Reads:** data/auto_genesis_state.json, data/live_wire_report.json

**Writes:** data/auto_genesis_state.json, data/auto_genesis_log.json

---

### AUTO_HEALER

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | L0 |
| Lines | 47 |
| Functions | 2 |
| Has run() | No |

**Functions:** `heal_and_sync`, `clear_ingest_clogs`

---

### AUTO_RUNNER

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 48 |
| Functions | 2 |
| Has run() | No |

**Functions:** `run_self`, `_wire_state`

---

### BOTTLENECK_SCANNER

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | L0 |
| Lines | 272 |
| Functions | 7 |
| Has run() | Yes |

**Functions:** `check_secrets`, `check_engines`, `check_gumroad_listings`, `check_revenue`, `identify_bottlenecks`, `write_html_report`, `run`

---

### CAPABILITY_SCANNER

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | L0 |
| Lines | 196 |
| Functions | 3 |
| Has run() | Yes |

**Functions:** `scan`, `_build_html`, `run`

---

### CAPACITY_BOOSTER

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 48 |
| Functions | 3 |
| Has run() | No |

**Functions:** `get_idle_time`, `regulate_swarm`, `_wire_state`

---

### CHAOS_TEST

**Purpose:** CHAOS_TEST.py

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 333 |
| Functions | 7 |
| Has run() | No |

**Functions:** `_record`, `test_honeytoken_deployment`, `test_tripwire_fires`, `test_mirror_room`, `test_unsigned_branch_block`, `test_branch_protection`, `print_summary`

---

### ENGINE_INTEGRITY

**Purpose:** ENGINE_INTEGRITY.py — SHA-based tamper detection for all 37 engines

| Property | Value |
|----------|-------|
| Layer | L0 |
| Lines | 102 |
| Functions | 4 |
| Has run() | Yes |

**Functions:** `gh`, `load_registry`, `save_registry`, `run`

---

### GENERATED_SELF_BUILDER_CONSUMER

**Purpose:** GENERATED_SELF_BUILDER_CONSUMER.py -- Auto-generated by FRACTAL_GENESIS_ENGINE

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 49 |
| Functions | 1 |
| Has run() | Yes |

**Functions:** `run`

**Reads:** self_builder_state.json, architect_plan.json

**Writes:** data/self_builder_insights.json

---

### GENERATED_SELF_BUILDER_QUEUE_POPULATOR

**Purpose:** GENERATED_SELF_BUILDER_QUEUE_POPULATOR.py -- Auto-generated by FRACTAL_GENESIS_ENGINE

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 47 |
| Functions | 1 |
| Has run() | Yes |

**Functions:** `run`

**Reads:** self_builder_queue.json

**Writes:** data/self_builder_queue.json

---

### HEALTH_BOOSTER

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | L3 |
| Lines | 190 |
| Functions | 5 |
| Has run() | Yes |

**Functions:** `check_api_key`, `check_revenue`, `score_and_report`, `update_brain_state`, `run`

---

### LEGACY_SIFTED_full_autonomous_deploy

**Purpose:** FULLY AUTONOMOUS DEPLOYMENT SYSTEM

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 499 |
| Functions | 24 |
| Has run() | No |

**Functions:** `__init__`, `log`, `load_or_create_config`, `run_full_deployment`, `generate_content`, `generate_images`, `generate_images_local`, `generate_images_api`, `build_website`, `deploy_hosting`, `deploy_vercel`, `deploy_netlify`, `deploy_github_pages`, `configure_domain`, `configure_namecheap`, `configure_cloudflare`, `setup_email`, `setup_beehiiv`, `setup_mailchimp`, `setup_convertkit`, `generate_affiliate_links`, `schedule_social`, `setup_analytics`, `start_monitoring`

---

### LEGACY_SIFTED_self_heal

**Purpose:** SELF-HEALING AI SYSTEM v1.0

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 209 |
| Functions | 10 |
| Has run() | No |

**Functions:** `__init__`, `log`, `fix_main_py`, `fix_vscode`, `fix_ollama`, `fix_fastapi`, `fix_continue_extension`, `fix_config`, `fix_python_packages`, `heal_all`

---

### LEGACY_SIFTED_ultimate_ai_self

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 942 |
| Functions | 48 |
| Has run() | Yes |

**Functions:** `with_retry`, `decorator`, `__init__`, `run`, `submit`, `stop`, `get_info`, `__init__`, `heal`, `_record`, `_fix_import_error`, `_fix_attribute_error`, `_fix_key_error`, `_fix_index_error`, `_fix_connection_error`, `_fix_memory_error`, `_fix_recursion_error`, `_fix_type_error`, `_fix_value_error`, `_generic_fix`, `get_stats`, `__init__`, `_collect_metrics`, `diagnose`, `get_stats`, `__init__`, `_init_db`, `_connect`, `add`, `get`, `search`, `vacuum`, `get_stats`, `__init__`, `_spawn_subsystem`, `_reap_dead_subsystems`, `self_heal`, `self_diagnose`, `self_learn`, `self_evolve`, `submit_task`, `get_state`, `run_forever`, `stop`, `_shutdown_handler`, `heavy_task`, `on_done`, `wrapper`

---

### LEGACY_SIFTED_ultimate_ai_self_1

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 1598 |
| Functions | 71 |
| Has run() | Yes |

**Functions:** `build_event`, `_emit`, `with_retry`, `make_file_sink`, `make_print_sink`, `make_prometheus_sink`, `decorator`, `__init__`, `run`, `submit`, `stop`, `get_info`, `__init__`, `heal`, `_record`, `_fix_import_error`, `_fix_attribute_error`, `_fix_key_error`, `_fix_index_error`, `_fix_connection_error`, `_fix_memory_error`, `_fix_recursion_error`, `_fix_type_error`, `_fix_value_error`, `_generic_fix`, `get_stats`, `__init__`, `_collect_metrics`, `diagnose`, `get_stats`, `__init__`, `_init_db`, `_connect`, `add`, `get`, `search`, `vacuum`, `get_stats`, `__init__`, `_make_handler`, `start`, `stop`, `as_fastapi_app`, `__init__`, `_spawn_subsystem`, `_reap_dead_subsystems`, `self_heal`, `self_diagnose`, `self_learn`, `self_evolve`, `submit_task`, `get_state`, `run_forever`, `stop`, `_shutdown_handler`, `sink`, `sink`, `wrapper`, `ver`, `auth_ok`, `health`, `metrics`, `full_state`, `sink`, `log_message`, `_send_json`, `_send_redirect`, `_versioned`, `_check_bearer`, `do_GET`, `_redir`

---

### NANOBOT_HEALER

**Purpose:** NANOBOT_HEALER.py -- Self-Repair Engine

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 257 |
| Functions | 8 |
| Has run() | Yes |

**Functions:** `load_json`, `check_syntax`, `fix_nested_getenv`, `fix_encoding_issues`, `fix_print_encoding`, `heal_engine`, `scan_and_heal`, `run`

---

### PROOF_LEDGER

**Purpose:** PROOF_LEDGER.py — public verifiable Gaza donation tracker

| Property | Value |
|----------|-------|
| Layer | L5 |
| Lines | 235 |
| Functions | 6 |
| Has run() | Yes |

**Functions:** `load_ledger`, `log_sale`, `log_transfer`, `check_gumroad_sales`, `check_delivery_log`, `run`

---

### SELF_BUILDER

**Purpose:** SELF_BUILDER.py v3 — Infinite engine generator

| Property | Value |
|----------|-------|
| Layer | L6 |
| Lines | 286 |
| Functions | 8 |
| Has run() | Yes |

**Functions:** `load`, `save`, `get_existing_engines`, `get_next_idea`, `generate_code`, `validate`, `push_to_github`, `run`

---

### STRESS_TEST

**Purpose:** STRESS_TEST — Fire Drill for the Living Organism

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 328 |
| Functions | 6 |
| Has run() | No |

**Functions:** `timestamp`, `test_hungry_input_heal`, `test_corruption_detection`, `test_canary_tamper`, `test_sovereignty_resilience`, `main`

---

### UPGRADE_ENGINE

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 30 |
| Functions | 2 |
| Has run() | No |

**Functions:** `check_for_upgrades`, `_wire_state`

---

## Crisis Response & Defense

*26 engines in this category*

### APOPTOSIS

**Purpose:** APOPTOSIS.py -- Programmed Engine Retirement (Cell Death Pattern)

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 216 |
| Functions | 3 |
| Has run() | No |

**Functions:** `load_json`, `scan_engine_vitality`, `main`

**Reads:** data/pheromone_map.json, data/pathway_strength.json,

**Writes:** data/apoptosis_report.json

---

### BIOLUMINESCENCE

**Purpose:** BIOLUMINESCENCE.py — Silence Detection (Deep-Sea Pattern)

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 309 |
| Functions | 8 |
| Has run() | No |

**Functions:** `load_json`, `load_bio_state`, `save_bio_state`, `count_signals_by_region`, `update_baselines`, `detect_silence`, `generate_light`, `main`

**Reads:** data/crisis_signals.json, data/crisis_monitor_history.json,

**Writes:** data/bioluminescence.json, data/silence_alerts.json

---

### CORRUPTION_SENTINEL

**Purpose:** CORRUPTION_SENTINEL — Immune System for the Codebase

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 111 |
| Functions | 3 |
| Has run() | No |

**Functions:** `check_file`, `scan_all`, `main`

---

### CRISIS_MONITOR

**Purpose:** CRISIS_MONITOR.py — Humanitarian Action Trigger Engine

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 754 |
| Functions | 13 |
| Has run() | No |

**Functions:** `score_urgency`, `classify`, `match_aid_orgs`, `fetch_reliefweb`, `fetch_gdelt`, `fetch_reddit_crisis`, `fetch_wikipedia_current`, `build_amplification`, `build_dashboard`, `email_critical`, `build_triggers`, `build_ngo_handshakes`, `main`

---

### DARK_WATCH

**Purpose:** DARK_WATCH.py — Silent Weekend Guardian

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 178 |
| Functions | 5 |
| Has run() | No |

**Functions:** `check_crisis_signals`, `verify_engine_integrity`, `prune_stale_data`, `fire_alert`, `main`

---

### GENERATED_DARK_WATCH_ALERT_POPULATOR

**Purpose:** GENERATED_DARK_WATCH_ALERT_POPULATOR.py -- Auto-generated by FRACTAL_GENESIS_ENGINE

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 47 |
| Functions | 1 |
| Has run() | Yes |

**Functions:** `run`

**Reads:** dark_watch_alert.json

**Writes:** data/dark_watch_alert.json

---

### GENERATED_IMMUNE_SYSTEM_CONSUMER

**Purpose:** GENERATED_IMMUNE_SYSTEM_CONSUMER.py -- Auto-generated by FRACTAL_GENESIS_ENGINE

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 49 |
| Functions | 1 |
| Has run() | Yes |

**Functions:** `run`

**Reads:** quarantine_log.json, immune_system_report.json

**Writes:** data/immune_system_insights.json

---

### GENERATED_INBOUND_SIGNALS_POPULATOR

**Purpose:** GENERATED_INBOUND_SIGNALS_POPULATOR.py -- Auto-generated by FRACTAL_GENESIS_ENGINE

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 48 |
| Functions | 1 |
| Has run() | Yes |

**Functions:** `run`

**Reads:** inbound_signals.json

**Writes:** data/inbound_signals.json

---

### GENERATED_QUORUM_SENSE_CONSUMER

**Purpose:** GENERATED_QUORUM_SENSE_CONSUMER.py -- Auto-generated by FRACTAL_GENESIS_ENGINE

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 48 |
| Functions | 1 |
| Has run() | Yes |

**Functions:** `run`

**Reads:** quorum_state.json

**Writes:** data/quorum_sense_insights.json

---

### GENERATED_SECRETS_CHECKER_CONSUMER

**Purpose:** GENERATED_SECRETS_CHECKER_CONSUMER.py -- Auto-generated by FRACTAL_GENESIS_ENGINE

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 47 |
| Functions | 1 |
| Has run() | Yes |

**Functions:** `run`

**Reads:** secrets_checker_state.json

**Writes:** data/secrets_checker_insights.json

---

### GENERATED_SIGNAL_BOOST_LOG_POPULATOR

**Purpose:** GENERATED_SIGNAL_BOOST_LOG_POPULATOR.py -- Auto-generated by FRACTAL_GENESIS_ENGINE

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 47 |
| Functions | 1 |
| Has run() | Yes |

**Functions:** `run`

**Reads:** signal_boost_log.json

**Writes:** data/signal_boost_log.json

---

### GUARDIAN

**Purpose:** GUARDIAN.py — SolarPunk Immune System v2

| Property | Value |
|----------|-------|
| Layer | L0 |
| Lines | 127 |
| Functions | 8 |
| Has run() | No |

**Functions:** `runcmd`, `alert`, `log`, `save_state`, `check`, `best_restore_tag`, `restore`, `main`

---

### GUARDIAN_GATEKEEPER

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 28 |
| Functions | 2 |
| Has run() | No |

**Functions:** `check_intent`, `_wire_state`

---

### IMMUNE_MEMORY

**Purpose:** IMMUNE_MEMORY.py — Adaptive Crisis Response (T-Cell Pattern)

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 409 |
| Functions | 8 |
| Has run() | No |

**Functions:** `load_json`, `load_memory`, `save_memory`, `extract_pattern`, `build_response_chain`, `update_effectiveness`, `build_cross_immunity_map`, `main`

**Reads:** data/crisis_signals.json, data/crisis_triggers.json,

**Writes:** data/immune_memory.json, data/immune_responses.json

---

### IMMUNE_SYSTEM

**Purpose:** IMMUNE_SYSTEM.py -- Active Defense Against Code Corruption

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 308 |
| Functions | 8 |
| Has run() | Yes |

**Functions:** `load_json`, `save_json`, `fix_nested_getenv`, `fix_merge_conflicts`, `fix_duplicate_imports`, `scan_engine`, `repair_engine`, `run`

**Reads:** mycelium/*.py, data/sentinel_report.json

**Writes:** data/immune_system_report.json, data/quarantine_log.json

---

### LEGACY_SIFTED_crisis_response_ai

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 134 |
| Functions | 4 |
| Has run() | No |

**Functions:** `__init__`, `identify_most_effective_allocation`, `generate_smart_contract`, `monitor_impact`

---

### QUORUM_SENSE

**Purpose:** QUORUM_SENSE.py — Collective Signal Threshold (Bacterial Pattern)

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 294 |
| Functions | 6 |
| Has run() | No |

**Functions:** `load_json`, `load_quorum`, `gather_signal_molecules`, `evaluate_quorum`, `build_response_directives`, `main`

**Reads:** data/crisis_signals.json, data/knowledge_pulses.json,

**Writes:** data/quorum_state.json

---

### REVENUE_MONITOR

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 7 |
| Functions | 1 |
| Has run() | No |

**Functions:** `check_market`

---

### SCAM_SHIELD

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | L1 |
| Lines | 163 |
| Functions | 7 |
| Has run() | Yes |

**Functions:** `load`, `save`, `quick_score`, `analyze_with_claude`, `alert_meeko`, `scan_inbox`, `run`

---

### SECRETS_CHECKER

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | L0 |
| Lines | 357 |
| Functions | 3 |
| Has run() | Yes |

**Functions:** `check_secrets`, `build_html`, `run`

---

### SIGNAL_BOOST

**Purpose:** SIGNAL_BOOST.py — Permanent Public Record via GitHub Issues

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 299 |
| Functions | 8 |
| Has run() | No |

**Functions:** `load_log`, `save_log`, `is_cooled_down`, `classify`, `get_resource_kit_snippet`, `build_issue_body`, `create_issue`, `main`

**Reads:** data/crisis_signals.json, data/resource_kits.json

**Writes:** data/signal_boost_log.json

---

### SIGNAL_CHAIN

**Purpose:** SIGNAL_CHAIN.py — Every signal becomes an action. Nothing leaks.

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 178 |
| Functions | 3 |
| Has run() | Yes |

**Functions:** `load`, `run`, `action`

**Writes:** data/signal_chain_queue.json

---

### SIGNAL_INTEGRITY

**Purpose:** SIGNAL_INTEGRITY.py -- The Honest Audit

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 313 |
| Functions | 6 |
| Has run() | Yes |

**Functions:** `load_json`, `save_json`, `classify_data_file`, `audit_wires`, `audit_engines`, `run`

**Reads:** data/live_wire_report.json, data/*.json (all flowing data)

**Writes:** data/signal_integrity_report.json

---

### SPORE_DISPERSAL

**Purpose:** SPORE_DISPERSAL.py — Maximum Redundancy Distribution (Fungal Pattern)

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 358 |
| Functions | 9 |
| Has run() | No |

**Functions:** `load_json`, `classify_pulse`, `generate_social_spores`, `generate_reddit_spores`, `generate_broadcast_spores`, `generate_mesh_spores`, `generate_qr_spores`, `calculate_dispersal_reach`, `main`

**Reads:** data/knowledge_pulses.json, data/survival_telegrams.json,

**Writes:** data/spore_dispersal.json, data/spore_manifest.json

---

### SPORE_SERVER

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 28 |
| Functions | 2 |
| Has run() | No |

**Functions:** `broadcast`, `_wire_state`

---

### VANISH_PROTOCOL

**Purpose:** VANISH_PROTOCOL.py

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 181 |
| Functions | 4 |
| Has run() | Yes |

**Functions:** `load_json_safe`, `load_stats`, `build_templates`, `run`

---

## Topology & Wiring

*24 engines in this category*

### BRAVE_BRIDGE

**Purpose:** BRAVE_BRIDGE.py — SolarPunk browser hands

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 272 |
| Functions | 15 |
| Has run() | Yes |

**Functions:** `cdp_get`, `cdp_send`, `get_tabs`, `get_tab_by_url`, `open_tab`, `eval_in_tab`, `screenshot_tab`, `check_gumroad_via_browser`, `check_kofi_via_browser`, `post_to_reddit_via_browser`, `post_to_bluesky_via_browser`, `scan_desktop_blueprints`, `load_state`, `save_state`, `run`

---

### BRIDGE_BUILDER

**Purpose:** BRIDGE_BUILDER.py — Self-Wiring Nervous System

| Property | Value |
|----------|-------|
| Layer | L4 |
| Lines | 1073 |
| Functions | 67 |
| Has run() | Yes |

**Functions:** `load_json`, `bridge_grants_found`, `bridge_sentinel_report`, `bridge_knowledge_graph`, `bridge_quick_revenue`, `seed_json`, `seed_text`, `bridge_social_queue`, `bridge_brave_browser_state`, `bridge_conversion_log`, `bridge_desktop_daemon_state`, `bridge_knowledge_bank`, `bridge_neuron_reports`, `bridge_newsletter_subscribers`, `bridge_pending_publication`, `bridge_resurrections`, `bridge_sponsors_inbox`, `bridge_storefront_builder_state`, `bridge_synergy_mutations`, `bridge_system_directive`, `bridge_newsletter_archive`, `bridge_river_watch`, `bridge_desktop_blueprints`, `bridge_orphan_tweets`, `bridge_orphan_daemon_task`, `bridge_chimera_evolution`, `bridge_nanobot_heal`, `bridge_mutation_leaderboard`, `bridge_polymarket_scan`, `bridge_hemisphere_state`, `bridge_relay_baton`, `bridge_amplification_posts`, `bridge_amplify_cooldown`, `bridge_murmuration_trap`, `bridge_revenue_state`, `bridge_sentinel_scan`, `bridge_sovereignty_state`, `bridge_stress_backup_river_watch`, `bridge_public_ledger`, `bridge_agent_link_verifier_state`, `bridge_ai_council_report`, `bridge_art_log`, `bridge_atomizer_state`, `bridge_claude_autonomous_report`, `bridge_compound_tracker`, `bridge_cycle_memory`, `bridge_desktop_agent_log`, `bridge_dual_brain_conversation`, `bridge_external_signals`, `bridge_finance_ledger`, `bridge_handshake_results`, `bridge_kimi_conductor_report`, `bridge_known_devices`, `bridge_local_needs_radar`, `bridge_master_config`, `bridge_mutual_aid_routing`, `bridge_neural_weights`, `bridge_open_loops`, `bridge_product_ideas`, `bridge_reminders`, `bridge_revenue_data`, `bridge_secrets`, `bridge_self_wiring_report`, `bridge_system_manifest`, `bridge_system_wants_next`, `bridge_workflow_health`, `run`

---

### CHAIN_ORCHESTRATOR

**Purpose:** CHAIN_ORCHESTRATOR.py — The loop that runs the loop.

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 305 |
| Functions | 3 |
| Has run() | Yes |

**Functions:** `load`, `run_chain`, `run`

---

### CHIMERA_EVOLUTION_ENGINE

**Purpose:** CHIMERA_EVOLUTION_ENGINE.py -- The Sovereign Evolution Loop

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 313 |
| Functions | 11 |
| Has run() | Yes |

**Functions:** `load_json`, `save_json`, `run_engine`, `phase_scan`, `phase_heal`, `phase_bridge`, `phase_mutate`, `phase_score`, `phase_evolve`, `phase_report`, `run`

---

### CLAUDE_BRIDGE

**Purpose:** CLAUDE_BRIDGE — send tasks to Claude running in Brave browser via CDP

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 298 |
| Functions | 9 |
| Has run() | Yes |

**Functions:** `load_state`, `save_state`, `load_queue`, `check_cdp_alive`, `get_playwright`, `send_task_via_cdp`, `process_queue`, `run`, `ask_claude_in_brave`

---

### EVENT_RELAY

**Purpose:** EVENT_RELAY.py -- Event-driven trigger system for local machine

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 391 |
| Functions | 10 |
| Has run() | Yes |

**Functions:** `load_json`, `save_json`, `git_run`, `check_git_status`, `check_new_products`, `check_article_drafts`, `check_cortex_directive`, `action_stage_and_commit_products`, `action_mark_articles_for_publisher`, `run`

---

### GENERATED_BRIDGE_BUILDER_CONSUMER

**Purpose:** GENERATED_BRIDGE_BUILDER_CONSUMER.py -- Auto-generated by FRACTAL_GENESIS_ENGINE

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 50 |
| Functions | 1 |
| Has run() | Yes |

**Functions:** `run`

**Reads:** bridge_report.json, fund_scout_results.json, sentinel_report.json

**Writes:** data/bridge_builder_insights.json

---

### GENERATED_SWARM_COORDINATOR_CONSUMER

**Purpose:** GENERATED_SWARM_COORDINATOR_CONSUMER.py -- Auto-generated by FRACTAL_GENESIS_ENGINE

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 47 |
| Functions | 1 |
| Has run() | Yes |

**Functions:** `run`

**Reads:** swarm_state.json

**Writes:** data/swarm_coordinator_insights.json

---

### GMAIL_BRIDGE

**Purpose:** GMAIL_BRIDGE.py — Unified email interface for SolarPunk Nerve Center

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 194 |
| Functions | 7 |
| Has run() | No |

**Functions:** `_write_wire_state`, `__init__`, `send`, `draft`, `send_outreach`, `send_payout_notification`, `health_check`

---

### KNOWLEDGE_BRIDGE

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | L6 |
| Lines | 53 |
| Functions | 1 |
| Has run() | No |

**Functions:** `process_and_plug`

---

### LIVE_WIRE

**Purpose:** LIVE_WIRE.py — Neural Wiring Discovery Engine

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 435 |
| Functions | 7 |
| Has run() | Yes |

**Functions:** `scan_engine`, `scan_all_engines`, `discover_wires`, `find_orphans`, `test_chain`, `compute_topology_stats`, `run`

---

### MURMURATION_RELAY

**Purpose:** MURMURATION_RELAY.py — Push Help Outward to Real People

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 262 |
| Functions | 7 |
| Has run() | No |

**Functions:** `load_relay_log`, `save_relay_log`, `is_cooled_down`, `inject_social_queue`, `build_reddit_queue`, `build_broadcast_queue`, `main`

**Reads:** data/knowledge_pulses.json

**Writes:** data/social_queue.json (appends), data/murmuration_log.json,

---

### OLLAMA_BRIDGE

**Purpose:** OLLAMA_BRIDGE.py — Local LLM inference bridge for SolarPunk Nerve Center

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 323 |
| Functions | 13 |
| Has run() | Yes |

**Functions:** `quick_generate`, `quick_embed`, `semantic_similarity`, `run`, `__init__`, `_verify_connection`, `list_models`, `generate`, `chat`, `embed`, `batch_embed`, `route`, `health_check`

---

### RELAY_BATON

**Purpose:** RELAY_BATON.py -- Claude <-> SolarPunk Work Relay

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 310 |
| Functions | 10 |
| Has run() | Yes |

**Functions:** `load_json`, `save_json`, `load_baton`, `handoff_to_solarpunk`, `solarpunk_picks_up`, `attempt_task`, `run_engine_task`, `handoff_to_claude`, `gather_auto_tasks`, `run`

**Reads:** data/relay_baton.json, data/chimera_evolution_report.json

**Writes:** data/relay_baton.json

---

### SELF_WIRING_ENGINE

**Purpose:** SELF_WIRING_ENGINE.py -- SolarPunk Wires Itself

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 323 |
| Functions | 7 |
| Has run() | Yes |

**Functions:** `load_json`, `save_json`, `extract_engine_purpose`, `find_potential_connections`, `auto_seed_missing_state_files`, `auto_connect_low_wire_engines`, `run`

**Reads:** data/live_wire_report.json, mycelium/*.py

**Writes:** data/self_wiring_report.json, data/*.json (new bridge files)

---

### SWARM_COORDINATOR

**Purpose:** SWARM_COORDINATOR.py — ALL HANDS ON DECK

| Property | Value |
|----------|-------|
| Layer | L6 |
| Lines | 175 |
| Functions | 4 |
| Has run() | Yes |

**Functions:** `rj`, `run_engine`, `dispatch_workflow`, `run`

---

### SWARM_RECEPTOR

**Purpose:** SWARM_RECEPTOR.py — The Minnow Protocol (Regroup Phase)

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 220 |
| Functions | 8 |
| Has run() | Yes |

**Functions:** `derive_key`, `verify_signature`, `load_manifest`, `list_transmissions`, `gather_fragments`, `reassemble`, `run`, `_write_wire_state`

---

### SWARM_TOOLBOX

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 123 |
| Functions | 6 |
| Has run() | No |

**Functions:** `list_engines`, `engine_info`, `full_registry`, `viable_skills`, `save_registry_snapshot`, `main`

---

### SWARM_TRANSMITTER

**Purpose:** SWARM_TRANSMITTER.py — The Minnow Protocol (Scatter Phase)

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 173 |
| Functions | 6 |
| Has run() | Yes |

**Functions:** `derive_key`, `fragment_data`, `sign_fragment`, `compute_manifest_hash`, `scatter`, `run`

---

### SYNAPSE

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | L6 |
| Lines | 165 |
| Functions | 5 |
| Has run() | No |

**Functions:** `gather_real_stats`, `call_claude`, `build_email`, `send_email`, `main`

---

### SYNAPSE_BUILDER

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 22 |
| Functions | 1 |
| Has run() | No |

**Functions:** `weave_connections`

---

### TELEGRAM_BRIDGE

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 5 |
| Functions | 1 |
| Has run() | No |

**Functions:** `broadcast_status`

---

### TELEGRAM_RELAY

**Purpose:** TELEGRAM_RELAY.py — Route Survival Telegrams Through Every Pipe

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 326 |
| Functions | 10 |
| Has run() | No |

**Functions:** `load_telegrams`, `get_active_crises`, `format_sms_gateway`, `format_lora_packet`, `format_mesh_bundle`, `format_satellite`, `format_qr_data`, `format_gist`, `generate_relay_manifest`, `main`

**Reads:** data/survival_telegrams.json, data/crisis_signals.json

**Writes:** data/telegram_relay.json, docs/kits/relay-ready/

---

### swarm_scout

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 35 |
| Functions | 2 |
| Has run() | No |

**Functions:** `agent_task`, `_write_wire_state`

---

## Intelligence & Memory

*22 engines in this category*

### BIG_BRAIN_ORACLE

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | L6 |
| Lines | 185 |
| Functions | 3 |
| Has run() | Yes |

**Functions:** `get_system_context`, `ask_oracle`, `run`

---

### CALENDAR_BRAIN

**Purpose:** CALENDAR_BRAIN v2 - Appointment -> ICS -> TOMORROW reminder

| Property | Value |
|----------|-------|
| Layer | L1 |
| Lines | 234 |
| Functions | 6 |
| Has run() | Yes |

**Functions:** `load`, `save`, `is_real_appointment`, `build_ics`, `send_reminder`, `run`

---

### CORTEX

**Purpose:** CORTEX.py -- The System That Actually Thinks

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 299 |
| Functions | 9 |
| Has run() | Yes |

**Functions:** `load_json`, `save_json`, `gather_system_state`, `build_cortex_prompt`, `rule_based_analysis`, `run`, `ask_json`, `ai_available`, `ai_status`

**Reads:** data/brain_state.json, data/observatory_report.json,

**Writes:** data/cortex_analysis.json, data/cortex_directive.json

---

### CYCLE_MEMORY

**Purpose:** CYCLE_MEMORY.py — Cross-cycle learning layer

| Property | Value |
|----------|-------|
| Layer | L0 |
| Lines | 432 |
| Functions | 10 |
| Has run() | Yes |

**Functions:** `rj`, `load_ledger`, `save_ledger`, `snapshot`, `compute_delta`, `detect_persistent`, `health_trajectory`, `build_html`, `run`, `badge`

---

### EMAIL_BRAIN

**Purpose:** EMAIL_BRAIN - SolarPunk Communications Cortex v3

| Property | Value |
|----------|-------|
| Layer | L1 |
| Lines | 432 |
| Functions | 18 |
| Has run() | Yes |

**Functions:** `load`, `save`, `decode_str`, `get_body`, `fetch_unread`, `is_bot_sender`, `is_appt_sender`, `classify`, `extract_appt`, `queue_appointment`, `queue_revenue`, `queue_exchange_task`, `flag_personal`, `draft_business_reply`, `send_email`, `run`, `ask`, `ask_json`

---

### GENERATED_CYCLE_MEMORY_CONSUMER

**Purpose:** GENERATED_CYCLE_MEMORY_CONSUMER.py -- Auto-generated by FRACTAL_GENESIS_ENGINE

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 49 |
| Functions | 1 |
| Has run() | Yes |

**Functions:** `run`

**Reads:** cycle_ledger.json, cycle_delta.json

**Writes:** data/cycle_memory_insights.json

---

### GENERATED_KNOWLEDGE_TRACKER

**Purpose:** GENERATED_KNOWLEDGE_TRACKER.py -- Auto-generated by FRACTAL_GENESIS_ENGINE

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 48 |
| Functions | 1 |
| Has run() | Yes |

**Functions:** `run`

**Reads:** brain_state.json, live_wire_report.json

**Writes:** data/knowledge_tracker.json

---

### GENERATED_MEMORY_PALACE_CONSUMER

**Purpose:** GENERATED_MEMORY_PALACE_CONSUMER.py -- Auto-generated by FRACTAL_GENESIS_ENGINE

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 49 |
| Functions | 1 |
| Has run() | Yes |

**Functions:** `run`

**Reads:** memory_palace.json, lessons.json, growth_curve.json

**Writes:** data/memory_palace_insights.json

---

### GENERATED_RESONANCE_CONVERTER_CONSUMER

**Purpose:** GENERATED_RESONANCE_CONVERTER_CONSUMER.py -- Auto-generated by FRACTAL_GENESIS_ENGINE

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 50 |
| Functions | 1 |
| Has run() | Yes |

**Functions:** `run`

**Reads:** resonance_converter_state.json, asks_queue.json, claude_tasks_queue.json

**Writes:** data/resonance_converter_insights.json

---

### KNOWLEDGE_CHAIN

**Purpose:** KNOWLEDGE_CHAIN.py — The system learns from itself every cycle.

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 211 |
| Functions | 6 |
| Has run() | Yes |

**Functions:** `load`, `run`, `ask_json`, `ask`, `ai_available`, `_ai_call`

**Reads:** all data/*.json files (engine states)

**Writes:** data/knowledge_chain_synthesis.json

---

### KNOWLEDGE_DISTILLER

**Purpose:** KNOWLEDGE_DISTILLER.py -- SolarPunk Engine Encyclopedia Generator

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 447 |
| Functions | 7 |
| Has run() | Yes |

**Functions:** `parse_omnibus_layers`, `extract_reads_writes`, `classify_engine`, `extract_engine_info`, `generate_encyclopedia`, `register_product`, `run`

**Reads:** mycelium/*.py (all engine source files)

**Writes:** products/solarpunk-engine-encyclopedia.md

---

### KNOWLEDGE_PULSE

**Purpose:** KNOWLEDGE_PULSE.py — Actionable Micro-Knowledge Generator

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 215 |
| Functions | 4 |
| Has run() | No |

**Functions:** `classify_crisis`, `generate_pulse`, `get_subreddit_targets`, `main`

**Reads:** data/crisis_signals.json, data/aid_routing.json

**Writes:** data/knowledge_pulses.json (consumed by MURMURATION_RELAY)

---

### KNOWLEDGE_WEAVER

**Purpose:** KNOWLEDGE_WEAVER.py — Claude-powered autonomous engine builder

| Property | Value |
|----------|-------|
| Layer | L6 |
| Lines | 220 |
| Functions | 9 |
| Has run() | Yes |

**Functions:** `load_state`, `list_engines`, `read_snapshot`, `pick_next_engine`, `generate_code`, `parse_code`, `safety_check`, `build_page`, `run`

---

### MEMORY_PALACE

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | L7 |
| Lines | 145 |
| Functions | 6 |
| Has run() | No |

**Functions:** `load_memory`, `snapshot_current_state`, `detect_patterns`, `extract_lessons`, `build_growth_curve`, `main`

---

### OFFLINE_BRAIN

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 33 |
| Functions | 1 |
| Has run() | No |

**Functions:** `process_locally`

---

### RESONANCE_CONVERTER

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | L4 |
| Lines | 290 |
| Functions | 9 |
| Has run() | Yes |

**Functions:** `rj`, `call_claude`, `get_resonance_level`, `build_context`, `generate_asks`, `track_conversions`, `load_state`, `save_state`, `run`

---

### RESONANCE_ENGINE

**Purpose:** RESONANCE_ENGINE.py — The system listening for itself

| Property | Value |
|----------|-------|
| Layer | L1 |
| Lines | 402 |
| Functions | 10 |
| Has run() | Yes |

**Functions:** `rj`, `gh_api`, `get_github_stats`, `check_hn_mentions`, `check_github_search_mentions`, `check_email_replies`, `score_resonance`, `run`, `stat_card`, `mention_rows`

---

### SYNERGY_FORGE

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 33 |
| Functions | 1 |
| Has run() | No |

**Functions:** `forge_smart_mutation`

---

### SYNERGY_SCOUT

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 24 |
| Functions | 1 |
| Has run() | No |

**Functions:** `identify_synergies`

---

### SYNTHESIS_FACTORY

**Purpose:** SYNTHESIS_FACTORY — Auto-builds new engines using free AI (HuggingFace)

| Property | Value |
|----------|-------|
| Layer | L6 |
| Lines | 164 |
| Functions | 8 |
| Has run() | No |

**Functions:** `safe_to_write`, `safe_git_add_only`, `get_gen_number`, `discover_opportunities`, `synthesize_new_engine`, `write_engine`, `update_log`, `main`

---

### TEMPORAL_CORTEX

**Purpose:** TEMPORAL_CORTEX.py -- The System Remembers

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 301 |
| Functions | 9 |
| Has run() | Yes |

**Functions:** `load_json`, `save_json`, `git_log`, `git_file_stats`, `analyze_growth`, `analyze_corruption`, `analyze_activity_patterns`, `analyze_file_churn`, `run`

**Reads:** git log (subprocess), data/brain_state.json

**Writes:** data/temporal_analysis.json

---

### knowledge_dispatch

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 123 |
| Functions | 4 |
| Has run() | No |

**Functions:** `load_all_data`, `analyze_engines`, `extract_insights`, `main`

---

## Infrastructure & Scheduling

*22 engines in this category*

### BRIEFING_ENGINE

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | L7 |
| Lines | 239 |
| Functions | 9 |
| Has run() | Yes |

**Functions:** `load`, `save`, `gather_all`, `get_crypto_prices`, `get_news_headlines`, `build_morning_email`, `build_evening_report`, `send_email`, `run`

---

### CIRCADIAN_RHYTHM

**Purpose:** CIRCADIAN_RHYTHM.py -- Time-Aware Intelligence (Biological Clock Pattern)

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 318 |
| Functions | 7 |
| Has run() | No |

**Functions:** `load_json`, `get_region_local_time`, `analyze_global_clock`, `analyze_ngo_availability`, `analyze_social_timing`, `generate_time_directives`, `main`

**Reads:** data/crisis_signals.json, data/outreach_state.json

**Writes:** data/circadian_state.json

---

### DESKTOP_AGENT

**Purpose:** DESKTOP_AGENT.py — SolarPunk local desktop executor

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 283 |
| Functions | 13 |
| Has run() | No |

**Functions:** `ts`, `log`, `banner`, `fetch_raw`, `push_to_github`, `copy_to_clipboard`, `open_url`, `handle_social_queue`, `handle_setup_tasks`, `report_status`, `write_log`, `run_cycle`, `main`

---

### DESKTOP_DAEMON

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 521 |
| Functions | 18 |
| Has run() | No |

**Functions:** `log`, `rj`, `wj`, `load_queue`, `save_queue`, `load_results`, `load_state`, `save_state`, `build_context`, `call_claude`, `run_powershell`, `open_in_brave`, `git_commit_and_push`, `execute_task`, `run_loop`, `_idle_health_check`, `queue_task`, `install_autostart`

---

### DESKTOP_HARVESTER

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 76 |
| Functions | 1 |
| Has run() | No |

**Functions:** `harvest`

---

### DESKTOP_ORCHESTRATOR

**Purpose:** DESKTOP_ORCHESTRATOR.py — The engine that makes old blueprints live again

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 265 |
| Functions | 6 |
| Has run() | Yes |

**Functions:** `load_state`, `save_state`, `analyze_blueprints_with_ai`, `check_brave_cdp`, `run`, `ask`

---

### EXECUTIVE_BRIEFING

**Purpose:** EXECUTIVE_BRIEFING — High-Impact Summary Generator

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 322 |
| Functions | 4 |
| Has run() | No |

**Functions:** `load_json`, `gather_all_evidence`, `generate_briefing`, `main`

---

### GENERATED_CLAUDE_TASKS_QUEUE_POPULATOR

**Purpose:** GENERATED_CLAUDE_TASKS_QUEUE_POPULATOR.py -- Auto-generated by FRACTAL_GENESIS_ENGINE

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 47 |
| Functions | 1 |
| Has run() | Yes |

**Functions:** `run`

**Reads:** claude_tasks_queue.json

**Writes:** data/claude_tasks_queue.json

---

### GENERATED_DAEMON_TASK_XML_POPULATOR

**Purpose:** GENERATED_DAEMON_TASK_XML_POPULATOR.py -- Auto-generated by FRACTAL_GENESIS_ENGINE

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 47 |
| Functions | 1 |
| Has run() | Yes |

**Functions:** `run`

**Reads:** daemon_task.xml

**Writes:** data/daemon_task.xml

---

### GENERATED_DESKTOP_DAEMON_CONSUMER

**Purpose:** GENERATED_DESKTOP_DAEMON_CONSUMER.py -- Auto-generated by FRACTAL_GENESIS_ENGINE

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 50 |
| Functions | 1 |
| Has run() | Yes |

**Functions:** `run`

**Reads:** desktop_daemon_log.json, daemon_task.xml, claude_tasks_queue.json

**Writes:** data/desktop_daemon_insights.json

---

### GENERATED_TASK_FACTORY_CONSUMER

**Purpose:** GENERATED_TASK_FACTORY_CONSUMER.py -- Auto-generated by FRACTAL_GENESIS_ENGINE

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 49 |
| Functions | 1 |
| Has run() | Yes |

**Functions:** `run`

**Reads:** task_queue.json, task_factory_state.json

**Writes:** data/task_factory_insights.json

---

### HUMAN_TASK_BOARD

**Purpose:** HUMAN_TASK_BOARD -- Consolidate every human-action-required task across

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 830 |
| Functions | 20 |
| Has run() | Yes |

**Functions:** `_rj`, `_ts`, `_value_matches`, `_classify`, `_estimate_time`, `_extract_url`, `_task_fingerprint`, `_is_revenue_generating`, `_is_zero_cost`, `_is_blocking`, `_extract_tasks_from_value`, `scan_all_data`, `_safe_hint`, `deduplicate`, `prioritise`, `group_by_session`, `group_by_category`, `build_html`, `run`, `score`

---

### LEGACY_SIFTED_agency_orchestrator

**Purpose:** AUTONOMOUS AGENCY ORCHESTRATOR v1.0

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 410 |
| Functions | 0 |
| Has run() | No |

---

### LEGACY_SIFTED_continue_agent_task

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 32 |
| Functions | 2 |
| Has run() | No |

**Functions:** `generate`, `_wire_state`

---

### LEGACY_SIFTED_humanitarian_orchestrator

**Purpose:** HUMANITARIAN ORCHESTRATOR - PAUSED MODE

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 36 |
| Functions | 1 |
| Has run() | Yes |

**Functions:** `run`

---

### LEGACY_SIFTED_orchestrator

**Purpose:** AUTONOMOUS INCOME SYSTEM ORCHESTRATOR

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 230 |
| Functions | 8 |
| Has run() | No |

**Functions:** `__init__`, `_load_config`, `_create_default_config`, `log`, `run_daily_cycle`, `_generate_daily_report`, `run_weekly_cycle`, `status_check`

---

### LEGACY_SIFTED_simple_orchestrator

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 135 |
| Functions | 7 |
| Has run() | No |

**Functions:** `__init__`, `log`, `generate_content`, `run_daily`, `update_dashboard`, `create_html_report`, `setup`

---

### NIGHTLY_DIGEST

**Purpose:** NIGHTLY_DIGEST.py v2 — SolarPunk Daily Summary Engine

| Property | Value |
|----------|-------|
| Layer | L7 |
| Lines | 443 |
| Functions | 9 |
| Has run() | Yes |

**Functions:** `rj`, `load_state`, `should_send_email`, `collect_stats`, `format_email`, `send_email`, `build_status_page`, `run`, `ask`

---

### TASK_ATOMIZER

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | L7 |
| Lines | 20 |
| Functions | 1 |
| Has run() | No |

**Functions:** `atomize_tasks`

---

### TASK_FACTORY

**Purpose:** TASK_FACTORY.py -- Autonomous Task Generator

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 338 |
| Functions | 9 |
| Has run() | Yes |

**Functions:** `load_json`, `save_json`, `generate_product_tasks`, `generate_content_tasks`, `generate_wire_tasks`, `generate_heal_tasks`, `generate_grow_tasks`, `generate_deploy_tasks`, `run`

**Reads:** data/live_wire_report.json, data/product_registry.json,

**Writes:** data/task_queue.json, data/task_factory_state.json

---

### WAKE_ON_LAN

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 30 |
| Functions | 2 |
| Has run() | No |

**Functions:** `wake_machine`, `_wire_state`

---

### WEEKEND_PULSE

**Purpose:** WEEKEND_PULSE.py — Autonomous Heartbeat While Meeko Sleeps

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 279 |
| Functions | 4 |
| Has run() | No |

**Functions:** `safe_load`, `gather_pulse`, `build_pulse_html`, `main`

**Reads:** data/*.json (aggregates from all engines)

**Writes:** data/weekend_pulse.json, docs/pulse.html

---

## Outreach & Partnerships

*14 engines in this category*

### CONNECTION_FORGE

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | L4 |
| Lines | 239 |
| Functions | 6 |
| Has run() | Yes |

**Functions:** `load`, `save`, `check_active_secrets`, `build_setup_email`, `send_setup_email`, `run`

---

### CONTRIBUTOR_REGISTRY

**Purpose:** CONTRIBUTOR_REGISTRY.py — Manages humans who get automatic revenue shares

| Property | Value |
|----------|-------|
| Layer | L5 |
| Lines | 144 |
| Functions | 5 |
| Has run() | Yes |

**Functions:** `load_registry`, `save_registry`, `process_payout_queue`, `validate_splits`, `run`

---

### ECOLOGICAL_GRANT_SYNTHESIZER

**Purpose:** ECOLOGICAL_GRANT_SYNTHESIZER.py — Hybrid-3 Mutation

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 187 |
| Functions | 4 |
| Has run() | Yes |

**Functions:** `load_river_data`, `assess_conditions`, `search_grants`, `run`

---

### EMAIL_AGENT_EXCHANGE

**Purpose:** EMAIL_AGENT_EXCHANGE — AI agents that email AI agents, everyone gets paid per email

| Property | Value |
|----------|-------|
| Layer | L3 |
| Lines | 299 |
| Functions | 10 |
| Has run() | Yes |

**Functions:** `load`, `save`, `route_to_agent`, `run_agent`, `send_agent_reply`, `process_task_emails`, `generate_exchange_page`, `run`, `ask`, `ask_json`

---

### EMAIL_API_EXTRACTOR

**Purpose:** EMAIL_API_EXTRACTOR.py

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 179 |
| Functions | 8 |
| Has run() | No |

**Functions:** `extract_platform_links`, `is_confirmation_email`, `register_connection`, `_log_to_actual`, `process_email`, `get_registry`, `list_platforms`, `_write_wire_state`

---

### EMAIL_OUTREACH

**Purpose:** EMAIL_OUTREACH.py — SolarPunk's first real offensive channel

| Property | Value |
|----------|-------|
| Layer | L4 |
| Lines | 379 |
| Functions | 6 |
| Has run() | Yes |

**Functions:** `load_state`, `save_state`, `cooldown_active`, `draft`, `send`, `run`

---

### FIRST_CONTACT

**Purpose:** FIRST_CONTACT.py — watching for the first stranger

| Property | Value |
|----------|-------|
| Layer | L1 |
| Lines | 614 |
| Functions | 16 |
| Has run() | Yes |

**Functions:** `gh`, `load_fc`, `already_happened`, `check_stargazers`, `check_forks`, `check_issues`, `check_commit_comments`, `check_email_exchange`, `check_watchers`, `scan_for_stranger`, `record_first_contact`, `load_stats`, `build_waiting_page`, `build_contact_page`, `run`, `rj`

---

### GENERATED_GRANTS_FOUND_POPULATOR

**Purpose:** GENERATED_GRANTS_FOUND_POPULATOR.py -- Auto-generated by FRACTAL_GENESIS_ENGINE

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 48 |
| Functions | 1 |
| Has run() | Yes |

**Functions:** `run`

**Reads:** grants_found.json

**Writes:** data/grants_found.json

---

### GENERATED_GRANT_TRIGGER_POPULATOR

**Purpose:** GENERATED_GRANT_TRIGGER_POPULATOR.py -- Auto-generated by FRACTAL_GENESIS_ENGINE

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 47 |
| Functions | 1 |
| Has run() | Yes |

**Functions:** `run`

**Reads:** grant_trigger.json

**Writes:** data/grant_trigger.json

---

### GRANT_APPLICANT

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | L3 |
| Lines | 175 |
| Functions | 8 |
| Has run() | Yes |

**Functions:** `load`, `save`, `draft_email_app`, `draft_grant_reply`, `send_email`, `notify_meeko`, `check_grant_replies`, `run`

---

### GRANT_HUNTER

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | L2 |
| Lines | 83 |
| Functions | 3 |
| Has run() | Yes |

**Functions:** `score`, `research`, `run`

---

### HUMAN_CONNECTOR

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | L4 |
| Lines | 168 |
| Functions | 7 |
| Has run() | Yes |

**Functions:** `load`, `save`, `is_real_human`, `classify_human_intent`, `draft_human_reply`, `send_reply`, `run`

---

### LEGACY_SIFTED_email_sequences

**Purpose:** AUTONOMOUS EMAIL MARKETING SYSTEM

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 402 |
| Functions | 7 |
| Has run() | Yes |

**Functions:** `run`, `__init__`, `generate_welcome_sequence`, `generate_broadcast_emails`, `generate_segmentation_rules`, `export_to_mailchimp_format`, `save_sequences`

---

### OUTREACH_ENGINE

**Purpose:** OUTREACH_ENGINE.py — SolarPunk Autonomous Outreach System

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 463 |
| Functions | 5 |
| Has run() | Yes |

**Functions:** `discover_new_targets_via_ai`, `generate_email_via_ai`, `create_outreach_issue`, `save_draft_for_briefer`, `run`

---

## Creative & Brand

*9 engines in this category*

### ART_CATALOG

**Purpose:** ART_CATALOG.py — Gaza Rose Gallery engine

| Property | Value |
|----------|-------|
| Layer | L3 |
| Lines | 193 |
| Functions | 2 |
| Has run() | Yes |

**Functions:** `build_art_html`, `run`

---

### ART_GENERATOR

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | L3 |
| Lines | 148 |
| Functions | 4 |
| Has run() | No |

**Functions:** `generate_concept`, `generate_image`, `deliver`, `main`

---

### BRAND_LEGAL

**Purpose:** BRAND_LEGAL — SolarPunk™ legal infrastructure engine

| Property | Value |
|----------|-------|
| Layer | L7 |
| Lines | 131 |
| Functions | 3 |
| Has run() | No |

**Functions:** `load_state`, `rj_dict`, `milestone_rows`

---

### DESKTOP_BLUEPRINT_SCANNER

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 279 |
| Functions | 5 |
| Has run() | Yes |

**Functions:** `scan_local`, `generate_recommendations`, `load_state`, `save_state`, `run`

---

### GENERATED_ART_CATALOG_CONSUMER

**Purpose:** GENERATED_ART_CATALOG_CONSUMER.py -- Auto-generated by FRACTAL_GENESIS_ENGINE

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 47 |
| Functions | 1 |
| Has run() | Yes |

**Functions:** `run`

**Reads:** art_catalog.json

**Writes:** data/art_catalog_insights.json

---

### GENERATED_BRAND_LEGAL_CONSUMER

**Purpose:** GENERATED_BRAND_LEGAL_CONSUMER.py -- Auto-generated by FRACTAL_GENESIS_ENGINE

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 48 |
| Functions | 1 |
| Has run() | Yes |

**Functions:** `run`

**Reads:** brand_legal_state.json

**Writes:** data/brand_legal_insights.json

---

### LANDING_DEPLOYER

**Purpose:** LANDING_DEPLOYER.py v3 — Deploys landing pages to docs/ in THIS repo.

| Property | Value |
|----------|-------|
| Layer | L3 |
| Lines | 263 |
| Functions | 6 |
| Has run() | Yes |

**Functions:** `load_state`, `save_state`, `find_undeployed`, `build_landing_html`, `deploy_local`, `run`

---

### SELF_PORTRAIT

**Purpose:** *(no docstring)*

| Property | Value |
|----------|-------|
| Layer | L7 |
| Lines | 247 |
| Functions | 2 |
| Has run() | Yes |

**Functions:** `rj`, `run`

---

### SOLARPUNK_LEGAL

**Purpose:** SOLARPUNK_LEGAL.py — SolarPunk™ brand protection, trademark tracking, legal fund counter

| Property | Value |
|----------|-------|
| Layer | L7 |
| Lines | 261 |
| Functions | 6 |
| Has run() | Yes |

**Functions:** `load_state`, `save_state`, `update_legal_fund`, `log_evidence`, `generate_legal_doc`, `run`

---

## Bio-Inspired Patterns

*8 engines in this category*

### CHEMOTAXIS

**Purpose:** CHEMOTAXIS.py -- Gradient-Following Navigation (Bacterial Pattern)

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 334 |
| Functions | 7 |
| Has run() | No |

**Functions:** `load_json`, `load_chemo_state`, `measure_need_concentration`, `measure_help_concentration`, `navigate`, `generate_directives`, `main`

**Reads:** data/crisis_signals.json, data/osmosis_routing.json,

**Writes:** data/chemotaxis_state.json

---

### FRACTAL_GENESIS_ENGINE

**Purpose:** FRACTAL_GENESIS_ENGINE.py -- The System That Builds Itself

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 326 |
| Functions | 6 |
| Has run() | Yes |

**Functions:** `load_json`, `save_json`, `find_data_gaps`, `generate_engine_spec`, `write_engine_file`, `run`

**Reads:** data/observatory_report.json, data/self_wiring_report.json,

**Writes:** data/fractal_genesis_report.json, mycelium/GENERATED_*.py

---

### FRACTAL_REPLICATOR

**Purpose:** FRACTAL_REPLICATOR.py -- Template variant multiplier

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 817 |
| Functions | 5 |
| Has run() | Yes |

**Functions:** `load_json`, `save_json`, `file_hash`, `generate_variant_content`, `run`

**Reads:** products/templates/ for existing templates

**Writes:** products/templates/{domain}/variants/*

---

### GENERATED_FRACTAL_REPLICATOR_CONSUMER

**Purpose:** GENERATED_FRACTAL_REPLICATOR_CONSUMER.py -- Auto-generated by FRACTAL_GENESIS_ENGINE

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 48 |
| Functions | 1 |
| Has run() | Yes |

**Functions:** `run`

**Reads:** fractal_replicator_report.json

**Writes:** data/fractal_replicator_insights.json

---

### MYCELIUM_NETWORK

**Purpose:** MYCELIUM_NETWORK.py -- Bio-Inspired Nutrient Transport & Self-Healing Network

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 626 |
| Functions | 10 |
| Has run() | Yes |

**Functions:** `load_json`, `compute_nutrient_map`, `find_nutrient_gradients`, `assess_wire_health`, `detect_breaks`, `find_decomposition_targets`, `propagate_signals`, `compute_reciprocal_rewards`, `compute_network_memory`, `run`

**Writes:** data/mycelium_network_state.json

---

### OSMOSIS_ROUTER

**Purpose:** OSMOSIS_ROUTER.py — Help Flows Toward Information Voids (Molecular Pattern)

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 271 |
| Functions | 6 |
| Has run() | No |

**Functions:** `load_json`, `count_signals_by_region`, `calculate_attention_debt`, `generate_routing_directives`, `calculate_coverage_equity`, `main`

**Reads:** data/crisis_signals.json, data/quorum_state.json,

**Writes:** data/osmosis_routing.json

---

### STIGMERGY

**Purpose:** STIGMERGY.py -- Indirect Coordination Through Traces (Ant Pattern)

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 373 |
| Functions | 7 |
| Has run() | No |

**Functions:** `load_json`, `measure_trace_strength`, `identify_highways`, `identify_dead_ends`, `identify_exploration_targets`, `calculate_colony_health`, `main`

**Reads:** data/*.json (all engine output files as "pheromone traces")

**Writes:** data/stigmergy_state.json, data/pheromone_map.json

---

### SYMBIOGENESIS

**Purpose:** SYMBIOGENESIS.py -- Engine Capability Fusion (Endosymbiosis Pattern)

| Property | Value |
|----------|-------|
| Layer | ? |
| Lines | 315 |
| Functions | 4 |
| Has run() | No |

**Functions:** `load_json`, `evaluate_bond_strength`, `discover_new_pairs`, `main`

**Reads:** data/pathway_strength.json, data/pheromone_map.json,

**Writes:** data/symbiogenesis_state.json

---

## About This System

The SolarPunk Nerve Center is an autonomous, bio-inspired AI system
composed of 379 engines organized into 11 categories.
Each engine is a self-contained unit that reads data, processes it,
and writes results -- forming a living neural network of code.

The system runs without human intervention, healing itself,
generating revenue, monitoring crises, and amplifying voices
that powerful systems want silenced.

*Built by Meeko. Powered by the Mycelium.*

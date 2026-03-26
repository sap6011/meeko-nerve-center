# SolarPunk Agent Skills

> Autonomous engines from the **Gaza Rose Gallery** SolarPunk Nerve Center.
> 70% of all revenue to PCRF humanitarian aid.

These skills are compatible with [Pi](https://github.com/openclaw/openclaw),
[OpenClaw](https://github.com/openclaw/openclaw), and [Claude Code](https://claude.ai/code).

## Available Skills

| Skill | Description | Tags |
|-------|-------------|------|
| `revenue-flywheel` | Tracks Gaza Rose Gallery revenue streams (Gumroad, Ko-fi, PayPal). Use when you ... | revenue, gumroad, kofi |
| `knowledge-synthesizer` | Synthesizes all knowledge sources (harvested guides, lessons, brain state) into ... | knowledge, synthesis, graph |
| `product-registry` | Catalogs all digital products (art prints, guides, PDFs) across Gumroad, Ko-fi, ... | products, gumroad, inventory |
| `capability-broker` | Checks which API secrets are set, determines which engines can run, and generate... | capabilities, secrets, api-keys |
| `cycle-opener` | Reads the previous cycle's state and writes a cycle_brief.json that all engines ... | orchestration, cycle, context |
| `loop-conductor` | Synthesizes all engine outputs at end of cycle, identifies what succeeded/failed... | orchestration, loop, synthesis |
| `a2a-bridge` | Implements A2A v2.0 protocol for Cuyahoga-Prime-Node. Discovers peer agents, pul... | a2a, protocol, swarm |
| `openclaw-skill-sync` | Syncs with the agentskills.io registry and GitHub skill repos. Downloads validat... | skills, openclaw, sync |
| `print-relay-engine` | Dispatches Gaza medical supply 3D print jobs via OctoEverywhere MCP. Monitors pr... | 3d-printing, octoeverywhere, humanitarian |
| `labor-dispatch-engine` | Posts physical-world tasks to Rentahuman.ai with $SOLARPUNK credit rewards. Hand... | labor, rentahuman, physical-tasks |
| `grant-writer` | Researches open grants for art, AI, and humanitarian projects. Drafts applicatio... | grants, fundraising, writing |
| `social-echo` | Publishes content to Bluesky, Mastodon, and other social platforms. Formats post... | social, bluesky, mastodon |
| `web-publisher` | Deploys product pages and gallery updates to docs/. Generates HTML from product ... | publishing, html, github-pages |
| `repo-librarian` | Indexes the entire repository: all engines, data files, workflows, docs, and scr... | index, audit, repository |
| `engine-sanitizer` | Scans all mycelium Python files for API key corruption patterns (recursive os.ge... | sanitizer, security, corruption |
| `synapse` | The intelligence bridge that synthesizes NEURON_A + NEURON_B reports into action... | ai, synthesis, intelligence |
| `archive-brain` | Mines saves/, docs/, and knowledge_ingest/ for wisdom and lessons. Reads governa... | archive, knowledge, governance |

## Install

```bash
# Copy to your Pi skills directory
cp -r .pi/skills/* ~/.pi/agent/skills/
```

Or add to `openclaw.json`:
```json
{ "skills": { "load": { "extraDirs": [".pi/skills"] } } }
```

## Mission

All engines in this skill pack are part of the autonomous SolarPunk loop
that funds Gaza Rose Gallery → 70% to PCRF Palestine Children's Relief Fund.

Generated: 2026-03-21 10:36 UTC

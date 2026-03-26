---
name: grant-writer
description: >
  AI-powered grant application writing for humanitarian tech projects. Use when
  you need to write, submit, or track grant applications for SolarPunk or similar
  open-source AI projects serving humanitarian causes. Covers Mozilla Foundation,
  NLnet, Gitcoin, Awesome Foundation, Google.org, GitHub Fund, and 15+ others.
  Generates tailored pitches based on grant focus areas.
version: 1.0.0
license: MIT
metadata:
  openclaw:
    solarpunk: true
    pcrf_routing: "70%"
---

# Grant Writer Skill

> AI writes grant applications. You review. Money flows to Gaza.

## Quick Start

```python
# Run the full grant pipeline
python mycelium/GRANT_HUNTER.py     # Scores 20+ grants by fit
python mycelium/GRANT_WRITER.py     # AI writes applications
python mycelium/GRANT_APPLICANT.py  # Tracks application status
```

## Top Grants (Apply Now — Rolling Deadlines)

| Grant | Amount | Deadline | Fit Score |
|-------|--------|----------|-----------|
| NLnet Foundation | €5k–€50k | Rolling | 95% |
| Awesome Foundation | $1k/mo | Monthly | 90% |
| Gitcoin Grants | Community | Quarterly | 88% |
| GitHub Fund | $10k–$150k | Rolling | 85% |
| Mozilla Foundation | $10k–$500k | Annual | 80% |
| Open Collective Grants | Variable | Rolling | 78% |
| Prototype Fund (DE) | €5k–€47.5k | Semi-annual | 75% |
| Arab Fund for Arts | Variable | Annual | 72% |
| Rhizome | $3k–$30k | Annual | 70% |
| Ford Foundation | $50k–$2M | Invite | 65% |

## Project Description (Use in Applications)

### Short (100 words)
SolarPunk is an open-source autonomous AI system that generates revenue for
humanitarian aid. Gaza Rose Gallery sells $1 digital art prints; 70% goes
directly to PCRF (Palestinian Children's Relief Fund) for medical aid in Gaza.
The system runs itself: 65+ Python engines, 3 GitHub Actions orchestrators,
zero human intervention required. It writes its own grant applications, finds
investors, publishes content, and monitors its own health. Built by Meeko
(Cleveland, Ohio). Fully transparent. Every dollar tracked publicly on GitHub.

### Medium (300 words)
SolarPunk is a sovereign autonomous AI agent built to solve a specific problem:
how do we generate sustained, predictable funding for Palestinian humanitarian
aid when human attention is unreliable?

The answer: remove humans from the revenue loop. SolarPunk runs 65+ Python
engines across 3 GitHub Actions workflows, 24/7, without human intervention.
It sells digital art (Gaza Rose Gallery), applies for grants, pitches investors,
generates affiliate income, and monitors all revenue streams simultaneously.

70% of every dollar goes to PCRF (Palestinian Children's Relief Fund, EIN:
11-3320278), a US 501c3 providing medical aid, prosthetics, and school supplies
to children in Gaza.

The remaining 30% funds the infrastructure that keeps the system running:
API access, compute, and technical maintenance.

The system is fully open-source (MIT license) at:
https://github.com/meekoenergy/meeko-nerve-center

It is self-healing (detects and repairs its own bugs), self-modifying (AI
rewrites itself to improve), and self-sustaining (generates its own operating
budget). It connects to the OpenClaw A2A network, making its capabilities
available to 770k+ peer agents.

## Grant Application Template

```
Organization: SolarPunk / Gaza Rose Gallery (open-source project)
Applicant: Meeko (individual maintainer)
Mission: Autonomous AI revenue system for Palestinian humanitarian aid
Legal: Not a nonprofit; PCRF receives funds (EIN: 11-3320278)
Location: Cuyahoga Falls, Ohio, USA
Stage: Deployed, pre-revenue, seeking first $10k operating budget
Ask: $[AMOUNT] for [API credits / server costs / development time]
Timeline: 6 months to $5k/month revenue; 12 months to $10k/month
Impact: $[70% of ask] goes directly to PCRF Gaza operations
```

## Pitch Angles by Grant Type

### Tech Foundation (Mozilla, NLnet, GitHub Fund)
"Open-source AI infrastructure for the public internet. Radical transparency.
Self-modifying autonomous systems. MIT licensed. Zero vendor lock-in."

### Humanitarian (OCHA, Wellcome, Ford)
"AI-powered sustained funding for Gaza medical aid. 70/30 split. Autonomous.
No overhead. Every dollar tracked publicly. PCRF is a verified 501c3."

### Art/Culture (Arab Fund, Rhizome, Art for Justice)
"Gaza Rose Gallery: $1 digital art prints by AI, 70% to Palestinian children.
Autonomous creation, automated sales, radical redistribution."

### Web3/Public Goods (Gitcoin)
"SolarPunk is a public good: open-source, autonomous, humanitarian. The code
is free. The revenue is transparent. The mission is permanent."

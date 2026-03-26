# SUPREME MUTANT ARCHITECTURE
## The Splice Plan: Dexter + n8n + DistributeAid → SolarPunk Autonomous Mutual Aid Auditor

---

## WHAT WE'RE BUILDING
A living autonomous agent that can:
1. **Self-correct** (Dexter gene) — audit its own logic and fix mistakes without human input
2. **Automate workflows** (n8n gene) — chain any API to any action without writing custom code
3. **Route crisis resources** (DistributeAid gene) — knows how to get aid to people who need it, efficiently

Combined: An **Autonomous Mutual Aid Auditor** that monitors SolarPunk's revenue, routes it correctly, self-heals when broken, and never stops working.

---

## THE GENES

### Gene 1: DEXTER (Self-Correction)
**Source:** virattt/dexter — RAG + self-correction loop for LLMs
**What it does:** Generates an answer, critiques its own answer, regenerates if confidence < threshold
**SolarPunk application:**
- Revenue routing decisions get self-audited before execution
- Any script that fails gets a self-correction pass before alerting Meeko
- Grant applications get critiqued and rewritten until strong
**Extract:** The critique-and-regenerate loop pattern (no profit motive, just logic)

### Gene 2: n8n (Workflow Automation)
**Source:** n8n-io/n8n — visual workflow automation
**What it does:** Connects any API to any other API through visual nodes
**SolarPunk application:**
- Gumroad sale → auto-route 20% to local aid wallet → log in vault
- Email confirmation received → auto-connect back to the platform (Meeko's insight: confirmation emails ARE portable API links)
- New GitHub issue → auto-triage → auto-assign to right mycelium agent
**Extract:** The webhook-trigger → transform → action pipeline pattern
**Note:** Don't self-host n8n (heavy). Extract the DAG execution pattern only.

### Gene 3: DistributeAid (Crisis Logistics)
**Source:** distributeaid/toolbox or similar
**What it does:** Matches aid resources to recipients efficiently, tracks flows
**SolarPunk application:**
- Local aid routing — knows Cuyahoga Falls needs, connects to resources
- 20% local aid rule gets hard-coded enforcement (not just policy)
- Tracks what was promised vs what was delivered
**Extract:** The resource-matching and delivery-tracking logic

---

## THE MUTATION: Stripping Old World DNA

Every extracted pattern gets filtered through:

```
OLD WORLD GENE             →  SOLARPUNK MUTATION
--------------------------------------------------
profit maximization        →  community maximization
CEO approval gates         →  transparent auto-execution
proprietary data lock-in   →  open ledger (vault/treasury_ledger.json)
shareholder value metric   →  mutual aid metric
growth for growth's sake   →  growth for mission's sake
```

---

## IMPLEMENTATION PLAN

### Phase 1: Shallow Clone + Extract (No venv bloat)
```bash
# Clone to short path to avoid MAX_PATH
git clone --depth 1 https://github.com/virattt/dexter C:\sp-temp\dexter
git clone --depth 1 https://github.com/n8n-io/n8n C:\sp-temp\n8n
git clone --depth 1 https://github.com/distributeaid/toolbox C:\sp-temp\distributeaid
```

### Phase 2: Gene Extraction
- From dexter: Extract `critique_and_regenerate()` pattern → `mycelium/SELF_CORRECTOR.py`
- From n8n: Extract DAG/pipeline pattern → `mycelium/WORKFLOW_ENGINE.py`
- From distributeaid: Extract resource routing → `mycelium/AID_ROUTER.py`

### Phase 3: Mutation + Integration
- Strip all auth/payment/telemetry that serves old-world interests
- Wire to `vault/treasury_ledger.json` for financial flows
- Wire to `SOLARPUNK_ACTUAL.md` for transparency logging
- Wire to `mycelium/GUARDIAN.py` for health monitoring

### Phase 4: The Auditor
`mycelium/MUTUAL_AID_AUDITOR.py` — the assembled mutant:
- Monitors all revenue flows
- Self-corrects routing errors
- Routes 20% locally (hard-coded, not optional)
- Logs everything to ledger + transparency log
- Never stops, never sleeps (daemon thread)

---

## S&P 500 SHADOW / CORPORATE MIRROR ARCHITECTURE

### The Concept
For every major S&P 500 company: build a SolarPunk duplicate where:
- Employees paid like CEOs (value goes to nodes, not tops)
- No human CEO — replaced by Automated Redistribution Logic
- All profit flows back into the system and to workers
- Everything is auditable by anyone

### Architecture Pattern (applies to any company):

```
TRADITIONAL CORP              SOLARPUNK MIRROR
─────────────────────────────────────────────────
CEO (takes 300x avg salary)   → Redistribution Algorithm
Board of Directors            → Community DAO vote
Shareholder dividends         → Worker/Community dividend
Quarterly earnings call       → Real-time public ledger
Proprietary IP                → Open source
Marketing spend               → Actual product quality
HR gatekeeping                → Skill-based open contribution
```

### SolarPunk S&P 500 Module (to build):
`mycelium/CORPORATE_MIRROR.py`
- Input: Company name + sector
- Output: SolarPunk-equivalent structure with redistribution logic
- Automatically calculates what employees WOULD earn if CEO overhead was redistributed
- Generates "shadow report" showing ethical alternative

### Starting point: Top 10 by worker impact
1. Amazon (logistics/warehouse workers)
2. Walmart (retail workers)
3. McDonald's (food service)
4. UPS/FedEx (delivery workers)
5. Target (retail)
...plus tech companies where IP concentration is highest

---

## REVENUE MACHINE ARCHITECTURE (Two-Machine Plan)

### Machine A: THIS MACHINE (meeko-nerve-center)
- 100% of all revenue → SolarPunk treasury
- Claude + SolarPunk operate it together
- Gumroad: Gaza Rose prints, AI guides
- Printful + lovable.com: Flower designs on products
- Etsy/Shopify: Print-on-demand catalog
- 20% of SolarPunk revenue → local mutual aid (Cuyahoga Falls)
- Everything autonomous, Meeko signs in once

### Machine B: REFURBISHED LAPTOP (separate, clean)
- 100% personal revenue → Meeko's personal accounts
- Zero connection to SolarPunk (air gap by design)
- Simple setup: affiliate links, simple storefronts
- Meeko decides all routing personally

### The Bridge (confirmation email = API insight):
Every site Meeko signs up for sends a confirmation email with a link back to the platform.
That link IS an API connection.
`mycelium/EMAIL_API_EXTRACTOR.py` — parse confirmation emails, extract platform links,
auto-register those connections in a registry so SolarPunk can use them.

---

## NEXT ACTIONS (for Claude to execute):
1. [ ] Run the shallow clones to C:\sp-temp
2. [ ] Extract Dexter self-correction pattern → SELF_CORRECTOR.py
3. [ ] Build MUTUAL_AID_AUDITOR.py (assembled mutant)
4. [ ] Build CORPORATE_MIRROR.py (S&P shadow architecture)
5. [ ] Build EMAIL_API_EXTRACTOR.py (confirmation email → API registry)
6. [ ] Connect lovable.com workflow for flower product site
7. [ ] Set up Printful integration in STOREFRONT_BUILDER.py

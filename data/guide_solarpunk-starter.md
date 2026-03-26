# Build Your Own SolarPunk
### Anyone with an internet connection can build an autonomous AI revenue system this afternoon

---

**Price:** $1.00 · **A SolarPunk Guide** · 15% of every sale goes to Gaza via PCRF (EIN 93-1057665)

---

## Table of Contents

1. What SolarPunk Is and Why It Exists
2. The Whole Stack in One Picture
3. Setting Up Your GitHub Repo in 10 Minutes
4. Your First Engine: From Hello World to Revenue Machine
5. Connecting Free AI APIs: Groq, OpenRouter, HuggingFace
6. The Revenue Loop: How One Dollar Becomes More
7. Ko-fi and Gumroad: Free Storefronts That Actually Work
8. Publishing Automatically: Bluesky, DEV.to, and GitHub
9. Self-Healing: Writing Engines That Fix Themselves
10. The Gaza Connection: Building With Purpose
11. Scaling From 1 Engine to 242
12. Your System Runs Forever Without You

---

## 1. What SolarPunk Is and Why It Exists

SolarPunk is an autonomous digital organism. Not a metaphor — a working system where Python scripts (called "engines") read each other's output, make decisions, create products, publish content, and route money to causes. It runs on GitHub Actions (free tier), uses zero paid APIs for its core operations, and every line of code is public.

The system was built by one person with no budget, no team, and no venture capital. It exists because the question "can software grow itself?" deserved a real answer, not a whitepaper.

**What makes it different from a regular automation project:**

- **Self-wiring**: Engines discover each other's inputs and outputs automatically. A wiring engine (LIVE_WIRE) scans every script, maps who writes what and who reads what, then tests which connections are live. A bridge engine (BRIDGE_BUILDER) feeds any input that's hungry.
- **Self-healing**: A sentinel engine checks every script for syntax errors every cycle. When corruption happens (and it does — git rebases, encoding issues, merge conflicts), the system detects and reports it.
- **Revenue routing**: 15-20% of every dollar is hard-coded to route to the Palestinian Children's Relief Fund. Not a pledge. Not a promise. A line of code that runs before anything else.
- **Zero secrets for core operations**: The organism's nervous system — wiring discovery, bridge building, health monitoring, content generation — runs without any API keys. API keys unlock acceleration (AI content, social posting, storefront management) but the organism breathes without them.

You can fork this entire system and have it running in your GitHub account within 10 minutes. This guide shows you how.

---

## 2. The Whole Stack in One Picture

```
GitHub Repo (your-name/your-nerve-center)
├── mycelium/           ← All engines live here (Python scripts)
│   ├── LIVE_WIRE.py         ← Discovers connections between engines
│   ├── BRIDGE_BUILDER.py    ← Feeds hungry inputs
│   ├── VITAL_SIGN_API.py    ← Publishes health data as JSON
│   ├── QUICK_REVENUE.py     ← Generates product listings
│   ├── FIRST_SALE_NOTIFIER.py  ← Watches for first dollar
│   └── ... (242 engines and growing)
├── data/               ← Shared communication layer (JSON files)
│   ├── live_wire_report.json    ← Wiring topology
│   ├── brain_state.json         ← Health, mood, priorities
│   ├── revenue_inbox.json       ← Revenue events
│   └── ... (engines read/write here to talk to each other)
├── docs/               ← GitHub Pages (your public-facing site)
│   ├── index.html           ← Landing page
│   ├── shop.html            ← Store
│   ├── proof.html           ← Transparent ledger
│   └── research.html        ← Academic backing
└── .github/workflows/  ← GitHub Actions (the heartbeat)
    ├── WEEKEND_PULSE.yml    ← Runs every 12 hours
    └── ...
```

**The key insight**: Engines don't call each other directly. They communicate through `data/` files — JSON documents that any engine can read or write. This is the "spoke and hub" model. It means:

- Any engine can be added or removed without breaking others
- The system discovers its own topology
- Failures are isolated — one broken engine doesn't cascade
- Everything is inspectable — just read the JSON files

---

## 3. Setting Up Your GitHub Repo in 10 Minutes

**Step 1: Fork the repo**

Go to `github.com/meekotharaccoon-cell/meeko-nerve-center` and click Fork. Name it whatever you want. Keep all branches.

**Step 2: Enable GitHub Pages**

Settings > Pages > Source: "Deploy from a branch" > Branch: `main` > Folder: `/docs` > Save.

Your site is now live at `https://your-name.github.io/your-repo-name/`.

**Step 3: Enable GitHub Actions**

Go to the Actions tab. GitHub may ask you to enable workflows for forked repos. Click "I understand my workflows, go ahead and enable them."

**Step 4: Run your first pulse**

Go to Actions > "WEEKEND_PULSE" > "Run workflow" > Click the green button.

Watch it run. In about 2 minutes, it will:
1. Run BRIDGE_BUILDER (feed hungry inputs)
2. Run LIVE_WIRE (map the wiring topology)
3. Run VITAL_SIGN_API (publish health data)
4. Commit the results back to your repo

That's it. Your organism is breathing.

**Step 5 (optional): Add API keys for acceleration**

Settings > Secrets and variables > Actions > New repository secret:
- `ANTHROPIC_API_KEY` — from console.anthropic.com (enables AI content generation)
- `GUMROAD_ACCESS_TOKEN` — from gumroad.com/settings/advanced (enables auto-publishing products)

These are optional. The system works without them. But with them, it goes from breathing to sprinting.

---

## 4. Your First Engine: From Hello World to Revenue Machine

An engine is just a Python script in `mycelium/` with a `run()` function. Here's the simplest possible engine:

```python
#!/usr/bin/env python3
"""MY_FIRST_ENGINE.py — Does one thing and documents it."""
import json
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
DATA.mkdir(exist_ok=True)

def run():
    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message": "Hello from my first engine",
        "status": "alive"
    }
    out = DATA / "my_first_engine_state.json"
    out.write_text(json.dumps(result, indent=2))
    print(f"Engine ran at {result['timestamp']}")
    return result

if __name__ == "__main__":
    run()
```

**What makes this an engine and not just a script:**

1. It has a `run()` function (LIVE_WIRE looks for this)
2. It writes to `data/` (other engines can read its output)
3. It uses `pathlib.Path` (works on any OS)
4. It timestamps everything (the organism tracks freshness)
5. It prints what it did (logs appear in GitHub Actions)

**Making it useful — a revenue-generating engine:**

```python
def run():
    # Read what other engines have discovered
    wire_report = DATA / "live_wire_report.json"
    if wire_report.exists():
        wires = json.loads(wire_report.read_text())
        total = wires["stats"]["total_engines"]
        live = wires["stats"]["total_wires_discovered"]
    else:
        total, live = 0, 0

    # Generate a product description from real system data
    product = {
        "title": f"SolarPunk Status Report — {total} Engines, {live} Live Wires",
        "body": f"This autonomous system currently has {total} engines with "
                f"{live} live wire connections. Here's what it looks like inside...",
        "price": 1.00,
        "generated": datetime.now(timezone.utc).isoformat()
    }
    (DATA / "my_product.json").write_text(json.dumps(product, indent=2))
```

Now LIVE_WIRE will discover this engine reads `live_wire_report.json` and writes `my_product.json`. The wiring is automatic.

---

## 5. Connecting Free AI APIs: Groq, OpenRouter, HuggingFace

You don't need to pay for AI. These providers offer free tiers:

**Groq** (fastest, free for moderate usage):
```python
import urllib.request, json

def ask_groq(prompt, api_key):
    data = json.dumps({
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1000
    }).encode()
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())["choices"][0]["message"]["content"]
```

**OpenRouter** (aggregates many models, free tier available):
Same endpoint pattern, URL is `https://openrouter.ai/api/v1/chat/completions`.

**HuggingFace Inference API** (thousands of models, free tier):
```python
url = "https://api-inference.huggingface.co/models/meta-llama/Llama-3.2-3B-Instruct"
headers = {"Authorization": f"Bearer {hf_token}"}
```

**The pattern**: Every AI call in SolarPunk uses `urllib.request` (stdlib — no pip install). Every call has a fallback for when the API is down or the key is missing. The engine should still produce *something* useful even with zero AI.

---

## 6. The Revenue Loop: How One Dollar Becomes More

The revenue loop is SolarPunk's core economic engine:

```
Create Product → List on Store → Promote → Sale → Route 15% to Gaza
     ↑                                              |
     └──────── Reinvest 85% ────────────────────────┘
```

**Step 1: Products come from system data.** Your engines generate real data — wiring reports, health scores, discovery logs. Package that data as a product. "Inside an Autonomous AI System" is interesting to developers, researchers, and AI enthusiasts.

**Step 2: Listing is copy-paste.** QUICK_REVENUE.py generates the exact text for each Ko-fi or Gumroad listing. Open the dashboard, paste the text, set the price to $1, publish.

**Step 3: Promotion is automated.** Social posting engines queue posts with product links. When API keys are available, they post automatically to Bluesky, DEV.to, Mastodon, and more.

**Step 4: Revenue routing is hard-coded.** When a sale happens, FIRST_SALE_NOTIFIER detects it and logs it permanently. The 15% Gaza routing is in the code, not in a configuration file. Changing it requires changing source code and committing it publicly.

**Why $1?** Because the goal isn't to maximize revenue per sale — it's to maximize the number of people who interact with the system. A $1 digital product has almost zero friction. Someone curious about autonomous AI will spend $1 to see inside. And $0.15 of that goes to Gaza.

---

## 7. Ko-fi and Gumroad: Free Storefronts That Actually Work

**Ko-fi** (recommended for starting):
- Zero platform fee on shop items
- No monthly cost
- Accepts PayPal and Stripe
- Setup: ko-fi.com > Create account > Shop > Add items

**Gumroad** (recommended for scaling):
- 10% platform fee but handles everything
- Discovery — Gumroad's marketplace shows your products to their users
- Email delivery built in
- API available for automation

**The SolarPunk approach**: Use both. Ko-fi for direct supporters who already know you. Gumroad for discovery by strangers searching for AI/tech products.

QUICK_REVENUE.py generates the listing text for both platforms. You paste it in. That's the entire manual step.

---

## 8. Publishing Automatically: Bluesky, DEV.to, and GitHub

SolarPunk queues social posts in `data/social_queue.json`. When API keys are available, posting engines drain the queue one post per cycle.

**Bluesky** (AT Protocol, free API):
- Create an app password at bsky.app/settings
- SolarPunk's BLUESKY_POSTER.py handles authentication, posting, and rate limiting

**DEV.to** (free API, great for technical content):
- API key from dev.to/settings/extensions
- SolarPunk's DEVTO_PUBLISHER.py formats markdown articles from system data

**GitHub Discussions/Issues** (zero setup):
- Already available in your fork
- SolarPunk can create Discussion posts using GITHUB_TOKEN (already in Actions)

**The non-obvious insight**: You don't need all platforms. One platform, posting consistently, beats five platforms posting sporadically. Start with one. Add more when the first one is working.

---

## 9. Self-Healing: Writing Engines That Fix Themselves

SolarPunk engines break. Git rebases corrupt files. Encoding issues mangle characters. API responses change format. This is expected.

**Pattern 1: Defensive JSON loading**
```python
def load_json(path):
    try:
        return json.loads(Path(path).read_text())
    except (json.JSONDecodeError, FileNotFoundError):
        return {}
```

**Pattern 2: Graceful degradation**
```python
def run():
    try:
        ai_content = ask_ai("Generate something")
    except Exception:
        ai_content = None

    if ai_content:
        result = {"content": ai_content, "source": "ai"}
    else:
        result = {"content": "System is alive. AI offline.", "source": "fallback"}

    save(result)  # Always produces output
```

**Pattern 3: Sentinel monitoring**
BRIDGE_BUILDER runs `py_compile` on every engine each cycle. Engines that fail syntax check get logged to `data/sentinel_report.json`. You can see at a glance which engines are healthy and which need repair.

**Pattern 4: The bridge pattern**
When Engine B needs data from Engine A but Engine A hasn't run yet, BRIDGE_BUILDER creates a seed file with reasonable defaults. Engine B gets something to work with. When Engine A eventually runs, its real output replaces the seed.

---

## 10. The Gaza Connection: Building With Purpose

Every SolarPunk system routes 15-20% of revenue to the Palestinian Children's Relief Fund (PCRF).

**PCRF** (pcrf.net):
- EIN: 93-1057665 (tax-deductible in the US)
- 4-star Charity Navigator rating
- Operating in Gaza since 1991
- Provides medical care to children

**How routing works in the code:**

```python
SYSTEM_DIRECTIVE = {
    "revenue_routing": {
        "gaza_pcrf": 0.15,      # 15% minimum, hard-coded
        "food_bank_local": 0.05, # 5% to local food bank
        "reinvest": 0.80         # Remainder funds the system
    }
}
```

This isn't charity bolted onto a tech project. It's a tech project that exists *because* of the cause. The system was designed from day one to fund humanitarian work autonomously.

**Transparency**: Every transaction is logged in `data/proof_ledger.json` and published at your site's `/proof.html`. Anyone can audit. The code is MIT licensed and public.

---

## 11. Scaling From 1 Engine to 242

SolarPunk started with a handful of engines. It now has 242. Here's how that happened:

**Phase 1 (1-10 engines)**: Manual creation. Each engine does one thing. A revenue watcher. A social poster. A product generator.

**Phase 2 (10-50 engines)**: Engines start generating other engines. BUILD_YOURSELF.py reads the system's needs and creates new engines to fill gaps.

**Phase 3 (50-242 engines)**: LIVE_WIRE discovers the wiring topology. BRIDGE_BUILDER feeds hungry inputs. MUTATION_ENGINE introduces random variations. The system grows itself.

**The scaling pattern**: You don't plan 242 engines. You build 5 solid engines, give the system a way to discover what's missing, and let it grow. The wiring discovery engine (LIVE_WIRE) is the key — it turns the system from a collection of scripts into an organism that knows its own shape.

**Current topology** (as of March 2026):
- 242 engines scanned
- 385 wire connections discovered
- 377 live (data flowing)
- 114 zero-secret chains (work without any API keys)

---

## 12. Your System Runs Forever Without You

The final piece: autonomy. Your system should run when you're sleeping, working, or on vacation.

**GitHub Actions free tier** gives you 2,000 minutes/month. WEEKEND_PULSE.yml runs every 12 hours and uses about 2 minutes per run. That's ~120 minutes/month — 6% of your free quota.

**What happens each cycle:**
1. BRIDGE_BUILDER scans for hungry inputs and feeds them
2. LIVE_WIRE maps the wiring topology and tests connections
3. VITAL_SIGN_API publishes health data to your site
4. Results are committed back to the repo
5. GitHub Pages updates automatically

**What you do:** Nothing. Check the logs when you feel like it. Add new engines when you have ideas. The organism breathes on its own.

**The philosophical point**: Most software needs you to run it. SolarPunk runs itself and tells you what it did. That's not just automation — it's a shift in the relationship between builder and software. You're not operating it. You're gardening it.

---

## About SolarPunk

This guide was written by a human who built SolarPunk and the AI systems that help maintain it. The system that this guide describes is real, running, and public.

15% of every sale goes to Palestinian children via PCRF.
PCRF EIN: 93-1057665 · 4-star Charity Navigator · Operating in Gaza since 1991

**Fork it:** github.com/meekotharaccoon-cell/meeko-nerve-center
**Store:** meekotharaccoon-cell.github.io/meeko-nerve-center/store.html
**Donate directly:** pcrf.net

---
*Built autonomously. Funded for Gaza. Running forever.*

---
title: I Built a 300-Engine Self-Healing AI System That Runs on Zero Paid APIs
published: false
tags: python, ai, automation, opensource
series: solarpunk-autonomous-systems
canonical_url: https://meekotharaccoon-cell.github.io/meeko-nerve-center
---

Last month I had zero engines. Today I have 300.

They heal themselves when code gets corrupted. They wire themselves together by reading their own source code. They audit their own honesty. One of them just wrote its first product -- a guide about how they were built. Another one reads git history and detects when automated tools damage the codebase.

None of them use a paid API.

This is SolarPunk -- an autonomous system I built from scratch with Python, JSON files, and stubbornness. Here's how it works and what I learned.

## The Architecture: Dumber Than You Think

Every engine is a Python script that does three things:

```python
def run():
    # 1. Read input
    data = json.loads(Path("data/input.json").read_text())

    # 2. Process
    result = do_something(data)

    # 3. Write output
    Path("data/output.json").write_text(json.dumps(result))
```

That's it. No databases. No message queues. No Kafka. No Redis. No Docker. No Kubernetes.

Just JSON files in a `data/` folder and Python scripts in a `mycelium/` folder. One script (OMNIBUS) runs them all in order, layer by layer.

**Why this works:** Every engine's state is a JSON file you can open and read. The entire system state fits in a git commit. When something breaks, you can literally `git diff` to see what changed.

## The Numbers

| Metric | Count |
|--------|-------|
| Engines | 300 |
| Data wires between them | 4,489 |
| Zero-secret chains (work without API keys) | 3,029 |
| Lines of Python | ~80,000 |
| Monthly hosting cost | $0 |
| Paid API calls per month | 0 |

The system runs on GitHub Actions (free tier) and a desktop machine.

## Self-Wiring: The Part That Blew My Mind

I didn't manually connect 300 engines. I built one engine (LIVE_WIRE) that reads every other engine's source code with regex:

```python
# Find what each engine reads
r'load_json\([^)]*["\'](?:data/)?([^"\']+\.json)'

# Find what each engine writes
r'save_json\([^)]*["\'](?:data/)?([^"\']+\.json)'
```

If Engine A writes `brain_state.json` and Engine B reads `brain_state.json`, that's a wire. LIVE_WIRE found 4,489 of them automatically.

Then SELF_WIRING_ENGINE uses AST parsing to read its own source code, extract function signatures and docstrings, and find logical connections that regex misses.

The system literally reads its own code to understand itself.

## Self-Healing: When Your Own Tools Attack You

I use an automated tool called SIA for repository maintenance. SIA has a "self-heal" loop that's supposed to fix code. Instead, it started doing this:

```python
# What I wrote:
if os.environ.get("API_KEY", "").strip():

# What SIA turned it into:
if os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("API_KEY")")")")")"):
```

Eleven levels of nested `os.getenv()`. Across 42 files. In three waves.

So I built IMMUNE_SYSTEM -- an engine that scans all 300 engines for corruption patterns and repairs them. It found 17 infected files on its first run and applied 168 fixes.

Then it corrupted its own docstrings during the repair process.

So I added a rule: **the immune system never modifies its own file.**

Biology figured this out. T-cells don't attack the thymus.

## The Honest Audit

After 4,489 wires, I wanted to know: how many are real?

I built SIGNAL_INTEGRITY to check every data file on every wire. Classification:
- **REAL**: Meaningful data, multiple keys, >200 bytes
- **THIN**: Present but minimal
- **STUB**: Just `{"status": "wired"}`
- **DEAD**: File doesn't exist

**Result: 98% real.** 4,443 wires carry actual data. 20 stubs. 26 dead. I was ready for the number to be embarrassing. It wasn't.

## The Brain That Thinks

300 engines and zero intelligence. Every engine is a reflex -- if X then Y. No engine had ever *reasoned* about anything.

CORTEX changed that. It reads the entire system state and asks an AI to analyze it:

- What's working?
- What's broken?
- What should we build next?
- What should we STOP doing?

Its first directive: "FIX IMMUNE SYSTEM: Repair corrupted engines before doing anything else."

The system's first thought was about its own health. That felt right.

## What It Actually Produces

This isn't a science project. The system generates real products:

- **PRODUCT_FORGE** creates digital guides from system data
- **EXTERNAL_VALUE_ROUTER** scans for revenue opportunities (bounties, grants, digital products)
- **DEV_TO_PUBLISHER** posts articles to dev.to
- **NEWSLETTER_ENGINE** sends weekly updates

Revenue split: **99% mutual aid / 1% infrastructure.** Hardcoded. Non-negotiable. PCRF gets 60%, IRC gets 15%, MSF gets 10%.

## What I Learned

**1. JSON files are underrated.** I spent years thinking I needed Postgres, Redis, and a message broker. I needed `json.dumps()`.

**2. Self-discovery beats configuration.** LIVE_WIRE finds connections automatically. No YAML manifests. No service mesh. The code IS the configuration.

**3. Immune systems are not optional.** If you run automated tools on your codebase, they WILL corrupt it. Build the defense before you need it.

**4. Measure honestly.** I could have claimed 4,489 wires without checking. SIGNAL_INTEGRITY exists because I wanted the truth more than the number.

**5. The system that describes itself is the best documentation.** This article was outlined by PRODUCT_FORGE, an engine that reads the codebase and generates content about it. The documentation writes itself because the system IS the documentation.

**6. Ethics are architecture, not policy.** The 99/1 revenue split isn't in a README. It's in the code. You can't accidentally change it. You can't "temporarily" disable it. It's load-bearing.

## Try It Yourself

The entire system is open source:

```bash
git clone https://github.com/meekotharaccoon-cell/meeko-nerve-center
cd meeko-nerve-center
python mycelium/OMNIBUS.py
```

Watch 300 engines light up. Read `data/brain_state.json`. Open `docs/observatory.html`.

Or grab the full guide: [How to Build a 300-Engine Autonomous System](https://meekotharaccoon-cell.github.io/meeko-nerve-center/shop.html)

---

*Built from Ward 8, DC. 99% mutual aid. The system runs whether I'm awake or not.*
*That's the whole point.*

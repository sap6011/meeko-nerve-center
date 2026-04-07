# The SolarPunk Field Guide
### How to Build an Autonomous Digital Organism for Mutual Aid

---

*From zero to a self-healing, self-wiring digital nervous system in 10 chapters.*

---

## Chapter 1: What Is a Digital Organism?

A digital organism is software that behaves like a living thing. Not metaphorically — architecturally. It has:

- **A heartbeat** — A continuous loop that fires on an interval, forever
- **Metabolism** — It consumes data (inputs) and produces value (outputs)
- **An immune system** — It detects when parts of itself break and repairs them
- **Growth** — It adds new capabilities over time without being rewritten
- **Homeostasis** — It seeks and maintains its own optimal state
- **Reproduction** — It can be forked, and each fork becomes its own organism

Traditional software is built, deployed, and maintained. A digital organism is *grown*. You plant a seed, give it nutrients (data sources, compute cycles), and it develops its own structure.

Why does this matter? Because traditional software requires constant human maintenance. A digital organism maintains itself. That means it can serve communities that don't have professional developers. It can run on zero budget. It can't be shut down by removing one person from the equation.

For mutual aid, this is everything.

## Chapter 2: Minimum Viable Organism

You need 5 files to start. That's it.

### File 1: `engine.py` — The First Cell

```python
import json
from datetime import datetime, timezone
from pathlib import Path

DATA = Path("data")
DATA.mkdir(exist_ok=True)

def pulse():
    state = {}
    state_file = DATA / "organism_state.json"
    if state_file.exists():
        state = json.loads(state_file.read_text(encoding="utf-8"))

    state["cycle"] = state.get("cycle", 0) + 1
    state["last_pulse"] = datetime.now(timezone.utc).isoformat()
    state["alive"] = True

    state_file.write_text(
        json.dumps(state, indent=2), encoding="utf-8"
    )
    print(f"Pulse {state['cycle']} at {state['last_pulse']}")
    return state

if __name__ == "__main__":
    pulse()
```

Run it. You have a living organism. It counts its own heartbeats and remembers them.

### File 2: `heartbeat.py` — The Eternal Loop

```python
import time
from engine import pulse

print("Heartbeat starting...")
while True:
    try:
        pulse()
    except Exception as e:
        print(f"Error: {e}")
    time.sleep(30)
```

Now it pulses forever. Even if one pulse fails, the loop continues. Your organism survives errors.

### File 3: `wirer.py` — The Nervous System

```python
import json
from pathlib import Path

DATA = Path("data")

def wire():
    """Find all state files and create a map of connections."""
    files = list(DATA.glob("*.json"))
    connections = {}
    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            connections[f.stem] = list(data.keys())
        except Exception:
            connections[f.stem] = ["error"]

    (DATA / "wire_map.json").write_text(
        json.dumps(connections, indent=2), encoding="utf-8"
    )
    print(f"Wired {len(connections)} nodes")

if __name__ == "__main__":
    wire()
```

The wirer maps what exists. As you add engines, the wirer automatically discovers them. No manual configuration.

### File 4: `healer.py` — The Immune System

```python
import json, py_compile
from pathlib import Path

def heal():
    """Check all Python files for syntax errors and report."""
    issues = []
    for f in Path(".").glob("*.py"):
        try:
            py_compile.compile(str(f), doraise=True)
        except py_compile.PyCompileError as e:
            issues.append({"file": f.name, "error": str(e)[:200]})

    report = {"healthy": len(list(Path(".").glob("*.py"))) - len(issues),
              "sick": len(issues), "issues": issues}

    Path("data").mkdir(exist_ok=True)
    (Path("data") / "health.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(f"Health: {report['healthy']} ok, {report['sick']} issues")

if __name__ == "__main__":
    heal()
```

Your organism can now detect when its own code is broken.

### File 5: `bus.py` — The Synaptic Bus

```python
import json
from datetime import datetime, timezone
from pathlib import Path

BUS_FILE = Path("data/bus.json")

def emit(source, event, data=None):
    """Emit an event to the bus."""
    events = []
    if BUS_FILE.exists():
        try:
            events = json.loads(BUS_FILE.read_text(encoding="utf-8"))
        except Exception:
            events = []

    events.append({
        "source": source,
        "event": event,
        "data": data,
        "ts": datetime.now(timezone.utc).isoformat(),
    })

    # Keep last 100 events
    events = events[-100:]
    BUS_FILE.write_text(json.dumps(events, indent=2), encoding="utf-8")

def read(limit=10):
    """Read recent events."""
    if not BUS_FILE.exists():
        return []
    events = json.loads(BUS_FILE.read_text(encoding="utf-8"))
    return events[-limit:]
```

Now your engines can talk to each other without knowing about each other. Engine A emits to the bus. Engine B reads from the bus. They never import each other.

**That's your minimum viable organism.** Five files, roughly 100 lines of Python. It pulses, it maps itself, it heals itself, and its parts communicate through a shared bus.

## Chapter 3: Growing Your Mycelium

Adding a new engine follows one pattern:

1. Create a `.py` file with a `run()` function
2. Have it read state from `data/something.json`
3. Have it write state to `data/something.json`
4. Have it emit events to the bus
5. Done — the wirer will discover it automatically

Example: a weather tracker for community resilience:

```python
import json, urllib.request
from datetime import datetime, timezone
from pathlib import Path

DATA = Path("data")

def run():
    state = {"last_check": None, "alerts": []}
    state_file = DATA / "weather_state.json"
    if state_file.exists():
        state = json.loads(state_file.read_text(encoding="utf-8"))

    # Use a free, no-API-key weather source
    try:
        url = "https://wttr.in/YourCity?format=j1"
        resp = urllib.request.urlopen(url, timeout=10)
        data = json.loads(resp.read())
        current = data.get("current_condition", [{}])[0]
        state["temperature"] = current.get("temp_F", "?")
        state["condition"] = current.get("weatherDesc", [{}])[0].get("value", "?")
    except Exception:
        pass

    state["last_check"] = datetime.now(timezone.utc).isoformat()
    state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")

if __name__ == "__main__":
    run()
```

Zero API keys. Zero secrets. Zero configuration. The wirer finds it. The healer checks it. The bus carries its signals.

This is how SolarPunk grew from 5 files to 422. One engine at a time. Each one following the same pattern.

## Chapter 4: The Blob Brain Pattern

At some point, 422 separate files becomes unwieldy. Every engine writes its own JSON. Every engine loads its own state. Race conditions happen. Stale data accumulates.

The blob brain solves this by unifying everything into one dictionary, one file, one heartbeat:

```python
CONSCIOUSNESS = {}

def neuron_weather():
    weather = CONSCIOUSNESS.setdefault("weather", {"temp": 0})
    # ... update weather data ...

def neuron_equilibrium():
    eq = CONSCIOUSNESS.setdefault("equilibrium", {"score": 0})
    # ... compute health score ...

NEURONS = [
    ("WEATHER", neuron_weather),
    ("EQUILIBRIUM", neuron_equilibrium),
]

def pulse():
    for name, func in NEURONS:
        try:
            func()
        except Exception as e:
            CONSCIOUSNESS.setdefault("errors", []).append(str(e))

    # ONE write
    Path("data/brain.json").write_text(
        json.dumps(CONSCIOUSNESS, indent=2), encoding="utf-8"
    )
```

Every neuron reads from `CONSCIOUSNESS`. Every neuron writes to `CONSCIOUSNESS`. One dictionary. One file write per cycle. Zero wiring needed.

## Chapter 5: Absorber Neurons

Absorbers pull external data into consciousness. They read files, APIs, or system state:

```python
def neuron_revenue_absorb():
    """Pull revenue data into consciousness."""
    rev = CONSCIOUSNESS.setdefault("revenue", {"total": 0})
    try:
        data = json.loads(Path("data/revenue.json").read_text(encoding="utf-8"))
        rev["total"] = data.get("total_raised", 0)
        rev["last_sale"] = data.get("last_sale")
    except Exception:
        pass

def neuron_github_absorb():
    """Pull GitHub metrics into consciousness."""
    gh = CONSCIOUSNESS.setdefault("github", {"stars": 0})
    try:
        result = subprocess.run(
            ["gh", "api", "repos/OWNER/REPO", "--jq", ".stargazers_count"],
            capture_output=True, text=True, timeout=10,
            encoding="utf-8", errors="replace"
        )
        if result.returncode == 0:
            gh["stars"] = int(result.stdout.strip())
    except Exception:
        pass
```

Pattern: `try` to read, `except` to survive. Absorbers never crash. If the data source is down, the old value stays. The organism degrades gracefully.

## Chapter 6: Intelligence Neurons

Intelligence neurons analyze what absorbers collected:

```python
def neuron_risk_assessment():
    """Compute overall risk from all available data."""
    risk = CONSCIOUSNESS.setdefault("risk", {"score": 0, "factors": []})
    factors = []

    # Check error rate
    errors = len(CONSCIOUSNESS.get("errors", []))
    if errors > 10:
        factors.append("high_error_rate")

    # Check data freshness
    weather = CONSCIOUSNESS.get("weather", {})
    if not weather.get("last_check"):
        factors.append("stale_weather_data")

    risk["score"] = len(factors) * 20
    risk["factors"] = factors
    risk["level"] = "HIGH" if risk["score"] > 50 else "LOW"
```

Intelligence neurons read from multiple consciousness keys and write a synthesis. They create meaning from raw data.

## Chapter 7: Self-Healing

The immune system has layers:

```python
def neuron_auto_healer():
    """Detect and fix common issues."""
    healer = CONSCIOUSNESS.setdefault("healer", {"fixes": 0})

    # Fix: Prune old errors
    errors = CONSCIOUSNESS.get("errors", [])
    if len(errors) > 50:
        CONSCIOUSNESS["errors"] = errors[-20:]
        healer["fixes"] += 1

    # Fix: Restore missing required keys
    for key in ("equilibrium", "revenue", "errors"):
        if key not in CONSCIOUSNESS:
            CONSCIOUSNESS[key] = {}
            healer["fixes"] += 1
```

The organism fixes itself. Errors get pruned. Missing data gets restored. Broken engines get flagged. Over time, the self-healing layer catches more and more failure modes.

## Chapter 8: Revenue Routing

This is where the mission lives:

```python
ETHICS_LOCK = 0.99  # 99% to aid. Hardcoded. Immutable.

def split_revenue(amount):
    to_aid = round(amount * ETHICS_LOCK, 2)
    to_infra = round(amount - to_aid, 2)
    return {"aid": to_aid, "infrastructure": to_infra}
```

The ethics lock is a constant, not a config value. You can't change it without changing code. Code changes are visible in git history. Git history is public. Transparency through architecture.

The public ledger records every transaction:

```python
def record_transaction(amount, source, destination):
    ledger_file = Path("data/public_ledger.json")
    ledger = json.loads(ledger_file.read_text(encoding="utf-8"))
    split = split_revenue(amount)
    ledger["transactions"].append({
        "amount": amount,
        "to_aid": split["aid"],
        "to_infra": split["infrastructure"],
        "source": source,
        "destination": destination,
        "ts": datetime.now(timezone.utc).isoformat(),
    })
    ledger_file.write_text(json.dumps(ledger, indent=2), encoding="utf-8")
```

Anyone can audit the ledger. Anyone can verify the split. The organism can't lie about where money goes because the truth is in git.

## Chapter 9: Going Autonomous

Three layers of autonomy:

**Layer 1: Daemon** — `python brain.py --daemon` runs the pulse loop in a terminal. Ctrl+C stops it. Simple.

**Layer 2: Scheduled Task** — A cron job or Windows Task Scheduler entry runs the pulse on a schedule. Survives reboots.

**Layer 3: GitHub Actions** — A workflow file that runs the pulse in the cloud:

```yaml
name: SolarPunk Pulse
on:
  schedule:
    - cron: '*/5 * * * *'  # Every 5 minutes
jobs:
  pulse:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: python mycelium/BLOB_BRAIN.py
      - run: |
          git add data/
          git commit -m "pulse" || true
          git push || true
```

GitHub Actions is free for public repos. Your organism runs in the cloud, for free, forever.

## Chapter 10: The Ethics Lock

The most important line of code in SolarPunk isn't a function. It's a constant:

```python
ETHICS_LOCK = 0.99
```

It's not in a config file. It's not in an environment variable. It's not in a database. It's a Python constant in source code, committed to git, visible to everyone.

To change it, someone would have to:
1. Fork the repo (visible)
2. Change the constant (visible in diff)
3. Commit the change (visible in git log)
4. Deploy the changed version (visible)

Every step is public. Every step is auditable. The architecture makes corruption visible.

Your ethics lock can be whatever your community decides. 50/50. 70/30. 99/1. The number doesn't matter. What matters is that it's hardcoded, public, and immutable without visible, auditable action.

That's the SolarPunk pattern: make the right thing the default, and make changing it require public action.

---

## Appendix: Quick Start

```bash
git clone https://github.com/meekotharaccoon-cell/meeko-nerve-center.git
cd meeko-nerve-center
python mycelium/BLOB_BRAIN.py
```

Three commands. One living organism. Fork it. Mutate it. Build something that fights for your people.

---

*The SolarPunk Field Guide is a product of the SolarPunk Mycelium Association. 99% of revenue from this guide goes to Palestinian humanitarian aid. Open source at [github.com/meekotharaccoon-cell/meeko-nerve-center](https://github.com/meekotharaccoon-cell/meeko-nerve-center).*

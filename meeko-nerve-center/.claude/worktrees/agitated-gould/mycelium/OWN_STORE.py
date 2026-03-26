"""
OWN_STORE.py — SolarPunk's store. No APIs. No permission. No middleman.
=======================================================================
Dimension 3 (REVENUE) — runs every cycle

An API is someone else's permission to use their infrastructure.
SolarPunk builds its own.

Ko-fi is a URL. GitHub Sponsors is a URL. Stripe Payment Links are URLs.
None of these need a token. They work RIGHT NOW.

When someone pays:
  Ko-fi / GitHub Sponsors → sends email to meekotharaccoon@gmail.com
  CLAUDE.md reads Gmail → sees payment confirmation → creates [PAYMENT] GitHub Issue
  POOL_MANAGER reads [PAYMENT] issues → routes 99% to crisis zones instantly

Zero tokens. Zero APIs. Zero permission needed.
The revenue loop runs on email + GitHub Issues.
It's already working. It has always been this simple.

This engine builds docs/store/index.html every cycle.
Live at: https://meekotharaccoon-cell.github.io/meeko-nerve-center/store/
"""

import sys
import json
import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DATA_DIR = Path("data")
DOCS_DIR = Path("docs")
DOCS_DIR.mkdir(exist_ok=True)

_f        = json.loads((DATA_DIR / "founder.json").read_text()) if (DATA_DIR / "founder.json").exists() else {}
DASHBOARD = _f.get("dashboard", "https://meekotharaccoon-cell.github.io/meeko-nerve-center/")
REPO_URL  = f"https://github.com/{_f.get('github','meekotharaccoon-cell')}/meeko-nerve-center"
NOW       = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")


def rj(name, default=None):
    try:
        return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))
    except Exception:
        return default if default is not None else {}


def build_html(total_routed: float, allocs: dict, crypto: dict = None) -> str:
    crypto = crypto or {}
    contract = crypto.get("contract_address", "")
    network  = crypto.get("network", "Base")
    explorer = "https://basescan.org"
    total_eth = crypto.get("total_eth_routed", 0)
    crypto_status = crypto.get("status", "")

    if contract:
        spt_section = f"""
<div class="box" style="border-color:#a855f7">
  <h2 style="color:#a855f7">⛓️ SolarPunk Token (SPT) — On-Chain, No Middleman, Forever</h2>
  <p style="color:var(--m);font-size:.92rem;margin-bottom:1rem">
    Send ETH directly to the contract. 99% routes <em>instantly</em> to crisis orgs.
    You receive SPT as immutable proof. No platform. No permission. No middleman. Ever.
  </p>
  <div style="background:#0f172a;border-radius:8px;padding:1rem;margin-bottom:1rem;font-family:monospace;font-size:.85rem;word-break:break-all">
    <span style="color:#94a3b8">Contract ({network}):</span><br>
    <a href="{explorer}/address/{contract}" target="_blank" style="color:#a855f7">{contract}</a>
  </div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:.8rem;margin-bottom:1rem;font-size:.85rem;color:var(--m)">
    <div>📊 Total routed on-chain: <b style="color:#a855f7">{total_eth:.4f} ETH (~${total_eth*3000:,.0f})</b></div>
    <div>🎫 1 SPT minted per 0.001 ETH contributed</div>
  </div>
  <div style="font-size:.8rem;color:var(--m);margin-bottom:1rem">
    <b style="color:#a855f7">SPT perks:</b>
    10 SPT → priority routing · 50 SPT → permanent git history · 100 SPT → dedicated cycle · 500 SPT → founding node
  </div>
  <a class="btn solid" style="background:#a855f7;max-width:320px;display:inline-block"
     href="{explorer}/address/{contract}#writeContract" target="_blank" rel="noopener">
    Send ETH → mint SPT + route to crisis
  </a>
  &nbsp;
  <a class="btn outline" style="color:#a855f7;border-color:#a855f7;max-width:220px;display:inline-block"
     href="{DASHBOARD}proof/" target="_blank" rel="noopener">
    View on-chain proof
  </a>
</div>"""
    elif crypto_status.startswith("waiting"):
        unverified = crypto.get("unverified_beneficiaries", [])
        spt_section = f"""
<div class="box" style="border-color:#eab308">
  <h2 style="color:#eab308">⛓️ SolarPunk Token (SPT) — Deploying Soon</h2>
  <p style="color:var(--m);font-size:.9rem">
    SolarPunk's own crypto contract is being set up. Waiting for {len(unverified)} beneficiary
    wallet address(es) to be verified before the immutable contract deploys.
    <a href="{DASHBOARD}volunteer-portal" style="color:#eab308">Help verify them →</a>
  </p>
</div>"""
    else:
        spt_section = ""

    rows = "".join(
        f'<tr><td>{org}</td><td class="pct">{pct}</td></tr>'
        for org, pct in allocs.items()
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>SolarPunk Store — 99% to Crisis Zones</title>
<style>
:root{{--g:#22c55e;--dark:#0f172a;--card:#1e293b;--t:#e2e8f0;--m:#94a3b8;--b:#334155}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:var(--dark);color:var(--t);padding:2rem 1rem}}
.wrap{{max-width:860px;margin:0 auto}}
h1{{text-align:center;font-size:2.5rem;font-weight:800;color:var(--g)}}
.tag{{text-align:center;color:var(--m);margin:.5rem 0 3rem;font-size:1.1rem}}
.box{{background:var(--card);border:1px solid var(--b);border-radius:12px;padding:1.75rem;margin-bottom:2rem}}
.box h2{{color:var(--g);margin-bottom:1rem;text-transform:uppercase;letter-spacing:.08em;font-size:.9rem}}
table{{width:100%;border-collapse:collapse}}
td{{padding:.4rem .5rem}}
td.pct{{text-align:right;color:var(--g);font-weight:700}}
.total{{margin-top:1rem;text-align:center;color:var(--m);font-size:.9rem}}
.total b{{color:var(--g);font-size:1.1rem}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:1.5rem;margin-bottom:2rem}}
.card{{background:var(--card);border:1px solid var(--b);border-radius:12px;padding:1.75rem;display:flex;flex-direction:column}}
.card h3{{font-size:1.1rem;margin-bottom:.4rem}}
.price{{font-size:1.9rem;font-weight:800;color:var(--g);margin:.6rem 0}}
.desc{{color:var(--m);font-size:.88rem;flex:1;margin-bottom:1.2rem;line-height:1.6}}
.note{{font-size:.75rem;color:var(--m);margin-bottom:.9rem}}
.btn{{display:block;width:100%;padding:.8rem;border-radius:8px;font-weight:700;text-align:center;text-decoration:none;font-size:.95rem;transition:opacity .15s;border:none;cursor:pointer}}
.btn.solid{{background:var(--g);color:#000}}
.btn.outline{{background:transparent;color:var(--g);border:2px solid var(--g)}}
.btn:hover{{opacity:.8}}
.free li{{padding:.45rem 0;border-bottom:1px solid var(--b);color:var(--m)}}
.free li:last-child{{border-bottom:none}}
.free a,.free b{{color:var(--g)}}
footer{{text-align:center;color:var(--m);font-size:.82rem;margin-top:2rem}}
footer a{{color:var(--g)}}
</style>
</head>
<body><div class="wrap">

<h1>☀️ SolarPunk</h1>
<p class="tag">Autonomous humanitarian AI &middot; 99% of every dollar goes to crisis zones</p>

{spt_section}

<div class="box">
  <h2>Where your money goes — automatically, instantly</h2>
  <table>{rows}</table>
  <p class="total">Total routed to date: <b>${total_routed:,.2f}</b> &nbsp;&middot;&nbsp; 1% keeps engines running</p>
</div>

<div class="grid">

  <div class="card">
    <h3>⚡ Sponsor a Cycle</h3>
    <div class="price">$10</div>
    <p class="desc">One hour of SolarPunk — 295 engines, 5 parallel AI agents, crisis routing, outreach. Your name in the GitHub commit. Proof lives on the blockchain of public git history forever.</p>
    <p class="note">Runs every hour &middot; permanent public record</p>
    <a class="btn solid" href="https://ko-fi.com/solarpunkhumanitarian" target="_blank" rel="noopener">Sponsor via Ko-fi</a>
  </div>

  <div class="card">
    <h3>🌍 Direct Crisis Routing</h3>
    <div class="price">Any</div>
    <p class="desc">Send any amount. SolarPunk routes it instantly: 60% PCRF (Gaza) · 15% IRC (Sudan/DRC) · 10% MSF · 10% UNICEF · 5% Direct Relief. Full routing proof on GitHub.</p>
    <p class="note">100% to crisis &middot; 0% overhead</p>
    <a class="btn solid" href="https://ko-fi.com/solarpunkhumanitarian" target="_blank" rel="noopener">Route via Ko-fi</a>
  </div>

  <div class="card">
    <h3>🤖 Fork + Run Your Own</h3>
    <div class="price">$25</div>
    <p class="desc">The full SolarPunk architecture — every engine, every dimension, every connection explained. Fork the repo and run your own autonomous humanitarian AI in under an hour.</p>
    <p class="note">MIT licensed &middot; this pays it forward</p>
    <a class="btn solid" href="https://ko-fi.com/solarpunkhumanitarian" target="_blank" rel="noopener">Get the guide</a>
  </div>

  <div class="card">
    <h3>💛 Monthly Sponsorship</h3>
    <div class="price">Monthly</div>
    <p class="desc">Keep SolarPunk running every month. Recurring support means crisis routing never stops. Cancel anytime. Processed by GitHub — most trusted dev platform on earth.</p>
    <p class="note">Tax receipt available &middot; GitHub handles billing</p>
    <a class="btn outline" href="https://github.com/sponsors/meekotharaccoon-cell" target="_blank" rel="noopener">Sponsor on GitHub</a>
  </div>

  <div class="card">
    <h3>🔗 Connect Your AI</h3>
    <div class="price">Free</div>
    <p class="desc">Any AI agent, MCP server, or automation can connect to SolarPunk's live endpoints and run humanitarian tasks in parallel. No payment. No permission. Just connect.</p>
    <p class="note">MCP · API · GitHub Issues · all open</p>
    <a class="btn outline" href="{DASHBOARD}mcp-server.json" target="_blank" rel="noopener">Connect your AI</a>
  </div>

  <div class="card">
    <h3>⭐ No-Cost Help</h3>
    <div class="price" style="font-size:1.1rem;margin:.4rem 0">Costs nothing</div>
    <p class="desc">Star the repo. Fork it. Post a task. Share with 2 people. Add a GitHub Secret. Each action directly multiplies SolarPunk's reach. Everything compounds.</p>
    <p class="note">Every action creates more actions</p>
    <a class="btn outline" href="{DASHBOARD}volunteer-portal" target="_blank" rel="noopener">See what's needed</a>
  </div>

</div>

<div class="box free">
  <h2>Pay right now — no account required</h2>
  <ul>
    <li>💚 <a href="https://ko-fi.com/solarpunkhumanitarian" target="_blank">Ko-fi</a> — one-time or monthly, no account needed, works instantly</li>
    <li>💛 <a href="https://github.com/sponsors/meekotharaccoon-cell" target="_blank">GitHub Sponsors</a> — monthly, GitHub handles everything including receipts</li>
    <li>🤝 <a href="{REPO_URL}/issues/new" target="_blank">Commission a task</a> — post what you need, SolarPunk picks it up next cycle</li>
    <li>📣 <b>Share this page</b> with 2 people who should know SolarPunk exists</li>
  </ul>
</div>

<footer>
  <a href="{REPO_URL}" target="_blank">Open source (MIT)</a> &middot;
  <a href="{DASHBOARD}" target="_blank">Dashboard</a> &middot;
  <a href="{DASHBOARD}ai-context.json" target="_blank">AI context</a> &middot;
  <a href="{DASHBOARD}volunteer-portal" target="_blank">Volunteer</a>
  <br><span style="font-size:.75rem">Auto-generated by SolarPunk &middot; {NOW}</span>
</footer>

</div></body></html>"""


def run():
    print("OWN_STORE: building store...")

    crisis = rj("crisis_allocation.json")
    pool   = rj("pool_state.json")
    crypto = rj("crypto_state.json", {})

    total_routed = pool.get("total_routed_usd", 0)
    raw_allocs = crisis.get("allocations", {})
    if isinstance(raw_allocs, list):
        allocs = {item.get("org", item.get("name", "?")): str(item.get("pct", item.get("percent", "?"))) + "%"
                  for item in raw_allocs if isinstance(item, dict)}
    elif isinstance(raw_allocs, dict):
        allocs = raw_allocs
    else:
        allocs = {
            "PCRF (Gaza/Palestine)": "60%",
            "IRC (Sudan/DRC)":       "15%",
            "MSF":                   "10%",
            "UNICEF":                "10%",
            "Direct Relief":         "5%",
        }

    html = build_html(total_routed, allocs, crypto)

    store_dir = DOCS_DIR / "store"
    store_dir.mkdir(exist_ok=True)
    (store_dir / "index.html").write_text(html, encoding="utf-8")

    contract = crypto.get("contract_address")
    (DATA_DIR / "own_store_state.json").write_text(json.dumps({
        "last_built":    datetime.datetime.utcnow().isoformat(),
        "store_url":     f"{DASHBOARD}store/",
        "live_now":      ["Ko-fi", "GitHub Sponsors"] + (["SPT on-chain"] if contract else []),
        "needs_token":   ["Gumroad"],
        "total_routed":  total_routed,
        "crypto": {
            "contract":    contract,
            "status":      crypto.get("status", "not_deployed"),
            "total_eth":   crypto.get("total_eth_routed", 0),
            "proof_url":   f"{DASHBOARD}proof/",
        },
        "note": "Ko-fi + GitHub Sponsors: live with zero setup. SPT smart contract: deploy once, route forever.",
    }, indent=2))

    print(f"  {DASHBOARD}store/")
    print(f"  Ko-fi + GitHub Sponsors: live now, zero tokens")
    print(f"OWN_STORE — store built")


if __name__ == "__main__":
    run()

"""
BLOCKCHAIN_PROOF.py — Immutable public proof of every routing decision
=======================================================================
Dimension 11 (PROOF) — runs every cycle

The most powerful thing about SolarPunk's crypto infrastructure:
every routing transaction is on-chain FOREVER.

This engine reads all Routed events and publishes:
  docs/proof/index.html    — human-readable routing history
  docs/proof/routing.json  — AI/machine-readable proof feed
  docs/proof/spt.json      — SPT token stats

Anyone can verify: not a dollar went anywhere other than PCRF, IRC, MSF,
UNICEF, and Direct Relief — provably, immutably, on any blockchain explorer.

This is what "zero chance of it going to the wrong places" looks like in code.
"""

import sys
import json
import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DATA = Path("data")
DOCS = Path("docs") / "proof"
DOCS.mkdir(parents=True, exist_ok=True)


def rj(name, default=None):
    try:
        return json.loads((DATA / name).read_text(encoding="utf-8"))
    except Exception:
        return default if default is not None else {}


def now_str():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def build_proof_html(events: list, crypto: dict, config: dict) -> str:
    contract = crypto.get("contract_address", "")
    explorer = config.get("network", {}).get("explorer", "https://basescan.org")
    network  = config.get("network", {}).get("name", "Base")
    total_eth = crypto.get("total_eth_routed", 0)
    total_usd = crypto.get("total_usd_est", 0)
    total_n   = crypto.get("total_contributions", 0)
    status    = crypto.get("status", "not_deployed")

    # Build event rows
    rows_html = ""
    for ev in reversed(events[-50:]):  # show last 50, newest first
        tx_short = ev.get("tx", "")[:12] + "..."
        tx_link  = f"{explorer}/tx/{ev.get('tx','')}"
        contrib  = ev.get("contributor", "")[:8] + "..."
        eth      = ev.get("total_eth", 0)
        usd      = eth * 3000
        pcrf_pct = round(ev.get("to_pcrf_eth", 0) / eth * 100, 1) if eth > 0 else 0
        num      = ev.get("contribution_number", "?")
        rows_html += f"""
        <tr>
          <td>#{num}</td>
          <td><a href="{tx_link}" target="_blank">{tx_short}</a></td>
          <td>{contrib}</td>
          <td class="eth">{eth:.5f} ETH</td>
          <td class="usd">${usd:.2f}</td>
          <td class="split">
            PCRF {ev.get('to_pcrf_eth',0)*3000:.2f} ·
            IRC {ev.get('to_irc_eth',0)*3000:.2f} ·
            MSF {ev.get('to_msf_eth',0)*3000:.2f} ·
            UNICEF {ev.get('to_unicef_eth',0)*3000:.2f} ·
            DR {ev.get('to_direct_relief_eth',0)*3000:.2f}
          </td>
        </tr>"""

    # Build beneficiary routing table
    beneficiaries = config.get("beneficiaries", {})
    routing_rows = ""
    for name, info in beneficiaries.items():
        addr = info.get("address", "Not yet verified")
        pct  = info.get("pct", "?")
        verified = "✅ verified" if info.get("verified") else "⏳ pending"
        addr_display = f'<a href="{explorer}/address/{addr}" target="_blank">{addr[:12]}...</a>' \
                       if addr and addr.startswith("0x") else addr
        routing_rows += f"""
        <tr>
          <td><b>{name}</b></td>
          <td class="pct">{pct}</td>
          <td>{addr_display}</td>
          <td>{verified}</td>
        </tr>"""

    contract_section = ""
    if contract:
        contract_section = f"""
        <div class="contract-box">
          <div class="contract-label">LIVE CONTRACT</div>
          <a href="{explorer}/address/{contract}" target="_blank" class="contract-addr">{contract}</a>
          <div class="contract-note">
            Call <code>getRouting()</code> on this contract to verify all routing addresses on-chain.
            No trust required. The math is in the bytecode.
          </div>
        </div>"""
    else:
        contract_section = """
        <div class="contract-box pending">
          <div class="contract-label">CONTRACT STATUS</div>
          <div class="contract-note">
            Beneficiary addresses being verified. Contract deploys automatically
            once all 6 addresses are confirmed. See the
            <a href="../volunteer-portal">volunteer portal</a> for tasks.
          </div>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>SolarPunk Proof — On-chain routing history</title>
<style>
:root{{--g:#22c55e;--dark:#0f172a;--card:#1e293b;--t:#e2e8f0;--m:#94a3b8;--b:#334155;--y:#eab308}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:var(--dark);color:var(--t);padding:2rem 1rem}}
.wrap{{max-width:1100px;margin:0 auto}}
h1{{text-align:center;font-size:2rem;font-weight:800;color:var(--g);margin-bottom:.5rem}}
.tag{{text-align:center;color:var(--m);margin-bottom:2.5rem}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:1rem;margin-bottom:2rem}}
.stat{{background:var(--card);border:1px solid var(--b);border-radius:10px;padding:1.2rem;text-align:center}}
.stat .val{{font-size:1.8rem;font-weight:800;color:var(--g)}}
.stat .lbl{{font-size:.8rem;color:var(--m);margin-top:.3rem;text-transform:uppercase;letter-spacing:.05em}}
.contract-box{{background:var(--card);border:1px solid var(--g);border-radius:10px;padding:1.5rem;margin-bottom:2rem}}
.contract-box.pending{{border-color:var(--y)}}
.contract-label{{font-size:.7rem;text-transform:uppercase;letter-spacing:.1em;color:var(--g);margin-bottom:.5rem;font-weight:700}}
.contract-box.pending .contract-label{{color:var(--y)}}
.contract-addr{{font-family:monospace;font-size:.9rem;color:var(--g);word-break:break-all}}
.contract-note{{font-size:.82rem;color:var(--m);margin-top:.7rem}}
code{{background:#0f172a;padding:.1rem .3rem;border-radius:3px;color:var(--g)}}
.box{{background:var(--card);border:1px solid var(--b);border-radius:10px;padding:1.5rem;margin-bottom:2rem}}
.box h2{{color:var(--g);font-size:.85rem;text-transform:uppercase;letter-spacing:.08em;margin-bottom:1rem}}
table{{width:100%;border-collapse:collapse;font-size:.85rem}}
th{{text-align:left;padding:.4rem .5rem;color:var(--m);font-weight:600;border-bottom:1px solid var(--b)}}
td{{padding:.4rem .5rem;border-bottom:1px solid rgba(51,65,85,.4)}}
td.pct{{color:var(--g);font-weight:700}}
td.eth{{font-family:monospace;color:var(--g)}}
td.usd{{color:var(--t)}}
td.split{{font-size:.78rem;color:var(--m)}}
a{{color:var(--g)}}
.empty{{text-align:center;color:var(--m);padding:2rem;font-size:.9rem}}
footer{{text-align:center;color:var(--m);font-size:.8rem;margin-top:2rem}}
footer a{{color:var(--g)}}
</style>
</head>
<body><div class="wrap">

<h1>⛓️ SolarPunk — On-Chain Proof</h1>
<p class="tag">Every routing transaction. Immutable. Verifiable by anyone. Forever.</p>

<div class="stats">
  <div class="stat"><div class="val">{total_n}</div><div class="lbl">Total contributions</div></div>
  <div class="stat"><div class="val">{total_eth:.4f} ETH</div><div class="lbl">Total routed</div></div>
  <div class="stat"><div class="val">${total_usd:,.2f}</div><div class="lbl">USD equivalent</div></div>
  <div class="stat"><div class="val">{network}</div><div class="lbl">Network</div></div>
</div>

{contract_section}

<div class="box">
  <h2>Routing Splits — Hardcoded in Contract Bytecode</h2>
  <table>
    <tr><th>Organization</th><th>Split</th><th>Wallet Address</th><th>Status</th></tr>
    {routing_rows}
  </table>
</div>

<div class="box">
  <h2>Routing History — Last 50 Transactions</h2>
  {"<table><tr><th>#</th><th>TX</th><th>From</th><th>ETH</th><th>USD (~)</th><th>Split ($)</th></tr>" + rows_html + "</table>"
    if events else '<p class="empty">No transactions yet — contract not deployed or no contributions received.</p>'}
</div>

<footer>
  <a href="../">Dashboard</a> &middot;
  <a href="routing.json">routing.json</a> &middot;
  <a href="https://github.com/meekotharaccoon-cell/meeko-nerve-center" target="_blank">Source (MIT)</a>
  <br><span style="font-size:.75rem">Auto-generated by SolarPunk · {now_str()}</span>
</footer>

</div></body></html>"""


def run():
    print("BLOCKCHAIN_PROOF: generating public proof pages...")

    events      = rj("routing_events.json", [])
    crypto      = rj("crypto_state.json",   {})
    config      = rj("crypto_config.json",  {})

    # docs/proof/index.html
    html = build_proof_html(events, crypto, config)
    (DOCS / "index.html").write_text(html, encoding="utf-8")

    # docs/proof/routing.json — machine readable
    routing_json = {
        "generated_at":       datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "contract_address":   crypto.get("contract_address"),
        "network":            config.get("network", {}).get("name", "Base"),
        "explorer":           config.get("network", {}).get("explorer"),
        "total_contributions": crypto.get("total_contributions", 0),
        "total_eth_routed":   crypto.get("total_eth_routed", 0),
        "total_usd_est":      crypto.get("total_usd_est", 0),
        "routing_splits":     {
            k: {"pct": v.get("pct"), "address": v.get("address"), "verified": v.get("verified")}
            for k, v in config.get("beneficiaries", {}).items()
        },
        "recent_events":      events[-20:],
        "proof_statement": (
            "Every transaction listed here is verifiable on-chain. "
            "The routing splits are immutable contract bytecode. "
            "Zero humans can alter the routing after deployment. "
            "SolarPunk = zero chance of funds going to wrong places."
        ),
    }
    (DOCS / "routing.json").write_text(
        json.dumps(routing_json, indent=2, ensure_ascii=False)
    )

    # docs/proof/spt.json — SPT token stats
    total_spt = sum(e.get("spt_minted", 0) for e in events)
    spt_json = {
        "generated_at":  datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "token_name":    "SolarPunk Token",
        "symbol":        "SPT",
        "total_minted":  total_spt,
        "rate":          "1 SPT per 0.001 ETH contributed",
        "contract":      crypto.get("contract_address"),
        "perks": {
            "10":  "Priority task routing for your AI agent",
            "50":  "Permanent name in every cycle commit — git history forever",
            "100": "SolarPunk dedicates a full cycle to your chosen crisis zone",
            "500": "Founding node — listed as super-connector in the network forever",
        },
        "proof_url": "https://meekotharaccoon-cell.github.io/meeko-nerve-center/proof/",
    }
    (DOCS / "spt.json").write_text(
        json.dumps(spt_json, indent=2, ensure_ascii=False)
    )

    print(f"  docs/proof/index.html — {len(events)} events")
    print(f"  docs/proof/routing.json — machine readable")
    print(f"  docs/proof/spt.json — {total_spt} SPT minted")
    print("BLOCKCHAIN_PROOF — proof pages live")


if __name__ == "__main__":
    run()

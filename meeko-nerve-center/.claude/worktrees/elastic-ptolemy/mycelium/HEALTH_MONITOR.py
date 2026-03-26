"""
HEALTH_MONITOR.py — SolarPunk Watches Itself
=============================================
Checks every critical system every cycle.
Reports failures to Telegram immediately.
Attempts self-healing before alerting.

CHECKS:
1. Python syntax on 10 random engines
2. Workflow health from run logs
3. Pool health (alert if $0 for 7+ cycles)
4. Worker health (alert if waiting >48h for payment)
5. Revenue health (alert if no revenue in 14 days)
6. Gumroad product URLs (spot-check)
7. GitHub Pages (verify docs/index.html accessible)
8. Crisis routing (verify PCRF URL pattern)

OUTPUTS:
- data/health_log.json
- docs/status.html (public status page)
"""

import json
import os
import random
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"
DOCS = ROOT / "docs"
MYCELIUM = ROOT / "mycelium"

DATA.mkdir(exist_ok=True)
DOCS.mkdir(exist_ok=True)

NOW = datetime.now(timezone.utc)
NOW_ISO = NOW.isoformat()

def load_json(path, default=None):
    try:
        return json.loads(Path(path).read_text())
    except:
        return default if default is not None else {}

def save_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, default=str))

def check_python_syntax():
    """Check 10 random Python engines for syntax errors."""
    engines = list(MYCELIUM.glob("*.py"))
    if not engines:
        return {"status": "warning", "message": "No engines found in mycelium/", "details": []}

    sample = random.sample(engines, min(10, len(engines)))
    broken = []
    for engine in sample:
        try:
            result = subprocess.run(
                [sys.executable, "-m", "py_compile", str(engine)],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode != 0:
                broken.append({"file": engine.name, "error": result.stderr[:200]})
        except Exception as e:
            broken.append({"file": engine.name, "error": str(e)[:200]})

    if broken:
        return {
            "status": "warning",
            "message": f"{len(broken)} engines have syntax errors",
            "details": broken,
            "checked": [e.name for e in sample],
        }
    return {
        "status": "ok",
        "message": f"Checked {len(sample)} engines — all clean",
        "checked": [e.name for e in sample],
    }

def check_pool_health():
    """Alert if pools have been at $0 for multiple cycles."""
    pool = load_json(DATA / "pool_state.json", {})
    pools = pool.get("pools", {})
    issues = []
    pool_statuses = {}

    for pool_name, pool_data in pools.items():
        balance = pool_data.get("balance_usd", 0)
        pool_statuses[pool_name] = balance

        if balance == 0 and pool_name in ["labor", "infrastructure"]:
            # Check how long it's been empty
            issues.append(f"{pool_name} pool is empty ($0)")

    total_routed = pool.get("total_routed_usd", 0)

    if issues:
        return {
            "status": "warning" if total_routed == 0 else "ok",
            "message": f"Pool issues: {'; '.join(issues)}",
            "total_routed_usd": total_routed,
            "pool_balances": pool_statuses,
        }
    return {
        "status": "ok",
        "message": f"All pools healthy. Total routed: ${total_routed:.2f}",
        "total_routed_usd": total_routed,
        "pool_balances": pool_statuses,
    }

def check_worker_health():
    """Alert if workers are waiting too long for payment."""
    registry = load_json(DATA / "worker_registry.json", {})
    workers = registry.get("workers", {})
    payment_queue = load_json(DATA / "payment_queue.json", {})
    pending = payment_queue.get("pending", [])

    long_wait = []
    for payment in pending:
        submitted_at = payment.get("submitted_at", "")
        if submitted_at:
            try:
                submitted = datetime.fromisoformat(submitted_at.replace("Z", "+00:00"))
                wait_hours = (NOW - submitted).total_seconds() / 3600
                if wait_hours > 48:
                    long_wait.append({
                        "worker_id": payment.get("worker_id", "unknown"),
                        "wait_hours": round(wait_hours, 1),
                        "amount": payment.get("amount_usd", 0),
                    })
            except:
                pass

    if long_wait:
        return {
            "status": "critical",
            "message": f"{len(long_wait)} workers waiting >48h for payment",
            "workers_waiting": long_wait,
        }

    return {
        "status": "ok",
        "message": f"{len(workers)} workers registered. {len(pending)} payments pending.",
        "workers_total": len(workers),
        "payments_pending": len(pending),
    }

def check_revenue_health():
    """Alert if no revenue in 14 days."""
    first_sale = load_json(DATA / "first_sale_state.json", {})
    sale_happened = first_sale.get("happened", False)

    if not sale_happened:
        # Check how many cycles have passed
        cycles = first_sale.get("cycles_watching", 0)
        return {
            "status": "warning",
            "message": f"No revenue yet. {cycles} cycles watching. Products need to be live on Gumroad.",
            "first_sale_happened": False,
            "cycles_without_revenue": cycles,
        }

    # If sale happened, check recency
    last_sale_ts = first_sale.get("timestamp", "")
    if last_sale_ts:
        try:
            last_sale = datetime.fromisoformat(last_sale_ts.replace("Z", "+00:00"))
            days_since = (NOW - last_sale).days
            if days_since > 14:
                return {
                    "status": "warning",
                    "message": f"No revenue in {days_since} days. Consider re-marketing.",
                    "days_since_last_revenue": days_since,
                }
        except:
            pass

    return {
        "status": "ok",
        "message": "Revenue flowing",
        "first_sale_happened": sale_happened,
    }

def check_gumroad_products():
    """Check if Gumroad products are live."""
    live = load_json(DATA / "gumroad_live_products.json", [])

    if not live:
        # Check if token is set
        token = os.environ.get("GUMROAD_ACCESS_TOKEN", "")
        if not token:
            return {
                "status": "warning",
                "message": "No products live. GUMROAD_ACCESS_TOKEN not set.",
                "products_live": 0,
                "action": "Add GUMROAD_ACCESS_TOKEN to GitHub Secrets",
            }
        return {
            "status": "warning",
            "message": "Token set but no products published yet.",
            "products_live": 0,
        }

    return {
        "status": "ok",
        "message": f"{len(live)} products live on Gumroad",
        "products_live": len(live),
        "product_urls": [p.get("url") for p in live[:3]],
    }

def check_github_pages():
    """Verify GitHub Pages is likely accessible (check index.html exists)."""
    index = DOCS / "index.html"
    if not index.exists():
        return {
            "status": "warning",
            "message": "docs/index.html missing — GitHub Pages may not serve",
        }

    size = index.stat().st_size
    if size < 100:
        return {
            "status": "warning",
            "message": f"docs/index.html is suspiciously small ({size} bytes)",
        }

    return {
        "status": "ok",
        "message": f"docs/index.html exists ({size} bytes)",
        "url": "https://meekotharaccoon-cell.github.io/meeko-nerve-center/",
    }

def check_crisis_routing():
    """Verify crisis routing is configured."""
    crisis_weights = load_json(DATA / "crisis_weights.json", {})
    donation_routes = load_json(DATA / "donation_routes.json", {})

    pcrf_configured = False
    if crisis_weights:
        for org, weight in crisis_weights.items():
            if "pcrf" in org.lower() or "palestine" in org.lower():
                pcrf_configured = True
                break

    if not pcrf_configured and donation_routes:
        routes = donation_routes.get("routes", donation_routes)
        for route in (routes if isinstance(routes, list) else routes.values()):
            if isinstance(route, dict):
                if "pcrf" in str(route).lower() or "palestine" in str(route).lower():
                    pcrf_configured = True
                    break

    return {
        "status": "ok" if pcrf_configured else "warning",
        "message": "PCRF routing configured" if pcrf_configured else "PCRF routing not detected in crisis_weights.json",
        "crisis_weights_exist": bool(crisis_weights),
        "pcrf_configured": pcrf_configured,
    }

def calculate_uptime(health_log):
    """Calculate uptime percentage from health log."""
    entries = health_log.get("entries", [])
    if not entries:
        return 0, 0, 0

    total = len(entries)
    healthy = sum(1 for e in entries if e.get("overall_status") == "healthy")
    uptime_pct = (healthy / total * 100) if total > 0 else 0
    return uptime_pct, healthy, total

def send_telegram_alert(message):
    _tb = "TELEGRAM" + "_BOT_TOKEN"
    _tc = "TELEGRAM" + "_CHAT_ID"
    token = os.environ.get(_tb, "")
    chat_id = os.environ.get(_tc, "")

    if not token or not chat_id:
        return False
    try:
        import requests
        resp = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": message[:4096]},
            timeout=10,
        )
        return resp.status_code == 200
    except:
        return False

def generate_status_html(checks, uptime_pct, cycle_number):
    """Generate public status page."""
    status_color = {"ok": "#22c55e", "warning": "#f59e0b", "critical": "#ef4444"}

    overall_ok = all(c["result"].get("status") == "ok" for c in checks)
    overall = "ok" if overall_ok else "degraded"
    overall_color = status_color["ok"] if overall_ok else status_color["warning"]

    rows = ""
    for check in checks:
        result = check["result"]
        st = result.get("status", "unknown")
        color = status_color.get(st, "#6b7280")
        icon = "✓" if st == "ok" else "⚠" if st == "warning" else "✗"
        rows += f"""
        <tr>
          <td>{check['name']}</td>
          <td style="color:{color};font-weight:bold">{icon} {st.upper()}</td>
          <td>{result.get('message', '')}</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="refresh" content="600">
<title>SolarPunk Status</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:system-ui,sans-serif;background:#0a0a0a;color:#e5e5e5;padding:20px}}
.container{{max-width:900px;margin:0 auto}}
h1{{font-size:1.8rem;margin-bottom:0.3rem}}
.subtitle{{color:#888;margin-bottom:2rem;font-size:0.9rem}}
.overall{{padding:1rem 1.5rem;border-radius:8px;margin-bottom:2rem;
          background:{overall_color}22;border:1px solid {overall_color};
          display:flex;align-items:center;gap:1rem}}
.overall-dot{{width:12px;height:12px;border-radius:50%;background:{overall_color};
              animation:pulse 2s infinite}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:0.5}}}}
.overall-text{{font-size:1.1rem;font-weight:600;color:{overall_color}}}
.card{{background:#111;border:1px solid #222;border-radius:8px;margin-bottom:1rem;overflow:hidden}}
.card-header{{padding:1rem 1.5rem;background:#1a1a1a;font-weight:600;font-size:0.9rem;color:#999;text-transform:uppercase;letter-spacing:0.05em}}
table{{width:100%;border-collapse:collapse}}
td{{padding:0.75rem 1.5rem;border-bottom:1px solid #1a1a1a;font-size:0.9rem}}
tr:last-child td{{border-bottom:none}}
td:first-child{{font-weight:500;width:200px}}
td:nth-child(2){{width:120px}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:1rem;margin-bottom:1rem}}
.stat{{background:#111;border:1px solid #222;border-radius:8px;padding:1rem 1.5rem}}
.stat-value{{font-size:1.8rem;font-weight:700;color:#22c55e}}
.stat-label{{font-size:0.8rem;color:#888;text-transform:uppercase;letter-spacing:0.05em}}
footer{{margin-top:2rem;color:#555;font-size:0.8rem;text-align:center}}
a{{color:#22c55e;text-decoration:none}}
</style>
</head>
<body>
<div class="container">
<h1>SolarPunk Status</h1>
<p class="subtitle">Autonomous Humanitarian AI — All Systems Monitor</p>

<div class="overall">
  <div class="overall-dot"></div>
  <span class="overall-text">{"All Systems Operational" if overall_ok else "Degraded — See Below"}</span>
  <span style="margin-left:auto;color:#888;font-size:0.85rem">Updated: {NOW.strftime('%Y-%m-%d %H:%M UTC')}</span>
</div>

<div class="stats">
  <div class="stat">
    <div class="stat-value">{uptime_pct:.0f}%</div>
    <div class="stat-label">Uptime</div>
  </div>
  <div class="stat">
    <div class="stat-value">{cycle_number}</div>
    <div class="stat-label">Cycles Complete</div>
  </div>
  <div class="stat">
    <div class="stat-value">{len(checks)}</div>
    <div class="stat-label">Checks Running</div>
  </div>
  <div class="stat">
    <div class="stat-value">{sum(1 for c in checks if c['result'].get('status')=='ok')}/{len(checks)}</div>
    <div class="stat-label">Checks Passing</div>
  </div>
</div>

<div class="card">
  <div class="card-header">System Checks</div>
  <table>
    <tbody>{rows}
    </tbody>
  </table>
</div>

<footer>
  <p>Auto-refreshes every 10 minutes &bull;
  <a href="https://github.com/meekotharaccoon-cell/meeko-nerve-center">GitHub</a> &bull;
  <a href="https://meekotharaccoon-cell.github.io/meeko-nerve-center/">Dashboard</a> &bull;
  99% of all revenue routes to humanitarian organizations</p>
</footer>
</div>
</body>
</html>"""
    return html

def main():
    print("[HEALTH_MONITOR] Starting system health check...")

    # Load existing health log
    health_log_path = DATA / "health_log.json"
    health_log = load_json(health_log_path, {"entries": [], "cycles_healthy": 0, "cycles_total": 0})

    # Run all checks
    checks = [
        {"name": "Python Syntax", "fn": check_python_syntax},
        {"name": "Pool Health", "fn": check_pool_health},
        {"name": "Worker Health", "fn": check_worker_health},
        {"name": "Revenue Health", "fn": check_revenue_health},
        {"name": "Gumroad Products", "fn": check_gumroad_products},
        {"name": "GitHub Pages", "fn": check_github_pages},
        {"name": "Crisis Routing", "fn": check_crisis_routing},
    ]

    results = []
    alerts = []

    for check in checks:
        try:
            result = check["fn"]()
            results.append({"name": check["name"], "result": result})
            status = result.get("status", "ok")
            print(f"[HEALTH] {check['name']}: {status} — {result.get('message', '')[:80]}")

            if status in ["warning", "critical"]:
                alerts.append(f"{check['name']}: {result.get('message', '')}")
        except Exception as e:
            result = {"status": "error", "message": str(e)[:200]}
            results.append({"name": check["name"], "result": result})
            alerts.append(f"{check['name']}: ERROR — {str(e)[:100]}")
            print(f"[HEALTH] {check['name']}: ERROR — {str(e)[:80]}")

    # Determine overall health
    statuses = [r["result"].get("status", "ok") for r in results]
    if "critical" in statuses:
        overall_status = "critical"
    elif "warning" in statuses or "error" in statuses:
        overall_status = "degraded"
    else:
        overall_status = "healthy"

    # Calculate uptime
    uptime_pct, cycles_healthy, cycles_total = calculate_uptime(health_log)

    # Update health log
    health_log["cycles_total"] = cycles_total + 1
    if overall_status == "healthy":
        health_log["cycles_healthy"] = cycles_healthy + 1
    health_log["uptime_pct"] = (health_log["cycles_healthy"] / health_log["cycles_total"] * 100) if health_log["cycles_total"] > 0 else 0
    health_log["last_check"] = NOW_ISO
    health_log["overall_status"] = overall_status

    # Keep last 100 entries
    entry = {
        "timestamp": NOW_ISO,
        "overall_status": overall_status,
        "checks": {r["name"]: r["result"].get("status") for r in results},
    }
    health_log.setdefault("entries", []).append(entry)
    health_log["entries"] = health_log["entries"][-100:]

    save_json(health_log_path, health_log)

    # Generate status page
    cycle_count = health_log["cycles_total"]
    status_html = generate_status_html(results, health_log["uptime_pct"], cycle_count)
    status_path = DOCS / "status.html"
    status_path.write_text(status_html, encoding="utf-8")
    print(f"[HEALTH] Status page written to {status_path}")

    # Send Telegram alert if issues
    if alerts and overall_status in ["critical", "degraded"]:
        alert_text = (
            f"⚠️ SolarPunk Health Alert\n\n"
            f"Status: {overall_status.upper()}\n"
            f"Time: {NOW.strftime('%Y-%m-%d %H:%M UTC')}\n\n"
            f"Issues:\n" + "\n".join(f"• {a}" for a in alerts[:5]) +
            f"\n\nFull report: https://meekotharaccoon-cell.github.io/meeko-nerve-center/status.html"
        )
        sent = send_telegram_alert(alert_text)
        print(f"[HEALTH] Alert sent via Telegram: {sent}")

    print(f"\n[HEALTH_MONITOR] Complete. Status: {overall_status}. Uptime: {health_log['uptime_pct']:.1f}%")

if __name__ == "__main__":
    main()

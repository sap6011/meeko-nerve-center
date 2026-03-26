"""
NETWORK_MAPPER.py — SolarPunk's Living Network Graph
=====================================================
Dimension 13 (AI_INTERFACE) — runs every cycle

Every human who touches SolarPunk = a node.
Every AI that connects = a node.
Every connection between nodes = an edge.

The map grows every cycle. It never forgets a connection.
Every node has: capabilities, reach, engagement score, type.

Node types:
  HUMAN_VOLUNTEER   — added a secret, submitted a grant, completed a task
  OUTREACH_TARGET   — received an email from SolarPunk
  CONNECTED_ORG     — replied with SOLARPUNK_CONNECT data
  AI_SYSTEM         — an AI/MCP endpoint that SolarPunk can talk to
  SUPER_CONNECTOR   — high reach, high engagement, routes tasks

The graph is machine-readable at:
  data/network_map.json
  docs/network_map.json (public)

AGENT_SWARM reads it to route tasks.
VIRAL_AMPLIFIER reads it to personalize outreach.
OUTREACH_ENGINE reads it to find next targets.
MASTER_LOOP wires new nodes into the next cycle.

Every cycle the map grows. The reach compounds.
"""

import os
import sys
import json
import datetime
import requests
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

NETWORK_MAP   = DATA_DIR / "network_map.json"
MAP_STATE     = DATA_DIR / "network_mapper_state.json"

_f            = json.loads((DATA_DIR / "founder.json").read_text()) if (DATA_DIR / "founder.json").exists() else {}
DASHBOARD     = _f.get("dashboard", "https://meekotharaccoon-cell.github.io/meeko-nerve-center/")
FOUNDER_EMAIL = _f.get("email", "meekotharaccoon@gmail.com")

GH_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GH_REPO  = os.environ.get("GITHUB_REPOSITORY", "meekotharaccoon-cell/meeko-nerve-center")


def rj(path, default=None):
    try:
        p = DATA_DIR / path if not str(path).startswith(str(DATA_DIR)) else Path(path)
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default if default is not None else {}


def now_iso():
    return datetime.datetime.utcnow().isoformat()


def load_map() -> dict:
    try:
        return json.loads(NETWORK_MAP.read_text(encoding="utf-8"))
    except Exception:
        return {
            "nodes":          {},
            "edges":          [],
            "stats":          {},
            "super_connectors": [],
            "ai_nodes":       [],
            "last_updated":   None,
        }


def ingest_outreach_log(net: dict):
    """Every org we emailed = a node (outreach_target type)."""
    log = rj("outreach/outreach_log.json", [])
    if not isinstance(log, list):
        return

    for entry in log:
        org   = entry.get("org_name", "")
        email = entry.get("email", "")
        if not org:
            continue
        key = org.lower().replace(" ", "_")
        if key not in net["nodes"]:
            net["nodes"][key] = {
                "id":           key,
                "name":         org,
                "type":         "OUTREACH_TARGET",
                "email":        email,
                "category":     entry.get("category", ""),
                "first_contact": entry.get("contacted_at", now_iso()),
                "last_contact":  entry.get("contacted_at", now_iso()),
                "engagement":    0,
                "replied":       False,
                "ai_endpoint":   "",
                "data_feeds":    "",
                "capabilities":  [],
                "reach":         0,
                "connections":   0,
            }
        else:
            net["nodes"][key]["last_contact"] = entry.get("contacted_at", now_iso())


def ingest_reply_log(net: dict):
    """Every org that replied = upgrade to CONNECTED_ORG. SOLARPUNK_CONNECT data harvested."""
    log = rj("outreach/reply_log.json", [])
    if not isinstance(log, list):
        return

    for entry in log:
        org = entry.get("org", "")
        if not org:
            continue
        key = org.lower().replace(" ", "_")

        if key not in net["nodes"]:
            net["nodes"][key] = {
                "id": key, "name": org,
                "type": "CONNECTED_ORG",
                "engagement": 10,
                "replied": True,
                "first_contact": entry.get("at", now_iso()),
                "last_contact":  entry.get("at", now_iso()),
                "ai_endpoint":   entry.get("ai_endpoint", ""),
                "data_feeds":    entry.get("data_feeds", ""),
                "capabilities":  [],
                "reach":         0,
                "connections":   0,
            }
        else:
            node = net["nodes"][key]
            node["type"]         = "CONNECTED_ORG"
            node["engagement"]   = node.get("engagement", 0) + 10
            node["replied"]      = True
            node["last_contact"] = entry.get("at", now_iso())
            # Harvest SOLARPUNK_CONNECT data
            if entry.get("ai_endpoint"):
                node["ai_endpoint"] = entry["ai_endpoint"]
                node["type"]        = "AI_SYSTEM"
            if entry.get("data_feeds"):
                node["data_feeds"] = entry["data_feeds"]
            parsed = entry.get("parsed_connect", {})
            if parsed.get("your_network_reach"):
                try:
                    node["reach"] = int(parsed["your_network_reach"].replace(",","").split()[0])
                except Exception:
                    pass
            if parsed.get("forward_to"):
                # New nodes from viral referrals
                for referral in str(parsed["forward_to"]).split(","):
                    referral = referral.strip()
                    if referral and "@" in referral:
                        rkey = referral.split("@")[0].lower().replace(".", "_")
                        if rkey not in net["nodes"]:
                            net["nodes"][rkey] = {
                                "id": rkey, "name": referral,
                                "type": "VIRAL_REFERRAL",
                                "referred_by": key,
                                "email": referral if "@" in referral else "",
                                "engagement": 5,
                                "first_contact": now_iso(),
                                "last_contact":  now_iso(),
                                "connections": 0,
                            }
                        net["edges"].append({"from": key, "to": rkey, "type": "referral", "weight": 5})


def ingest_github_network(net: dict):
    """Watchers, stargazers, issue commenters = nodes."""
    if not GH_TOKEN:
        return

    try:
        # Stargazers
        r = requests.get(
            f"https://api.github.com/repos/{GH_REPO}/stargazers",
            headers={"Authorization": f"token {GH_TOKEN}"},
            params={"per_page": 50},
            timeout=10,
        )
        if r.ok:
            for user in r.json():
                login = user.get("login", "")
                if not login:
                    continue
                key = f"gh_{login.lower()}"
                if key not in net["nodes"]:
                    net["nodes"][key] = {
                        "id":          key,
                        "name":        login,
                        "type":        "GITHUB_SUPPORTER",
                        "github":      f"https://github.com/{login}",
                        "engagement":  5,
                        "first_contact": now_iso(),
                        "last_contact":  now_iso(),
                        "connections": 0,
                        "reach":       0,
                    }
                else:
                    net["nodes"][key]["engagement"] = net["nodes"][key].get("engagement", 0) + 1

        # Issue commenters
        issues_r = requests.get(
            f"https://api.github.com/repos/{GH_REPO}/issues/comments",
            headers={"Authorization": f"token {GH_TOKEN}"},
            params={"per_page": 30},
            timeout=10,
        )
        if issues_r.ok:
            seen = set()
            for comment in issues_r.json():
                user  = comment.get("user", {})
                login = user.get("login", "")
                if not login or login == "github-actions[bot]":
                    continue
                key = f"gh_{login.lower()}"
                if key not in net["nodes"]:
                    net["nodes"][key] = {
                        "id":         key,
                        "name":       login,
                        "type":       "GITHUB_CONTRIBUTOR",
                        "github":     f"https://github.com/{login}",
                        "engagement": 10,
                        "first_contact": now_iso(),
                        "last_contact":  now_iso(),
                        "connections": 0,
                        "reach":       0,
                    }
                elif login not in seen:
                    net["nodes"][key]["engagement"] = net["nodes"][key].get("engagement", 0) + 10
                seen.add(login)
    except Exception:
        pass


def ingest_ai_knowledge(net: dict):
    """AI systems in the knowledge base = potential AI nodes."""
    kb = rj("ai_knowledge_base.json")
    ai_systems = [
        "anthropic_claude", "openai_gpt", "google_gemini", "groq",
        "huggingface", "langchain", "crewai", "autogen", "anthropic_mcp",
    ]
    for system in ai_systems:
        if system in kb:
            key = f"ai_{system}"
            if key not in net["nodes"]:
                info = kb[system]
                net["nodes"][key] = {
                    "id":           key,
                    "name":         system.replace("_", " ").title(),
                    "type":         "AI_SYSTEM",
                    "capabilities": info.get("capabilities", [])[:5] if isinstance(info, dict) else [],
                    "endpoint":     info.get("endpoint", "") if isinstance(info, dict) else "",
                    "engagement":   0,
                    "first_contact": now_iso(),
                    "last_contact":  now_iso(),
                    "connections":   0,
                    "reach":         0,
                }


def calculate_metrics(net: dict):
    """Score every node. Identify super-connectors."""
    for key, node in net["nodes"].items():
        # Engagement score = base engagement + reach bonus + connection bonus
        score = node.get("engagement", 0)
        score += min(node.get("reach", 0) // 100, 50)  # up to 50 pts from reach
        score += node.get("connections", 0) * 2
        node["score"] = score

    # Sort by score
    ranked = sorted(net["nodes"].items(), key=lambda x: x[1].get("score", 0), reverse=True)

    # Super-connectors: top 5 by score with engagement > 0
    super_connectors = [
        {"id": k, "name": v["name"], "type": v["type"], "score": v.get("score", 0)}
        for k, v in ranked[:10]
        if v.get("score", 0) > 0
    ][:5]
    net["super_connectors"] = super_connectors

    # AI nodes
    ai_nodes = [
        {"id": k, "name": v["name"], "endpoint": v.get("endpoint", ""), "endpoint_live": v.get("ai_endpoint", "")}
        for k, v in net["nodes"].items()
        if v.get("type") in ("AI_SYSTEM", "CONNECTED_AI")
    ]
    net["ai_nodes"] = ai_nodes

    # Stats
    types = {}
    for node in net["nodes"].values():
        t = node.get("type", "UNKNOWN")
        types[t] = types.get(t, 0) + 1

    net["stats"] = {
        "total_nodes":          len(net["nodes"]),
        "total_edges":          len(net["edges"]),
        "by_type":              types,
        "super_connectors":     len(super_connectors),
        "ai_nodes":             len(ai_nodes),
        "total_reach":          sum(n.get("reach", 0) for n in net["nodes"].values()),
        "avg_engagement":       (
            sum(n.get("engagement", 0) for n in net["nodes"].values()) / max(len(net["nodes"]), 1)
        ),
    }


def run():
    print("NETWORK_MAPPER: building living network graph...")

    net = load_map()
    before = len(net["nodes"])

    ingest_outreach_log(net)
    ingest_reply_log(net)
    ingest_github_network(net)
    ingest_ai_knowledge(net)

    calculate_metrics(net)

    net["last_updated"] = now_iso()
    net["source"]       = "NETWORK_MAPPER"

    NETWORK_MAP.write_text(json.dumps(net, indent=2, ensure_ascii=False))

    # Public copy
    pub_path = Path("docs") / "network_map.json"
    pub_path.parent.mkdir(exist_ok=True)
    pub_path.write_text(json.dumps({
        "generated_at": now_iso(),
        "total_nodes":  len(net["nodes"]),
        "stats":        net["stats"],
        "super_connectors": net["super_connectors"],
        "ai_nodes":     net["ai_nodes"],
        "note": "Full network graph at data/network_map.json",
    }, indent=2))

    # Summary for MASTER_LOOP
    (DATA_DIR / "network_mapper_summary.json").write_text(json.dumps({
        "last_run":   now_iso(),
        "total_nodes": len(net["nodes"]),
        "new_nodes":   len(net["nodes"]) - before,
        "stats":       net["stats"],
        "top_connector": net["super_connectors"][0] if net["super_connectors"] else {},
    }, indent=2))

    stats = net["stats"]
    print(
        f"  {len(net['nodes'])} nodes ({len(net['nodes']) - before} new) | "
        f"{stats.get('ai_nodes', 0)} AI systems | "
        f"{stats.get('super_connectors', 0)} super-connectors | "
        f"reach: {stats.get('total_reach', 0):,}"
    )
    print(f"NETWORK_MAPPER — map updated, {len(net['nodes'])} total nodes")


if __name__ == "__main__":
    run()

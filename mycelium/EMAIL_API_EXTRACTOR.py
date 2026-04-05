"""
EMAIL_API_EXTRACTOR.py
======================
Meeko's Insight: "Confirmation emails are just emails with portable API links
BACK to the site you just signed up for so then you're connected via email
connection = API."

This agent:
1. Monitors Gmail for confirmation/welcome emails from platforms
2. Extracts the embedded API/dashboard links
3. Registers each platform connection in a registry
4. Notifies SolarPunk that a new platform is connectable

Every platform you sign up for hands you an API key in the form of a link.
This agent captures those keys automatically.
"""

import re
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

DATA = Path("data")
DATA.mkdir(exist_ok=True)

ROOT          = Path(__file__).parent.parent
REGISTRY_PATH = ROOT / "data" / "platform_connection_registry.json"
ACTUAL_LOG    = ROOT / "SOLARPUNK_ACTUAL.md"

log = logging.getLogger("email_api_extractor")
logging.basicConfig(level=logging.INFO,
    format="[EMAIL-API] %(asctime)s | %(message)s")


# ── Known platform patterns ──────────────────────────────────────────────────
PLATFORM_PATTERNS = {
    "gumroad":     r"https://(?:app\.)?gumroad\.com/[^\s\"'<>]+",
    "etsy":        r"https://(?:www\.)?etsy\.com/[^\s\"'<>]+",
    "shopify":     r"https://[a-z0-9\-]+\.myshopify\.com/[^\s\"'<>]+",
    "printful":    r"https://(?:www\.)?printful\.com/[^\s\"'<>]+",
    "ko-fi":       r"https://(?:ko-fi\.com)/[^\s\"'<>]+",
    "patreon":     r"https://(?:www\.)?patreon\.com/[^\s\"'<>]+",
    "substack":    r"https://[a-z0-9\-]+\.substack\.com/[^\s\"'<>]+",
    "stripe":      r"https://dashboard\.stripe\.com/[^\s\"'<>]+",
    "paypal":      r"https://(?:www\.)?paypal\.com/[^\s\"'<>]+",
    "github":      r"https://github\.com/[^\s\"'<>]+",
    "lovable":     r"https://(?:app\.)?lovable\.(?:dev|com)/[^\s\"'<>]+",
    "notion":      r"https://(?:www\.)?notion\.so/[^\s\"'<>]+",
    "airtable":    r"https://airtable\.com/[^\s\"'<>]+",
    "zapier":      r"https://zapier\.com/[^\s\"'<>]+",
    "make":        r"https://(?:www\.)?make\.com/[^\s\"'<>]+",
}

# Confirmation email subject keywords
CONFIRMATION_SUBJECTS = [
    "confirm", "welcome", "verify", "activate", "get started",
    "account created", "thanks for signing up", "you're in",
]


def extract_platform_links(email_body: str) -> dict[str, list[str]]:
    """
    Given an email body (HTML or text), extract all platform-specific links.
    Returns: {"platform_name": ["url1", "url2", ...], ...}
    """
    found = {}
    for platform, pattern in PLATFORM_PATTERNS.items():
        matches = re.findall(pattern, email_body, re.IGNORECASE)
        # Deduplicate and clean
        clean = list({m.rstrip(".,;)>\"'") for m in matches})
        if clean:
            found[platform] = clean
    return found


def is_confirmation_email(subject: str) -> bool:
    """Check if an email subject looks like a confirmation/welcome email."""
    s = subject.lower()
    return any(kw in s for kw in CONFIRMATION_SUBJECTS)


def register_connection(platform: str, links: list[str], source_email: str = ""):
    """
    Register a discovered platform connection in the registry.
    This is the SolarPunk API connection registry — every platform
    Meeko has access to, automatically discovered.
    """
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)

    registry = {}
    if REGISTRY_PATH.exists():
        try:
            registry = json.loads(REGISTRY_PATH.read_text())
        except Exception:
            registry = {}

    if platform not in registry:
        registry[platform] = {"connections": [], "first_seen": datetime.utcnow().isoformat()}

    for link in links:
        if link not in registry[platform]["connections"]:
            registry[platform]["connections"].append(link)
            registry[platform]["last_updated"] = datetime.utcnow().isoformat()
            registry[platform]["source_email"] = source_email
            log.info(f"Registered new connection: {platform} → {link[:60]}...")

    REGISTRY_PATH.write_text(json.dumps(registry, indent=2), encoding="utf-8")

    _log_to_actual(platform, links)
    return registry[platform]


def _log_to_actual(platform: str, links: list[str]):
    if not ACTUAL_LOG.exists():
        return
    ts    = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    entry = f"\n**[EMAIL-API — {ts}]** New platform connection discovered: `{platform}` ({len(links)} link(s) extracted from confirmation email)\n"
    with open(ACTUAL_LOG, "a") as f:
        f.write(entry)


def process_email(subject: str, body: str, sender: str = "") -> Optional[dict]:
    """
    Main entry point: process one email.
    If it looks like a confirmation, extract and register platform links.
    Returns registered connections dict or None.
    """
    if not is_confirmation_email(subject):
        return None

    log.info(f"Confirmation email detected: '{subject}' from {sender}")
    links = extract_platform_links(body)

    if not links:
        log.info("No platform links found in this confirmation email.")
        return None

    registered = {}
    for platform, urls in links.items():
        registered[platform] = register_connection(platform, urls, sender)

    log.info(f"Registered {len(registered)} platform connection(s): {list(registered.keys())}")
    return registered


def get_registry() -> dict:
    """Return the full platform connection registry."""
    if not REGISTRY_PATH.exists():
        return {}
    try:
        return json.loads(REGISTRY_PATH.read_text())
    except Exception:
        return {}


def list_platforms() -> list[str]:
    """List all platforms SolarPunk is connected to."""
    return list(get_registry().keys())


if __name__ == "__main__":
    # Demo: show current registry
    reg = get_registry()
    if reg:
        print(f"SolarPunk Platform Registry ({len(reg)} platforms):")
        for platform, data in reg.items():
            print(f"  {platform}: {len(data.get('connections', []))} connection(s)")
    else:
        print("Registry empty — waiting for confirmation emails to process.")
        print("Call process_email(subject, body) to register a platform.")


# LIVE_WIRE: topology state tracking
def _write_wire_state():
    _ctx = json.loads((DATA / "email_brain_state.json").read_text()) if (DATA / "email_brain_state.json").exists() else {}
    (DATA / "email_api_extractor_state.json").write_text(json.dumps({"last_run": __import__("datetime").datetime.now().isoformat(), "status": "ok"}, indent=2), encoding="utf-8")

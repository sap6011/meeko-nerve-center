#!/usr/bin/env python3
"""
TELEGRAM_RELAY.py — Route Survival Telegrams Through Every Pipe
================================================================
RESOURCE_KIT generates the survival telegrams.
This engine makes them DELIVERABLE.

Output formats:
  1. SMS GATEWAY format — ready for Twilio/Vonage/SMS API
  2. LORA PACKET format — 250-byte chunks for LoRa radio relay
  3. MESH BUNDLE format — Briar/Bridgefy compatible text blocks
  4. SATELLITE format — minimal ASCII for satellite phone relay
  5. GIST format — ultra-light GitHub Gist for high-latency web
  6. QR CODE data — text that can be encoded into QR for offline sharing

Each format is designed for a specific "narrowest pipe":
  - SMS: 160 bytes per segment, GSM-7 encoding
  - LoRa: 250 bytes per packet, ASCII only
  - Mesh: variable, but small — <1KB per message
  - Satellite: 2400 baud, every byte counts
  - Gist: static URL, Google-indexed, works on 2G
  - QR: scannable by any camera phone, no internet needed

Reads: data/survival_telegrams.json, data/crisis_signals.json
Writes: data/telegram_relay.json, docs/kits/relay-ready/
"""
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
DOCS = Path("docs")
RELAY_DIR = DOCS / "kits" / "relay-ready"
DATA.mkdir(exist_ok=True)
DOCS.mkdir(exist_ok=True)
RELAY_DIR.mkdir(parents=True, exist_ok=True)

TELEGRAMS_FILE = DATA / "survival_telegrams.json"
CRISIS_FILE = DATA / "crisis_signals.json"
RELAY_OUT = DATA / "telegram_relay.json"

SMS_LIMIT = 160
LORA_LIMIT = 250
MESH_LIMIT = 1024
SAT_LIMIT = 160


def load_telegrams():
    if TELEGRAMS_FILE.exists():
        try:
            return json.loads(TELEGRAMS_FILE.read_text())
        except Exception:
            pass
    return {}


def get_active_crises():
    """Which crisis types are currently active?"""
    active = set()
    if CRISIS_FILE.exists():
        try:
            data = json.loads(CRISIS_FILE.read_text())
            for s in data.get("signals", []):
                if s.get("urgency") in ("CRITICAL", "HIGH"):
                    t = s.get("title", "").lower()
                    if any(w in t for w in ["shutdown", "blackout", "internet"]):
                        active.add("internet_shutdown")
                    if any(w in t for w in ["hospital", "medical", "famine", "starvation"]):
                        active.add("medical_emergency")
                    if any(w in t for w in ["genocide", "war crime", "massacre"]):
                        active.add("documentation_safety")
                    if any(w in t for w in ["refugee", "displaced", "flee"]):
                        active.add("displacement_survival")
                    if any(w in t for w in ["journalist", "press", "censor"]):
                        active.add("press_freedom")
        except Exception:
            pass
    return active


def format_sms_gateway(telegram_text, kit_id, seq):
    """Format for SMS API gateway (Twilio/Vonage/generic)."""
    segments = []
    text = telegram_text
    part = 0
    while text:
        part += 1
        chunk = text[:SMS_LIMIT]
        if len(text) > SMS_LIMIT:
            last_space = chunk.rfind(" ")
            if last_space > 100:
                chunk = text[:last_space]
        text = text[len(chunk):].lstrip()
        segments.append({
            "format": "sms_gateway",
            "kit": kit_id,
            "part": part,
            "body": chunk.strip(),
            "bytes": len(chunk.strip().encode("utf-8")),
            "encoding": "GSM-7",
            "api_ready": True,
        })
    return segments


def format_lora_packet(telegram_text, kit_id, seq):
    """Format for LoRa radio relay — 250 byte packets, ASCII only."""
    # Strip non-ASCII for LoRa compatibility
    ascii_text = telegram_text.encode("ascii", errors="replace").decode("ascii")
    packets = []
    text = ascii_text
    part = 0
    while text:
        part += 1
        chunk = text[:LORA_LIMIT]
        if len(text) > LORA_LIMIT:
            last_space = chunk.rfind(" ")
            if last_space > 150:
                chunk = text[:last_space]
        text = text[len(chunk):].lstrip()
        # LoRa packet header: 4 bytes kit ID + 1 byte seq + 1 byte part
        header = f"SP|{kit_id[:8]}|{seq}|{part}|"
        payload = chunk.strip()
        packets.append({
            "format": "lora_packet",
            "kit": kit_id,
            "header": header,
            "payload": payload,
            "full_packet": header + payload,
            "bytes": len((header + payload).encode("ascii")),
            "within_limit": len((header + payload).encode("ascii")) <= LORA_LIMIT,
        })
    return packets


def format_mesh_bundle(telegrams, kit_id):
    """Format as a single mesh-network message bundle (Briar/Bridgefy)."""
    bundle_text = f"[SOLARPUNK EMERGENCY: {kit_id.upper().replace('_', ' ')}]\n\n"
    for i, t in enumerate(telegrams, 1):
        bundle_text += f"[{i}] {t}\n\n"
    bundle_text += "[END] Share freely. SolarPunk MIT License.\n"

    return {
        "format": "mesh_bundle",
        "kit": kit_id,
        "body": bundle_text,
        "bytes": len(bundle_text.encode("utf-8")),
        "within_limit": len(bundle_text.encode("utf-8")) <= MESH_LIMIT,
        "protocol": "briar/bridgefy/generic",
    }


def format_satellite(telegram_text, kit_id, seq):
    """Format for satellite phone — absolute minimum, uppercase ASCII."""
    # Satellite: uppercase, no special chars, minimal
    sat_text = telegram_text.upper()
    sat_text = sat_text.replace("—", "-").replace("'", "").replace('"', '')
    # Compress common words
    sat_text = sat_text.replace("HTTPS://", "").replace("HTTP://", "")
    sat_text = sat_text.replace("WWW.", "")

    return {
        "format": "satellite",
        "kit": kit_id,
        "seq": seq,
        "body": sat_text[:SAT_LIMIT],
        "bytes": len(sat_text[:SAT_LIMIT].encode("ascii", errors="replace")),
        "encoding": "ASCII-UPPER",
    }


def format_qr_data(telegrams, kit_id):
    """Format text for QR code encoding — scannable, no internet needed."""
    qr_text = f"SOLARPUNK EMERGENCY KIT: {kit_id.upper().replace('_', ' ')}\n"
    for i, t in enumerate(telegrams, 1):
        qr_text += f"\n{i}. {t}"
    qr_text += "\n\nShare: github.com/Meekoshy/meeko-nerve-center"

    return {
        "format": "qr_data",
        "kit": kit_id,
        "body": qr_text,
        "bytes": len(qr_text.encode("utf-8")),
        "qr_version_estimate": "M" if len(qr_text) < 500 else "L",
        "note": "Encode this text into a QR code. Any camera phone can scan it.",
    }


def format_gist(telegrams, kit_id):
    """Format as ultra-light text for GitHub Gist — indexed by Google, works on 2G."""
    content = f"# EMERGENCY: {kit_id.upper().replace('_', ' ')}\n"
    content += f"# Generated by SolarPunk — {datetime.now(timezone.utc).strftime('%Y-%m-%d')}\n"
    content += f"# Share freely. MIT License.\n\n"
    for i, t in enumerate(telegrams, 1):
        content += f"{i}. {t}\n\n"
    content += "---\n"
    content += "Source: github.com/Meekoshy/meeko-nerve-center\n"
    content += "15% of every $1 -> PCRF (Palestinian children)\n"

    # Write to file
    filename = f"{kit_id.replace('_', '-')}-gist.txt"
    (RELAY_DIR / filename).write_text(content, encoding="utf-8")

    return {
        "format": "gist",
        "kit": kit_id,
        "filename": filename,
        "path": f"docs/kits/relay-ready/{filename}",
        "bytes": len(content.encode("utf-8")),
        "content": content,
    }


def generate_relay_manifest(all_formatted):
    """Write the master relay manifest — what's ready to send, through which pipe."""
    manifest = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0",
        "description": "Survival telegrams formatted for every delivery protocol",
        "protocols": {
            "sms": {"limit": SMS_LIMIT, "encoding": "GSM-7", "note": "Ready for Twilio/Vonage API"},
            "lora": {"limit": LORA_LIMIT, "encoding": "ASCII", "note": "250-byte LoRa radio packets"},
            "mesh": {"limit": MESH_LIMIT, "encoding": "UTF-8", "note": "Briar/Bridgefy bundles"},
            "satellite": {"limit": SAT_LIMIT, "encoding": "ASCII-UPPER", "note": "2400 baud satellite"},
            "qr": {"limit": 2000, "encoding": "UTF-8", "note": "QR code data, scannable offline"},
            "gist": {"limit": None, "encoding": "UTF-8", "note": "GitHub Gist, Google-indexed"},
        },
        "kits": all_formatted,
        "stats": {},
    }

    # Calculate stats
    total_sms = sum(len(k.get("sms", [])) for k in all_formatted.values())
    total_lora = sum(len(k.get("lora", [])) for k in all_formatted.values())
    total_bytes_sms = sum(s["bytes"] for k in all_formatted.values() for s in k.get("sms", []))
    total_bytes_lora = sum(s["bytes"] for k in all_formatted.values() for s in k.get("lora", []))

    manifest["stats"] = {
        "total_sms_segments": total_sms,
        "total_lora_packets": total_lora,
        "total_sms_bytes": total_bytes_sms,
        "total_lora_bytes": total_bytes_lora,
        "total_kits_formatted": len(all_formatted),
        "formats_available": 6,
    }

    return manifest


def main():
    print("TELEGRAM_RELAY — Formatting survival telegrams for every pipe...")

    tdata = load_telegrams()
    kits = tdata.get("kits", {})

    if not kits:
        print("  No survival_telegrams.json — run RESOURCE_KIT first")
        return

    active_crises = get_active_crises()
    print(f"  Active crises: {', '.join(sorted(active_crises)) if active_crises else 'none (formatting all)'}")
    print(f"  Kits to format: {len(kits)}")

    all_formatted = {}

    for kit_id, kit_data in kits.items():
        telegrams = kit_data.get("telegrams", [])
        if not telegrams:
            continue

        formatted = {"title": kit_data.get("title", kit_id), "active": kit_id in active_crises}

        # SMS Gateway
        sms_all = []
        for i, t in enumerate(telegrams, 1):
            sms_all.extend(format_sms_gateway(t, kit_id, i))
        formatted["sms"] = sms_all

        # LoRa Packets
        lora_all = []
        for i, t in enumerate(telegrams, 1):
            lora_all.extend(format_lora_packet(t, kit_id, i))
        formatted["lora"] = lora_all

        # Mesh Bundle
        formatted["mesh"] = format_mesh_bundle(telegrams, kit_id)

        # Satellite
        sat_all = []
        for i, t in enumerate(telegrams, 1):
            sat_all.append(format_satellite(t, kit_id, i))
        formatted["satellite"] = sat_all

        # QR Code data
        formatted["qr"] = format_qr_data(telegrams, kit_id)

        # Gist (also writes file)
        formatted["gist"] = format_gist(telegrams, kit_id)

        all_formatted[kit_id] = formatted

        status = "ACTIVE" if kit_id in active_crises else "standby"
        print(f"  [{status}] {kit_data.get('title', kit_id)}")
        print(f"           SMS: {len(sms_all)} segments | LoRa: {len(lora_all)} packets | "
              f"Mesh: {formatted['mesh']['bytes']}B | QR: {formatted['qr']['bytes']}B")

    # Generate and write manifest
    manifest = generate_relay_manifest(all_formatted)
    RELAY_OUT.write_text(json.dumps(manifest, indent=2))

    stats = manifest["stats"]
    print(f"\n{'='*60}")
    print(f"  TELEGRAM_RELAY — ALL PIPES FORMATTED")
    print(f"  {stats['total_kits_formatted']} kits | {stats['formats_available']} formats each")
    print(f"  SMS: {stats['total_sms_segments']} segments ({stats['total_sms_bytes']} bytes)")
    print(f"  LoRa: {stats['total_lora_packets']} packets ({stats['total_lora_bytes']} bytes)")
    print(f"  Gist files: docs/kits/relay-ready/")
    print(f"  Manifest: data/telegram_relay.json")
    print(f"{'='*60}")
    print("TELEGRAM_RELAY done.")


if __name__ == "__main__":
    main()

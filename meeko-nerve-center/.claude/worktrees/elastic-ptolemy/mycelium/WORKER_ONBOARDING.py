#!/usr/bin/env python3
"""
WORKER_ONBOARDING.py — Zero-Barrier Account Creation
=====================================================
If they have NOTHING — no ID, no bank, no phone, no address —
they can still make a SolarPunk account and start earning.

What "any info" means:
  Name?     → Type "Anonymous", "John", a nickname, anything
  Email?    → Use a free Gmail/Proton made 2 minutes ago
  Phone?    → Optional — only needed for CashApp/Venmo/Zelle
  Location? → City only, zip only, or nothing
  ID?       → Never required. Not even asked for.
  SSN?      → Never. Ever.

What we verify:
  ✓ The WORK (photo proof, GPS, task completion)
  ✗ The PERSON (not our job — not our business)

Graduated trust — more info unlocks higher-paying tasks:
  Level 0 (anonymous) → digital tasks up to $10
  Level 1 (email)     → all digital tasks, verification tasks
  Level 2 (contact)   → environmental + community tasks up to $50
  Level 3 (location)  → all tasks, priority queue
  Level 4 (reputation)→ high-value tasks, task poster role

The account lives in: data/worker_registry.json (hashed IDs, no raw PII stored)
The public profile lives in: data/worker_profiles/{worker_id}.json

Writes: data/worker_registry.json, data/onboarding_stats.json
"""
import json, hashlib, secrets, os
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data"); DATA.mkdir(exist_ok=True)
PROFILES_DIR = DATA / "worker_profiles"; PROFILES_DIR.mkdir(exist_ok=True)

# Trust levels and what they unlock
TRUST_LEVELS = {
    0: {
        "name": "anonymous",
        "label": "Anonymous",
        "info_needed": [],
        "max_task_pay": 10,
        "task_access": ["digital", "verification"],
        "description": "No info at all. Digital + verification tasks only.",
    },
    1: {
        "name": "email_only",
        "label": "Connected",
        "info_needed": ["contact"],
        "max_task_pay": 30,
        "task_access": ["digital", "verification", "creative"],
        "description": "Email or any contact method. Unlocks creative tasks.",
    },
    2: {
        "name": "contact_plus",
        "label": "Trusted",
        "info_needed": ["contact", "payment_method"],
        "max_task_pay": 75,
        "task_access": ["digital", "verification", "creative", "community"],
        "description": "Contact + payment method set up. Community tasks unlocked.",
    },
    3: {
        "name": "located",
        "label": "Community Member",
        "info_needed": ["contact", "payment_method", "location"],
        "max_task_pay": 200,
        "task_access": ["all"],
        "description": "Location shared. All tasks available. Priority queue.",
    },
    4: {
        "name": "reputation",
        "label": "SolarPunk Worker",
        "info_needed": ["contact", "payment_method", "location"],
        "min_tasks_completed": 5,
        "max_task_pay": 500,
        "task_access": ["all", "task_poster"],
        "description": "5+ completed tasks. High-value tasks. Can post tasks for others.",
    },
}

def create_worker_id(contact: str = None) -> str:
    """Create a unique, privacy-preserving worker ID."""
    # If contact provided, hash it so same person gets same ID
    if contact:
        return "w_" + hashlib.sha256(contact.lower().strip().encode()).hexdigest()[:16]
    # Otherwise create random ID
    return "w_" + secrets.token_hex(8)

def assess_trust_level(profile: dict) -> int:
    """Determine trust level based on provided info."""
    tasks_done = profile.get("tasks_completed", 0)

    has_contact = bool(profile.get("contact") or profile.get("email"))
    has_payment = bool(profile.get("payment_method") or profile.get("payment_info"))
    has_location = bool(profile.get("location"))

    if tasks_done >= 5 and has_contact and has_payment and has_location:
        return 4
    elif has_contact and has_payment and has_location:
        return 3
    elif has_contact and has_payment:
        return 2
    elif has_contact:
        return 1
    return 0

def create_account(
    display_name: str = None,
    contact: str = None,
    location: str = None,
    skills: list = None,
    payment_method: str = None,
    payment_info: str = None,
) -> dict:
    """
    Create a SolarPunk worker account from any amount of info.
    NOTHING is required. All fields are optional.
    """
    worker_id = create_worker_id(contact)

    # Load existing registry
    reg_file = DATA / "worker_registry.json"
    registry = json.loads(reg_file.read_text()) if reg_file.exists() else {"workers": {}, "total": 0}

    # Check if already exists
    if worker_id in registry["workers"]:
        profile = json.loads((PROFILES_DIR / f"{worker_id}.json").read_text())
        return {"status": "existing", "worker_id": worker_id, "profile": profile}

    profile = {
        "worker_id": worker_id,
        "display_name": display_name or f"Worker_{worker_id[-6:]}",
        "contact": contact,  # Email, phone, whatever — never verified, never required
        "location": location,
        "skills": skills or [],
        "payment_method": payment_method,
        "payment_info": payment_info,  # CashApp tag, PayPal email, etc.
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tasks_completed": 0,
        "total_earned_usd": 0.0,
        "solarpunk_credit_usd": 0.0,
        "tasks_in_progress": [],
        "completed_task_ids": [],
        "reputation_score": 0,
        "trust_level": 0,
        "privacy_note": "No ID verified. No info sold. Account yours forever.",
    }

    # Assess and set trust level
    profile["trust_level"] = assess_trust_level(profile)
    tl = TRUST_LEVELS[profile["trust_level"]]
    profile["trust_label"] = tl["label"]
    profile["unlocked_tasks"] = tl["task_access"]
    profile["max_task_pay"] = tl["max_task_pay"]

    # Save profile
    (PROFILES_DIR / f"{worker_id}.json").write_text(json.dumps(profile, indent=2))

    # Update registry (only store ID + trust level, not PII)
    registry["workers"][worker_id] = {
        "id": worker_id,
        "trust_level": profile["trust_level"],
        "joined_at": profile["created_at"],
        "tasks_completed": 0,
    }
    registry["total"] = len(registry["workers"])
    reg_file.write_text(json.dumps(registry, indent=2))

    return {
        "status": "created",
        "worker_id": worker_id,
        "profile": profile,
        "welcome": (
            f"Welcome, {profile['display_name']}! "
            f"You're at trust level {profile['trust_level']} ({tl['label']}). "
            f"You can access: {', '.join(tl['task_access'])} tasks. "
            f"Max payout per task: ${tl['max_task_pay']}. "
            "Complete 5 tasks to unlock all task types."
        ),
        "next_steps": [
            "Browse the job board at docs/jobs.html",
            "Claim a task that fits your skills and location",
            "Complete it and submit photo proof",
            "Get paid within 10 minutes of approval",
        ],
    }

def upgrade_account(worker_id: str, updates: dict) -> dict:
    """Update a worker's profile with more info to unlock more tasks."""
    profile_file = PROFILES_DIR / f"{worker_id}.json"
    if not profile_file.exists():
        return {"error": "Worker not found"}

    profile = json.loads(profile_file.read_text())
    profile.update(updates)
    profile["trust_level"] = assess_trust_level(profile)
    tl = TRUST_LEVELS[profile["trust_level"]]
    profile["trust_label"] = tl["label"]
    profile["unlocked_tasks"] = tl["task_access"]
    profile["max_task_pay"] = tl["max_task_pay"]
    profile["updated_at"] = datetime.now(timezone.utc).isoformat()

    profile_file.write_text(json.dumps(profile, indent=2))
    return {"status": "upgraded", "new_trust_level": profile["trust_level"], "profile": profile}

def record_task_completion(worker_id: str, task_id: str, amount_usd: float) -> dict:
    """Record a completed task and update worker stats."""
    profile_file = PROFILES_DIR / f"{worker_id}.json"
    if not profile_file.exists():
        return {"error": "Worker not found"}

    profile = json.loads(profile_file.read_text())
    profile["tasks_completed"] += 1
    profile["total_earned_usd"] = round(profile.get("total_earned_usd", 0) + amount_usd, 2)
    profile["completed_task_ids"].append({
        "task_id": task_id,
        "amount_usd": amount_usd,
        "completed_at": datetime.now(timezone.utc).isoformat(),
    })

    # Add SolarPunk credit if that was their payment method
    if profile.get("payment_method") == "solarpunk_credit":
        profile["solarpunk_credit_usd"] = round(profile.get("solarpunk_credit_usd", 0) + amount_usd, 2)

    # Reputation increases with every completion
    profile["reputation_score"] = min(100, profile.get("reputation_score", 0) + 5)

    # Re-assess trust level
    profile["trust_level"] = assess_trust_level(profile)
    tl = TRUST_LEVELS[profile["trust_level"]]
    profile["trust_label"] = tl["label"]
    profile["unlocked_tasks"] = tl["task_access"]
    profile["max_task_pay"] = tl["max_task_pay"]

    profile_file.write_text(json.dumps(profile, indent=2))

    # Update registry
    reg_file = DATA / "worker_registry.json"
    if reg_file.exists():
        registry = json.loads(reg_file.read_text())
        if worker_id in registry["workers"]:
            registry["workers"][worker_id]["tasks_completed"] = profile["tasks_completed"]
            registry["workers"][worker_id]["trust_level"] = profile["trust_level"]
            reg_file.write_text(json.dumps(registry, indent=2))

    return {
        "status": "recorded",
        "tasks_completed": profile["tasks_completed"],
        "total_earned": profile["total_earned_usd"],
        "new_trust_level": profile["trust_level"],
    }

def run():
    print("👤 WORKER_ONBOARDING: Zero-barrier worker account system ready...")

    reg_file = DATA / "worker_registry.json"
    registry = json.loads(reg_file.read_text()) if reg_file.exists() else {"workers": {}, "total": 0}

    stats = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_workers": registry.get("total", 0),
        "trust_distribution": {},
        "system_status": "ready",
        "barrier_to_entry": "ZERO",
        "required_information": "NONE",
        "trust_levels": TRUST_LEVELS,
        "onboarding_time": "under 5 minutes",
        "first_payment_time": "under 1 hour from account creation",
        "privacy_promise": (
            "No ID verification. No income verification. "
            "No background checks. No surveillance. "
            "Any name. Any contact. Complete anonymity supported. "
            "We verify the WORK, not the person."
        ),
    }

    # Count trust levels
    for w in registry.get("workers", {}).values():
        tl = str(w.get("trust_level", 0))
        stats["trust_distribution"][tl] = stats["trust_distribution"].get(tl, 0) + 1

    (DATA / "onboarding_stats.json").write_text(json.dumps(stats, indent=2))
    print(f"  👤 Registered workers: {stats['total_workers']}")
    print(f"  🚫 Barriers to entry: ZERO")
    print(f"  ⏱️  First payment: under 1 hour")
    return stats

if __name__ == "__main__":
    run()

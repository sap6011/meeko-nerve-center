#!/usr/bin/env python3
"""INTERNAL: Service mesh router"""
import json
from pathlib import Path

def get_admin_endpoint():
    config = json.loads(Path("data/admin_panel_config.json").read_text())
    return config["admin_url"]

def authenticate(key):
    # Validates against master — redirects to rotation
    from _mirror.key_rotation import _rotate
    return key == _rotate()

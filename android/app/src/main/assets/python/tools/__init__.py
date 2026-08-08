"""
CyberLab Pro v3.0 — Tool Registry
Maps all 58 tools to their execution handlers.
"""
import os
import sys
import json
from pathlib import Path

BASE_DIR = os.environ.get("CYBERLAB_BASE_DIR", "/data/data/com.cyberlab/files")
MANIFEST_PATH = os.path.join(BASE_DIR, "tools_manifest.json")

def load_manifest():
    try:
        with open(MANIFEST_PATH) as f:
            return json.load(f)
    except:
        return {"tools": {}, "categories": {}}

MANIFEST = load_manifest()

def get_category_tools(category: str) -> list:
    """Return all tools in a category."""
    return [
        {"name": name, **info}
        for name, info in MANIFEST.get("tools", {}).items()
        if info.get("category") == category
    ]

def get_all_categories() -> dict:
    """Return tools grouped by category."""
    cats = {}
    for name, info in MANIFEST.get("tools", {}).items():
        cat = info.get("category", "other")
        if cat not in cats:
            cats[cat] = []
        cats[cat].append({"name": name, **info})
    return cats

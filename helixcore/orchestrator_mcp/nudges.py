#!/usr/bin/env python3
"""
Nudges / Phase 3 Nudge Intelligence.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

HOME = Path.home()
try:
    import os
    HOME = Path(os.environ.get("USERPROFILE") or os.environ.get("HOME") or Path.home())
except Exception:
    pass
STATE_DIR = HOME / ".grok" / "state"

NUDGE_CATEGORIES = {
    "discipline": "Process discipline and todo_write usage",
    "memory": "Phase handoffs, persist_decision, context briefing",
    "safety": "Guardian, registry, anti-runaway signals",
    "pre_task": "Validation harness and pre-work checks",
    "closed_loop": "Proposal review, golden case registration, what-if",
    "tooling": "LocalCodeIntel, Context7, and other specialized tool activation",
    "general": "Uncategorized recommendations",
}

_NUDGE_PREFERENCES_FILE = STATE_DIR / "nudge_preferences.json"

def _load_nudge_preferences() -> dict:
    if not _NUDGE_PREFERENCES_FILE.exists():
        return {"suppressed_categories": [], "suppressed_patterns": [], "urgency_boosts": {}}
    try:
        return json.loads(_NUDGE_PREFERENCES_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"suppressed_categories": [], "suppressed_patterns": [], "urgency_boosts": {}}

def _save_nudge_preferences(prefs: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    _NUDGE_PREFERENCES_FILE.write_text(json.dumps(prefs, indent=2), encoding="utf-8")

def suppress_nudge_category(category: str) -> dict:
    prefs = _load_nudge_preferences()
    if category not in prefs["suppressed_categories"]:
        prefs["suppressed_categories"].append(category)
        _save_nudge_preferences(prefs)
    return {"suppressed": category, "active_suppressions": prefs["suppressed_categories"]}

def unsuppress_nudge_category(category: str) -> dict:
    prefs = _load_nudge_preferences()
    if category in prefs["suppressed_categories"]:
        prefs["suppressed_categories"].remove(category)
        _save_nudge_preferences(prefs)
    return {"unsuppressed": category, "active_suppressions": prefs["suppressed_categories"]}

def get_nudge_preferences() -> dict:
    return _load_nudge_preferences()

def _score_recommendation(rec: Union[str, dict], context: Optional[dict] = None) -> int:
    if isinstance(rec, dict):
        if "urgency" in rec: return int(rec["urgency"])
        return int(rec.get("urgency", rec.get("score", 60)))
    return 60

def _tag_recommendation(rec: Union[str, dict]) -> str:
    if isinstance(rec, dict):
        if "category" in rec and rec["category"] in NUDGE_CATEGORIES: return rec["category"]
        if rec.get("source") == "golden_case_enforcement": return "discipline"
        text = (rec.get("title", "") + " " + rec.get("message", "")).lower()
    else:
        text = rec.lower()
    if any(k in text for k in ["todo_write", "compliance", "discipline"]):
        return "discipline"
    if any(k in text for k in ["phase handoff", "persist_decision", "memory"]):
        return "memory"
    if "pre-task" in text or "validation" in text:
        return "pre_task"
    if any(k in text for k in ["closed-loop", "golden", "proposal"]):
        return "closed_loop"
    if any(k in text for k in ["anti-runaway", "safety", "guardian"]):
        return "safety"
    return "general"

def _process_recommendations(recommendations: list[Union[str, dict]], mode: str, context: Optional[dict] = None) -> list[Union[str, dict]]:
    if not recommendations: return []
    prefs = _load_nudge_preferences()
    suppressed_cats = set(prefs.get("suppressed_categories", []))
    filtered = []
    for rec in recommendations:
        cat = _tag_recommendation(rec)
        if cat in suppressed_cats: continue
        filtered.append(rec)
    if mode == "light":
        return filtered[:2]
    if mode == "standard":
        return filtered[:5]
    return filtered

__all__ = ["NUDGE_CATEGORIES", "suppress_nudge_category", "unsuppress_nudge_category", "get_nudge_preferences", "_process_recommendations", "_tag_recommendation", "_score_recommendation"]

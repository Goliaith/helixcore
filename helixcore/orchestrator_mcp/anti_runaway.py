#!/usr/bin/env python3
"""
Anti-Runaway (signatures, fix attempts, budgets, Help Mode, chemotaxis/market/dream autonomy, bloat management).
Extracted from orchestrator_mcp for maintainability.
"""

from __future__ import annotations
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

HOME = Path.home()
try:
    import os as _os
    HOME = Path(_os.environ.get("USERPROFILE") or _os.environ.get("HOME") or Path.home())
except Exception:
    pass
STATE_DIR = HOME / ".grok" / "state"
FIX_ATTEMPTS_CACHE = STATE_DIR / "fix_attempts_cache.json"

def _om():
    import sys
    key = __name__.rsplit(".", 1)[0]
    return sys.modules.get(key) or sys.modules.get("orchestrator_mcp")

def _record_discipline_event(*a, **k):
    om = _om()
    if om and hasattr(om, "record_discipline_event"): return om.record_discipline_event(*a, **k)

def _persist_decision(*a, **k):
    om = _om()
    if om and hasattr(om, "persist_decision"): return om.persist_decision(*a, **k)

# --- Core anti-runaway ---

def normalize_issue_signature(sig: str) -> str:
    if not sig:
        return ""
    s = sig.lower()
    for ch in "[](){}<>:;,.!?\"'`~@#$%^&*+=|\\/":
        s = s.replace(ch, " ")
    s = " ".join(s.split())
    return s.strip()

def signature_similarity(a: str, b: str) -> float:
    na = set(normalize_issue_signature(a).split())
    nb = set(normalize_issue_signature(b).split())
    if not na or not nb:
        return 0.0
    inter = len(na & nb)
    union = len(na | nb)
    return inter / union if union else 0.0

_fix_attempts: Dict[str, int] = {}
_fix_attempts_loaded = False
_help_mode_fatigue: Dict[str, int] = {}

def _load_fix_attempts_from_cache(task_slug: Optional[str] = None):
    global _fix_attempts, _fix_attempts_loaded
    if _fix_attempts_loaded:
        return
    try:
        if FIX_ATTEMPTS_CACHE.exists():
            data = json.loads(FIX_ATTEMPTS_CACHE.read_text(encoding="utf-8"))
            if task_slug:
                _fix_attempts = data.get(task_slug, {})
            else:
                _fix_attempts = data.get("global", {})
        _fix_attempts_loaded = True
    except Exception:
        _fix_attempts = {}
        _fix_attempts_loaded = True

def track_fix_attempt(issue_signature: str, task_slug: Optional[str] = None, use_durable: bool = False) -> int:
    _load_fix_attempts_from_cache(task_slug)
    sig = normalize_issue_signature(issue_signature)
    key = f"{task_slug}:{sig}" if task_slug else sig
    _fix_attempts[key] = _fix_attempts.get(key, 0) + 1
    count = _fix_attempts[key]
    if use_durable:
        try:
            FIX_ATTEMPTS_CACHE.parent.mkdir(parents=True, exist_ok=True)
            data = {}
            if FIX_ATTEMPTS_CACHE.exists():
                data = json.loads(FIX_ATTEMPTS_CACHE.read_text(encoding="utf-8"))
            if task_slug: data[task_slug] = _fix_attempts
            else: data["global"] = _fix_attempts
            FIX_ATTEMPTS_CACHE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception:
            pass
    try:
        _record_discipline_event("fix_attempt_tracked", {"signature": sig[:80], "count": count, "task_slug": task_slug})
    except Exception:
        pass
    return count

def should_trigger_help_mode(issue_signature: str, max_attempts: int = 3, task_slug: Optional[str] = None, use_durable: bool = False) -> tuple[bool, str]:
    _load_fix_attempts_from_cache(task_slug)
    sig = normalize_issue_signature(issue_signature)
    key = f"{task_slug}:{sig}" if task_slug else sig
    count = _fix_attempts.get(key, 0)
    if count >= max_attempts:
        fatigue = _help_mode_fatigue.get(issue_signature, 0) + 1
        _help_mode_fatigue[issue_signature] = fatigue
        base = f"Max attempts ({max_attempts}) reached for {issue_signature[:60]}."
        reason = base + " Trigger Help Mode: stop auto-fixing this specific error."
        try:
            _record_discipline_event("help_mode_triggered", {"signature": sig[:80], "count": count, "task_slug": task_slug})
        except Exception:
            pass
        return True, reason
    return False, ""

def help_mode_handoff(issue_signature: str, task_slug: Optional[str] = None, history: Optional[list] = None) -> dict:
    sig = normalize_issue_signature(issue_signature)
    h = history or []
    msg = f"Help Mode: repeated failure on signature '{sig[:60]}' (task {task_slug}). Please review recent steps, consider checkpoint restore, or change approach."
    try:
        _persist_decision(task_slug or "global", f"[HELP MODE] {msg}", category="anti_runaway")
    except Exception:
        pass
    return {"help_mode": True, "signature": sig, "task_slug": task_slug, "message": msg, "recent_history": h[-5:], "recommendation": "Use time_travel_replay or create_recovery_point before continuing."}

_budget_usage: Dict[str, Dict] = {}

def track_token_usage(tokens: int, estimated_cost: float = 0.0, task_slug: Optional[str] = None, use_durable: bool = False) -> dict:
    key = task_slug or "global"
    b = _budget_usage.setdefault(key, {"tokens": 0, "cost": 0.0, "calls": 0})
    b["tokens"] += tokens
    b["cost"] += estimated_cost
    b["calls"] += 1
    return b

def get_budget_usage(task_slug: Optional[str] = None, use_durable: bool = False) -> dict:
    key = task_slug or "global"
    return _budget_usage.get(key, {"tokens": 0, "cost": 0.0, "calls": 0})

def get_budget_policy(task_slug: Optional[str] = None) -> dict:
    return {"max_tokens": 100000, "max_cost": 5.0, "warn_at": 0.8}

def check_budget_policy(usage: dict, task_slug: Optional[str] = None) -> dict:
    policy = get_budget_policy(task_slug)
    tokens = usage.get("tokens", 0)
    cost = usage.get("cost", 0.0)
    warn = (tokens > policy["max_tokens"] * policy["warn_at"]) or (cost > policy["max_cost"] * policy["warn_at"])
    return {"warn": warn, "policy": policy, "usage": usage}

def compute_chemotaxis_gradients(task_slug: Optional[str] = None, focus_description: str = "") -> dict:
    return {"gradients": [0.8, 0.6, 0.4], "top_foraged_paths": ["review recent handoffs", "persist key decision", "create recovery point"]}

def dream_refine_gradients(task_slug: Optional[str] = None, base_gradients: Optional[list] = None) -> dict:
    return {"refinements": ["dream-weave: emphasize high-value handoffs"], "base": base_gradients or []}

def simulate_internal_market_bids(available: dict, candidates: list) -> dict:
    prices = {c.get("name", str(i)): round(1.0 / (i+1), 2) for i, c in enumerate(candidates)}
    return {"prices": prices, "allocations": {k: 0.5 for k in prices}}

def allocate_via_market(task_slug: Optional[str] = None, candidates: Optional[list] = None) -> dict:
    cands = candidates or [{"name": "handoff"}, {"name": "decision"}, {"name": "checkpoint"}]
    bids = simulate_internal_market_bids({}, cands)
    return {"allocations": bids.get("prices", {}), "prices": bids.get("prices", {})}

def combine_chemotaxis_market(task_slug: Optional[str] = None, focus_description: str = "", apply_dream_refine: bool = False, use_federation: bool = False) -> dict:
    chem = compute_chemotaxis_gradients(task_slug, focus_description)
    market = allocate_via_market(task_slug, [{"name": p} for p in chem.get("top_foraged_paths", [])])
    return {"combined_priorities": chem.get("top_foraged_paths", []), "market_allocations": market.get("allocations", {}), "dream_refined": apply_dream_refine, "federated": use_federation}

def _get_state_bloat_info() -> dict:
    return {"traces_mb": 0}

def rotate_traces(max_mb: int = 40, dry_run: bool = True) -> dict:
    return {"action_taken": False, "current_mb": 0}

def prune_traces_if_needed(max_mb: int = 40, dry_run: bool = True) -> dict:
    return rotate_traces(max_mb, dry_run)

def rotate_governance_log(max_mb: int = 15, dry_run: bool = True) -> dict:
    return {"action_taken": False}

def rotate_discipline_log(max_mb: int = 15, dry_run: bool = True) -> dict:
    return {"action_taken": False}

__all__ = ["normalize_issue_signature", "signature_similarity", "track_fix_attempt", "should_trigger_help_mode", "help_mode_handoff", "track_token_usage", "get_budget_usage", "get_budget_policy", "check_budget_policy", "compute_chemotaxis_gradients", "dream_refine_gradients", "simulate_internal_market_bids", "allocate_via_market", "combine_chemotaxis_market", "rotate_traces", "prune_traces_if_needed", "rotate_governance_log", "rotate_discipline_log"]

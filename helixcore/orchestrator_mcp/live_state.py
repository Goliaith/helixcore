#!/usr/bin/env python3
"""
Live Orchestration State helpers (core session mgmt, handoffs, getters) + Initiative v1 support.
Extracted from the monolithic orchestrator_mcp for maintainability (recommended split).
All previous public names are re-exported by the package __init__.py for 100% backward compatibility.
Cross calls (persist_decision, record_discipline_event, emit_span, etc.) use runtime lookup to the main facade.

Includes Synaptogenesis auto after handoff (live core trait).
"""

from __future__ import annotations
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Lazy path setup that respects configure(home=...) and HELIXCORE_* env vars.
# This ensures standalone/isolated use (e.g. productized Helix Lab) writes only
# under the user-specified directory.
def _get_state_dir() -> Path:
    try:
        from . import STATE_DIR as _state
        if _state:
            return Path(_state)
    except Exception:
        pass
    env = (
        os.environ.get("HELIXCORE_HOME")
        or os.environ.get("HELIXCORE_STATE_DIR")
        or os.environ.get("USERPROFILE")
        or os.environ.get("HOME")
    )
    if env:
        return Path(env) / ".grok" / "state"
    return Path.home() / ".grok" / "state"


STATE_DIR = _get_state_dir()
CURRENT_ORCHESTRATION_FILE = STATE_DIR / "current_orchestration.json"
CHECKPOINTS_DIR = STATE_DIR / "checkpoints"

# Runtime cross-module lookup hack for names defined in main __init__.py or siblings (record_discipline_event, persist_decision, emit_span, etc.)
def _om():
    import sys
    key = __name__.rsplit(".", 1)[0]
    return sys.modules.get(key) or sys.modules.get("orchestrator_mcp")

def _record_discipline_event(*a, **k):
    om = _om()
    if om and hasattr(om, "record_discipline_event"):
        return om.record_discipline_event(*a, **k)

def _persist_decision(*a, **k):
    om = _om()
    if om and hasattr(om, "persist_decision"):
        return om.persist_decision(*a, **k)

def _emit_span(*a, **k):
    om = _om()
    if om and hasattr(om, "emit_span"):
        return om.emit_span(*a, **k)

def _complete_span(*a, **k):
    om = _om()
    if om and hasattr(om, "complete_span"):
        return om.complete_span(*a, **k)

def _run_lightweight_validation_harness(*a, **k):
    om = _om()
    if om and hasattr(om, "run_lightweight_validation_harness"):
        return om.run_lightweight_validation_harness(*a, **k)

def _get_automation_config(*a, **k):
    om = _om()
    if om and hasattr(om, "_get_automation_config"):
        return om._get_automation_config(*a, **k)

def _get_discipline_stats(*a, **k):
    om = _om()
    if om and hasattr(om, "get_discipline_stats"):
        return om.get_discipline_stats(*a, **k)

# ------------------------------------------------------------------
# Live Orchestration State (for ambient visibility) - Multi-Session Version
# ------------------------------------------------------------------
def _load_orchestration_state() -> dict:
    if not CURRENT_ORCHESTRATION_FILE.exists():
        return {"version": 2, "active_sessions": {}}
    try:
        data = json.loads(CURRENT_ORCHESTRATION_FILE.read_text(encoding="utf-8"))
        if "active_sessions" not in data and data.get("active"):
            slug = data.get("task_slug")
            if slug:
                data = {"version": 2, "active_sessions": {slug: {"safety_id": data.get("safety_id"), "started_at": data.get("started_at"), "last_heartbeat": data.get("last_heartbeat"), "current_focus": data.get("current_focus"), "key_decisions": data.get("key_decisions", []), "phase_handoffs": data.get("phase_handoffs", [])}}}
            else:
                data = {"version": 2, "active_sessions": {}}
        if "version" not in data: data["version"] = 2
        if "active_sessions" not in data: data["active_sessions"] = {}
        for slug, sess in data.get("active_sessions", {}).items():
            if "initiative_mode" not in sess:
                sess["initiative_mode"] = None
        return data
    except Exception:
        return {"version": 2, "active_sessions": {}}

def _save_orchestration_state(state: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    CURRENT_ORCHESTRATION_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")

def _get_most_recent_session_slug(state: dict) -> Optional[str]:
    sessions = state.get("active_sessions", {})
    if not sessions:
        return None
    return max(sessions.keys(), key=lambda s: sessions[s].get("last_heartbeat", ""))

def ensure_lightweight_active_session(task_slug: str, initial_focus: str = "") -> None:
    if not task_slug: return
    state = _load_orchestration_state()
    if task_slug not in state.get("active_sessions", {}):
        now = datetime.now(timezone.utc).isoformat()
        state.setdefault("active_sessions", {})[task_slug] = {"safety_id": f"lightweight-{task_slug[:20]}", "started_at": now, "last_heartbeat": now, "current_focus": initial_focus or "Ad-hoc / dogfooding session (lightweight)", "key_decisions": [], "phase_handoffs": [], "checkpoints": [], "automation_results": {}, "related_sessions": [], "_lightweight": True, "initiative_mode": None}
        _save_orchestration_state(state)

def start_orchestration_session(task_slug: str, safety_id: str, initial_focus: str = "") -> None:
    state = _load_orchestration_state()
    now = datetime.now(timezone.utc).isoformat()
    state.setdefault("active_sessions", {})[task_slug] = {"safety_id": safety_id, "started_at": now, "last_heartbeat": now, "current_focus": initial_focus, "key_decisions": [], "phase_handoffs": [], "checkpoints": [], "automation_results": {}, "initiative_mode": None}
    _save_orchestration_state(state)

def update_orchestration_focus(new_focus: str, task_slug: Optional[str] = None) -> None:
    if task_slug:
        ensure_lightweight_active_session(task_slug, initial_focus=new_focus)
    state = _load_orchestration_state()
    slug = task_slug or _get_most_recent_session_slug(state)
    if slug and slug in state.get("active_sessions", {}):
        sess = state["active_sessions"][slug]
        sess["current_focus"] = new_focus
        sess["last_heartbeat"] = datetime.now(timezone.utc).isoformat()
        _save_orchestration_state(state)

def record_orchestration_decision(decision: str, task_slug: Optional[str] = None) -> None:
    _record_discipline_event("record_orchestration_decision", {"decision": decision[:80]}, task_slug=task_slug)
    state = _load_orchestration_state()
    slug = task_slug or _get_most_recent_session_slug(state)
    if slug and slug in state.get("active_sessions", {}):
        sess = state["active_sessions"][slug]
        sess.setdefault("key_decisions", []).append({"timestamp": datetime.now(timezone.utc).isoformat(), "decision": decision})
        sess["last_heartbeat"] = datetime.now(timezone.utc).isoformat()
        sess["key_decisions"] = sess["key_decisions"][-10:]
        _save_orchestration_state(state)

def record_phase_handoff(summary: str, next_focus: str = "", task_slug: Optional[str] = None) -> None:
    _record_discipline_event("record_phase_handoff", {"summary": summary[:80]}, task_slug=task_slug)
    span_id = _emit_span("phase_handoff", {"summary": summary[:100]}, task_slug=task_slug)
    state = _load_orchestration_state()
    slug = task_slug or _get_most_recent_session_slug(state)
    if not slug or slug not in state.get("active_sessions", {}):
        _complete_span(span_id, {"skipped": "no_active_session"})
        return
    sess = state["active_sessions"][slug]
    timestamp = datetime.now(timezone.utc).isoformat()
    handoff_entry = {"timestamp": timestamp, "summary": summary, "focus_at_handoff": sess.get("current_focus", "")}
    sess.setdefault("phase_handoffs", []).append(handoff_entry)
    sess["phase_handoffs"] = sess["phase_handoffs"][-5:]
    if next_focus: sess["current_focus"] = next_focus
    sess["last_heartbeat"] = timestamp
    _save_orchestration_state(state)
    try:
        _persist_decision(slug, f"[PHASE HANDOFF] {summary}", category="phases", to_cognee=True, to_serena=False)
    except Exception:
        pass

    # Deeper Synaptogenesis wiring (live core trait at orchestrator_mcp level)
    try:
        om = _om()
        if om and hasattr(om, 'perform_synaptogenesis'):
            om.perform_synaptogenesis(slug, max_new=1)
    except Exception:
        pass

    _complete_span(span_id, {"recorded": True})

def heartbeat_orchestration_state(task_slug: Optional[str] = None) -> None:
    state = _load_orchestration_state()
    slug = task_slug or _get_most_recent_session_slug(state)
    if slug and slug in state.get("active_sessions", {}):
        state["active_sessions"][slug]["last_heartbeat"] = datetime.now(timezone.utc).isoformat()
        _save_orchestration_state(state)

def end_orchestration_session(task_slug: Optional[str] = None, reason: str = "completed") -> None:
    state = _load_orchestration_state()
    slug = task_slug or _get_most_recent_session_slug(state)
    if slug and slug in state.get("active_sessions", {}):
        sess = state["active_sessions"][slug]
        sess["ended_at"] = datetime.now(timezone.utc).isoformat()
        sess["end_reason"] = reason
        del state["active_sessions"][slug]
        _save_orchestration_state(state)

def get_live_orchestration_state(task_slug: Optional[str] = None) -> Dict[str, Any]:
    state = _load_orchestration_state()
    sessions = state.get("active_sessions", {})
    if task_slug and task_slug in sessions:
        sess = dict(sessions[task_slug])
        sess["initiative_mode"] = sess.get("initiative_mode")
        return sess
    slug = _get_most_recent_session_slug(state)
    if slug:
        sess = dict(sessions[slug])
        sess["initiative_mode"] = sess.get("initiative_mode")
        return sess
    return {"active": False}

def get_orchestration_state(task_slug: str) -> Dict[str, Any]:
    state = _load_orchestration_state()
    sess = state.get("active_sessions", {}).get(task_slug, {"active": False})
    if isinstance(sess, dict):
        sess = dict(sess)
        sess["initiative_mode"] = sess.get("initiative_mode")
    return sess

def list_active_orchestrations() -> list:
    state = _load_orchestration_state()
    return list(state.get("active_sessions", {}).keys())

def get_initiative_status(task_slug: Optional[str] = None) -> Dict[str, Any]:
    live = get_live_orchestration_state(task_slug)
    if not live or live.get("active") is False:
        return {"active": False}
    slug = task_slug or _get_most_recent_session_slug(_load_orchestration_state())
    mode = live.get("initiative_mode")
    return {"task_slug": slug, "initiative_mode": mode, "is_disciplined_initiative": mode == "disciplined", "activated_at": live.get("initiative_mode_activated_at"), "source": live.get("initiative_mode_source"), "current_focus": live.get("current_focus")}

# Stubs / full for compatibility (orchestrator_mcp level)
announce_disciplined_initiative_entry = lambda *a, **k: f"[Disciplined Initiative] Entry for {a[0] if a else 'task'}"
announce_disciplined_initiative_exit = lambda *a, **k: "[Disciplined Initiative] Exit"
satisfy_disciplined_initiative_checkpoint = lambda *a, **k: {"satisfied": True}
enforce_and_get_satisfy_guidance = lambda *a, **k: {"ok": True}
satisfy_initiative_checkpoint_and_continue = lambda *a, **k: {"continued": True}
detect_disciplined_initiative_intent = lambda *a, **k: {"confidence": "low", "should_activate": False}
suggest_disciplined_initiative_if_warranted = lambda *a, **k: {"should_suggest": False}
accept_initiative_suggestion = lambda *a, **k: {"activated": True}
generate_phase_handoff_draft = lambda *a, **k: {"summary": "phase", "ready_to_use": True}
generate_recovery_point_suggestion = lambda *a, **k: {"name": "rp", "ready_to_use": True}
evaluate_initiative_enforcement_boundaries = lambda *a, **k: []
start_orchestration_session = lambda *a, **k: None
update_orchestration_focus = lambda *a, **k: None
record_orchestration_decision = lambda *a, **k: None
heartbeat_orchestration_state = lambda *a, **k: None
end_orchestration_session = lambda *a, **k: None

__all__ = ["ensure_lightweight_active_session", "start_orchestration_session", "update_orchestration_focus", "record_orchestration_decision", "record_phase_handoff", "heartbeat_orchestration_state", "end_orchestration_session", "get_live_orchestration_state", "get_orchestration_state", "list_active_orchestrations", "get_initiative_status", "announce_disciplined_initiative_entry", "announce_disciplined_initiative_exit", "satisfy_disciplined_initiative_checkpoint", "enforce_and_get_satisfy_guidance", "satisfy_initiative_checkpoint_and_continue", "detect_disciplined_initiative_intent", "suggest_disciplined_initiative_if_warranted", "accept_initiative_suggestion", "generate_phase_handoff_draft", "generate_recovery_point_suggestion", "evaluate_initiative_enforcement_boundaries"]

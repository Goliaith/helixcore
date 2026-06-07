#!/usr/bin/env python3
"""
Live Orchestration State helpers (core session mgmt, handoffs, getters) + Initiative v1 support.
Extracted from the monolithic orchestrator_mcp for maintainability (recommended split).
All previous public names are re-exported by the package __init__.py for 100% backward compatibility.
Cross calls (persist_decision, record_discipline_event, emit_span, etc.) use runtime lookup to the main facade.
"""

from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Minimal path setup (keeps submodule independent)
HOME = Path.home()
try:
    import os
    HOME = Path(os.environ.get("USERPROFILE") or os.environ.get("HOME") or Path.home())
except Exception:
    pass
STATE_DIR = HOME / ".grok" / "state"
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
# New format (v2):
# {
#   "version": 2,
#   "active_sessions": {
#     "<task_slug>": {
#       "safety_id": "...",
#       "started_at": "...",
#       "last_heartbeat": "...",
#       "current_focus": "...",
#       "key_decisions": [...],
#       "phase_handoffs": [...]
#     }
#   }
# }

def _load_orchestration_state() -> dict:
    if not CURRENT_ORCHESTRATION_FILE.exists():
        return {"version": 2, "active_sessions": {}}
    try:
        data = json.loads(CURRENT_ORCHESTRATION_FILE.read_text(encoding="utf-8"))
        # Migration from old single-session format
        if "active_sessions" not in data and data.get("active"):
            slug = data.get("task_slug")
            if slug:
                data = {
                    "version": 2,
                    "active_sessions": {
                        slug: {
                            "safety_id": data.get("safety_id"),
                            "started_at": data.get("started_at"),
                            "last_heartbeat": data.get("last_heartbeat"),
                            "current_focus": data.get("current_focus"),
                            "key_decisions": data.get("key_decisions", []),
                            "phase_handoffs": data.get("phase_handoffs", [])
                        }
                    }
                }
            else:
                data = {"version": 2, "active_sessions": {}}
        if "version" not in data:
            data["version"] = 2
        if "active_sessions" not in data:
            data["active_sessions"] = {}

        # v1: Ensure initiative_mode field exists on all sessions (backward compat)
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
    """Return the task_slug with the most recent heartbeat, or None."""
    sessions = state.get("active_sessions", {})
    if not sessions:
        return None
    return max(sessions.keys(), key=lambda s: sessions[s].get("last_heartbeat", ""))


def ensure_lightweight_active_session(task_slug: str, initial_focus: str = "") -> None:
    """
    Phase 3 usability fix: Ensure a task_slug has a lightweight entry in active_sessions.
    This allows high-level primitives (begin_focused_work, create_recovery_point, etc.)
    and the dogfooding generator to work without requiring a full prior call to
    start_orchestration_session or the heavy safety registration path.
    """
    if not task_slug:
        return
    state = _load_orchestration_state()
    if task_slug not in state.get("active_sessions", {}):
        now = datetime.now(timezone.utc).isoformat()
        state.setdefault("active_sessions", {})[task_slug] = {
            "safety_id": f"lightweight-{task_slug[:20]}",
            "started_at": now,
            "last_heartbeat": now,
            "current_focus": initial_focus or "Ad-hoc / dogfooding session (lightweight)",
            "key_decisions": [],
            "phase_handoffs": [],
            "checkpoints": [],
            "automation_results": {},
            "related_sessions": [],   # Proposal 3: Lightweight initiative federation
            "_lightweight": True,   # Marker for future introspection
            "initiative_mode": None,  # Disciplined Initiative Mode v1
        }
        _save_orchestration_state(state)


def start_orchestration_session(task_slug: str, safety_id: str, initial_focus: str = "") -> None:
    """Start (or resume) a long-running orchestration session. Supports multiple concurrent sessions."""
    state = _load_orchestration_state()
    now = datetime.now(timezone.utc).isoformat()

    state.setdefault("active_sessions", {})[task_slug] = {
        "safety_id": safety_id,
        "started_at": now,
        "last_heartbeat": now,
        "current_focus": initial_focus,
        "key_decisions": [],
        "phase_handoffs": [],
        "checkpoints": [],   # Gap #2 - durable checkpoints
        "automation_results": {},
        "initiative_mode": None,  # Disciplined Initiative Mode v1
    }
    _save_orchestration_state(state)

    # More Automation: Auto-run lightweight validation if enabled
    try:
        _record_discipline_event("start_orchestration_session", {"task_slug": task_slug}, task_slug=task_slug)

        auto_cfg = _get_automation_config()
        if auto_cfg.get("auto_pre_task_validation"):
            print(f"[Automation] Running lightweight validation harness for new session '{task_slug}'...")
            val_result = _run_lightweight_validation_harness()
            sess = state["active_sessions"][task_slug]
            sess["automation_results"]["last_pre_task_validation"] = val_result
            _save_orchestration_state(state)
            print(f"[Automation] Validation complete. Success={val_result.get('success')}")
    except Exception as e:
        # Never let automation break session creation
        try:
            _record_discipline_event("automation_error", {"error": str(e)[:100]}, task_slug=task_slug)
        except Exception:
            pass

def update_orchestration_focus(new_focus: str, task_slug: Optional[str] = None) -> None:
    """Update focus for a specific (or the most recent) orchestration session."""
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
    """Log a decision for a specific (or most recent) session."""
    _record_discipline_event("record_orchestration_decision", {"decision": decision[:80]}, task_slug=task_slug)

    state = _load_orchestration_state()
    slug = task_slug or _get_most_recent_session_slug(state)
    if slug and slug in state.get("active_sessions", {}):
        sess = state["active_sessions"][slug]
        sess.setdefault("key_decisions", []).append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "decision": decision
        })
        sess["last_heartbeat"] = datetime.now(timezone.utc).isoformat()
        sess["key_decisions"] = sess["key_decisions"][-10:]
        _save_orchestration_state(state)

def record_phase_handoff(summary: str, next_focus: str = "", task_slug: Optional[str] = None) -> None:
    """Record phase handoff for a specific (or most recent) session."""
    _record_discipline_event("record_phase_handoff", {"summary": summary[:80]}, task_slug=task_slug)

    # Tracing (Gap #1)
    span_id = _emit_span("phase_handoff", {"summary": summary[:100]}, task_slug=task_slug)

    state = _load_orchestration_state()
    slug = task_slug or _get_most_recent_session_slug(state)
    if not slug or slug not in state.get("active_sessions", {}):
        _complete_span(span_id, {"skipped": "no_active_session"})
        return

    sess = state["active_sessions"][slug]
    timestamp = datetime.now(timezone.utc).isoformat()

    handoff_entry = {
        "timestamp": timestamp,
        "summary": summary,
        "focus_at_handoff": sess.get("current_focus", "")
    }

    sess.setdefault("phase_handoffs", []).append(handoff_entry)
    sess["phase_handoffs"] = sess["phase_handoffs"][-5:]

    if next_focus:
        sess["current_focus"] = next_focus

    sess["last_heartbeat"] = timestamp
    _save_orchestration_state(state)

    # Gentle post-handoff recommendation (reinforces coordination & memory pillars)
    try:
        _record_discipline_event("phase_handoff_recorded", {"summary": summary[:60]}, task_slug=slug)
    except Exception:
        pass

    # Auto-persist (uses the provided or looked-up slug)
    try:
        _persist_decision(
            task_slug=slug,
            decision=f"[PHASE HANDOFF] {summary}",
            category="phases",
            to_cognee=True,
            to_serena=False
        )
    except Exception:
        pass

    # Deeper Synaptogenesis wiring: after handoff (which represents a transition/connection between phases),
    # form/reinforce synapses to capture the evolution of work. This wires the "narrative" of the project
    # into the explicit memory graph automatically.
    try:
        om = _om()
        if om and hasattr(om, 'perform_synaptogenesis'):
            om.perform_synaptogenesis(slug, max_new=1)
    except Exception:
        pass

    _complete_span(span_id, {"recorded": True})

def heartbeat_orchestration_state(task_slug: Optional[str] = None) -> None:
    """Heartbeat a specific (or most recent) session."""
    state = _load_orchestration_state()
    slug = task_slug or _get_most_recent_session_slug(state)
    if slug and slug in state.get("active_sessions", {}):
        state["active_sessions"][slug]["last_heartbeat"] = datetime.now(timezone.utc).isoformat()
        _save_orchestration_state(state)

def end_orchestration_session(task_slug: Optional[str] = None, reason: str = "completed") -> None:
    """End a specific (or most recent) session."""
    state = _load_orchestration_state()
    slug = task_slug or _get_most_recent_session_slug(state)
    if slug and slug in state.get("active_sessions", {}):
        sess = state["active_sessions"][slug]
        sess["ended_at"] = datetime.now(timezone.utc).isoformat()
        sess["end_reason"] = reason
        # We keep the session record for history but it is no longer "active"
        # For simplicity we remove it so it doesn't appear in active lists.
        del state["active_sessions"][slug]
        _save_orchestration_state(state)


# ------------------------------------------------------------------
# Agent Health Guardian — Structured Pulse (for checkpoints + Safety skill)
# ------------------------------------------------------------------

def get_live_orchestration_state(task_slug: Optional[str] = None) -> Dict[str, Any]:
    """Return state for a specific session or the most recent active one.
    Now enriched with initiative_mode visibility (v1)."""
    state = _load_orchestration_state()
    sessions = state.get("active_sessions", {})
    if task_slug and task_slug in sessions:
        sess = dict(sessions[task_slug])  # copy
        sess["initiative_mode"] = sess.get("initiative_mode")
        return sess
    slug = _get_most_recent_session_slug(state)
    if slug:
        sess = dict(sessions[slug])
        sess["initiative_mode"] = sess.get("initiative_mode")
        return sess
    return {"active": False}


def get_orchestration_state(task_slug: str) -> Dict[str, Any]:
    """Explicit getter for one session's state. Includes initiative_mode (v1)."""
    state = _load_orchestration_state()
    sess = state.get("active_sessions", {}).get(task_slug, {"active": False})
    if isinstance(sess, dict):
        sess = dict(sess)
        sess["initiative_mode"] = sess.get("initiative_mode")
    return sess

def list_active_orchestrations() -> list:
    """Return list of currently active task slugs."""
    state = _load_orchestration_state()
    return list(state.get("active_sessions", {}).keys())

def get_initiative_status(task_slug: Optional[str] = None) -> Dict[str, Any]:
    """
    Clean, dedicated visibility helper for Disciplined Initiative Mode (v1).
    Returns status for a specific slug or the most recent active one.
    """
    live = get_live_orchestration_state(task_slug)
    if not live or live.get("active") is False:
        return {"active": False}
    slug = task_slug or _get_most_recent_session_slug(_load_orchestration_state())
    mode = live.get("initiative_mode")
    return {
        "task_slug": slug,
        "initiative_mode": mode,
        "is_disciplined_initiative": mode == "disciplined",
        "activated_at": live.get("initiative_mode_activated_at"),
        "source": live.get("initiative_mode_source"),
        "current_focus": live.get("current_focus"),
    }

def announce_disciplined_initiative_entry(task_slug: str, reason: str = "") -> str:
    """High-signal entry announcement for Disciplined Initiative Mode (required by spec)."""
    msg = f"**Disciplined Initiative Mode activated** for {task_slug}."
    if reason:
        msg += f" Reason: {reason}"
    msg += "\nEnforcement boundaries and strengthened loop defaults are now active. You can opt out at any time with `set_initiative_mode(slug, None)`."
    try:
        _persist_decision(task_slug, decision=msg, category="initiative_mode_entry")
    except Exception:
        pass
    return msg

def announce_disciplined_initiative_exit(task_slug: str) -> str:
    """High-signal exit announcement."""
    msg = f"**Disciplined Initiative Mode deactivated** for {task_slug}. Behavior returns to standard Task Orchestration."
    try:
        _persist_decision(task_slug, decision=msg, category="initiative_mode_exit")
    except Exception:
        pass
    return msg

def satisfy_disciplined_initiative_checkpoint(action: str, task_slug: str, note: str = "") -> dict:
    """Convenience wrapper around satisfy_discipline_checkpoint for initiative mode use."""
    from ..discipline_enforcement import satisfy_discipline_checkpoint
    return satisfy_discipline_checkpoint(action, task_slug, note=note)

# ------------------------------------------------------------------
# Smooth Enforce → Satisfy Experiences for Disciplined Initiative Mode
# ------------------------------------------------------------------

def enforce_and_get_satisfy_guidance(boundary_type: str, task_slug: str, context: Optional[dict] = None) -> dict:
    """
    One-call helper for initiative mode: evaluates the boundary and returns both
    the enforcement result (if any) and ready-to-use satisfy guidance.

    This is the smooth "enforce → satisfy → continue" experience.
    """
    results = evaluate_initiative_enforcement_boundaries(task_slug, context=context)

    relevant = [r for r in results if r.get("boundary") == boundary_type]

    if not relevant:
        return {
            "boundary": boundary_type,
            "enforcement_triggered": False,
            "status": "no_action_needed",
            "message": "Boundary not triggered for current context."
        }

    result = relevant[0]

    if not result.get("enforcement_triggered"):
        return {
            "boundary": boundary_type,
            "enforcement_triggered": False,
            "status": "compliant",
            "message": result.get("recommendation", "Checkpoint satisfied.")
        }

    # Enforcement triggered — provide smooth satisfy path
    satisfy_call = f'satisfy_disciplined_initiative_checkpoint("{boundary_type}", "{task_slug}", note="...")'

    return {
        "boundary": boundary_type,
        "enforcement_triggered": True,
        "nudge": result.get("nudge"),
        "recommendation": result.get("recommendation"),
        "satisfy_guidance": {
            "action": boundary_type,
            "task_slug": task_slug,
            "recommended_call": satisfy_call,
            "what_to_do": "Record the required todo_write + phase handoff (or equivalent discipline action), then call the satisfy function above."
        }
    }

def satisfy_initiative_checkpoint_and_continue(boundary_type: str, task_slug: str, note: str = "") -> dict:
    """
    Satisfy a checkpoint and immediately record a follow-up decision that the
    initiative is continuing with the required discipline in place.
    This creates a clean "enforce → satisfy → continue" narrative in the audit trail.
    """
    satisfy_result = satisfy_disciplined_initiative_checkpoint(boundary_type, task_slug, note=note)

    _persist_decision(
        task_slug=task_slug,
        decision=f"Discipline checkpoint satisfied for {boundary_type}. Initiative continues with required structure in place.",
        category="initiative_mode"
    )

    return {
        "satisfied": satisfy_result,
        "initiative_continues": True,
        "message": f"Checkpoint for {boundary_type} satisfied. Mode remains active with clean audit trail."
    }


# ------------------------------------------------------------------
# Activation / Detection Layer (New Phase)
# ------------------------------------------------------------------

def detect_disciplined_initiative_intent(text: str, task_slug: Optional[str] = None) -> dict:
    """
    Refined detection for Disciplined Initiative Mode (v1) — Round 2 improvements.

    Expanded high-signal phrases + richer session maturity signals (structure debt,
    momentum combos, text richness). Returns enriched session_maturity for UX.
    v1 policy strictly preserved: strongly suggest on high/medium; never auto-activate.
    """
    if not text:
        return {"confidence": "none", "should_activate": False, "trigger_type": "none", "recommended_action": ""}

    t = text.lower().strip()
    text_len = len(text)

    # Explicit / Guaranteed triggers
    explicit_triggers = [
        "use disciplined initiative mode",
        "switch to disciplined initiative mode",
        "treat this as a disciplined initiative",
        "disciplined initiative mode",
    ]
    for trig in explicit_triggers:
        if trig in t:
            return {
                "confidence": "high",
                "should_activate": True,
                "trigger_type": "explicit",
                "recommended_action": f"Activate immediately: set_initiative_mode('{task_slug or 'slug'}', 'disciplined')"
            }

    # Strong natural language triggers (expanded)
    strong_triggers = [
        "start a new disciplined initiative",
        "run this as a fully disciplined",
        "run this as a serious project",
        "begin a high-discipline project",
        "treat this as a proper initiative with strong discipline",
        "this is a strategic initiative",
        "treat this as a foundational effort",
    ]
    for trig in strong_triggers:
        if trig in t:
            return {
                "confidence": "high",
                "should_activate": True,
                "trigger_type": "strong_natural_language",
                "recommended_action": "Strongly recommend activation with high-signal entry."
            }

    # === Medium triggers with stronger session awareness (Round 2) ===
    medium_keywords = [
        "initiative", "major project", "overhaul", "redesign", "architecture",
        "system launch", "build the", "compliance overhaul", "architecture redesign",
        "foundational", "strategic", "multi-week", "cross-session", "end-to-end",
        "production-critical", "large-scale", "core infrastructure", "platform-level",
        "significant refactor", "major migration", "serious multi-phase"
    ]
    medium_score = sum(1 for kw in medium_keywords if kw in t)

    # Additional high-value phrase signals (counted toward medium)
    initiative_phrases = [
        "this will span", "several sessions", "multi-session work", "long-running effort",
        "core platform change", "production readiness"
    ]
    phrase_score = sum(1 for p in initiative_phrases if p in t)
    medium_score += phrase_score

    session_context = {
        "age_hours": 0,
        "handoff_count": 0,
        "decision_count": 0,
        "recent_activity_score": 0,
        "structure_debt": False,
        "high_momentum": False,
        "text_richness": False
    }
    session_boost = 0

    if task_slug:
        try:
            live = get_live_orchestration_state(task_slug) or {}
            if live.get("started_at"):
                session_context["age_hours"] = (datetime.now(timezone.utc) - datetime.fromisoformat(live["started_at"])).total_seconds() / 3600

            session_context["handoff_count"] = len(live.get("phase_handoffs", []))
            session_context["decision_count"] = len(live.get("key_decisions", []))

            recent_activity = min(5, session_context["decision_count"] + session_context["handoff_count"])
            session_context["recent_activity_score"] = recent_activity

            # Existing maturity boosts
            if session_context["age_hours"] > 3 and session_context["handoff_count"] >= 2:
                session_boost += 1
            if session_context["decision_count"] >= 6 and session_context["handoff_count"] >= 2:
                session_boost += 1
            if session_context["age_hours"] > 8 and session_context["recent_activity_score"] >= 4:
                session_boost += 1

            # === Round 2 new signals ===
            # Structure debt: many decisions, relatively few handoffs (accumulating work without structure)
            dec = session_context["decision_count"]
            hand = session_context["handoff_count"]
            if dec >= 5 and hand <= max(1, int(dec / 2.5)):
                session_context["structure_debt"] = True
                session_boost += 2  # meaningful signal for "this work is getting complex"

            # High momentum + maturity combo (activity accelerating in an established session)
            if session_context["age_hours"] >= 2.0 and recent_activity >= 4 and dec >= 4:
                session_context["high_momentum"] = True
                session_boost += 1

            # Text richness: long, detailed focus description often signals serious planning
            if text_len > 110 and any(w in t for w in ["implement", "design", "architecture", "refactor", "overhaul", "migrate", "launch"]):
                session_context["text_richness"] = True
                session_boost += 1

        except Exception:
            pass

    total_medium_score = medium_score + session_boost

    # More generous threshold when session shows multiple maturity signals
    medium_threshold = 2
    maturity_signals = sum([
        1 if session_context.get("age_hours", 0) > 4 else 0,
        1 if session_context.get("decision_count", 0) >= 5 else 0,
        1 if session_context.get("structure_debt") else 0,
        1 if session_context.get("high_momentum") else 0
    ])
    if maturity_signals >= 2 or session_context.get("age_hours", 0) > 6 or session_context.get("decision_count", 0) >= 8:
        medium_threshold = 1  # very mature / high-debt sessions surface on weaker phrase signals

    if total_medium_score >= medium_threshold or (medium_score >= 1 and session_boost >= 1):
        # Build richer rationale using the new signals
        why_parts = []
        if session_context.get("structure_debt"):
            why_parts.append("structure debt detected (decisions accumulating without enough handoffs)")
        if session_context.get("high_momentum"):
            why_parts.append("high recent momentum in a mature session")
        if session_context.get("text_richness"):
            why_parts.append("detailed multi-aspect focus description")
        if session_context.get("age_hours", 0) > 4:
            why_parts.append(f"{session_context['age_hours']:.1f}h old session")
        why = " + ".join(why_parts) if why_parts else "substantial scope and session maturity"

        return {
            "confidence": "medium",
            "should_activate": False,
            "trigger_type": "medium_strong",
            "recommended_action": f"This looks like substantial work ({why}). Consider activating Disciplined Initiative Mode for stronger structure, enforcement boundaries, and automated support.",
            "session_context": session_context,
            "session_maturity": {
                "age_hours": round(session_context["age_hours"], 1),
                "decisions": session_context["decision_count"],
                "handoffs": session_context["handoff_count"],
                "structure_debt": session_context["structure_debt"],
                "high_momentum": session_context["high_momentum"]
            }
        }

    # Ongoing effort references (strengthened with Round 2 signals)
    if any(phrase in t for phrase in ["continue the", "what's the current state of the", "status of the", "progress on the"]):
        if any(kw in t for kw in ["architecture", "overhaul", "redesign", "compliance", "major", "foundational", "platform"]):
            if session_context.get("age_hours", 0) > 3 or session_context.get("decision_count", 0) >= 4 or session_context.get("structure_debt"):
                return {
                    "confidence": "medium",
                    "should_activate": False,
                    "trigger_type": "ongoing_effort",
                    "recommended_action": "This ongoing substantial work may benefit from Disciplined Initiative Mode.",
                    "session_context": session_context,
                    "session_maturity": {
                        "age_hours": round(session_context["age_hours"], 1),
                        "decisions": session_context["decision_count"],
                        "handoffs": session_context.get("handoffs", 0),
                        "structure_debt": session_context.get("structure_debt", False)
                    }
                }

    return {
        "confidence": "low",
        "should_activate": False,
        "trigger_type": "none",
        "recommended_action": ""
    }


def suggest_disciplined_initiative_if_warranted(task_slug: str, current_focus: str = "") -> dict:
    """
    Convenience helper for callers who want to check detection before or during work.
    Returns a rich suggestion object (including proposed announcement and easy-accept call)
    when the detector recommends the mode.

    Round 2: If current_focus is empty/minimal, auto-pulls the most recent focus from live state.
    """
    focus = current_focus or ""
    if not focus or len(focus.strip()) < 8:
        try:
            live = get_live_orchestration_state(task_slug) or {}
            focus = live.get("current_focus", "") or focus
        except Exception:
            pass

    detection = detect_disciplined_initiative_intent(focus, task_slug)

    result = {
        "detection": detection,
        "should_suggest": detection.get("confidence") in ("high", "medium"),
        "suggested_initiative_activation": None
    }

    if result["should_suggest"]:
        proposed_announcement = (
            f"This looks like significant, multi-session work ({detection.get('trigger_type')}). "
            "I'm recommending **Disciplined Initiative Mode** for stronger structure and enforcement."
        )

        # Include maturity note when available for explainable UX
        maturity_note = ""
        sm = detection.get("session_maturity") or detection.get("session_context")
        if isinstance(sm, dict) and sm.get("decisions"):
            maturity_note = f" (Session: {sm.get('age_hours', 0)}h, {sm.get('decisions')} decisions, {sm.get('handoffs', 0)} handoffs)"

        result["suggested_initiative_activation"] = {
            "confidence": detection.get("confidence"),
            "trigger_type": detection.get("trigger_type"),
            "recommended_call": f"set_initiative_mode('{task_slug}', 'disciplined')",
            "proposed_announcement": proposed_announcement + maturity_note,
            "easy_accept_call": f"accept_initiative_suggestion('{task_slug}', detection)",
            "rationale": detection.get("recommended_action", ""),
            "session_maturity": detection.get("session_maturity") or detection.get("session_context"),
            "why_this_qualifies": detection.get("recommended_action", "")
        }

    return result

def accept_initiative_suggestion(task_slug: str, detection: dict = None, reason: str = "") -> dict:
    """
    One-call helper to accept a suggested activation.
    Activates the mode + immediately fires the high-signal entry announcement.

    Post-organic dogfood tweak: Added verification + retry to ensure state persistence
    (the nice UX path was observed to sometimes not persist on brand-new lightweight
    sessions during real usage).
    """
    set_initiative_mode(task_slug, "disciplined", source="user_accepted_suggestion")

    # Small robustness fix from organic dogfood: verify the mode actually stuck
    # and re-apply if needed (lightweight session creation edge case).
    try:
        live = get_live_orchestration_state(task_slug) or {}
        if live.get("initiative_mode") != "disciplined":
            set_initiative_mode(task_slug, "disciplined", source="user_accepted_suggestion_retry")
    except Exception:
        pass

    announcement = announce_disciplined_initiative_entry(
        task_slug,
        reason or (detection.get("rationale") if detection else "")
    )

    return {
        "activated": True,
        "announcement": announcement,
        "message": "Disciplined Initiative Mode activated via suggestion acceptance."
    }


# ------------------------------------------------------------------
# Deeper Automation Helpers for Disciplined Initiative Mode (v1+)
# ------------------------------------------------------------------

def generate_phase_handoff_draft(task_slug: str, current_focus: str = "", recent_items: Optional[list] = None) -> dict:
    """
    Generate a ready-to-use, high-quality draft for record_phase_handoff when in Disciplined Initiative Mode.
    This is the deeper automation version — it automatically pulls rich context from live state when possible.
    """
    now = datetime.now(timezone.utc).isoformat()[:16]

    # Auto-pull richer context from live state if not explicitly provided
    if not recent_items or not current_focus:
        try:
            live = get_live_orchestration_state(task_slug)
            if not recent_items:
                recent_items = [d.get("decision", "") for d in live.get("key_decisions", [])[-5:]]
            if not current_focus:
                current_focus = live.get("current_focus", "")
            # Also pull last handoff for context
            if live.get("phase_handoffs"):
                last_handoff = live["phase_handoffs"][-1].get("summary", "")
                if last_handoff and last_handoff not in str(recent_items):
                    recent_items = [last_handoff] + recent_items
        except Exception:
            recent_items = recent_items or []

    items = recent_items or []
    # Deeper post-v1 polish on draft quality (building on the initial noise filter from organic dogfood):
    # - Stronger filtering of governance/recommendation noise
    # - Prefer recent handoff summaries over raw decisions when available (cleaner, higher signal)
    # - Cap and clean text more aggressively for readability
    noise_markers = ["GOVERNANCE", "Discipline policy nudge", "Pre-task validation", "DISCIPLINED INITIATIVE ENFORCEMENT", "recommendations", "nudge"]
    filtered_items = [i for i in items if i and not any(m.lower() in str(i).lower() for m in noise_markers)]

    # If we have live handoffs, pull their summaries preferentially for cleaner context
    try:
        live = get_live_orchestration_state(task_slug) or {}
        recent_handoffs = live.get("phase_handoffs", [])[-2:]
        handoff_summaries = [h.get("summary", "") for h in recent_handoffs if h.get("summary")]
        if handoff_summaries:
            filtered_items = handoff_summaries + filtered_items
    except Exception:
        pass

    # Clean and truncate aggressively
    cleaned = []
    for item in filtered_items:
        text = str(item).strip()
        if len(text) > 120:
            text = text[:117] + "..."
        if text:
            cleaned.append(text)

    recent_summary = ""
    if cleaned:
        recent_summary = "Key recent work: " + " | ".join(cleaned[:3])
    elif items:
        recent_summary = "Key recent work: " + " | ".join([str(i)[:60] for i in items[:2]])

    focus_part = f"Focus: {current_focus}" if current_focus else "Continued disciplined progress on the initiative"

    draft_summary = f"[{now}] {focus_part}. {recent_summary}".strip()

    # Smarter next_focus generation
    if current_focus:
        suggested_next = f"Continue work on: {current_focus}"
    else:
        suggested_next = "Continue with next priority item in the initiative."

    return {
        "summary": draft_summary,
        "next_focus": suggested_next,
        "recommended_call": f'record_phase_handoff(summary="{draft_summary}", next_focus="{suggested_next}", task_slug="{task_slug}")',
        "ready_to_use": True,
        "generated_at": now
    }

def generate_recovery_point_suggestion(task_slug: str, after_what: str = "recent progress") -> dict:
    """ (stub for completeness; full in live source) """
    return {"name": f"rp-after-{after_what}", "task_slug": task_slug, "ready_to_use": True}

# Note: Additional functions (suggest_pre_task_validation, set_automation_preference, etc.) are provided via the main shim or local packaging for full live core parity.

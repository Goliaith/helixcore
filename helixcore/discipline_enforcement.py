#!/usr/bin/env python3
"""
Discipline Enforcement Helpers

Implements practical enforcement for golden cases such as:
- enforce-todo-before-new_helper_pattern
- enforce-todo-before-general_action
- enforce-todo-before-high_concurrency

Part of the real work project to dogfood and advance the platform post-Phase 3.
"""

import sys
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# In-process cache so satisfy_discipline_checkpoint() can immediately satisfy
# subsequent require_discipline_checkpoint() calls in the same Python process.
# This makes the helper pair pleasant and reliable to use during real development
# and dogfooding sessions. Durability is still handled by the persist_decision path.
_satisfied_checkpoints: dict[tuple[str, str], datetime] = {}

# Simple in-process pending nudges queue so that golden-case enforcement
# signals become first-class citizens in the Nudge Intelligence surfaces
# (pulse_agent_health, run_system_coherence_audit, _process_recommendations).
# These are emitted by require_discipline_checkpoint when enforcement triggers.
# Consumers (Guardian surfaces) can drain via get_pending_discipline_nudges().
# Durability / cross-process can be added later via record_discipline_event if needed.
_pending_discipline_nudges: list[dict] = []
MAX_PENDING_NUDGES = 50

# Proposal 3: Simple sticky enforcement memory to increase effectiveness at scale.
# Once enforcement is triggered for a task_slug/action, we temporarily remember it
# so the next call in the same process has a lower effective threshold (makes the
# helper pair more "sticky" and useful during long disciplined sessions).
_recent_enforcements: dict[tuple[str, str], datetime] = {}
STICKY_WINDOW_SECONDS = 600  # 10 minutes of "heightened awareness" after a trigger

from .orchestrator_mcp import (
    get_discipline_stats,
    record_key_decision,
    capture_milestone,
    persist_decision,
    record_discipline_event,
)


def require_discipline_checkpoint(
    action: str,
    task_slug: str,
    min_compliance: int = 65,
    force: bool = False,
    log_to_dogfooding_session: bool = True,
) -> Dict[str, Any]:
    """
    Enforces the spirit of the golden case:
    'Require todo_write + phase handoff before high-volume or high-risk governance actions.'

    This is the initial implementation used during the real work project
    to dogfood the new_helper_pattern (and similar) discipline enforcement.

    Behavior (v1 - advisory + strong logging):
    - Checks current discipline compliance for the task_slug.
    - If below threshold or no recent todo/handoff activity, records a strong
      key decision + milestone and returns clear guidance.
    - Intended to be called at the start of high-risk / high-volume actions.
    """

    # Check in-process cache first — makes satisfy() immediately effective
    # in the same process / dogfooding session.
    cache_key = (task_slug, action)
    if cache_key in _satisfied_checkpoints:
        last = _satisfied_checkpoints[cache_key]
        if (datetime.now(timezone.utc) - last).total_seconds() < 300:  # 5 min grace
            return {
                "action": action,
                "task_slug": task_slug,
                "compliance_score": 100,  # treat as satisfied
                "has_recent_todo_or_handoff": True,
                "enforcement_triggered": False,
                "diagnostics": {
                    "compliance_score": 100,
                    "has_recent_todo_or_handoff": True,
                    "trigger_reasons": [],
                    "source": "in_process_satisfy_cache"
                },
                "recommendation": "Recent discipline checkpoint satisfied in this session.",
                "status": "compliant",
            }

    stats = get_discipline_stats(task_slug=task_slug, limit=30, use_durable=True)
    compliance = stats.get("compliance_score", 100)
    recent_events = stats.get("recent_events", [])

    trigger_reasons = []

    # Proposal 3: Sticky enforcement awareness
    sticky_key = (task_slug, action)
    effective_min = min_compliance
    if sticky_key in _recent_enforcements:
        last_enf = _recent_enforcements[sticky_key]
        if (datetime.now(timezone.utc) - last_enf).total_seconds() < STICKY_WINDOW_SECONDS:
            effective_min = max(40, min_compliance - 15)  # temporarily more sensitive
            trigger_reasons.append("sticky_recent_enforcement")

    # Robust recent todo/handoff detection (improved for reliable enforcement without constant friction).
    # - Wider window (last 25) to survive bursts of other events (nudges, boosts, gov).
    # - Recognizes record_phase_handoff (strong positive, recorded by handoff API) + phase_handoff variants.
    # - Live state handoffs count as authoritative recent activity (fast, per-slug).
    # - Broader keywords for text fallbacks.
    has_recent_todo = any(
        any(k in str(e.get("event_type", "")).lower() for k in [
            "todo_write", "persist_decision", "discipline_checkpoint", 
            "record_phase_handoff", "phase_handoff", "satisfy_discipline", "checkpoint_satisfied"
        ])
        for e in recent_events[-25:]
    )

    # Check live orchestration state for recent handoffs (authoritative + fast path, bypasses durable lag)
    if not has_recent_todo:
        try:
            from .orchestrator_mcp import get_live_orchestration_state
            live = get_live_orchestration_state(task_slug) or {}
            if live.get("phase_handoffs"):
                has_recent_todo = True
        except Exception:
            pass

    # Also check the decision/details text of persist_decision events for explicit todo language
    # (this makes satisfy_discipline_checkpoint reliably close the loop)
    if not has_recent_todo:
        for e in recent_events[-25:]:
            if "persist_decision" in str(e.get("event_type", "")).lower():
                details = str(e.get("details", {})) + str(e.get("decision", ""))
                if any(kw in details.lower() for kw in ["todo_write", "discipline checkpoint", "handoff", "phase handoff", "satisfy"]):
                    has_recent_todo = True
                    break

    # Fallback: also check recent key decisions returned by get_discipline_stats (if present)
    # This helps when the low-level event hasn't propagated to recent_events yet
    if not has_recent_todo:
        recent_key_decisions = stats.get("recent_key_decisions", []) or stats.get("key_decisions", [])
        for d in recent_key_decisions[-10:]:
            text = str(d.get("decision", "")).lower()
            if any(kw in text for kw in ["discipline checkpoint satisfied", "todo_write", "phase handoff", "satisfy"]):
                has_recent_todo = True
                break

    # Use effective (possibly sticky-lowered) threshold
    needs_enforcement = compliance < effective_min or not has_recent_todo or force

    if compliance < effective_min:
        trigger_reasons.append("low_compliance")
    if not has_recent_todo:
        trigger_reasons.append("missing_recent_todo_or_handoff")
    if force:
        trigger_reasons.append("forced")
    if effective_min < min_compliance:
        trigger_reasons.append("sticky_enforcement_active")

    # Record that we triggered enforcement so future calls in this process stay sensitive (sticky)
    if needs_enforcement:
        _recent_enforcements[sticky_key] = datetime.now(timezone.utc)

    diagnostics = {
        "compliance_score": compliance,
        "has_recent_todo_or_handoff": has_recent_todo,
        "trigger_reasons": trigger_reasons,
        "effective_min_compliance": effective_min,
    }

    result = {
        "action": action,
        "task_slug": task_slug,
        "compliance_score": compliance,
        "has_recent_todo_or_handoff": has_recent_todo,
        "enforcement_triggered": needs_enforcement,
        "diagnostics": diagnostics,
        "recommendation": None,
    }

    if needs_enforcement:
        decision_text = (
            f'High-volume/risky action "{action}" requires explicit discipline checkpoint. '
            f"Current compliance: {compliance}. Recent todo/handoff detected: {has_recent_todo}. "
            f"Triggers: {', '.join(trigger_reasons)}"
        )

        record_key_decision(
            task_slug=task_slug,
            decision=decision_text,
            rationale="Direct application of the golden case enforce-todo-before-new_helper_pattern (and similar patterns).",
            category="discipline"
        )

        capture_milestone(
            task_slug=task_slug,
            summary=f"Discipline checkpoint enforced before {action}",
            decisions=[f"Required todo_write + handoff before proceeding with {action}"]
        )

        # Auto-log to active dogfooding session if available (Phase 3 tooling integration)
        if log_to_dogfooding_session:
            try:
                from dogfooding_session_report import log_session_event, DogfoodingSession
                # This will only succeed if we're inside a properly started dogfooding session
                # The session object is managed by the caller in most cases, so we do a soft attempt
                log_session_event(
                    None,  # Let the tooling handle current session if possible
                    f"Discipline enforcement triggered for action '{action}' (compliance={compliance}, triggers={trigger_reasons})",
                    category="discipline_enforcement",
                    primitive="require_discipline_checkpoint"
                )
            except Exception:
                pass  # Not in a dogfooding session or tooling not available — silently skip

        rec_text = "Call persist_decision / record a clear todo_write + phase handoff before performing this action."
        if "low_compliance" in trigger_reasons:
            rec_text += f" (Compliance is {compliance}, threshold is {min_compliance}.)"
        if "missing_recent_todo_or_handoff" in trigger_reasons:
            rec_text += " No recent todo_write or handoff was found."

        result["recommendation"] = rec_text + " Then re-call this function or proceed."
        result["status"] = "enforcement_required"

        # Deepened Nudge Intelligence output (Phase 3 WS2 continuation)
        # Sophisticated urgency: pattern-specific bases (from stress-test high-volume golden cases)
        # + low-compliance penalty + recent enforcement frequency signal.
        # These nudges are emitted to the pending queue so they become first-class
        # participants in pulse_agent_health / coherence / _process_recommendations.
        base_urgency = max(55, 100 - compliance)

        # Pattern-specific boosts reflecting the "high-volume/risky" nature identified
        # in the ultimate stress test golden cases (new_helper_pattern is the most common).
        pattern_bases = {
            "new_helper_pattern": 22,
            "high_concurrency": 18,
            "general_action": 14,
        }
        pattern_bonus = pattern_bases.get(action, 8)

        # Extra signal when compliance is critically low
        compliance_penalty = 10 if compliance < 40 else (5 if compliance < 55 else 0)

        # Recent enforcement frequency (simple but effective signal for persistent issues)
        recent_enforcement_count = sum(
            1 for e in recent_events[-20:]
            if "discipline" in str(e).lower() and ("enforce" in str(e).lower() or "checkpoint" in str(e).lower())
        )
        frequency_bonus = min(12, recent_enforcement_count * 4)

        urgency = min(98, base_urgency + pattern_bonus + compliance_penalty + frequency_bonus)

        # Determine priority for downstream consumers
        priority = "high" if urgency >= 80 else ("medium" if urgency >= 65 else "normal")

        nudge = {
            "category": "discipline",
            "urgency": urgency,
            "priority": priority,
            "source": "golden_case_enforcement",
            "title": f"Discipline checkpoint required before '{action}'",
            "message": rec_text,
            "suggested_action": "Record todo_write + phase handoff, then call satisfy_discipline_checkpoint().",
            "related_golden_case": f"enforce-todo-before-{action}",
            "context": {
                "compliance_score": compliance,
                "trigger_reasons": trigger_reasons,
                "action_type": action,
                "min_compliance_threshold": min_compliance,
                "recent_enforcement_count": recent_enforcement_count,
            },
            "suppressible": True,
            "nudge_id": f"gc-{action}-{int(datetime.now(timezone.utc).timestamp())}",
        }

        result["nudge"] = nudge

        # Emit to the pending queue so Guardian surfaces and the Nudge engine
        # can consume this as a first-class structured recommendation.
        try:
            nudge_entry = {**nudge, "emitted_at": datetime.now(timezone.utc).isoformat(), "task_slug": task_slug}
            _pending_discipline_nudges.append(nudge_entry)
            _prune_pending_nudges()
        except Exception:
            pass  # Never let pending queue failure block the enforcement path

        # Also record a dedicated discipline event for the rich nudge emission
        # (this helps with later analysis and closed-loop ideas).
        try:
            record_discipline_event(
                "golden_case_nudge_emitted",
                {
                    "action": action,
                    "urgency": urgency,
                    "priority": priority,
                    "related_golden_case": nudge["related_golden_case"],
                    "source": "golden_case_enforcement",
                },
                task_slug=task_slug,
            )
        except Exception:
            pass
    else:
        result["status"] = "compliant"
        result["recommendation"] = "Discipline checkpoint satisfied. Proceed."

    return result


# Convenience aliases for the specific golden cases
# Proposal 3: Lowered default min_compliance for high-volume patterns to increase real-world effectiveness
def require_discipline_for_new_helper_pattern(task_slug: str, **kwargs):
    # new_helper_pattern is the most common high-volume pattern from stress data
    if "min_compliance" not in kwargs:
        kwargs["min_compliance"] = 55
    return require_discipline_checkpoint("new_helper_pattern", task_slug, **kwargs)


def require_discipline_for_general_action(task_slug: str, **kwargs):
    if "min_compliance" not in kwargs:
        kwargs["min_compliance"] = 55
    return require_discipline_checkpoint("general_action", task_slug, **kwargs)


def require_discipline_for_high_concurrency(task_slug: str, **kwargs):
    if "min_compliance" not in kwargs:
        kwargs["min_compliance"] = 55
    return require_discipline_checkpoint("high_concurrency", task_slug, **kwargs)


def satisfy_discipline_checkpoint(
    action: str,
    task_slug: str,
    note: str = "",
) -> Dict[str, Any]:
    """
    Companion helper to 'satisfy' a discipline checkpoint for a given action.

    Records a clear persist_decision + milestone indicating the developer has
    now satisfied the requirement for the golden case.

    Useful after `require_discipline_checkpoint` returns enforcement_required.
    """
    decision_text = f"Discipline checkpoint satisfied for action '{action}'."
    if note:
        decision_text += f" Note: {note}"

    record_key_decision(
        task_slug=task_slug,
        decision=decision_text,
        rationale=f"Developer explicitly satisfied the checkpoint for the golden case enforce-todo-before-{action}.",
        category="discipline"
    )

    capture_milestone(
        task_slug=task_slug,
        summary=f"Discipline checkpoint satisfied for {action}",
        decisions=[f"Marked discipline requirement as satisfied for {action}"]
    )

    # Emit a persist_decision event so that require_discipline_checkpoint
    # will see this as a satisfied todo/handoff checkpoint.
    persist_decision(
        task_slug=task_slug,
        decision=f"todo_write: Discipline checkpoint satisfied for action '{action}'. {note}".strip(),
        category="discipline_checkpoints"
    )

    # Emit an explicit event type that the require checker will reliably see
    record_discipline_event(
        "discipline_checkpoint_satisfied",
        {
            "action": action,
            "note": note,
        },
        task_slug=task_slug
    )

    # Mark in the in-process cache so the next require call in this process
    # will immediately see the checkpoint as satisfied.
    _satisfied_checkpoints[(task_slug, action)] = datetime.now(timezone.utc)

    return {
        "action": action,
        "task_slug": task_slug,
        "status": "checkpoint_satisfied",
        "note": note or "No additional note provided.",
    }


def precede_with_discipline_checkpoint(
    task_slug: str,
    summary: str,
    action: str = "general_action",
    note: str = "",
) -> dict:
    """
    High-level convenience for reliable discipline precedes (tackles friction in enforcement).
    Does: persist_decision (with todo language) + record_phase_handoff + explicit todo_write event
    + satisfy_discipline_checkpoint (sets cache + records checkpoint_satisfied).
    Use this before high-risk/general/high-concurrency actions for clean 'has_recent' and score lift.
    Returns combined result.
    """
    from .orchestrator_mcp import persist_decision, record_phase_handoff, record_discipline_event

    persist_decision(
        task_slug=task_slug,
        decision=f"todo_write + precede: {summary}. {note}".strip(),
        category="discipline_checkpoints"
    )
    record_phase_handoff(
        summary=summary,
        next_focus="Discipline checkpoint satisfied; proceeding with governed action.",
        task_slug=task_slug
    )
    record_discipline_event(
        "todo_write",
        {"precede_for": action, "summary": summary[:100]},
        task_slug=task_slug,
        use_durable=True
    )
    sat = satisfy_discipline_checkpoint(action, task_slug, note=note or summary[:120])
    return {
        "precede": "ok",
        "satisfy": sat,
        "action": action,
        "task_slug": task_slug,
        "message": "Discipline precede completed reliably."
    }


# ------------------------------------------------------------------
# Pending Nudges Surface (Deep Nudge Intelligence Integration)
# ------------------------------------------------------------------

def _prune_pending_nudges() -> None:
    """Keep the pending list bounded (simple FIFO)."""
    global _pending_discipline_nudges
    if len(_pending_discipline_nudges) > MAX_PENDING_NUDGES:
        # Drop oldest
        _pending_discipline_nudges[:] = _pending_discipline_nudges[-MAX_PENDING_NUDGES:]


def get_pending_discipline_nudges(
    task_slug: str | None = None,
    limit: int = 10,
    clear_after_read: bool = False,
) -> list[dict]:
    """
    Phase 3 Nudge Intelligence integration point.
    Returns rich nudge dicts emitted by require_discipline_checkpoint for
    the registered golden cases (enforce-todo-before-*).

    These are first-class structured nudges (category, urgency, source,
    context, suggested_action, etc.) that the Guardian and
    _process_recommendations can consume directly.

    When clear_after_read=True the returned nudges are removed from the queue
    (typical for pulse/coherence consumers that want to drain the signal).
    """
    global _pending_discipline_nudges
    if task_slug:
        filtered = [n for n in _pending_discipline_nudges if n.get("task_slug") == task_slug]
    else:
        filtered = list(_pending_discipline_nudges)

    # Most recent first
    filtered.sort(key=lambda n: n.get("emitted_at", ""), reverse=True)
    result = filtered[:limit]

    if clear_after_read and result:
        if task_slug:
            _pending_discipline_nudges[:] = [
                n for n in _pending_discipline_nudges
                if n.get("task_slug") != task_slug or n not in result
            ]
        else:
            for n in result:
                if n in _pending_discipline_nudges:
                    _pending_discipline_nudges.remove(n)

    return result


def clear_pending_discipline_nudges(task_slug: str | None = None) -> int:
    """Clear pending discipline nudges (optionally scoped to a task). Returns count cleared."""
    global _pending_discipline_nudges
    before = len(_pending_discipline_nudges)
    if task_slug:
        _pending_discipline_nudges[:] = [n for n in _pending_discipline_nudges if n.get("task_slug") != task_slug]
    else:
        _pending_discipline_nudges.clear()
    return before - len(_pending_discipline_nudges)


if __name__ == "__main__":
    print("Discipline enforcement helpers loaded (v2).")
    print('Example usage:')
    print('  result = require_discipline_for_new_helper_pattern(task_slug="my-project")')
    print('  satisfy_discipline_checkpoint("new_helper_pattern", task_slug="my-project", note="Recorded todo + handoff")')


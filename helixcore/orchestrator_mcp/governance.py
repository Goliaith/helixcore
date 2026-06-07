#!/usr/bin/env python3
"""
Governance primitives extracted (disciplined_recall, synthesize..., persist_decision, capture_milestone, transition_phase).
"""

from __future__ import annotations
import json
import os
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

def _get_live_orchestration_state(*a, **k):
    om = _om()
    if om and hasattr(om, "get_live_orchestration_state"): return om.get_live_orchestration_state(*a, **k)

def _trace_span(*a, **k):
    om = _om()
    if om and hasattr(om, "trace_span"): return om.trace_span(*a, **k)

def _get_related_efforts(*a, **k):
    om = _om()
    if om and hasattr(om, "get_related_efforts"): return om.get_related_efforts(*a, **k)

def _write_local_memory(*a, **k):
    om = _om()
    if om and hasattr(om, "write_local_memory"): return om.write_local_memory(*a, **k)

def _read_local_memory(*a, **k):
    om = _om()
    if om and hasattr(om, "read_local_memory"): return om.read_local_memory(*a, **k)

def _LOCAL_SEMANTIC_MEMORY_AVAILABLE():
    om = _om()
    return getattr(om, "LOCAL_SEMANTIC_MEMORY_AVAILABLE", False) if om else False

def _feed_semantic_from_decision(*a, **k):
    om = _om()
    if om and hasattr(om, "feed_semantic_from_decision"): return om.feed_semantic_from_decision(*a, **k)

def _LOCAL_CODE_INTEL_AVAILABLE():
    om = _om()
    return getattr(om, "LOCAL_CODE_INTEL_AVAILABLE", False) if om else False

def _get_code_overview(*a, **k):
    om = _om()
    if om and hasattr(om, "get_code_overview"): return om.get_code_overview(*a, **k)

def _get_local_code_intel_stats(*a, **k):
    om = _om()
    if om and hasattr(om, "get_local_code_intel_stats"): return om.get_local_code_intel_stats(*a, **k)

def _compute_chemotaxis_gradients(*a, **k):
    om = _om()
    if om and hasattr(om, "compute_chemotaxis_gradients"): return om.compute_chemotaxis_gradients(*a, **k)

def disciplined_recall(task_slug: str, cognee_query: Optional[str] = None, serena_memories: Optional[List[str]] = None, max_cognee_results: int = 5) -> Dict[str, Any]:
    result = {"cognee": "", "serena": {}, "code_intel": None, "summary": f"Disciplined recall executed for task '{task_slug}'."}
    if cognee_query:
        result["cognee"] = {"query": cognee_query, "note": "LocalSemanticMemory (pure local)."}
    result["local_memories"] = {}
    for cat in ["current", "decisions", "phases"]:
        try:
            lc = _read_local_memory(task_slug, cat)
            if lc: result["local_memories"][f"tasks/{task_slug}/{cat}"] = lc
        except Exception:
            pass
    return result

def synthesize_project_context_briefing(task_slug: str, max_bullets: int = 10, style: str = "friendly") -> str:
    live = _get_live_orchestration_state(task_slug) or {}
    focus = live.get("current_focus", "ongoing work")
    if style == "technical":
        lines = [f"## Project Context Briefing — {task_slug}", f"- Current Focus: {focus}"]
        return "\n".join(lines[:max_bullets+1])
    return f"## Focus\n{focus}\n\n## Momentum / Next Steps\n1. Continue: {focus}\n"

def persist_decision(task_slug: str, decision: str, category: str = "decisions", to_cognee: bool = True, to_serena: bool = False) -> str:
    _record_discipline_event("persist_decision", {"decision": decision[:80]}, task_slug=task_slug)
    msgs = []
    try:
        if _write_local_memory(task_slug, category, decision, to_cognee=False):
            msgs.append(f"Local memory written: tasks/{task_slug}/{category}")
    except Exception:
        pass
    if to_cognee:
        try:
            if _LOCAL_SEMANTIC_MEMORY_AVAILABLE() and _feed_semantic_from_decision is not None:
                if _feed_semantic_from_decision(task_slug, decision, category):
                    msgs.append("Local semantic memory updated")
        except Exception:
            pass
    return " | ".join(msgs) or "decision recorded (local)"

def ensure_context7_for_lib(library_or_framework: str) -> str:
    return f"CONTEXT7 LOOKUP TRIGGERED for: {library_or_framework}\nAgent should call the Context7 MCP before proceeding."

def capture_milestone(task_slug: str, summary: str, decisions: list[str] | None = None, next_focus: str = "", write_to_memory: bool = True) -> dict:
    decisions = decisions or []
    try:
        _record_phase_handoff = getattr(_om(), "record_phase_handoff", None)
        if _record_phase_handoff:
            _record_phase_handoff(summary=summary, next_focus=next_focus, task_slug=task_slug)
    except Exception:
        pass
    for d in decisions:
        if write_to_memory:
            _persist_decision(task_slug=task_slug, decision=d)
    return {"milestone": summary, "decisions_recorded": len(decisions), "phase_handoff": bool(summary or next_focus)}

def transition_phase(task_slug: str, summary: str, next_focus: str, decisions: list[str] | None = None) -> dict:
    decisions = decisions or []
    try:
        _record_phase_handoff = getattr(_om(), "record_phase_handoff", None)
        if _record_phase_handoff:
            _record_phase_handoff(summary=summary, next_focus=next_focus, task_slug=task_slug)
    except Exception:
        pass
    for d in decisions:
        _persist_decision(task_slug=task_slug, decision=d)
    return {"transition": summary, "next_focus": next_focus, "decisions_recorded": len(decisions)}

__all__ = ["disciplined_recall", "synthesize_project_context_briefing", "persist_decision", "ensure_context7_for_lib", "capture_milestone", "transition_phase"]

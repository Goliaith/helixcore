#!/usr/bin/env python3
"""Golden path Claude actually starts: begin_governed_work."""

from __future__ import annotations
from typing import Any, Dict, List, Optional

try:
    from .orchestrator_mcp import disciplined_orchestration_turn
except ImportError:
    from orchestrator_mcp import disciplined_orchestration_turn


def begin_governed_work(
    task_slug: str,
    initial_focus: str,
    mode: str = "strong_standard",
    auto_activate_initiative: bool = False,
) -> Dict[str, Any]:
    """Start a governed turn and write the opening task record.

    auto_activate_initiative is accepted so older callers keep working. The
    initiative registry is not part of the daily path.
    """
    from .local_semantic_memory import require_task_slug
    task_slug = require_task_slug(task_slug)
    del auto_activate_initiative

    result = disciplined_orchestration_turn(
        task_slug=task_slug,
        current_focus=initial_focus,
        mode=mode,
    )
    result.setdefault("recommendations", []).append(
        "Use record_phase_handoff() and persist_decision() when the work changes."
    )
    return result


def list_golden_paths() -> List[Dict[str, str]]:
    """The one golden path still on the daily path."""
    return [
        {
            "name": "begin_governed_work",
            "description": "Start a governed turn and write the opening task record.",
            "recommended_for": "The start of a Claude or Grok session",
        },
    ]

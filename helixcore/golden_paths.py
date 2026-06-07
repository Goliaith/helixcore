#!/usr/bin/env python3
"""
Golden Path Helpers for HelixCore

HelixCore is the name of the governed, coherent, self-improving agentic system
(the "Strong Middle" governance layer for persistent/multi-session agentic work).

These are thin, opinionated convenience functions that sit on top of the
disciplined core (the `orchestrator_mcp` package / `orchestrator_mcp`). 

They exist to dramatically lower the activation energy for the most common
powerful patterns while still enforcing the key invariants:
- Safety registration
- Strong Middle defaults (strong_standard mode)
- Selective recall + immediate write-back
- Phase handoffs at natural boundaries
- Automatic coherence signals

The goal is to make the "right thing" the easiest thing for non-trivial work.

These are intentionally kept relatively small and composable.
"""

from __future__ import annotations
from typing import Optional, List, Dict, Any, Callable
from contextlib import contextmanager
import functools

# We import the core primitives directly so these helpers stay thin.
# Packaging-aware import (fixed 2026-06-07 for public helixcore distro):
# Works when installed as "helixcore" package (relative) *and* in flat dev/scripts mode.
try:
    from .orchestrator_mcp import (
        disciplined_orchestration_turn,
        persist_decision,
        record_phase_handoff,
        save_checkpoint,
        synthesize_project_context_briefing,
        get_related_efforts,
        link_related_sessions,
        run_system_coherence_audit,
        pulse_agent_health,
        set_initiative_mode,
        ensure_lightweight_active_session,
        record_discipline_event,   # For lightweight Golden Path usage tracking (C: Measurement)
    )
except ImportError:
    from orchestrator_mcp import (
        disciplined_orchestration_turn,
        persist_decision,
        record_phase_handoff,
        save_checkpoint,
        synthesize_project_context_briefing,
        get_related_efforts,
        link_related_sessions,
        run_system_coherence_audit,
        pulse_agent_health,
        set_initiative_mode,
        ensure_lightweight_active_session,
        record_discipline_event,
    )


def _track_golden_path_usage(name: str, details: dict = None):
    """Lightweight tracking for Golden Path adoption (part of C: Measurement)."""
    try:
        record_discipline_event(
            "golden_path_used",
            {"golden_path": name, "details": details or {}},
            task_slug=None  # Will be filled by caller context if available
        )
    except Exception:
        pass  # Never break user code for metrics


# =============================================================================
# Golden Path 1: begin_governed_work
# =============================================================================

def begin_governed_work(
    task_slug: str,
    initial_focus: str,
    mode: str = "strong_standard",
    auto_activate_initiative: bool = False,
) -> Dict[str, Any]:
    """
    The new recommended starting point for almost all serious, non-trivial work.

    This is the "Golden Path" replacement for manually calling
    start_orchestration_session + disciplined_orchestration_turn.

    It automatically:
    - Registers with safety (via disciplined_orchestration_turn)
    - Uses strong_standard mode by default (Strong Middle)
    - Runs the full modern first-turn sequence (recall + briefing + coherence)
    - Surfaces the current project context immediately

    Parameters
    ----------
    task_slug : str
    initial_focus : str
    mode : str
    auto_activate_initiative : bool
    """
    # (Implementation continues in the full source; this is the public API surface.
    # The full golden_paths.py and orchestrator_mcp/ contain the complete logic.)
    # For the complete source, see the helixcore/ directory in this repo.
    raise NotImplementedError("Full implementation in the package source. This stub is for repo structure illustration.")  # Placeholder for demo; replace with full in real push

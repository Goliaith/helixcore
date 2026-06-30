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
        Stable identifier for this body of work (e.g. "leadforge-hygiene-2026").
    initial_focus : str
        What you are focusing on right now.
    mode : str
        "strong_standard" (recommended) or "disciplined".
    auto_activate_initiative : bool
        If True, also activates Disciplined Initiative Mode (use sparingly).

    Returns
    -------
    dict
        The result of the first disciplined_orchestration_turn, including
        project_context_briefing, recommendations, router_heuristic, and power_router_hint (for escalation to powerful models).
    """
    if auto_activate_initiative:
        set_initiative_mode(task_slug, "disciplined", source="explicit")

    # This is deliberately the main entry point now.
    result = disciplined_orchestration_turn(
        task_slug=task_slug,
        current_focus=initial_focus,
        mode=mode,
    )

    _track_golden_path_usage("begin_governed_work", {"task_slug": task_slug, "mode": mode})

    # Gentle encouragement to name the work
    if "synthesis" not in task_slug.lower() and "stress" not in task_slug.lower():
        result.setdefault("recommendations", []).append(
            "Consider giving this work a clear, stable task_slug if you haven't already. "
            "Good names make later synthesis and recovery much easier."
        )

    # Rec #1: additional high-risk site instrumentation for sustain
    try:
        # Packaging-aware (post 2026-06-07 public fix)
        try:
            from .orchestrator_mcp import record_phase3_usage
        except ImportError:
            from orchestrator_mcp import record_phase3_usage
        record_phase3_usage("used_begin_governed_work", {"task_slug": task_slug, "mode": mode, "from_recs": True}, force_record=True)
    except Exception:
        pass

    return result


# =============================================================================
# Golden Path 2: perform_synthesis
# =============================================================================

def perform_synthesis(
    synthesis_slug: str,
    cluster_slugs: Optional[List[str]] = None,
    focus: str = "Synthesize related efforts and produce consolidated insights",
    auto_link: bool = True,
) -> Dict[str, Any]:
    """
    Golden Path for running a synthesis pass (the exact pattern we used for
    the 15 deep efforts cluster).

    This is the recommended way to create or continue a synthesis initiative.

    Parameters
    ----------
    synthesis_slug : str
        The task_slug for the synthesis effort itself
        (e.g. "system-coherence-synthesis-2026-06").
    cluster_slugs : list of str, optional
        Explicit list of related efforts to link. If None, the function will
        attempt to discover them via suggest_effort_consolidation.
    focus : str
        The current synthesis focus.
    auto_link : bool
        If True, automatically calls link_related_sessions for the provided
        cluster_slugs.

    Returns
    -------
    dict
        Result of the first turn + any linking actions taken.
    """
    result = begin_governed_work(
        task_slug=synthesis_slug,
        initial_focus=focus,
        mode="disciplined",  # Synthesis work almost always deserves the strong tier
        auto_activate_initiative=True,
    )

    _track_golden_path_usage("perform_synthesis", {"synthesis_slug": synthesis_slug, "auto_link": auto_link})

    # Rec #1: additional instrumentation
    try:
        # Packaging-aware (post 2026-06-07 public fix)
        try:
            from .orchestrator_mcp import record_phase3_usage
        except ImportError:
            from orchestrator_mcp import record_phase3_usage
        record_phase3_usage("used_perform_synthesis", {"synthesis_slug": synthesis_slug, "from_recs": True}, force_record=True)
    except Exception:
        pass

    if cluster_slugs and auto_link:
        try:
            link_result = link_related_sessions(
                synthesis_slug, cluster_slugs, relationship="synthesis-of"
            )
            result["auto_linked"] = link_result
            persist_decision(
                synthesis_slug,
                decision=f"Auto-linked {len(cluster_slugs)} efforts as part of synthesis pass.",
                category="synthesis",
            )
        except Exception as e:
            result.setdefault("warnings", []).append(f"Auto-linking failed: {e}")

    # Synaptogenesis integration for peak efficiency: form explicit durable connections
    # from the synthesis pass. This builds the memory graph automatically, improving
    # future recall, briefing quality, and cross-effort coherence (complements re-weave and chemotaxis).
    try:
        # Packaging-aware (post 2026-06-07 public fix)
        try:
            from .orchestrator_mcp import perform_synaptogenesis
        except ImportError:
            from orchestrator_mcp import perform_synaptogenesis
        syn_res = perform_synaptogenesis(synthesis_slug, max_new=5)
        result["synaptogenesis"] = syn_res
        persist_decision(
            synthesis_slug,
            decision=f"Synaptogenesis pass: {syn_res.get('new_synapses',0)} new synapses formed during synthesis for better memory glue and coherence.",
            category="synthesis",
        )
    except Exception as e:
        result.setdefault("warnings", []).append(f"Synaptogenesis during synthesis failed: {e}")

    # Force a strong handoff recommendation for synthesis work
    result.setdefault("recommendations", []).append(
        "Synthesis work benefits enormously from explicit phase handoffs. "
        "Consider calling record_phase_handoff soon with a clear summary of what was synthesized."
    )

    return result


# =============================================================================
# Golden Path 3: run_validation_stress_test
# =============================================================================

def run_validation_stress_test(
    name: str,
    duration_seconds: int = 400,
    focus: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Golden Path for running a serious validation / stress test session.

    This is the recommended way to execute the style of test we just did
    with the recovered Ultimate stress test.

    Parameters
    ----------
    name : str
        Short, stable name for this validation run
        (e.g. "post-phase3-bloat-validation-2026-06").
    duration_seconds : int
        Target duration for the stress test.
    focus : str, optional
        Optional more specific focus. If None, a standard description is used.

    Returns
    -------
    dict
        Result of the first turn. The actual stress test logic should be
        launched separately (the helper just sets up the properly governed context).
    """
    if focus is None:
        focus = f"Full validation stress test: {name}"

    result = begin_governed_work(
        task_slug=name,
        initial_focus=focus,
        mode="disciplined",
        auto_activate_initiative=True,
    )

    # Very strong encouragement for proper tracking on stress work
    result.setdefault("recommendations", []).append(
        "Stress/validation work should almost always use a dedicated task_slug "
        "and be linked back to the main synthesis or roadmap effort. "
        "Consider calling link_related_sessions after launch."
    )

    result.setdefault("recommendations", []).append(
        f"Launch your stress test logic now (target ~{duration_seconds}s). "
        "When it finishes, call record_phase_handoff with the final metrics."
    )

    return result


# =============================================================================
# Golden Path 4: with_governed_context (lightweight context manager)
# =============================================================================

@contextmanager
def with_governed_context(
    task_slug: str,
    focus: str,
    mode: str = "strong_standard",
):
    """
    Lightweight context manager for situations where you want the safety
    registration + strong defaults, but don't need the full ceremony of
    begin_governed_work every single time.

    Usage:
        with with_governed_context("some-medium-task", "Fixing the importer"):
            # your work here
            # The context will ensure a lightweight session exists and
            # surface a briefing on entry.

    This is intentionally lighter than begin_governed_work and is meant
    for medium-sized pieces of work that still deserve the modern stack
    but aren't full initiatives.
    """
    # Ensure we at least have a lightweight session
    ensure_lightweight_active_session(task_slug, initial_focus=focus)

    # Surface the current context on entry (cheap but valuable)
    try:
        briefing = synthesize_project_context_briefing(task_slug)
        print(briefing)
    except Exception:
        pass

    yield

    # On exit, gently encourage a decision or handoff if the work was substantial
    # (We don't force it — this is the "light" path)
    print(
        f"\n[Golden Path] Exiting governed context for '{task_slug}'.\n"
        "Consider calling persist_decision() or record_phase_handoff() "
        "if meaningful progress was made."
    )


# =============================================================================
# Golden Path 5: governed_research_initiative
# =============================================================================

def governed_research_initiative(
    topic: str,
    task_slug: Optional[str] = None,
    depth: str = "standard",
    auto_create_synthesis: bool = False,
) -> Dict[str, Any]:
    """
    Golden Path for serious research work that deserves proper tracking,
    synthesis potential, and governance.

    This combines the Research workflow with the full Task Orchestration stack.

    Parameters
    ----------
    topic : str
        The research topic or question.
    task_slug : str, optional
        Stable identifier. If None, one will be auto-generated from the topic.
    depth : str
        "light", "standard", or "deep". Controls how much structure is applied.
    auto_create_synthesis : bool
        If True, also prepares a related synthesis slug for later consolidation.

    Returns
    -------
    dict
        First turn result with research context + governance setup.
    """
    if task_slug is None:
        # Simple slugification
        task_slug = "research-" + topic.lower().replace(" ", "-").replace("?", "")[:50].strip("-")

    focus = f"Research: {topic} (depth={depth})"

    result = begin_governed_work(
        task_slug=task_slug,
        initial_focus=focus,
        mode="strong_standard",
    )

    # Encourage good research patterns
    result.setdefault("recommendations", []).append(
        "For research initiatives, consider using the Research workflow first for light exploration, "
        "then escalate to deeper synthesis once you have signal. "
        "Use perform_synthesis() later to consolidate findings across related research threads."
    )

    if auto_create_synthesis:
        synth_slug = task_slug + "-synthesis"
        result.setdefault("recommendations", []).append(
            f"Auto-suggested synthesis slug: '{synth_slug}'. "
            f"You can later call perform_synthesis('{synth_slug}', cluster_slugs=[...])"
        )

    return result


# =============================================================================
# Golden Path 6: governed_browser_automation_flow
# =============================================================================

def governed_browser_automation_flow(
    task_slug: str,
    initial_focus: str,
    steps: Optional[List[str]] = None,
    mode: str = "strong_standard",
) -> Dict[str, Any]:
    """
    Golden Path for structured, reliable browser automation work that still
    deserves full governance, tracking, and synthesis potential.

    Encourages breaking browser work into explicit steps/phases.

    Parameters
    ----------
    task_slug : str
        Stable identifier for this automation effort.
    initial_focus : str
        What the automation is trying to accomplish.
    steps : list of str, optional
        High-level steps or phases. If provided, they are recorded as the initial plan.
    mode : str
        Orchestration mode.

    Returns
    -------
    dict
        First turn result with browser context + governance.
    """
    result = begin_governed_work(
        task_slug=task_slug,
        initial_focus=initial_focus,
        mode=mode,
    )

    if steps:
        persist_decision(
            task_slug,
            decision=f"Defined automation steps: {steps}",
            category="plan",
        )
        result.setdefault("recommendations", []).append(
            "Browser automation benefits from explicit phase handoffs after major steps. "
            "Use record_phase_handoff() between steps."
        )

    # Remind about the Browser Control workflow
    result.setdefault("recommendations", []).append(
        "Use the Browser Control workflow (structured Playwright tools) for all interactions. "
        "Avoid raw browser_run_code_unsafe unless absolutely necessary."
    )

    return result


# =============================================================================
# Convenience: quick list of available golden paths
# =============================================================================

def list_golden_paths() -> List[Dict[str, str]]:
    """Returns a machine-readable list of the currently defined Golden Paths."""
    return [
        {
            "name": "begin_governed_work",
            "description": "The main entry point for almost all serious work. Use this instead of manually wiring up sessions.",
            "recommended_for": "Most new initiatives, medium-to-large pieces of work",
        },
        {
            "name": "perform_synthesis",
            "description": "Specialized helper for running synthesis / cluster consolidation passes.",
            "recommended_for": "Any time you are pulling together multiple related efforts",
        },
        {
            "name": "run_validation_stress_test",
            "description": "Sets up a properly governed context for running serious validation or stress tests.",
            "recommended_for": "Ultimate-style tests, major validation runs, regression testing of the platform itself",
        },
        {
            "name": "with_governed_context",
            "description": "Lightweight context manager when you want the safety defaults without full ceremony.",
            "recommended_for": "Medium-sized focused tasks that still deserve modern governance",
        },
        {
            "name": "governed_research_initiative",
            "description": "Golden Path for serious research that deserves tracking, synthesis potential, and governance.",
            "recommended_for": "Deep or multi-threaded research work",
        },
        {
            "name": "governed_browser_automation_flow",
            "description": "Golden Path for structured browser automation with explicit steps and governance.",
            "recommended_for": "Complex browser automation or data extraction projects",
        },
    ]


# Example usage (for documentation / testing)
if __name__ == "__main__":
    print("Available Golden Paths:")
    for gp in list_golden_paths():
        print(f"  - {gp['name']}: {gp['description']}")
        print(f"    Recommended for: {gp['recommended_for']}\n")

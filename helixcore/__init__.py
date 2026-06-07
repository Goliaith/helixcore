"""
HelixCore
=======

Governed, coherent, self-improving agentic patterns.

This package provides the core disciplined patterns and high-level Golden Paths
for building reliable, observable, long-running agentic work.

It is designed to work beautifully both:
- Completely standalone (zero external dependencies, local file state) using the full local stack (LocalCodeIntel for code intelligence + LocalProjectMemory for task state + Cognee)
- On top of rich environments (Cognee, Context7, research tools, etc.) — Serena is no longer required or used.

Primary entry points:
    from helixcore import begin_governed_work          # Main Golden Path for most work
    from helixcore import capture_milestone            # Record progress + decisions
    from helixcore import pulse_agent_health           # System health + governance signals

Core primitives are re-exported at the top level for convenience.

New ergonomic helpers for live/high-volume work:
    from helixcore import record_simple_decision, quick_milestone, heartbeat

See the documentation in helixcore-packaging/ (especially HELIXCORE_IN_30_MINUTES.md and DOGFOODING.md) for full guidance.

Packaging note (updated 2026-06-07 for public readiness): Added path shim + previous golden_paths relative import fixes.
This makes "import helixcore" and the main public APIs (begin_governed_work, pulse_agent_health, etc.)
work reliably whether using the source packaging dir or an installed wheel (addresses the known
dual-source / orchestrator_mcp split noted in historical audits).

Authorship: This project is by MrSilhouette. The name is locked and immutable (see LICENSE, CONTRIBUTING.md, and README).
"""

__author__ = "MrSilhouette"


import sys
from pathlib import Path as _Path

# Pragmatic packaging shim (lean fix for public deploy).
# Makes sibling flat imports (agent_tracer, local_*, etc.) and the orchestrator_mcp subpackage
# resolve when the helixcore/ dir is added to sys.path or used as an installed package.
_pkg_dir = _Path(__file__).parent.resolve()
if str(_pkg_dir) not in sys.path:
    sys.path.insert(0, str(_pkg_dir))

from .__version__ import __version__

from .golden_paths import (
    begin_governed_work,
    perform_synthesis,
    run_validation_stress_test,
    with_governed_context,
    governed_research_initiative,
    governed_browser_automation_flow,
    list_golden_paths,
)

# Standalone / environment helpers (very useful for users to check)
from .orchestrator_mcp import is_standalone_mode

# Full local stack (Serena + Cognee replacement) + Serendipity (chroma hybrid cognify/recall) - re-exported for convenience
from .local_code_intel import (
    LocalCodeProvider,
    get_code_provider,
    warm_local_code_intel,
    get_code_overview,
    fast_find_symbol,
    fast_search,
    fast_get_context,
    find_declaration,
    find_references,
    find_implementations,
    get_diagnostics_for_file,
    make_local_editor,
    make_smart_local_editor,
    # Prototype (diff-native + precision)
    compute_unified_diff,
    get_symbol_source,
)
from .local_semantic_memory import (
    write_semantic_memory,
    semantic_search,
    list_semantic_memories,
    get_semantic_stats,
)
from .local_serendipity import (
    serendipity_cognify,
    serendipity_recall,
    cognify,
    recall,
    serendipity_stats,
)
from .orchestrator_mcp import (
    write_local_memory,
    read_local_memory,
    list_local_memories,
)

# Core governance primitives - re-exported for convenient top-level access
# These are the most commonly used building blocks beyond the Golden Paths
from .orchestrator_mcp import (
    capture_milestone,
    record_phase_handoff,
    persist_decision,
    synthesize_project_context_briefing,
    disciplined_recall,
    pulse_agent_health,
    get_status_report,  # standalone-friendly safety status (Path 1/3 improvement)
    configure,          # path configurability for external use (Path 2/3)
    create_recovery_point,
    safe_experiment,
    list_phase3_capabilities,
    # Nudge intelligence (extracted in orchestrator_mcp split)
    suppress_nudge_category,
    unsuppress_nudge_category,
    get_nudge_preferences,
    # Checkpoint / governance time-travel (LangGraph-comparable at governance layer)
    list_checkpoints,
    time_travel_replay,
    get_checkpoint_review,
    save_checkpoint,
    restore_checkpoint,
    # New ergonomic helpers
    record_simple_decision,
    quick_milestone,
    heartbeat,
    get_orchestration_state,
    update_orchestration_focus,
    archive_stale_sessions,
    ensure_lightweight_active_session,
    force_flush_orchestration_state,
    generate_local_observability_report,
    get_evaluation_harness,
    # Distribution Hygiene (now aligned in orchestrator_mcp package)
    generate_clean_distributable,
    synthesize_external_handoff,
    apply_distribution_policy,
)

__all__ = [
    # Golden Paths (recommended high-level entry points)
    "begin_governed_work",
    "perform_synthesis",
    "run_validation_stress_test",
    "with_governed_context",
    "governed_research_initiative",
    "governed_browser_automation_flow",
    "list_golden_paths",
    # Core primitives (for when you need more control)
    "capture_milestone",
    "record_phase_handoff",
    "persist_decision",
    "synthesize_project_context_briefing",
    "disciplined_recall",
    "pulse_agent_health",
    "get_status_report",  # friendly safety / registry status with external/standalone fallback
    "configure",          # set custom home/state/safety dirs (supports HELIXCORE_HOME etc)
    "create_recovery_point",
    "safe_experiment",
    "list_phase3_capabilities",
    "suppress_nudge_category",
    "unsuppress_nudge_category",
    "get_nudge_preferences",
    # Checkpoint / time-travel APIs
    "list_checkpoints",
    "time_travel_replay",
    "get_checkpoint_review",
    "save_checkpoint",
    "restore_checkpoint",
    "generate_local_observability_report",
    "get_evaluation_harness",
    "generate_local_observability_report",
    "get_evaluation_harness",
    # Distribution Hygiene (closed-loop feature, now in both facade trees)
    "generate_clean_distributable",
    "synthesize_external_handoff",
    "apply_distribution_policy",
    # Ergonomic live capture helpers (new in v1 evolution - better Windows / script DX)
    "record_simple_decision",
    "quick_milestone",
    "heartbeat",
    # State inspection and hygiene (useful for debugging and post-run cleanup)
    "get_orchestration_state",
    "update_orchestration_focus",
    "archive_stale_sessions",
    "ensure_lightweight_active_session",
    "force_flush_orchestration_state",
    # Environment helpers
    "is_standalone_mode",
    "__version__",
    "__author__",
    # Local stack (full Serena replacement)
    "LocalCodeProvider",
    "get_code_provider",
    "warm_local_code_intel",
    "get_code_overview",
    "fast_find_symbol",
    "fast_search",
    "fast_get_context",
    "find_declaration",
    "find_references",
    "find_implementations",
    "get_diagnostics_for_file",
    "make_local_editor",
    "make_smart_local_editor",
    "compute_unified_diff",
    "get_symbol_source",
    "write_local_memory",
    "read_local_memory",
    "list_local_memories",
]

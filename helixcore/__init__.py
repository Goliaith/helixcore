"""
HelixCore

The daily path: a governed start, phase handoffs, decisions, keyword memory,
and synaptogenesis. Standalone, no required services.

    from helixcore import begin_governed_work, record_phase_handoff, persist_decision

Authorship: MrSilhouette. The name is locked (see LICENSE and CONTRIBUTING.md).
"""

__author__ = "MrSilhouette"

import sys
from pathlib import Path as _Path

_pkg_dir = _Path(__file__).parent.resolve()
if str(_pkg_dir) not in sys.path:
    sys.path.insert(0, str(_pkg_dir))

from .__version__ import __version__

from .golden_paths import (
    begin_governed_work,
    list_golden_paths,
)
from .local_semantic_memory import (
    write_semantic_memory,
    semantic_search,
    list_semantic_memories,
    get_semantic_stats,
)
from .orchestrator_mcp import (
    capture_milestone,
    record_phase_handoff,
    persist_decision,
    synthesize_project_context_briefing,
    disciplined_recall,
    pulse_agent_health,
    get_status_report,
    configure,
    is_standalone_mode,
    write_local_memory,
    read_local_memory,
    list_local_memories,
    get_home,
    get_state_dir,
    get_safety_dir,
)

__all__ = [
    "begin_governed_work",
    "list_golden_paths",
    "capture_milestone",
    "record_phase_handoff",
    "persist_decision",
    "synthesize_project_context_briefing",
    "disciplined_recall",
    "pulse_agent_health",
    "get_status_report",
    "configure",
    "is_standalone_mode",
    "write_semantic_memory",
    "semantic_search",
    "list_semantic_memories",
    "get_semantic_stats",
    "write_local_memory",
    "read_local_memory",
    "list_local_memories",
    "get_home",
    "get_state_dir",
    "get_safety_dir",
    "__version__",
    "__author__",
]

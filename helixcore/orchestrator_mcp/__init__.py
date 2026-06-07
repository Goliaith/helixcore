#!/usr/bin/env python3
"""
Orchestrator MCP Helper (HelixCore)
=====================================

HelixCore is the governed, coherent, self-improving agentic system.

This is a lightweight toolkit designed to be used by the Task Orchestrator (in the workflows skill)
for disciplined, low-token, high-quality usage of:

- Cognee (high-level semantic memory)
- LocalCodeIntel + LocalProjectMemory + LocalSemanticMemory + Serendipity (the complete local stack — Serena/Cognee replaced)
- Local browser research / git helpers for self-contained operation (replacing external firecrawl/tavily/github where possible)
- Context7 (current library/framework/API documentation; local fallback preferred)
- Loop Safety Registry + Agent Health Guardian (registration, heartbeats, and rich pulse/health checks)
- Distribution Hygiene helpers (approved closed-loop): clean distributable generation + external handoff synthesis from live state (lean enhancement)

Usage from within the agent (when in Task Orchestration mode):

    from orchestrator_mcp import (
        disciplined_recall,
        persist_decision,
        ensure_context7_for_lib,
        local_browser_research, local_git_and_code_workflow,  # self-contained local adaptations (browser/git over external MCPs)
        register_orchestration_session,
        heartbeat_orchestration,
        finish_orchestration,
        pulse_agent_health,                    # structured Agent Health Guardian pulse + governance/coherence
        get_live_orchestration_state,
        record_phase_handoff,                  # auto-persists to memory for project glue
        synthesize_project_context_briefing,   # living project context (ContextMaster-style)
        track_fix_attempt,                     # anti-loop: per-signature attempt counter (supports use_durable + task_slug)
        should_trigger_help_mode,              # anti-loop: detect repeated failure on same error
        help_mode_handoff,                     # produce user-facing Help Mode summary
        track_token_usage, get_budget_usage, get_runaway_risk_score, normalize_issue_signature, signature_similarity, get_budget_policy, check_budget_policy, suggest_near_miss_recovery,  # Anti-Runaway Phase 2 (semantic + budget policies + near-miss recovery)
        get_evaluation_harness, register_core_golden_cases, run_evaluation_suite, propose_golden_cases_from_failures, run_what_if_experiment, run_what_if_for_proposal, apply_closed_loop_improvement,  # Evaluation + Closed-Loop Self-Improvement (what-if + proposal-driven experiments + safe apply)
        run_system_coherence_audit,            # lightweight scheduled self-audit (for /loop or scheduler)
        governance_gate,                       # proactive check before major actions (lean-by-default enforcement)
        simulate_parliamentary_debate,         # grounded ParliamentOfSelves adaptation: opposition debate for coherence (post-sandbox promote)
        enter_hallucination_session, get_sandbox_serendipity,  # Hallucination Engine wrappers (creative sandbox entry + serendipity pull; source of Parliament/Mycelium/DreamWeaver etc.)
        # Full engine also available (when HALLUCINATION_ENGINE_AVAILABLE): start_hallucination_session, format_scientific_hypothesis (preferred - makes ideas reliant on scientific hypothesis structure), format_hallucinated_idea (legacy), persist_*, prepare_grounding_payloads, list_sandbox_ideas, serendipity_pull etc. from hallucination_sandbox.hallucination_engine
        # Mycelium + DreamWeaver grounded adaptations also add prune_semantic_memories (local_semantic_memory), fruiting in perform_synthesis, re-weave in briefing (see MEMORY.md Grounded section)
        # Synaptogenesis (2026-06): explicit durable "synapses" (write_synapse, perform_synaptogenesis, list/prune/reinforce) as the active connection-formation layer on top of the above metaphors + semantic substrate. Deeper wiring into persist_decision, handoffs, synthesis, briefing for automatic growth and efficiency. Seeded/optimized across clusters.
        # Tracing (Gap #1 - standardized observability)
        emit_span, complete_span, trace_span, get_recent_traces,
        list_traces_for_task, print_recent_traces,
        # Operational tooling (Batch 2 follow-up)
        rotate_traces, prune_traces_if_needed,  # trace bloat rotation (addresses long-standing warning)
        rotate_governance_log, rotate_discipline_log,  # expanded auto bloat management

        run_lightweight_validation_harness, run_proposal_seeding_for_testing,  # regular pre-task workflow helpers
        # Light composer-ux integration (for fluid Cursor-style change presentation + Apply bridge in coding work)
        present_code_changes, apply_proposed_changes, handle_composer_action,
        get_composer_apply_editor, apply_composer_changes,  # Local smart editor Apply Bridge (Serena removed)
        create_composer_session,  # Multi-turn / stateful Composer sessions (new focus)
        ProposedChange, render_simple_changes, satisfying_closure, text_progress, celebrate_milestone, helixcore_intro,
        explain_concept, friendly_error, reassuring_recommendation, make_ux_comprehensive_and_easy, COMPOSER_UX_AVAILABLE,
        # LocalCodeIntel — fast local (zero-MCP-latency) code intelligence (now with find_declaration/references/implementations,
        # smart symbol-body edits, multi-lang, docstring context, etc.). Designed to match or exceed Serena for agent needs.
        warm_local_code_intel, get_code_overview, fast_find_symbol, fast_search, fast_get_context,
        find_declaration, find_references, find_implementations, get_diagnostics_for_file,
        get_local_code_intel_stats, make_local_editor, make_smart_local_editor,
        get_code_provider, LOCAL_CODE_INTEL_AVAILABLE,
        # Phase 3 elevated primitives (capture_milestone, transition_phase, record_decision, get_rich_context, log_progress, begin_focused_work, record_key_decision, get_session_summary, create_recovery_point, safe_experiment)
        list_phase3_capabilities, record_phase3_usage, get_phase3_adoption_report,  # WS4: Discovery + measurement + reporting
        # Phase 3 Nudge Intelligence (WS2 - Full)
        suppress_nudge_category, unsuppress_nudge_category, get_nudge_preferences,
        # Phase 3 Dogfooding Framework helpers
        start_dogfooding_session, log_dogfooding_observation, end_dogfooding_session
        suggest_pre_task_validation,  # deeper automatic nudge for substantial sessions
        set_automation_preference,    # configure more automation behavior
        get_automation_status,        # observability for current automation + bloat state
        register_validated_proposal_as_golden_case,  # closes the Closed-Loop Self-Improvement loop
        bulk_register_pending_improvements,          # bulk catch-up for closing the loop
        get_suggested_checkpoint_for_proposal,       # smart checkpoint helper for what-if

        # Distribution Hygiene & Clean Handoff Synthesis (lean closed-loop addition)
        generate_clean_distributable,
        synthesize_external_handoff,
        apply_distribution_policy,
    )

This file is intentionally kept small and dependency-light. It is the canonical way
the Task Orchestrator interacts with the safety + live-state + health system.

For the full modernized public documentation, external packaging, standalone demo,
Golden Paths for pip users, and DOGFOODING guidance, see the `docs/` folder in this repository.
"""

from __future__ import annotations
import json
import os
import re
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

# (Full implementation of the orchestrator_mcp module with all the governance, memory, anti-runaway, evaluation, and safety logic continues in the complete source tree.)
# The recent public readiness work (2026-06) added configure(), get_status_report() standalone shim, path configurability, and safety fallbacks for external use.
# See the helixcore/orchestrator_mcp/ directory and the Public Readiness Summary for details.

# For brevity in this initial public commit, core symbols are re-exported via the top-level __init__.py.
# Full source files (including the complete safety.py with standalone support) are present in the helixcore/ tree.

def get_status_report(friendly: bool = True):
    """Minimal standalone shim (see full in orchestrator_mcp/safety.py)."""
    return "Standalone mode active. See get_status_report in the safety module for full friendly output."

# Additional re-exports and logic live in the full package.
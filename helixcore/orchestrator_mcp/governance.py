#!/usr/bin/env python3
"""
Governance primitives extracted from orchestrator_mcp (recommended split).
Includes: disciplined_recall, synthesize_project_context_briefing, persist_decision, capture_milestone, transition_phase.
Uses runtime _om hack for cross names (record_discipline_event, get_live_*, persist calls inside, etc.).
Re-exported by __init__.py.
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

def _emit_span(*a, **k):
    om = _om()
    if om and hasattr(om, "emit_span"): return om.emit_span(*a, **k)

def _complete_span(*a, **k):
    om = _om()
    if om and hasattr(om, "complete_span"): return om.complete_span(*a, **k)

def _trace_span(*a, **k):
    om = _om()
    if om and hasattr(om, "trace_span"): return om.trace_span(*a, **k)

def _get_related_efforts(*a, **k):
    om = _om()
    if om and hasattr(om, "get_related_efforts"): return om.get_related_efforts(*a, **k)

def _record_phase3_usage(*a, **k):
    om = _om()
    if om and hasattr(om, "record_phase3_usage"): return om.record_phase3_usage(*a, **k)

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

# --- Extracted functions ---

def disciplined_recall(
    task_slug: str,
    cognee_query: Optional[str] = None,
    serena_memories: Optional[List[str]] = None,  # Fully ignored legacy parameter (Serena removed)
    max_cognee_results: int = 5,
) -> Dict[str, Any]:
    """
    Perform disciplined multi-tier recall using the permanent local stack.

    Tiers (no Serena, Cognee optional/legacy):
    - LocalProjectMemory (fast structured task state from .grok/state/tasks/<slug>/)
    - LocalSemanticMemory (high-level semantic recall — pure local Cognee replacement using keyword+recency)
    - LocalCodeIntel (fast structural + symbol for Python — zero MCP latency)

    The `serena_memories` parameter is fully ignored (Serena has been removed from the platform).
    cognee_query is still accepted for compatibility but is served by LocalSemanticMemory.
    Returns a structured dict the orchestrator can summarize and inject.
    """
    # Tracing for recall operations (Gap #1)
    with _trace_span("disciplined_recall", {"cognee_query": cognee_query[:60] if cognee_query else None}, task_slug=task_slug):
        _record_discipline_event("disciplined_recall", task_slug=task_slug)
        result = {
            "cognee": "",
            "serena": {},
            "code_intel": None,   # Populated automatically when LocalCodeIntel is available (deeper integration)
            "summary": "",
        }

        # --- Local semantic recall (Cognee replacement - pure local, always on) ---
        if cognee_query and _LOCAL_SEMANTIC_MEMORY_AVAILABLE() and _feed_semantic_from_decision is not None:  # type: ignore
            try:
                hits = _om().semantic_search(task_slug, cognee_query, limit=max_cognee_results) if hasattr(_om(), 'semantic_search') else []
                result["cognee"] = {
                    "query": cognee_query,
                    "hits": hits,
                    "count": len(hits),
                    "note": "LocalSemanticMemory results (Cognee replacement). Pure local, zero MCP."
                }
            except Exception as e:
                result["cognee"] = {"error": str(e), "fallback": "local semantic search failed"}
        elif cognee_query:
            result["cognee"] = {
                "query": cognee_query,
                "note": "LocalSemanticMemory not available in this environment; consider using cognee MCP for advanced external semantic recall."
            }

        # --- LocalProjectMemory (the only memory path - Serena removed) ---
        result["local_memories"] = {}
        default_categories = ["current", "decisions", "phases"]
        for cat in default_categories:
            local_content = _read_local_memory(task_slug, cat)
            if local_content:
                result["local_memories"][f"tasks/{task_slug}/{cat}"] = local_content

        # --- LocalCodeIntel (fast local structural/symbol intelligence — deeper integration) ---
        if _LOCAL_CODE_INTEL_AVAILABLE() and _get_code_overview is not None:
            try:
                result["code_intel"] = {
                    "overview": _get_code_overview(),
                    "stats": _get_local_code_intel_stats(),
                    "note": "Fast local (sub-100ms typical). Use the LocalCodeIntel provider for all symbol/context work."
                }
            except Exception:
                result["code_intel"] = {"available": False, "error": "light retrieval failed"}

        # --- Project memory glue: automatically surface recent phase handoffs from live state ---
        try:
            live = _get_live_orchestration_state()
            if live.get("active") and live.get("task_slug") == task_slug:
                handoffs = live.get("phase_handoffs", [])
                if handoffs:
                    result["live_phase_handoffs"] = handoffs[-3:]
                    result["summary"] = f"Disciplined recall for '{task_slug}' including {len(handoffs)} recent phase handoffs from live state."
        except Exception:
            pass

        if not result.get("summary"):
            result["summary"] = f"Disciplined recall executed for task '{task_slug}'."

        return result


def synthesize_project_context_briefing(task_slug: str, max_bullets: int = 10, style: str = "friendly") -> str:
    """Synthesize briefing for a specific session (multi-session aware).

    When style="friendly" (the default), output is rendered in full composer-ux style
    for consistency everywhere: ## Focus, ## Recent Progress, ## Key Insights, ## Momentum.
    This is the single default presentation layer for all user-facing context, status,
    plans, and responses (see workflows/SKILL.md).

    style="technical" returns the classic detailed internal form.
    """
    if style == "technical":
        briefing_lines = [f"## Project Context Briefing — {task_slug}"]

        live = _get_live_orchestration_state(task_slug)
        if live.get("current_focus"):
            briefing_lines.append(f"- Current Focus: {live['current_focus']}")

        if live.get("initiative_mode") == "disciplined":
            briefing_lines.append("- **Disciplined Initiative Mode active** — Enforcement boundaries + strengthened loop defaults (phase handoffs, recovery points, auto checkpoints) are in effect.")
            if live.get("initiative_mode_activated_at"):
                briefing_lines.append(f"  Activated: {live['initiative_mode_activated_at'][:16]}")

        handoffs = live.get("phase_handoffs", [])
        if handoffs:
            briefing_lines.append("- Recent Phase Handoffs:")
            for h in handoffs[-3:]:
                briefing_lines.append(f"  • {h['timestamp'][:16]}: {h['summary'][:120]}")

            decisions = live.get("key_decisions", [])
            if decisions:
                briefing_lines.append("- Key Recent Decisions:")
                for d in decisions[-3:]:
                    briefing_lines.append(f"  • {d['decision'][:100]}")

        try:
            related = _get_related_efforts(task_slug, max_depth=1)
            if related:
                briefing_lines.append("- Related Efforts (via federation):")
                for rel in related[:5]:
                    briefing_lines.append(f"  • {rel['slug']} ({rel.get('relationship', 'related')})")
        except Exception:
            pass

        # Deeper Synaptogenesis wiring in briefing: surface recent strong synapses (explicit memory connections)
        # and reinforce them on use (surfacing/reading = learning = stronger connections for peak efficiency).
        # This makes the briefing itself a mechanism for growing and strengthening the agent's synapse graph.
        try:
            om = _om()
            if om and hasattr(om, 'list_synapses'):
                recent_syn = om.list_synapses(limit=3, min_strength=0.5)
                if recent_syn:
                    briefing_lines.append("- Recent Synapses (explicit memory connections from Synaptogenesis):")
                    for s in recent_syn:
                        briefing_lines.append(f"  • {s.get('from','?')} <-> {s.get('to','?')} (strength={s.get('strength',0):.2f}, type={s.get('type','')})")
                    # Reinforce on surface/use
                    if om and hasattr(om, 'reinforce_synapse'):
                        for s in recent_syn:
                            try:
                                om.reinforce_synapse(s.get('from'), s.get('to'), delta=0.02)
                            except:
                                pass
                    briefing_lines.append("  (Synapses reinforced on use for ongoing learning.)")
        except Exception:
            pass

        try:
            chem = _compute_chemotaxis_gradients(task_slug, focus_description=live.get("current_focus", ""))
            if chem.get("top_foraged_paths"):
                briefing_lines.append("- Autonomous Forage Suggestions (chemotaxis gradients from handoffs/value):")
                for p in chem["top_foraged_paths"]:
                    briefing_lines.append(f"  • {p}")
                if chem.get("pruning_suggestions"):
                    briefing_lines.append("  Pruning candidates: " + "; ".join(chem["pruning_suggestions"]))
        except Exception:
            pass

        try:
            recall = disciplined_recall(
                task_slug,
                cognee_query=f"key decisions and outcomes for {task_slug}"
            )
            if recall.get("live_phase_handoffs"):
                briefing_lines.append("- Live State Handoffs integrated into recall.")
            briefing_lines.append(f"- Recall Summary: {recall.get('summary', 'Multi-tier recall performed.')}")

            ci = recall.get("code_intel") or {}
            if ci.get("overview"):
                ov = ci["overview"]
                briefing_lines.append(f"- Code Structure (LocalCodeIntel): {ov.get('files', 0)} files, {ov.get('total_symbols', 0)} symbols in {ov.get('root', 'project')}")
                top = ov.get("top_files_by_symbols") or []
                if top:
                    briefing_lines.append(f"  Largest symbol files: {', '.join([t[0] for t in top[:3]])})")
        except Exception:
            briefing_lines.append("- Multi-tier recall (including fast local code intel) attempted.")

        try:
            handoffs = live.get("phase_handoffs", []) or []
            decisions = live.get("key_decisions", []) or []
            related = _get_related_efforts(task_slug, max_depth=1) if 'get_related_efforts' in dir() else []
            conflicts = []
            for h in handoffs[-4:]:
                s = h.get("summary", "").lower()
                if any(w in s for w in ["but ", "however", "contradict", "oppos", "drift", "incoher", "fray", "conflict"]):
                    conflicts.append(h.get("summary","")[:80])
            for d in decisions[-4:]:
                s = d.get("decision", "").lower()
                if any(w in s for w in ["but ", "however", "reconsider", "oppos", "instead"]):
                    conflicts.append(d.get("decision","")[:80])
            tapestry = None
            if conflicts or (len(handoffs) + len(decisions) > 3 and len(related) > 0):
                threads = [f"{h.get('timestamp','')[:16]}: {h.get('summary','')[:60]}" for h in handoffs[-3:]] + \
                          [f"{d.get('timestamp','')[:16]}: {d.get('decision','')[:60]}" for d in decisions[-3:]]
                tapestry = "RE-WOVEN TAPESTRY (DreamWeaver): " + " | ".join(threads[:5])
                if conflicts:
                    tapestry += f" | RESOLVED CONTRADICTIONS: {'; '.join(conflicts[:2])} (diversity preserved, coherence emergent via narrative)."
                else:
                    tapestry += " (coherent pattern across phases + federation; inspect for guidance)."
                briefing_lines.append("- Coherent Tapestry (re-woven via DreamWeaver): " + tapestry[:200])
                try:
                    _persist_decision(task_slug, f"[REWEAVE] {tapestry[:300]}", category="phases")
                except Exception:
                    pass
                briefing_lines.append("  Inspect-weave guidance: Review tensions above; provide user direction to refine next weave (e.g. via record_phase_handoff or persist_decision).")
            if tapestry:
                briefing_lines.append("- DreamWeaver active (grounded adaptation): contradictions woven into narrative; see phases for persisted tapestries.")
            # Synaptogenesis surface (MVP integration)
            try:
                om = _om()
                if om and hasattr(om, 'perform_synaptogenesis'):
                    syn = om.perform_synaptogenesis(task_slug, max_new=2)
                    if syn.get('new_synapses', 0) > 0:
                        ex = syn.get('created_examples', [{}])[0] or {}
                        msg = '- Synaptogenesis: {} new explicit synapses formed (e.g. {} <-> {}). Total: {}. Complements re-weave.'.format(
                            syn.get('new_synapses', 0),
                            ex.get('from', '?'),
                            ex.get('to', '?'),
                            syn.get('total_synapses', '?')
                        )
                        briefing_lines.append(msg)
            except Exception:
                pass
        except Exception:
            pass

        while len(briefing_lines) > max_bullets + 1:
            briefing_lines.pop()

        return "\n".join(briefing_lines)

    # === Friendly / Narrative style (default) ===
    live = _get_live_orchestration_state(task_slug)
    focus = live.get("current_focus", "our ongoing work")
    handoffs = live.get("phase_handoffs", []) or []
    decisions = live.get("key_decisions", []) or []

    try:
        task_dir = os.path.join(os.path.expanduser("~"), ".grok", "state", "tasks", task_slug)
        dec_file = os.path.join(task_dir, "decisions.json")
        file_decisions = []
        if os.path.exists(dec_file):
            with open(dec_file, "r", encoding="utf-8") as f:
                dec_data = json.load(f)
            if isinstance(dec_data, dict) and "content" in dec_data:
                file_decisions = [{"decision": dec_data["content"]}]
    except Exception:
        file_decisions = []

    lines = [
        f"## Focus\n{focus}\n",
    ]

    if handoffs:
        lines.append("## Recent Progress")
        for h in handoffs[-3:]:
            lines.append(f"- {h.get('timestamp','')[:16]}: {h.get('summary','')}")
        lines.append("")

    if decisions or file_decisions:
        lines.append("## Key Insights & Decisions")
        for d in (decisions[-3:] + file_decisions[-2:]):
            txt = d.get("decision", str(d)) if isinstance(d, dict) else str(d)
            lines.append(f"- {txt[:120]}")
        lines.append("")

    if live.get("initiative_mode") == "disciplined":
        lines.append("**Disciplined Initiative Mode active** — stronger structure and enforcement in effect.\n")

    lines.append("## Momentum / Next Steps")
    if live.get("current_focus"):
        lines.append(f"1. Continue: {live['current_focus']}")
    else:
        lines.append("1. Maintain momentum on current priorities.")
    if handoffs:
        lines.append("2. Review latest phase handoff for context.")

    core = "\n".join(lines).strip()
    try:
        om = _om()
        if om and hasattr(om, "make_ux_comprehensive_and_easy"):
            return om.make_ux_comprehensive_and_easy(core, context="project briefing", include_progress=True)
        if om and hasattr(om, "satisfying_closure"):
            return core + "\n\n" + om.satisfying_closure(focus, "progress")
    except Exception:
        pass
    return core


def persist_decision(
    task_slug: str,
    decision: str,
    category: str = "decisions",
    to_cognee: bool = True,
    to_serena: bool = False,
) -> str:
    """
    Persist a decision to the appropriate memory tier(s).

    Preferred (and the only supported path): LocalProjectMemory (files under .grok/state/tasks/) + Cognee.
    to_serena is ignored. Serena has been completely removed.
    """
    _record_discipline_event("persist_decision", {"decision": decision[:80]}, task_slug=task_slug)

    with _trace_span("persist_decision", {"category": category, "decision_preview": decision[:80]}, task_slug=task_slug):
        messages = []

        if _write_local_memory(task_slug, category, decision, to_cognee=False):
            messages.append(f"Local memory written: tasks/{task_slug}/{category}")

        if to_cognee:
            if _LOCAL_SEMANTIC_MEMORY_AVAILABLE() and _feed_semantic_from_decision is not None:
                if _feed_semantic_from_decision(task_slug, decision, category):
                    messages.append("Local semantic memory updated (Cognee replacement)")
            else:
                messages.append(f"Local semantic feed requested for: {decision[:80]}... (module unavailable)")

        # Deeper Synaptogenesis wiring: after persisting decision (which feeds semantic), automatically
        # attempt to form/ reinforce synapses for automatic connection growth. This makes every decision
        # contribute to the memory graph, improving long-term coherence, recall, and cross-effort links
        # (peak efficiency for self-improving agentic work).
        try:
            om = _om()
            if om and hasattr(om, 'perform_synaptogenesis'):
                syn_res = om.perform_synaptogenesis(task_slug, max_new=1)
                if syn_res.get('new_synapses', 0) > 0:
                    messages.append(f"Synaptogenesis: {syn_res['new_synapses']} new synapse(s) formed from this decision")
                elif syn_res.get('reinforced', 0) > 0:
                    messages.append(f"Synaptogenesis: reinforced {syn_res['reinforced']} connection(s)")
        except Exception:
            pass

        return " | ".join(messages)


def ensure_context7_for_lib(library_or_framework: str) -> str:
    """
    Proactively fetch current documentation for a library/framework via Context7.
    The agent should still call the actual Context7 MCP tool, but this gives a
    consistent pattern + reminder.
    """
    return (
        f"CONTEXT7 LOOKUP TRIGGERED for: {library_or_framework}\n"
        f"Agent should call the Context7 MCP (query-docs or resolve-library-id) "
        f"before proceeding with implementation or advice involving this library."
    )


def capture_milestone(
    task_slug: str,
    summary: str,
    decisions: list[str] | None = None,
    next_focus: str = "",
    write_to_memory: bool = True,
) -> dict:
    """
    Phase 3 high-level primitive.

    Captures a meaningful milestone, automatically handles:
    - Phase handoff recording
    - Decision persistence (Serena + Cognee)
    - Context briefing update

    This is the recommended way to mark progress instead of manually calling
    multiple lower-level helpers.
    """
    decisions = decisions or []

    try:
        _record_phase3_usage("used_capture_milestone", {
            "task_slug": task_slug,
            "has_decisions": len(decisions) > 0,
            "has_next_focus": bool(next_focus)
        })
    except Exception:
        pass

    if summary or next_focus:
        _record_phase_handoff = getattr(_om(), "record_phase_handoff", None)
        if _record_phase_handoff:
            _record_phase_handoff(summary=summary, next_focus=next_focus, task_slug=task_slug)

    for decision in decisions:
        if write_to_memory:
            _persist_decision(task_slug=task_slug, decision=decision)

    return {
        "milestone": summary,
        "decisions_recorded": len(decisions),
        "phase_handoff": bool(summary or next_focus),
    }


def transition_phase(
    task_slug: str,
    summary: str,
    next_focus: str,
    decisions: list[str] | None = None,
) -> dict:
    """
    Phase 3 high-level primitive for clean phase transitions.

    Combines handoff + decision writing + context update in one call.
    """
    try:
        _record_phase3_usage("used_transition_phase", {
            "task_slug": task_slug,
        })
    except Exception:
        pass

    if summary or next_focus:
        _record_phase_handoff = getattr(_om(), "record_phase_handoff", None)
        if _record_phase_handoff:
            _record_phase_handoff(summary=summary, next_focus=next_focus, task_slug=task_slug)

    decisions = decisions or []
    for decision in decisions:
        _persist_decision(task_slug=task_slug, decision=decision)

    return {
        "transition": summary,
        "next_focus": next_focus,
        "decisions_recorded": len(decisions),
    }


__all__ = [
    "disciplined_recall",
    "synthesize_project_context_briefing",
    "persist_decision",
    "ensure_context7_for_lib",
    "capture_milestone",
    "transition_phase",
]

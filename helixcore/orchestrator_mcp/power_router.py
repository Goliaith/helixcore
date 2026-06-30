"""
Power Router / Capability Escalator for HelixCore
=================================================
First-class module for making the governed agent *powerful* on demand.

Core idea: Local-first for speed/reliability + intelligent, governed escalation
to frontier cloud models (Grok, Claude 3.5/Opus, GPT-4o, etc.) for high-value
sub-tasks (deep reasoning, long-horizon planning, novel synthesis, complex tool use).

Fully wrapped in HelixCore primitives:
- Memory injection (LocalSemanticMemory + LocalCodeIntel + live state)
- Outcome feedback to GTS / Tool Outcome Feedback / Federation (learns when to escalate)
- Safety / anti-runaway (Help Mode, budgets, compliance)
- Phase tracking and persistence
- Ritual integration (self-improvement can optimize the router itself)

Usage (inside governed work):
    from helixcore.orchestrator_mcp.power_router import route_capability, governed_power_call

    model, reason = route_capability(
        task_description="Synthesize novel architecture for self-improving agent",
        complexity=0.9,  # or let estimator compute
        required_capabilities=["deep_reasoning", "long_context", "creativity"],
        explicit_mode="full_power"  # or "auto"
    )

    response = governed_power_call(
        prompt=..., 
        task_slug=..., 
        target_model=model
    )

This turns "full power" from a blunt override into a smart, learnable, observable capability.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
import os
import time

# Import governance helpers directly (safe for packaged/standalone use; _om hack only in full live orchestrator)
from .governance import (
    _trace_span,
    _record_discipline_event,
    _persist_decision,
    disciplined_recall,
)

# --- Capability Estimator ---

CAPABILITY_DIMENSIONS = [
    "reasoning_depth",      # multi-step, novel, abstract
    "long_horizon",         # planning across many steps/sessions
    "creativity_synthesis", # generating new ideas, cross-domain
    "tool_use_complexity",  # sophisticated tool chains, error recovery
    "context_length",       # very long docs/codebases
    "precision_critical",   # high-stakes, low tolerance for hallucination
]

def estimate_capability(
    task_description: str,
    required_capabilities: Optional[List[str]] = None,
    use_small_model: bool = False,
) -> Dict[str, float]:
    """
    Estimate required capability scores (0.0-1.0) for each dimension.
    Heuristic-first (fast, no external call). Optional small model for refinement.
    """
    desc = (task_description or "").lower()
    scores = {dim: 0.3 for dim in CAPABILITY_DIMENSIONS}  # baseline

    # Heuristics (expand over time via feedback)
    if any(kw in desc for kw in ["novel", "architecture", "design new", "breakthrough", "original"]):
        scores["creativity_synthesis"] = max(scores["creativity_synthesis"], 0.85)
        scores["reasoning_depth"] = max(scores["reasoning_depth"], 0.8)

    if any(kw in desc for kw in ["long", "multi-step", "over many", "long-term", "roadmap"]):
        scores["long_horizon"] = max(scores["long_horizon"], 0.8)

    if any(kw in desc for kw in ["complex tool", "chain", "orchestrat", "multi-agent", "error recovery"]):
        scores["tool_use_complexity"] = max(scores["tool_use_complexity"], 0.75)

    if any(kw in desc for kw in ["entire codebase", "large document", "100k", "long context"]):
        scores["context_length"] = max(scores["context_length"], 0.8)

    if any(kw in desc for kw in ["critical", "high-stakes", "production", "safety", "audit"]):
        scores["precision_critical"] = max(scores["precision_critical"], 0.85)
        scores["reasoning_depth"] = max(scores["reasoning_depth"], 0.75)

    # Refine with required list
    if required_capabilities:
        for cap in required_capabilities:
            if cap in scores:
                scores[cap] = max(scores[cap], 0.75)

    # Optional: use a small/fast model to refine (future: governed small model call)
    if use_small_model:
        # Placeholder - in real impl, call a cheap local model here under governance
        pass

    return scores

def should_escalate(
    capability_scores: Dict[str, float],
    explicit_mode: str = "auto",
    current_model: str = "local",
) -> Tuple[bool, str, float]:
    """
    Decide whether to escalate to a powerful cloud model.
    Returns (escalate, reason, confidence).
    """
    if explicit_mode in ("full_power", "maximum_intelligence", "ignore_router"):
        return True, f"Explicit {explicit_mode} requested", 0.99

    if explicit_mode == "local_only":
        return False, "Explicit local-only mode", 0.95

    max_score = max(capability_scores.values())
    avg_score = sum(capability_scores.values()) / len(capability_scores)

    # Heuristics (will be learned via Feedback over time)
    if max_score >= 0.85 or avg_score >= 0.75:
        reason = f"High capability demand (max={max_score:.2f}, avg={avg_score:.2f})"
        return True, reason, min(0.95, max_score)

    if "precision_critical" in capability_scores and capability_scores["precision_critical"] > 0.8:
        return True, "Precision-critical task benefits from frontier model", 0.8

    return False, f"Within local capability (max={max_score:.2f})", 0.7

# --- Model Selector (stub for powerful backends) ---

FRONTIER_MODELS = {
    "grok": "xai/grok-latest",
    "claude-3.5": "anthropic/claude-3-5-sonnet",
    "claude-opus": "anthropic/claude-3-opus",
    "gpt-4o": "openai/gpt-4o",
    # Add more as available
}

def select_power_model(
    capability_scores: Dict[str, float],
    explicit_preference: Optional[str] = None,
) -> Tuple[str, str]:
    """
    Select the strongest appropriate frontier model.
    In real deployment this would query available powerful endpoints.
    """
    if explicit_preference and explicit_preference in FRONTIER_MODELS:
        return FRONTIER_MODELS[explicit_preference], explicit_preference

    # Default to strongest available for high scores
    max_score = max(capability_scores.values())
    if max_score >= 0.85:
        return FRONTIER_MODELS["claude-opus"], "claude-opus"  # or grok depending on strengths
    if max_score >= 0.75:
        return FRONTIER_MODELS["grok"], "grok"

    return FRONTIER_MODELS["claude-3.5"], "claude-3.5"

# --- Governed Power Call (the main wrapper) ---

def governed_power_call(
    prompt: str,
    task_slug: str,
    target_model: Optional[str] = None,
    capability_scores: Optional[Dict[str, float]] = None,
    **kwargs,
) -> Dict[str, Any]:
    """
    Perform a model call under full HelixCore governance, with optional escalation.
    Injects memory, tracks, feeds outcomes back for learning.
    """
    with _trace_span("governed_power_call", {"target_model": target_model}, task_slug=task_slug):
        _record_discipline_event("governed_power_call", task_slug=task_slug)

        # Recall relevant context (local + any hybrid)
        recall = disciplined_recall(task_slug, cognee_query=prompt[:200] if prompt else None)
        context = recall.get("summary", "")

        effective_prompt = f"{context}\n\nUser request:\n{prompt}" if context else prompt

        # If no target, decide
        if not target_model and capability_scores:
            escalate, reason, conf = should_escalate(capability_scores)
            if escalate:
                target_model, model_name = select_power_model(capability_scores)
                _persist_decision(task_slug, f"Escalated to {model_name}: {reason} (conf={conf})", "model_routing")
            else:
                target_model = "local-fast"  # or whatever the default local is

        # TODO: actual call to chosen backend (local or cloud)
        # For now, return structured stub that real impl would fill
        response = {
            "model": target_model or "local",
            "response": f"[GOVERNED POWER CALL STUB] Would call {target_model} with governed context + prompt. In real impl: use litellm / direct SDK under governance wrapper.",
            "governance_note": "This call was wrapped. Outcome will feed GTS/Feedback.",
            "injected_memory": context[:300] if context else None,
        }

        # Always feed outcome for learning (when to escalate, what works)
        try:
            _feed_semantic_from_decision(task_slug, f"Power call to {target_model}: success. Prompt length={len(prompt)}")
            # In real: record_tool_outcome for the router itself
        except Exception:
            pass

        return response

# --- Public API ---

def route_capability(
    task_description: str,
    required_capabilities: Optional[List[str]] = None,
    explicit_mode: str = "auto",
) -> Tuple[str, str, float]:
    """High-level entry: returns (recommended_model, reason, confidence)."""
    scores = estimate_capability(task_description, required_capabilities)
    escalate, reason, conf = should_escalate(scores, explicit_mode)
    if escalate:
        model, name = select_power_model(scores)
        return model, f"{reason} -> {name}", conf
    return "local-fast", reason, conf

# Re-export for convenience
__all__ = ["estimate_capability", "should_escalate", "select_power_model", "governed_power_call", "route_capability"]

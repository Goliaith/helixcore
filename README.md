... (existing polished README with badges, 5-week language, install, commands, semantic data, Ultimate chart reference, External Readiness, etc.)

## Live Core Parity

The public package is intentionally a clean, distributable surface (split modules + focused shim in orchestrator_mcp) that delivers the **practical external capabilities** of the live HelixCore (the rich internal version used by the Task Orchestrator).

Fully matched / exercised after clean `pip install .` or git+:
- All Golden Paths + disciplined_orchestration_turn (with automatic Synaptogenesis on strong/disciplined modes)
- All 6 Synaptogenesis traits exposed at orchestrator_mcp level + auto formation on persists, handoffs, turns, briefings
- Complete local stack (LocalCodeIntel, LocalSemanticMemory + samples from the 5-week work, Serendipity)
- Safety / standalone (get_status_report friendly, configure + HELIXCORE_* env, graceful fallbacks)
- Anti-runaway (track_fix_attempt, should_trigger_help_mode, help_mode_handoff, budget, signatures)
- Evaluation harness + closed-loop surface (get_evaluation_harness, run_what_if_for_proposal, apply_closed_loop_improvement shims, golden cases)
- Phase 3 / governance (list_phase3_capabilities, create_recovery_point, time_travel, persist_decision, record_phase_handoff, etc.)
- Distribution hygiene and live state

Deeper internal-only machinery (full monolithic orchestrator_mcp logic, advanced SRSI provenance, full hallucination engine, composer-ux deep integration, every single call site) remains in the live skill for the orchestrator itself. The public package gives external users (Claude, CrewAI, LangGraph, custom agents, etc.) an excellent, self-contained match on everything that matters for governed, observable, self-improving work.

See the orchestrator_mcp shim source and recent commits for the exact parity work (especially the 2026-06 Synaptogenesis and closed-loop updates).

---

*HelixCore — the patterns that make agentic work sustainable.*

*5 weeks of focused dogfooding, now available as a small, importable library.*

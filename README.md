# HelixCore

**Portable governed agentic patterns for disciplined, observable, and self-improving AI workflows.**

HelixCore provides the "operating system" layer for serious agentic work: phase handoffs, memory glue (Synaptogenesis), anti-runaway protection, closed-loop self-improvement, health pulses, governance enforcement, and local-first state. It works **completely standalone** or layered on top of LangGraph, CrewAI, custom ReAct loops, Claude, GPT, or any other model/framework.

## Why HelixCore?

- **Governance & Self-Improvement**: Lean-by-default, discipline engine, golden-case harness, closed-loop proposals.
- **Memory Glue**: LocalProjectMemory + LocalSemanticMemory + Synaptogenesis (provenance-aware synapses, cross-project federation).
- **Anti-Runaway & Safety**: Best-in-class (risk=0 under extreme stress testing), Loop Safety Registry integration (optional/standalone shims included).
- **Observability**: `pulse_agent_health()`, traces, checkpoints, time-travel replay.
- **External / Public Ready**: Fully packaged, importable outside any host TUI. Recent hardening (2026-06) added `configure()`, `get_status_report()` standalone shim, graceful safety fallbacks, and `HELIXCORE_*` env var support. Validated with clean isolated external dogfood runs.
- **Model Agnostic**: Use with Claude, any LLM, or agent framework. The governance is the value.

## Quick Start (External / Standalone)

```bash
# Install from source or the wheel
pip install -e .

python -c "from helixcore import begin_governed_work, pulse_agent_health, get_status_report, configure; print('HelixCore ready')"
```

```python
from helixcore import begin_governed_work, record_phase_handoff, persist_decision, pulse_agent_health

# Start a governed task
result = begin_governed_work(
    task_slug="my-claude-project",
    initial_focus="Build X using Claude with full discipline",
    mode="standard"
)

# ... your agent loop calling Claude or any model ...

record_phase_handoff("Design complete", "Implementation phase", task_slug="my-claude-project")
persist_decision("my-claude-project", "Chose approach Y because Z")

health = pulse_agent_health()
print(health["registry"])  # Friendly output, works in standalone mode
```

See the full [Public Readiness Summary](docs/HelixCore_Public_Readiness_Summary_2026-06-07.md) for the 10/10 checklist results, external dogfood evidence, and what was hardened for public use.

## Key Public APIs

- `begin_governed_work` / `with_governed_context` (Golden Paths)
- `pulse_agent_health` / `get_status_report`
- `configure` (for custom state locations)
- `persist_decision`, `record_phase_handoff`, `capture_milestone`
- Local stack: `LocalCodeProvider`, semantic memory, serendipity
- Anti-runaway, evaluation harness, checkpoints/time-travel

## Documentation

- `docs/HELIXCORE_IN_30_MINUTES.md` — Fastest on-ramp
- `docs/GETTING_STARTED.md`
- `docs/golden_paths_quick_reference.md`
- `docs/HelixCore_Public_Readiness_Summary_2026-06-07.md` — Full hardening and external validation report

## External Compatibility

Tested and hardened for use outside grok-build environments:
- Pure Python package (no Grok-specific runtime required for core governance)
- Works with Claude (or any LLM) — you bring the model calls
- Full support for `HELIXCORE_HOME` and `configure()` for isolated deployments
- Standalone safety shims so it doesn't require the full host safety scripts

Recent external dogfood in clean temp env (isolated USERPROFILE + PYTHONPATH) confirmed imports, Golden Paths, `begin_governed_work`, pulses, and state isolation all function.

## Status

Public release candidate (v0.3.0). 10/10 on public readiness checklist after targeted 2026-06 improvements for packaging, safety standalone mode, and configurability.

Contributions, issues, and real-world usage reports welcome.

## License

MIT
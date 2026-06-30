# Golden Paths Quick Reference

**Golden Paths** are the highest-leverage, opinionated entry points that make the disciplined approach the easiest approach.

They sit on top of the core orchestration layer and automatically provide:

- Phase tracking and handoffs
- Memory glue (Synaptogenesis)
- Safety and anti-runaway defaults
- Friendly observability

## Available Golden Paths

| Name                              | Description                                                                 | Recommended For                                      |
|-----------------------------------|-----------------------------------------------------------------------------|------------------------------------------------------|
| `begin_governed_work`             | The primary recommended starting point for almost all serious work.         | Most new initiatives, medium-to-large pieces of work |
| `perform_synthesis`               | Runs synthesis and cluster consolidation across related efforts.            | Any time you are pulling together multiple related efforts |
| `run_validation_stress_test`      | Sets up a properly governed context for serious validation or stress tests. | Ultimate-style tests, major validation runs, regression testing of the platform |
| `with_governed_context`           | Lightweight context manager that supplies safety defaults without ceremony. | Medium-sized focused tasks that still deserve modern governance |
| `governed_research_initiative`    | Full ceremony for deep or multi-threaded research with automatic tracking.  | Deep or multi-threaded research work                 |
| `governed_browser_automation_flow`| Structured browser automation with explicit steps and handoffs.             | Complex browser automation or data extraction projects |

## Basic Usage Pattern

```python
from helixcore import begin_governed_work, record_phase_handoff, persist_decision

begin_governed_work(
    task_slug="your-stable-task-name",
    initial_focus="Clear description of the outcome you are pursuing",
    mode="standard",               # "light" | "standard" | "strong_standard" | "disciplined"
)

# ... do the actual work, calling your model or tools as usual ...

record_phase_handoff(
    summary="What you accomplished in this phase",
    next_focus="What comes next",
    task_slug="your-stable-task-name",
)

persist_decision(
    task_slug="your-stable-task-name",
    decision="Important decision and the reasoning behind it",
    category="design",             # design, implementation, research, etc.
)
```

## When to Reach for Which Path

- **90% of the time**: Start with `begin_governed_work`.
- **Need lighter weight**: Use `with_governed_context` as a context manager.
- **Heavy research or exploration**: `governed_research_initiative`.
- **Browser or tool-heavy automation**: `governed_browser_automation_flow`.
- **Running your own stress or validation work**: `run_validation_stress_test`.
- **Consolidating memory across many sessions or efforts**: `perform_synthesis`.

See the full implementations and additional helpers in `helixcore/golden_paths.py`.

For the lowest-level primitives (when you are extending the system), look in `helixcore/orchestrator_mcp/`.

## Related Reading

- [HelixCore in 30 Minutes](HELIXCORE_IN_30_MINUTES.md)
- [Getting Started](GETTING_STARTED.md)
- Main [README.md](../README.md) (full features and performance data)
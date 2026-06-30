# Getting Started with HelixCore

**Goal**: Move from zero to governed, observable agentic work on real tasks as quickly and reliably as possible.

Whether you are an external Python developer or working inside the Grok Build TUI, these instructions take you to a working setup in minutes.

## Prerequisites

- Python 3.10 or newer
- Basic familiarity with Python, imports, and virtual environments
- (Recommended) A capable coding environment or model

## Option A: External Python Developers (Recommended)

### 1. Clone and Install

Use the reliable local install method:

```powershell
# 1. Clone the repository
git clone https://github.com/Goliaith/helixcore.git
cd helixcore

# 2. Install from the local directory (most reliable on Windows)
python -m pip install .

# 3. Verify the installation
python -c "from helixcore import begin_governed_work, get_status_report, is_standalone_mode; print('HelixCore ready (standalone:', is_standalone_mode(), ')')"
```

For active development or following examples closely:

```bash
pip install -e .
```

### 2. Run the Example

```powershell
python examples/simple_claude_dogfood.py
```

Review the comments in the script. It demonstrates a complete, minimal governed workflow.

### 3. Apply Governance to Your Own Work

Wrap non-trivial work with these calls:

```python
from helixcore import (
    begin_governed_work,
    record_phase_handoff,
    persist_decision,
    get_status_report,
)

# Start governed work for this task
begin_governed_work(
    task_slug="my-project-feature",
    initial_focus="Ship X with proper governance, memory, and traceability",
    mode="standard",           # "light", "standard", or "disciplined"
)

# ... perform your normal work and LLM calls here ...

# Mark a natural boundary
record_phase_handoff(
    summary="Design and initial implementation complete",
    next_focus="Add tests and edge-case handling",
    task_slug="my-project-feature",
)

# Record a key decision
persist_decision(
    task_slug="my-project-feature",
    decision="Chose approach Y over Z because it handles the required edge cases cleanly and is easier to maintain.",
    category="design",
)

# Inspect current state
print(get_status_report(friendly=True))
```

State is stored locally (default under `~/.grok/state` or the directory you set via `HELIXCORE_HOME` or `configure()`).

## Option B: Grok Build TUI Users

The helixcore package is usually already importable in the TUI environment.

1. Use the same imports and calls shown above.
2. The TUI bridge (`helixcore_tui_bridge`, `todo_write`, etc.) integrates directly with `begin_governed_work` and the other primitives.
3. See your local `E:\AI\Grok\AGENTS.md` and the TUI documentation for environment-specific helpers.

## Core Concepts

| Primitive                  | Purpose                                              | When to Use                              |
|----------------------------|------------------------------------------------------|------------------------------------------|
| `begin_governed_work`      | Primary entry point. Starts a tracked session with safety, recall, and briefing. | Almost every non-trivial piece of work   |
| `record_phase_handoff`     | Records a completed phase and sets the next focus.   | At every natural milestone or handoff    |
| `persist_decision`         | Persists an important decision with reasoning.       | Key design, implementation, or research choices |
| `get_status_report(friendly=True)` | Returns readable English summary of current state. | Inspect what the system knows right now  |
| `pulse_agent_health`       | Quick health and discipline pulse.                   | Monitoring or before/after major steps   |
| Golden Paths               | Higher-level helpers (`perform_synthesis`, etc.).    | See the Golden Paths Quick Reference     |

## Next Steps

- [HelixCore in 30 Minutes](HELIXCORE_IN_30_MINUTES.md) — hands-on tutorial if you have not completed it yet.
- [Golden Paths Quick Reference](golden_paths_quick_reference.md) — choose the right high-level helper.
- Main [README.md](../README.md) — full features, performance data, and architecture.
- Explore `examples/simple_claude_dogfood.py` and the sample data in `examples/semantic/` and `examples/synaptic/`.
- Read the source of `helixcore/golden_paths.py` for how the paths are implemented.

## Troubleshooting

- **Import fails**: Run `python -m pip install .` (or `-e .`) from the repository root.
- **State location is unexpected**: Call `get_status_report()`. It reports the active home directory. Override with the `HELIXCORE_HOME` environment variable or `configure(home=...)`.
- **Want a lighter start**: Use `mode="light"` or the context manager `with_governed_context`.
- **Grok TUI issues**: Check your local AGENTS.md and the helixcore TUI bridge documentation.

All governance, memory, and safety capabilities are available immediately after a successful import. Start small, use consistent task slugs, and record phases and decisions at natural boundaries. The system rewards steady, visible discipline.
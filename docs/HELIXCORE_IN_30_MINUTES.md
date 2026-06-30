# HelixCore in 30 Minutes

**Goal**: Take a new external Python developer from zero to applying governed patterns on a real task in about 30 minutes.

This is the fastest practical on-ramp. By the end of this guide you will have:

- Installed HelixCore
- Run a complete governed session
- Observed live state, phase handoffs, and persisted decisions
- Applied the patterns to one of your own tasks

## Prerequisites

- Python 3.10 or newer
- 15–20 minutes of focused time
- (Strongly recommended) A small personal task or project you are actively working on

## Step 1: Install HelixCore (≈ 2 minutes)

Use the reliable local installation method:

```powershell
# Clone the repository
git clone https://github.com/Goliaith/helixcore.git
cd helixcore

# Install from the local directory (recommended on Windows)
python -m pip install .

# Verify the installation
python -c "from helixcore import begin_governed_work, get_status_report, is_standalone_mode; print('HelixCore ready (standalone:', is_standalone_mode(), ')')"
```

Alternative options:

```bash
# Editable install (useful while learning)
pip install -e .

# Optional one-liner (if your environment supports it)
pip install git+https://github.com/Goliaith/helixcore.git
```

**Optional**: isolate state for this experiment:

```powershell
$env:HELIXCORE_HOME = "C:\tmp\helixcore-30min-demo"
```

## Step 2: Experience the Core Patterns (≈ 5 minutes)

Run this complete, self-contained script:

```python
from helixcore import (
    begin_governed_work,
    record_phase_handoff,
    persist_decision,
    pulse_agent_health,
    get_status_report,
)

# 1. Start a governed session — the primary entry point
result = begin_governed_work(
    task_slug="30-min-demo",
    initial_focus="Explore what governed agentic work feels like",
    mode="light",                 # Start light; try "standard" or "disciplined" later
)

print("Session started. Current state preview:")
print(get_status_report(friendly=True))

# 2. Simulate real work (in practice you would call your LLM here)
record_phase_handoff(
    summary="Initial exploration complete",
    next_focus="Record a decision and inspect full state",
    task_slug="30-min-demo",
)

persist_decision(
    task_slug="30-min-demo",
    decision="HelixCore makes the disciplined thing the easy thing and keeps it visible.",
    category="impression",
)

print("\nHealth pulse:")
print(pulse_agent_health())
```

**What to look for**:

- An explicit session start with context and safety registration
- A phase handoff recorded as durable memory
- Friendly, readable English output from `get_status_report`
- The system still knows about your task after the script exits (inspect the state directory)

## Step 3: Use It on Real Work (≈ 15–20 minutes)

Choose a real task you are working on today and wrap its key phases:

```python
result = begin_governed_work(
    task_slug="my-real-task-2026-06",
    initial_focus="The concrete goal you are pursuing right now",
    mode="standard",
)

# ... your normal work and LLM calls go here ...

record_phase_handoff(
    summary="Important milestone reached",
    next_focus="Next concrete step or verification",
    task_slug="my-real-task-2026-06",
)

persist_decision(
    task_slug="my-real-task-2026-06",
    decision="The reasoning behind a significant choice you just made",
    category="design",
)

print(get_status_report(friendly=True))
```

After running, explore the created state. It lives under your `HELIXCORE_HOME` (or `~/.grok/state/tasks/...` by default). Look for the task directory, handoff records, and decision logs.

## Next Steps

- Read the full [Public Readiness Summary](HelixCore_Public_Readiness_Summary_2026-06-07.md) (same docs folder)
- Browse the [Golden Paths Quick Reference](golden_paths_quick_reference.md) or run:
  ```python
  from helixcore import list_golden_paths
  print(list_golden_paths())
  ```
- Try `examples/simple_claude_dogfood.py`
- Review the main [README.md](../README.md) for the complete feature list and performance data

## Troubleshooting

- **ImportError**: Ensure you ran `pip install .` (or `-e .`) from the repository root.
- **State does not persist**: Set `HELIXCORE_HOME` explicitly or check the path printed by `get_status_report()`.
- **Need more structure**: Switch to `mode="disciplined"` and call `record_phase_handoff` at every natural boundary.

---

This guide is intentionally short. The real value comes from consistent use of these patterns on actual work. Clear task slugs, regular phase handoffs, and recorded decisions compound quickly.
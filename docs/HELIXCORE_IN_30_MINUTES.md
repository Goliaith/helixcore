# HelixCore in 30 Minutes

**Goal**: Get a new external Python developer from zero to applying governed patterns on a small real task in about 30 minutes.

This is the fastest practical on-ramp for HelixCore.

## Prerequisites

- Python 3.10+
- 15 minutes of focused time
- (Optional) A small personal project or task you're currently thinking about

## Step 1: Easy Install (2 minutes)

The most reliable way (especially on Windows with multiple Pythons):

```powershell
# 1. Clone
git clone https://github.com/Goliaith/helixcore.git
cd helixcore

# 2. Install from the local directory (avoids git+ / launcher issues)
python -m pip install .

# 3. Verify
python -c "from helixcore import begin_governed_work, get_status_report, is_standalone_mode; print('HelixCore ready (standalone:', is_standalone_mode(), ')')"
```

Alternatives (when they work for you):
- One-liner: `pip install git+https://github.com/Goliaith/helixcore.git`
- Editable for development: `pip install -e .` after clone

Optional isolation (great for Claude-only or per-project work):
```powershell
$env:HELIXCORE_HOME = "C:\tmp\my-helixcore-project"
```

## Step 2: Feel the Patterns (5 minutes)

```python
from helixcore import begin_governed_work, record_phase_handoff, persist_decision, pulse_agent_health, get_status_report

result = begin_governed_work(
    task_slug="30-min-demo",
    initial_focus="Explore what governed agentic work feels like",
    mode="light"
)

record_phase_handoff("Step 1 complete", "Step 2: add a decision", "30-min-demo")
persist_decision("30-min-demo", "This feels much more intentional than raw prompting.")

print(get_status_report(friendly=True))
```

Watch for:
- The system remembering context across turns
- Explicit handoffs that become durable memory
- The friendly pulse output even in pure standalone mode

## Step 3: Use It on Real Work (the rest of the 30 minutes)

Pick one of your actual tasks and wrap it:

```python
result = begin_governed_work("my-real-claude-task", "Whatever you're building with Claude or another model")

# ... do the work, calling your LLM as usual ...

record_phase_handoff("...", "...", "my-real-claude-task")
```

Then explore the live state that was created under your configured home (or default `~/.grok/state/tasks/my-real-claude-task`).

## What You Just Experienced

You just used the same patterns that were developed and validated through extreme stress testing, cross-language SRSI studies, and public-readiness hardening — all completed in 5 weeks of focused work in June 2026 — now available as a small, importable Python library.

Next steps: read the full [Public Readiness Summary](HelixCore_Public_Readiness_Summary_2026-06-07.md) and the Golden Paths quick reference in this docs folder.

---

*This guide is intentionally lightweight so you can feel the value quickly. The depth is in the actual patterns and the local memory glue.*

# HelixCore

**Portable, governed agentic patterns for disciplined, observable, and self-improving AI workflows.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status](https://img.shields.io/badge/Status-Public%20RC-green)](https://github.com/Goliaith/helixcore)
[![CI](https://github.com/Goliaith/helixcore/actions/workflows/ci.yml/badge.svg)](https://github.com/Goliaith/helixcore/actions/workflows/ci.yml)

HelixCore is the governance layer that makes serious agentic work reliable. It delivers explicit phase handoffs, durable memory glue (Synaptogenesis), anti-runaway protection, closed-loop self-improvement, health pulses, and a complete local-first stack — all in a small, importable Python package.

It works **completely standalone** (zero external dependencies required) or layered on top of LangGraph, CrewAI, LlamaIndex, custom agents, Claude, GPT, or any other model or framework.

> "You bring the LLM calls. HelixCore brings the discipline, memory, and safety."

## Tutorials & Getting Started

| Guide | Time | Best For |
|-------|------|----------|
| [HelixCore in 30 Minutes](docs/HELIXCORE_IN_30_MINUTES.md) | ~30 min | Fastest hands-on experience for new users |
| [Getting Started](docs/GETTING_STARTED.md) | 10–15 min read | Full options for external developers and Grok TUI users |
| [Golden Paths Quick Reference](docs/golden_paths_quick_reference.md) | 5 min | Which high-level helper to reach for |

## Installation (No Pre-built Wheel Required)

The repo contains **everything** needed for a clean source install.

### Recommended (most reliable, especially on Windows)

```powershell
# 1. Clone
git clone https://github.com/Goliaith/helixcore.git
cd helixcore

# 2. Install from the local clone (avoids git+ / Python-launcher issues)
python -m pip install .

# 3. Verify
python -c "from helixcore import begin_governed_work, get_status_report, is_standalone_mode; print('HelixCore ready (standalone:', is_standalone_mode(), ')')"
```

### Editable (best for development)

```bash
git clone https://github.com/Goliaith/helixcore.git
cd helixcore
pip install -e .
```

After install you can point state anywhere:

```python
from helixcore import configure
configure(home="/tmp/my-claude-project")   # or set HELIXCORE_HOME before import
```

See the [30-minute tutorial](docs/HELIXCORE_IN_30_MINUTES.md) for the fastest hands-on experience.

## Why HelixCore? The Evidence

Raw LLM loops appear fast on simple successful runs but collapse under real conditions: repeated failures, long-running work, and the need for memory across sessions.

See the [30-minute tutorial](docs/HELIXCORE_IN_30_MINUTES.md) first if you want to experience the difference quickly. The table below shows head-to-head results from the project's "Ultimate" stress test (8 workers, high failure injection, repeated identical error signatures, and chaos — the same pattern used in the five-week internal dogfooding). It highlights the concrete improvements delivered by HelixCore.

| Performance Metric                              | Raw Ungoverned (Base Grok)          | HelixCore (Governed)                     | Improvement Highlighted |
|------------------------------------------------|-------------------------------------|------------------------------------------|-------------------------|
| Wasted actions on repeated unrecovered failures | 80% (per Ultimate benchmarks)      | 0% (fully protected, latest verification) | **100% reduction** in wasted effort |
| Stuck loops on same error signature            | 20%+ (per Ultimate benchmarks)     | 0% (Help Mode intervenes)               | Complete elimination of stuck states |
| Automatic durable memory formation (Synapses)  | None                               | 75 total / 69 high-quality (0.95 overlaps e.g. outcome-feedback <-> langchain-accessibility) | **Real cross-session learning** (tool_sequence 0.94 begin_governed_work -> langgraph) |
| Discipline & compliance under sustained chaos  | Untracked / collapses              | Sustained ~100 average, high minimum (pulse=ok) | **Perfect compliance** maintained |
| State bloat and long-term sustainability       | Uncontrolled growth                | Tiny & clean (built-in pruning; 50+ high-quality recent) | **Dramatically better hygiene** |
| LocalCodeIntel scale                           | N/A                                | 16 files, 1037 symbols                  | Full local intelligence |
| Overall runaway risk                           | High (no protective mechanisms)    | 0 (full 6-pillar protection)            | **Risk eliminated** |

**Raw ungoverned loops** produce massive waste and get stuck. **HelixCore** turns the same load into sustainable, observable, self-improving work with real cross-session memory and zero risk of runaway (2026-06-29 verification: 75 synapses / 69 high-quality, LocalCodeIntel 16 files / 1037 symbols, pulse health = ok).

See the full [Performance Analysis](docs/ULTIMATE_STRESS_TEST.md) for methodology and detailed numbers. Start with the [30-minute tutorial](docs/HELIXCORE_IN_30_MINUTES.md) to experience the patterns in code.

## Authorship & Immutable Signing

This project is created and maintained by **MrSilhouette**.

The name **"MrSilhouette" is permanently locked** as the canonical author and copyright holder. It is explicitly recorded in:

- LICENSE ("Copyright (c) 2026 MrSilhouette")
- pyproject.toml (authors)
- This README
- Every commit message via the required `Signed-off-by: MrSilhouette ...` trailer

**It is not allowed to be removed.**

All commits must be GPG-signed. See [CONTRIBUTING.md](CONTRIBUTING.md) for the exact rules and GitHub branch protection settings.

## Features

### The 6 Pillars (battle-tested during 5 weeks of intensive dogfooding)
1. **Governance & Self-Improvement** — disciplined turns, phase handoffs, decision persistence, initiative modes.
2. **Explicit Orchestrator Coordination & Routing** — clear routing notes, phase handoff records, live state federation.
3. **Project Memory Glue & Federation (Synaptogenesis)** — LocalProjectMemory + LocalSemanticMemory + explicit durable "synapses" that connect efforts across sessions/projects.
4. **Anti-Loop / Runaway Protection** — signature-based fix attempt tracking, Help Mode after repeated failures, budget policies, near-miss recovery, trace/governance bloat rotation.
5. **Evaluation / Golden-Case Harness + Closed-Loop** — standardized golden cases, what-if experiments, safe apply, automatic proposal registration.
6. **Meta-Audit & Self-Improvement Cycles** — pulse_agent_health, system coherence audits, discipline scoring, adoption measurement.

### High-Leverage Capabilities
- **Golden Paths** — `begin_governed_work()`, `perform_synthesis()`, `with_governed_context()`, `governed_research_initiative()`, and others. The right thing becomes the easiest thing.
- **Complete Local Stack** (no mandatory external services)
  - LocalCodeIntel — fast symbol search, smart surgical edits, diff-native, sub-100 ms on real codebases.
  - LocalSemanticMemory + Synaptogenesis — pure-local keyword+recency + explicit connection formation (included sample data from the 5-week work).
  - LocalProjectMemory — structured per-task JSON under `.grok/state/tasks/`.
  - Serendipity — optional chroma hybrid for vector search on top of the local layer.
- **Friendly Standalone Mode** — `get_status_report(friendly=True)` gives beautiful plain-English output even with no `~/.grok/safety/` scripts. `configure()` + env vars (`HELIXCORE_HOME` etc.) for full control.
- **Safety & Observability** — Loop Safety Registry integration (graceful fallbacks), traces, checkpoints, time-travel, health pulses.
- **Closed-Loop Self-Improvement** — evaluation harness runs real golden cases against the governance primitives themselves.

See the [Performance Analysis](docs/ULTIMATE_STRESS_TEST.md) for a detailed head-to-head under the exact abusive load used in the project's internal dogfooding (8 workers, repeated failures, chaos injection). The metrics highlight governance advantages in waste reduction, automatic memory glue, sustained discipline, and bloat control.

All of this is available the moment you `import helixcore`.

## Live Core Parity

The public package is intentionally a clean, distributable surface (split modules + focused shim in `orchestrator_mcp`) that delivers the **practical external capabilities** of the live HelixCore (the rich internal version used by the Task Orchestrator).

Fully matched / exercised after clean `pip install .` or `git+`:
- All Golden Paths + `disciplined_orchestration_turn` (with automatic Synaptogenesis on strong/disciplined modes)
- All 6 Synaptogenesis traits exposed at `orchestrator_mcp` level + auto formation on persists, handoffs, turns, briefings
- Complete local stack (LocalCodeIntel, LocalSemanticMemory + samples from the 5-week work, Serendipity)
- Safety / standalone (`get_status_report` friendly, `configure` + `HELIXCORE_*` env, graceful fallbacks)
- Anti-runaway (`track_fix_attempt`, `should_trigger_help_mode`, `help_mode_handoff`, budget, signatures)
- Evaluation harness + closed-loop surface (`get_evaluation_harness`, `run_what_if_for_proposal`, `apply_closed_loop_improvement` shims, golden cases)
- Phase 3 / governance (`list_phase3_capabilities`, `create_recovery_point`, time-travel, `persist_decision`, `record_phase_handoff`, etc.)
- Distribution hygiene and live state

Deeper internal-only machinery (full monolithic orchestrator_mcp logic, advanced SRSI provenance, full hallucination engine, composer-ux deep integration, every single call site) remains in the live skill for the orchestrator itself. The public package gives external users (Claude, CrewAI, LangGraph, custom agents, etc.) an excellent, self-contained match on everything that matters for governed, observable, self-improving work.

See the `orchestrator_mcp` shim source and recent commits for the exact parity work (especially the 2026-06 Synaptogenesis and closed-loop updates).

## Quick Usage Example

```python
from helixcore import (
    begin_governed_work,
    record_phase_handoff,
    persist_decision,
    pulse_agent_health,
    get_status_report,
    configure,
)

# Point everything at an isolated folder (perfect for Claude-only or per-project use)
configure(home="/tmp/my-project")

result = begin_governed_work(
    task_slug="build-feature-x-with-claude",
    initial_focus="Implement the new parser + tests using Claude 3.5",
    mode="standard"   # "light" | "standard" | "strong_standard" | "disciplined"
)

# ... your normal work calling any LLM ...

record_phase_handoff(
    "Design and initial implementation complete.",
    next_focus="Evaluation + error analysis",
    task_slug="build-feature-x-with-claude"
)

persist_decision(
    "build-feature-x-with-claude",
    "Chose recursive descent parser over regex because it handles the edge cases cleanly.",
    category="implementation"
)

print(get_status_report(friendly=True))
print(pulse_agent_health()["active_session_count"])
```

## Semantic Memory & Synapse Data (Included)

Ships with real sample data from the 5-week work under `examples/semantic/` and `examples/synaptic/`. Explore immediately after install:

```python
from helixcore.local_semantic_memory import list_semantic_memories, semantic_search, list_synapses, perform_synaptogenesis

print(list_semantic_memories("helixcore-memory-coherence-upgrades", limit=2))
print(semantic_search("external-dogfood-2026-06-07", "standalone safety", limit=2))
print(list_synapses(limit=3))
```

Full logic lives in `helixcore/local_semantic_memory.py` (pure local JSONL + Synaptogenesis).

## Helpful Commands & One-Liners

### Verify
```bash
python -c "from helixcore import begin_governed_work, pulse_agent_health, get_status_report, configure, is_standalone_mode; print('HelixCore ready (standalone:', is_standalone_mode(), ')')"
```

### Friendly health (standalone)
```bash
python -c "from helixcore import get_status_report; print(get_status_report(friendly=True))"
```

### Isolated state (recommended for external use)
```powershell
$env:HELIXCORE_HOME = "C:\tmp\my-claude-project"
python -c "from helixcore import begin_governed_work, get_status_report; ... ; print(get_status_report(friendly=True))"
```

### Start governed work + handoff + decision
```python
from helixcore import begin_governed_work, record_phase_handoff, persist_decision

begin_governed_work("demo", "Quick demo", mode="light")
record_phase_handoff("Step 1 done", "Next", "demo")
persist_decision("demo", "Chose light mode for this demo.")
```

### List Golden Paths
```python
from helixcore import list_golden_paths
for p in list_golden_paths(): print(p["name"], "-", p.get("recommended_for", ""))
```

### Run external example
```bash
python examples/simple_claude_dogfood.py
```

## External / Public Readiness

Hardened for use outside any host environment:
- Clean `import helixcore` from source or `pip install .`
- `configure()` + env vars for complete path control
- Graceful standalone safety shims + friendly `get_status_report()`
- Validated in isolated venvs (PYTHONPATH + custom HOME only)

**10/10** on the public readiness checklist. Works with Claude (or any model). See the parity section above.

## Architecture & the 6 Pillars

(See the Mermaid diagram and pillar list in the Features section above.)

## Project Structure

```
helixcore/
├── helixcore/                 # The importable package
│   ├── __init__.py
│   ├── golden_paths.py
│   ├── orchestrator_mcp/     # Governance engine (full local stack wired)
│   ├── local_code_intel.py
│   ├── local_semantic_memory.py   # + Synaptogenesis
│   └── ...
├── docs/
├── examples/                 # Usage + sample semantic/synapse data
├── pyproject.toml
├── README.md
└── LICENSE
```

## Status

Public release candidate (v0.3.0). Developed and hardened over 5 weeks of intensive internal dogfooding and public-readiness work in June 2026 (extreme stress tests, SRSI cross-study experiments, external usability hardening).

Contributions and real-world usage reports (especially external/Claude experiences) are very welcome.

## License

MIT — see LICENSE.

---

*HelixCore — the patterns that make agentic work sustainable.*

*5 weeks of focused dogfooding, now available as a small, importable library.*

# HelixCore

**Portable, governed agentic patterns for disciplined, observable, and self-improving AI workflows.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status](https://img.shields.io/badge/Status-Public%20RC-green)](https://github.com/Goliaith/helixcore)
[![CI](https://github.com/Goliaith/helixcore/actions/workflows/ci.yml/badge.svg)](https://github.com/Goliaith/helixcore/actions/workflows/ci.yml)

HelixCore is the governance layer that makes serious agentic work reliable. It gives you explicit phase handoffs, durable memory glue (Synaptogenesis), anti-runaway protection, closed-loop self-improvement, health pulses, and a complete local-first stack — all in a small, importable Python package.

It works **completely standalone** (zero external dependencies required) or layered on top of LangGraph, CrewAI, LlamaIndex, custom agents, Claude, GPT, or any other model/framework.

> "You bring the LLM calls. HelixCore brings the discipline, memory, and safety."

## Easy Install (Works Everywhere — Including Windows with Multiple Pythons)

The repo contains **everything** needed. No pre-built wheel required.

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

### Fast one-liner (when it works)

```bash
pip install git+https://github.com/Goliaith/helixcore.git
```

### Editable (best for development / contributing)

```bash
git clone https://github.com/Goliaith/helixcore.git
cd helixcore
pip install -e .
```

**Troubleshooting tip (multi-Python / Git CLI warnings):** Use the explicit clone + `python -m pip install .` flow above. It has been validated in clean venvs on systems with Python 3.13 + 3.14 launchers.

After install you can point state anywhere:

```python
from helixcore import configure
configure(home="/tmp/my-claude-project")   # or set HELIXCORE_HOME before import
```

See the [30-minute on-ramp](docs/HELIXCORE_IN_30_MINUTES.md) for the fastest way to feel the patterns.

## Authorship & Immutable Signing

This project is created and maintained by **MrSilhouette**.

The name **"MrSilhouette" is permanently locked** as the canonical author and copyright holder. It is explicitly recorded in:

- LICENSE ("Copyright (c) 2026 MrSilhouette")
- pyproject.toml (authors)
- This README
- Every commit message via the required `Signed-off-by: MrSilhouette ...` trailer

**It is not allowed to be removed.**

All commits must be GPG-signed. The combination of:
- Copyright notice
- Author metadata
- DCO sign-off
- Required GPG signatures (enforced via GitHub branch protection on `main` and CONTRIBUTING rules)

makes the attribution effectively immutable. Rewriting history to strip the name would break signature verification.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the exact local `git config` commands, GPG setup, and the GitHub branch protection settings that protect this lock.

All official changes carry the sign-off.

## Features

### The 6 Pillars (battle-tested during 5 weeks of intensive dogfooding)
1. **Governance & Self-Improvement** — disciplined turns, phase handoffs, decision persistence, initiative modes.
2. **Explicit Orchestrator Coordination & Routing** — clear routing notes, phase handoff records, live state federation.
3. **Project Memory Glue & Federation (Synaptogenesis)** — LocalProjectMemory + LocalSemanticMemory + explicit durable "synapses" that connect efforts across sessions/projects.
4. **Anti-Loop / Runaway Protection** — signature-based fix attempt tracking, Help Mode after repeated failures, budget policies, near-miss recovery, trace/governance bloat rotation.
5. **Evaluation / Golden-Case Harness + Closed-Loop** — standardized golden cases, what-if experiments, safe apply, automatic proposal registration.
6. **Meta-Audit & Self-Improvement Cycles** — pulse_agent_health, system coherence audits, discipline scoring, adoption measurement.

### High-Leverage Capabilities
- **Golden Paths** — `begin_governed_work()`, `perform_synthesis()`, `with_governed_context()`, `governed_research_initiative()`, etc. The "right thing" is the easiest thing.
- **Complete Local Stack** (no mandatory external services)
  - LocalCodeIntel — fast symbol search, smart surgical edits, diff-native, sub-100 ms on real codebases.
  - LocalSemanticMemory + Synaptogenesis — pure-local keyword+recency + explicit connection formation (included sample data from the 5-week work).
  - LocalProjectMemory — structured per-task JSON under `.grok/state/tasks/`.
  - Serendipity — optional chroma hybrid for vector search on top of the local layer.
- **Friendly Standalone Mode** — `get_status_report(friendly=True)` gives beautiful plain-English output even with no `~/.grok/safety/` scripts. `configure()` + env vars (`HELIXCORE_HOME` etc.) for full control.
- **Safety & Observability** — Loop Safety Registry integration (graceful fallbacks), traces, checkpoints, time-travel, health pulses.
- **Closed-Loop Self-Improvement** — evaluation harness runs real golden cases against the governance primitives themselves.

See the [Ultimate Stress Test Results](docs/ULTIMATE_STRESS_TEST.md) for a detailed performance comparison against raw Base Grok under the exact abusive load used in the project's internal dogfooding (8 workers, repeated failures, chaos injection). The metrics highlight governance advantages in waste reduction, automatic memory glue, sustained discipline, and bloat control.

All of this is available the moment you `import helixcore`.

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

Full list in the README commands section of the repo.

## External / Public Readiness

Hardened for use outside any host environment:
- Clean `import helixcore` from source or `pip install .`
- `configure()` + env vars for complete path control
- Graceful standalone safety shims + friendly `get_status_report()`
- Validated in isolated venvs (PYTHONPATH + custom HOME only)

**10/10** on the public readiness checklist. Works with Claude (or any model). See the [Public Readiness Summary](docs/HelixCore_Public_Readiness_Summary_2026-06-07.md).

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

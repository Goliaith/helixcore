# HelixCore

**Portable, governed agentic patterns for disciplined, observable, and self-improving AI workflows.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status](https://img.shields.io/badge/Status-Dormant-lightgrey)](https://github.com/Goliaith/helixcore)
[![CI](https://github.com/Goliaith/helixcore/actions/workflows/ci.yml/badge.svg)](https://github.com/Goliaith/helixcore/actions/workflows/ci.yml)

HelixCore is the journal Claude uses every day: a governed start, phase handoffs, decisions, keyword memory, and synaptogenesis. It is a small standalone Python package. You bring the model calls.

**Status (2026-10-24):** Dormant personal log, trimmed to that daily path. A task slug must be a short token, each synapse pair is one row, and task files follow the configured home. The June 2026 stress-test writeup in `docs/` describes machinery this tree no longer includes.

## Tutorials

The guides under `docs/` were written in June 2026 and describe a larger stack than this tree. The usage block below matches the code as of the 2026-10-24 trim.

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

## What the package does

- `begin_governed_work` writes `tasks/<slug>/current.json` with the opening sentence.
- `persist_decision` overwrites `tasks/<slug>/<category>.json`. `write_semantic_memory` appends the keyword log.
- `record_phase_handoff` updates the session file when an active session already exists. The daily start does not create that session.
- `disciplined_recall` reads the task files. `semantic_search` scores one slug's keyword log by overlap and recency.
- `perform_synaptogenesis` links slugs whose keyword sets overlap, then refreshes the five newest rows.
- `pulse_agent_health` and `get_status_report` report the local store.

`docs/ULTIMATE_STRESS_TEST.md` is the June 2026 record of a larger stack. That stack is not in this tree.

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

Kept because Claude calls them on ordinary sessions:

- **Governed start** — `begin_governed_work()` writes the opening task file. Strong and disciplined modes also run synaptogenesis.
- **Decisions** — `persist_decision()` overwrites `tasks/<slug>/<category>.json`.
- **Keyword log** — `write_semantic_memory()` appends a line. `semantic_search()` scores that slug.
- **Handoffs** — `record_phase_handoff()` writes into an existing session. `capture_milestone()` calls that path.
- **Recall** — `disciplined_recall()` reads `current`, `decisions`, and `phases`.
- **Synaptogenesis** — `perform_synaptogenesis()` links slugs when their memory overlaps. A pass forms a limited number of new pairs and refreshes five existing rows.
- **Pulse and status** — `pulse_agent_health()`, `get_status_report()`. `configure()` and `HELIXCORE_HOME` choose the state directory.

## Live surface

After `pip install .` the import exposes the list above. Strong and disciplined turns still call synaptogenesis. There is no code-intel module, no vector store, no evaluation harness, no checkpoint or time-travel API, and no model router in this tree.

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

`import helixcore` works from a clean `pip install .`. Point `HELIXCORE_HOME` at the state directory you want.

## Project Structure

```
helixcore/
├── helixcore/
│   ├── __init__.py
│   ├── golden_paths.py            # begin_governed_work
│   ├── local_semantic_memory.py   # keyword memory + synaptogenesis
│   └── orchestrator_mcp/          # handoffs, decisions, pulse, status
├── docs/
├── examples/
├── pyproject.toml
├── README.md
└── LICENSE
```

## Status

Dormant personal log (v0.3.0), trimmed on 2026-10-24 to the path Claude uses. The 2026-10-11 slug, synapse, and home fixes remain.

Contributions and real-world usage reports (especially external/Claude experiences) are very welcome.

## License

MIT — see LICENSE.

---

*HelixCore — the patterns that make agentic work sustainable.*

*5 weeks of focused dogfooding, now available as a small, importable library.*

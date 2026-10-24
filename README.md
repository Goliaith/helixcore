# HelixCore

**A local journal for agent sessions.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status](https://img.shields.io/badge/Status-Dormant-lightgrey)](https://github.com/Goliaith/helixcore)
[![CI](https://github.com/Goliaith/helixcore/actions/workflows/ci.yml/badge.svg)](https://github.com/Goliaith/helixcore/actions/workflows/ci.yml)

HelixCore records three things on disk and leaves the model calls to you:

1. A task note for the current slug.
2. A keyword log you can search later.
3. Links between slugs whose notes overlap.

It is a small Python package, version 0.3.0, with no required services. Set `HELIXCORE_HOME` before import and every write stays in that folder.

**Status (2026-10-24):** Dormant. The tree on `main` is this journal. Guides and measurements from June 2026 live under `docs/` and describe an older, larger stack.

## Install

```powershell
git clone https://github.com/Goliaith/helixcore.git
cd helixcore
python -m pip install .
```

```powershell
$env:HELIXCORE_HOME = "C:\tmp\my-project"
python -c "import helixcore; print(helixcore.__version__, helixcore.get_home())"
```

`configure(home=...)` after import moves task files and the keyword log. Set `HELIXCORE_HOME` before import when you also care about the session file path.

Python 3.10 or newer. pytest is optional and only used for `tests/`.

## What a session stores

| Call | File |
|---|---|
| `begin_governed_work` | `tasks/<slug>/current.json` — the opening sentence |
| `persist_decision` | `tasks/<slug>/<category>.json` — latest text in that category |
| `write_semantic_memory` | `semantic/<slug>/memories.jsonl` — append, with exact-text dedup |
| `perform_synaptogenesis` | `synaptic/synapses.jsonl` — one row per ordered pair |

Paths are under `$HELIXCORE_HOME/.grok/state/`.

A slug is a short token: letters, digits, hyphens, underscores, at most 60 characters, starting with a letter or digit. Put the sentence in the note, not the slug.

`semantic_search` scores one slug. Keyword overlap is three quarters of the score and recency is one quarter. Recency reaches zero around 90 days. Words of one or two letters are skipped.

`perform_synaptogenesis` links two slugs when their keyword sets overlap by at least 0.12. Each pass also adds 0.05 strength, capped at 1.0, to the five newest rows. `persist_decision` runs that pass twice. Modes `strong_standard` and `disciplined` run it once more from the opening turn. `list_synapses` returns at most 50 rows.

`record_phase_handoff` writes the session file only when that file already has an active session. `begin_governed_work` does not create one. `pulse_agent_health` reports health `ok` and zero sessions. `get_status_report` describes this local journal.

## Use

```python
import os
os.environ["HELIXCORE_HOME"] = "/tmp/my-project"

from helixcore import (
    begin_governed_work,
    persist_decision,
    write_semantic_memory,
    semantic_search,
    get_status_report,
)

begin_governed_work(
    "parser-work",
    "Implement the parser and its tests.",
    mode="light",
)
write_semantic_memory(
    "parser-work",
    "Chose recursive descent because the edge cases stayed readable.",
)
persist_decision(
    "parser-work",
    "Chose recursive descent because the edge cases stayed readable.",
    category="implementation",
)
for hit in semantic_search("parser-work", "recursive descent", limit=3):
    print(hit["score"], hit["content"])
print(get_status_report(friendly=True))
```

`examples/simple_claude_dogfood.py` runs the same start, a handoff call, a decision, and a pulse.

`list_golden_paths()` returns one entry: `begin_governed_work`.

## Layout

```
helixcore/
├── helixcore/
│   ├── golden_paths.py            # begin_governed_work
│   ├── local_semantic_memory.py   # keyword log and synapses
│   └── orchestrator_mcp/          # decisions, recall, pulse, status
├── docs/                          # June 2026 records
├── examples/
├── tests/test_memory_regression.py
├── pyproject.toml
└── LICENSE
```

## June 2026 records

These files describe machinery this tree no longer includes. Read them as history.

- [30-minute notes, rewritten for this tree](docs/HELIXCORE_IN_30_MINUTES.md)
- [Getting started](docs/GETTING_STARTED.md)
- [The one golden path](docs/golden_paths_quick_reference.md)
- [Stress test, June 2026](docs/ULTIMATE_STRESS_TEST.md)
- [Readiness summary, 7 June 2026](docs/HelixCore_Public_Readiness_Summary_2026-06-07.md)

`system-overview.html` is a June snapshot of a local machine. It is not the package.

## Authorship

Created and maintained by **MrSilhouette**. The name is locked in LICENSE, `pyproject.toml`, and this file. Commits use a `Signed-off-by: MrSilhouette ...` trailer. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT. See [LICENSE](LICENSE).

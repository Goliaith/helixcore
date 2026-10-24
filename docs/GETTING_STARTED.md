# Getting started

HelixCore is a local journal for agent sessions. The current API is the [README](../README.md). This page is the short install path.

## Install

Python 3.10 or newer.

```powershell
git clone https://github.com/Goliaith/helixcore.git
cd helixcore
python -m pip install .
```

## Choose a state folder before import

```powershell
$env:HELIXCORE_HOME = "C:\tmp\my-project"
python -c "import helixcore; print(helixcore.get_home())"
```

Writes go to `$HELIXCORE_HOME/.grok/state/`:

- `tasks/<slug>/<category>.json` — latest note in that category
- `semantic/<slug>/memories.jsonl` — keyword log
- `synaptic/synapses.jsonl` — links between slugs

## First calls

```python
import os
os.environ.setdefault("HELIXCORE_HOME", "/tmp/my-project")

from helixcore import begin_governed_work, write_semantic_memory, semantic_search

begin_governed_work("my-task", "What this session is for.", mode="light")
write_semantic_memory("my-task", "The decision, in one or two sentences.")
print(semantic_search("my-task", "decision", limit=3))
```

A slug is a short token of at most 60 characters. The sentence belongs in the note.

The longer walkthrough is [HelixCore in 30 minutes](HELIXCORE_IN_30_MINUTES.md).

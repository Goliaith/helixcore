# HelixCore in 30 minutes

A short walkthrough of the package on `main`. The [README](../README.md) is the reference. June 2026 writeups in this folder describe an older stack.

## 1. Install

```powershell
git clone https://github.com/Goliaith/helixcore.git
cd helixcore
python -m pip install .
$env:HELIXCORE_HOME = "C:\tmp\helixcore-demo"
```

Set the home before Python imports the package.

## 2. Open a task

```python
from helixcore import begin_governed_work, list_golden_paths

print(list_golden_paths())
begin_governed_work(
    "demo-notes",
    "Capture one real decision from today's work.",
    mode="light",
)
```

That writes `tasks/demo-notes/current.json` with the opening sentence. `mode="light"` skips the extra synapse pass on the turn itself. `persist_decision`, used below, still runs one pass.

## 3. Keep a keyword log

```python
from helixcore import write_semantic_memory, semantic_search

write_semantic_memory(
    "demo-notes",
    "Store session notes as JSONL and search them by keyword overlap plus recency.",
)
write_semantic_memory(
    "demo-notes",
    "A repeated sentence refreshes the old line instead of appending a copy.",
)
for hit in semantic_search("demo-notes", "keyword overlap", limit=2):
    print(round(hit["score"], 3), hit["content"])
```

Search looks at this slug only. There is no embedding index.

## 4. Save the latest decision

```python
from helixcore import persist_decision, read_local_memory

persist_decision(
    "demo-notes",
    "Use the keyword log for history and the category file for the latest decision.",
    category="decisions",
)
print(read_local_memory("demo-notes", "decisions"))
```

The category file keeps the latest text. The keyword line from step 3 is a separate call to `write_semantic_memory`.

## 5. Read it back

```python
from helixcore import disciplined_recall, get_status_report, pulse_agent_health

print(disciplined_recall("demo-notes"))
print(get_status_report(friendly=True))
print(pulse_agent_health())
```

`disciplined_recall` reads `current.json`, `decisions.json`, and `phases.json`. The pulse reports zero active sessions. `record_phase_handoff` updates a session file only when one already exists, and this walkthrough does not create one.

## 6. Point the next project at its own folder

Use another `HELIXCORE_HOME` for the next project. Task notes, the keyword log, and the synapse file stay inside that folder.

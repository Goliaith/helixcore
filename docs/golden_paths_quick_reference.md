# Golden path

The package exposes one golden path.

| Name | What it writes | When to use it |
|---|---|---|
| `begin_governed_work` | `tasks/<slug>/current.json` with the opening sentence | The start of a session |

```python
from helixcore import begin_governed_work, list_golden_paths

print(list_golden_paths())
begin_governed_work("my-task", "Opening focus for this session.", mode="light")
```

After that, the daily calls are `write_semantic_memory`, `persist_decision`, `semantic_search`, and `get_status_report`. See the [README](../README.md).

`record_phase_handoff` updates an existing session file. `begin_governed_work` does not create that file.

Modes are `light`, `standard`, `strong_standard`, and `disciplined`. `strong_standard` is the default. `strong_standard` and `disciplined` run synaptogenesis from the opening turn.

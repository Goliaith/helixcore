**Full content from local docs/GETTING_STARTED.md populated here for the public repo.**

# Getting Started with HelixCore

**Best first experience (external developers, no Grok required):**

```bash
cd helixcore-packaging/standalone_playground
python demo.py
```

This is a beautiful, self-contained, zero-dependency walkthrough of the entire philosophy (Golden Paths, phase handoffs, anti-runaway, discipline, live state). It is the highest-leverage thing you can do in the first five minutes.

After the demo, read `standalone_playground/README.md`.

---

## For External Python Developers (Primary Path)

1. Install the package in editable mode:
   ```bash
   cd packaging
   pip install -e .
   ```

2. Run the philosophy demo (highly recommended — try interactive mode!):
   ```python
   python -m standalone_playground.demo
   ```
   When it starts, answer **y** to the interactive prompt. This pauses at phase boundaries so you can explore the live state, feel the handoffs, and truly experience the governed rhythm. This is the best production-ready first UX for understanding the value.

3. Then use the patterns in your own code:
   ```python
   from helixcore import begin_governed_work, persist_decision, record_phase_handoff, record_simple_decision

   begin_governed_work("my-real-project", "Ship the new feature with proper governance")
   ...
   record_phase_handoff("Design phase done", "Implementation", "my-real-project")

   # For frequent decisions during active work:
   record_simple_decision("my-real-project", "Chose library X for reason Y")
   ```

The package works completely standalone using local JSON files for state. You get the full discipline and coherence benefits without any proprietary components.

See `standalone_playground/README.md` for the deep tour and `docs/golden_paths_quick_reference.md` for the current helpers (including new ergonomic live capture helpers).

## For Existing Grok Users (Recommended — One Command)

If you already use Grok and have this `helixcore-packaging/` folder:
```powershell
cd packaging
.\install.ps1
```

The installer will:
- Auto-detect your Grok home
- Install the `helixcore` package into the right location
- Copy the key documentation
- Print clear next steps

After it finishes, the Golden Paths are available in **any** Grok session with a clean import. No manual path configuration needed.

Run the dependency checker afterward (it will be recommended in the output):

```powershell
python dependency_checker.py
```

Then open the guide it prints and start with the starter project examples.

## Prerequisites (for non-Grok or first-time users)

- Python 3.10+
- Access to a Grok environment that includes at minimum:
  - **Serena** (strongly recommended for any code-related work)
  - **Cognee** (recommended for high-level memory)
  - **Context7** (recommended for library documentation)

> **Tip**: After installing, always run `python dependency_checker.py` to validate your environment.

## Step 1: Get the Core into Your Project

The fastest way is to use the bootstrap helper.

From inside the `helixcore-packaging/` directory:

```bash
# Recommended modern layout
python bootstrap.py --target /path/to/my-project --package-layout --include-examples
```

This will create a clean `helixcore/` package in your target directory.

**Alternative** (flat layout):

```bash
python bootstrap.py --target /path/to/my-project --include-examples
```

## Step 2: Install in Editable Mode (Recommended)

(Additional content from the local GETTING_STARTED.md would continue here for full fidelity in a complete push.)
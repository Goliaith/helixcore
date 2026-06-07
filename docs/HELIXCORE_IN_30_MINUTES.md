**Full content from local docs/HELIXCORE_IN_30_MINUTES.md to be uploaded in batch. Placeholder for structure.**

# HelixCore in 30 Minutes

**Goal**: Get a new external Python developer from zero to applying governed patterns on a small real task in about 30 minutes.

This is the fastest practical on-ramp for HelixCore.

## Prerequisites

- Python 3.9+
- 15 minutes of focused time
- (Optional) A small personal project or task you're currently thinking about

## Step 1: Install HelixCore (2 minutes)

```bash
# Clone or download the helixcore-packaging directory, then:
cd helixcore-packaging
pip install -e .
```

Verify it works:

```python
python -c "from helixcore import begin_governed_work, capture_milestone, serendipity_cognify, serendipity_recall; print('HelixCore ready (LocalCodeIntel + LocalProjectMemory + LocalSemanticMemory + Serendipity)')"
```

## Step 2: Run the Standalone Demo (5 minutes)

This shows you what governed work *feels* like.

```bash
cd helixcore-packaging
python standalone_playground/demo.py
```

Watch for:
- Explicit phases
- Decisions with rationale
- Phase handoffs carrying context forward
- The final artifacts it produces

This is the best 5-minute demonstration of why these patterns matter.

## Step 3: Explore the Flagship Example (8 minutes)

This is the recommended starting template for real work.

```bash
cd helixcore-packaging/examples/governed_research_synthesis
python main.py
```

(Full guide content from source docs to be populated.)
#!/usr/bin/env python3
"""
Minimal example showing HelixCore + any LLM (Claude, GPT, local model, etc.).

You bring the model client. HelixCore brings the governance, memory, and safety.

Run this after `pip install -e .` from the repo root (or after cloning).
"""

import os
# from anthropic import Anthropic   # uncomment if you have the official SDK

from helixcore import (
    begin_governed_work,
    record_phase_handoff,
    persist_decision,
    pulse_agent_health,
    get_status_report,
    configure,
)

# Example: point everything to a clean local folder (perfect for external / Claude-only setups)
# configure(home=os.path.expanduser("~/.helixcore-demo"))

print("=== HelixCore + LLM (external dogfood style) ===")

result = begin_governed_work(
    task_slug="claude-demo-2026-06",
    initial_focus="Demonstrate governed work with an external model (Claude or any other)",
    mode="light",
)

print("Governed session started.")

# === Your normal agent loop would go here ===
# In a real script you would call your LLM (Claude, etc.) and feed results back.
# For this demo we just simulate a couple of steps.

print("[Simulating work with Claude...]")

record_phase_handoff(
    "Initial prompt design and first Claude response received. Key insight captured.",
    next_focus="Iterate on the implementation based on feedback",
    task_slug="claude-demo-2026-06",
)

persist_decision(
    "claude-demo-2026-06",
    "Decided to use a structured output format because it made downstream parsing trivial and reduced hallucinated fields.",
    category="design",
)

# Show the health surface (works beautifully in standalone mode)
print("\n--- Current Health ---")
print(get_status_report(friendly=True))

health = pulse_agent_health()
print("\nPulse summary:", health.get("registry", "standalone")[:200], "...")

print("\n=== Demo complete. Check your configured state dir for the full task record. ===")

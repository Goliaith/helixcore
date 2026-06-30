#!/usr/bin/env python
"""HelixCore System Analysis Diagnostic Script
Run with: py E:\AI\Projects\helixcore\helixcore_diag.py
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, r"E:\AI\Projects\helixcore")
import helixcore as hc

# Use the dedicated analysis state dir
STATE_HOME = r"E:\AI\Projects\helixcore-local-state"
hc.configure(home=STATE_HOME)

print("=" * 60)
print("HELIXCORE SYSTEM ANALYSIS - LIVE DIAGNOSTIC")
print("=" * 60)
print(f"HelixCore version: {hc.__version__}")
print(f"Package: {hc.__file__}")
print(f"Configured state home: {STATE_HOME}")
print(f"Standalone mode: {hc.is_standalone_mode()}")
print()

# 1. Status & Health
print("--- 1. STATUS & HEALTH ---")
print(hc.get_status_report(friendly=True))
print()
ph = hc.pulse_agent_health()
print("Pulse:", json.dumps(ph, indent=2, default=str))
print()

# 2. Memory & Synaptogenesis (use a neutral task for stats)
print("--- 2. SEMANTIC MEMORY & SYNAPSES ---")
task = "helixcore-system-analysis"
try:
    stats = hc.get_semantic_stats(task)  # may vary
except Exception as e:
    stats = f"stats requires task or not available: {e}"
print("Semantic stats:", stats)

from helixcore.local_semantic_memory import list_synapses, list_semantic_memories

syns = list_synapses(limit=25)
print(f"Synapses (showing up to 25 of {len(list_synapses())}):")
for s in syns:
    print(f"  {s.get('from')} -> {s.get('to')} | str={s.get('strength',0):.2f} type={s.get('type')}")
print()

mems = list_semantic_memories("helixcore", limit=6)
print(f"Semantic memories (helixcore, {len(mems)} shown):")
for m in mems:
    content = (m.get("content") or str(m))[:110] if isinstance(m, dict) else str(m)[:110]
    print("  -", content)
print()

# 3. Governance primitives
print("--- 3. GOVERNANCE STATE ---")
try:
    orch = hc.get_orchestration_state(task)
    print("Orchestration state for task:", orch)
except Exception as e:
    print("get_orchestration_state err (expected if no prior):", str(e)[:120])

try:
    cps = hc.list_checkpoints(task)
    print("Checkpoints:", cps)
except Exception as e:
    print("list_checkpoints:", str(e)[:80])

try:
    harness = hc.get_evaluation_harness()
    print("Evaluation harness available:", bool(harness))
except Exception as e:
    print("Evaluation harness:", str(e)[:80])
print()

# 4. Local stack health
print("--- 4. LOCAL STACK ---")
try:
    overview = hc.get_code_overview(r"E:\AI\Projects\helixcore\helixcore")
    print("LocalCodeIntel overview (first 400 chars):")
    print(str(overview)[:400] if overview else "None")
except Exception as e:
    print("LocalCodeIntel:", e)
print()

# 5. Golden paths
print("--- 5. GOLDEN PATHS ---")
paths = hc.list_golden_paths()
for p in paths:
    print(f"  - {p.get('name')}: {p.get('recommended_for', '')[:60]}")
print()

print("=" * 60)
print("DIAGNOSTIC COMPLETE")
print("=" * 60)
print(f"Active sessions: {ph.get('active_session_count', 0)}")
print("System ready for governed work.")
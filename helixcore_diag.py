#!/usr/bin/env python
"""Local diagnostic for one machine's HelixCore state folder.

The package is the journal described in README.md.
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

# 3. Golden paths
print("--- 3. GOLDEN PATHS ---")
paths = hc.list_golden_paths()
for p in paths:
    print(f"  - {p.get('name')}: {p.get('recommended_for', '')[:60]}")
print()

print("=" * 60)
print("DIAGNOSTIC COMPLETE")
print("=" * 60)
print(f"Active sessions: {ph.get('active_session_count', 0)}")
print("System ready for governed work.")
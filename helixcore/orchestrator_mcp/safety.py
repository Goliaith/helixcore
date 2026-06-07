#!/usr/bin/env python3
"""
Safety / Loop Registry wrappers (extracted).

Thin shims that exec code against the ~/.grok/safety/loop_registry to register
orchestration sessions for the Loop Safety Registry (anti-runaway for long running work).

Part of HelixCore split.

Standalone / external friendly:
- If no external safety scripts are present (pure packaged use outside grok-build),
  operations become no-ops or return dummy values with a "standalone" flag.
- A minimal get_status_report is provided for basic friendly output.
- Call helixcore.configure(...) or set HELIXCORE_SAFETY_DIR env to point at
  a bundled or custom safety implementation.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Optional

# These will be provided by the main __init__.py namespace (SAFETY_DIR, run_python)
# We use runtime lookup to avoid import cycles during split.

def _get_safety_dir():
    import sys
    om = sys.modules.get(__name__.rsplit(".", 1)[0]) or sys.modules.get("orchestrator_mcp")
    if om and hasattr(om, "SAFETY_DIR"):
        return om.SAFETY_DIR
    # fallback
    home = Path.home()
    try:
        import os
        home = Path(os.environ.get("USERPROFILE") or os.environ.get("HOME") or Path.home())
    except Exception:
        pass
    return home / ".grok" / "safety"


def _run_python(code: str) -> str:
    import sys
    om = sys.modules.get(__name__.rsplit(".", 1)[0]) or sys.modules.get("orchestrator_mcp")
    if om and hasattr(om, "run_python"):
        return om.run_python(code)
    # ultimate fallback
    import subprocess
    try:
        res = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=10)
        return res.stdout + res.stderr
    except Exception as e:
        return str(e)


def register_orchestration_session(
    name: str,
    max_duration_hours: int = 8,
    summary: str = "",
) -> str:
    """Register this orchestration session with the safety system.

    In standalone/external mode (no external safety scripts), returns a
    deterministic dummy id and does not enforce registry. The caller can
    still use the returned value for heartbeats (which will be no-ops).
    """
    SAFETY_DIR = _get_safety_dir()
    # Check if the external registry actually exists
    reg_file = SAFETY_DIR / "loop_registry.py"
    if not reg_file.exists():
        # Standalone mode - generate a local id, no external enforcement
        import uuid
        dummy_id = f"standalone-{uuid.uuid4().hex[:12]}"
        # Optionally persist a lightweight local record
        try:
            local_record = SAFETY_DIR / "standalone_sessions.json"
            local_record.parent.mkdir(parents=True, exist_ok=True)
            data = {}
            if local_record.exists():
                data = json.loads(local_record.read_text(encoding="utf-8"))
            data[dummy_id] = {"name": name, "started_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(), "summary": summary}
            local_record.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception:
            pass
        return dummy_id

    code = f'''
import sys
sys.path.insert(0, r"{SAFETY_DIR}")
from loop_registry import register_orchestrator_session
sid = register_orchestrator_session(
    name={json.dumps(name)},
    max_duration_hours={max_duration_hours},
    summary={json.dumps(summary)}
)
print(sid)
'''
    return _run_python(code)


def heartbeat_orchestration(safety_id: str) -> bool:
    """Heartbeat the orchestration session in the safety registry.

    In standalone mode (dummy ids starting with 'standalone-'), this is a no-op
    that returns True to keep calling code happy.
    """
    if safety_id and safety_id.startswith("standalone-"):
        return True
    SAFETY_DIR = _get_safety_dir()
    reg_file = SAFETY_DIR / "loop_registry.py"
    if not reg_file.exists():
        return True  # standalone no-op
    code = f'''
import sys
sys.path.insert(0, r"{SAFETY_DIR}")
from loop_registry import heartbeat
print(heartbeat({json.dumps(safety_id)}))
'''
    out = _run_python(code)
    return "True" in out


def finish_orchestration(safety_id: str, reason: str = "completed") -> None:
    """Unregister the orchestration session.

    In standalone mode this is a no-op (the lightweight local record is left
    for the user to inspect if desired).
    """
    if safety_id and safety_id.startswith("standalone-"):
        return
    SAFETY_DIR = _get_safety_dir()
    reg_file = SAFETY_DIR / "loop_registry.py"
    if not reg_file.exists():
        return  # standalone no-op
    code = f'''
import sys
sys.path.insert(0, r"{SAFETY_DIR}")
from loop_registry import unregister_loop
unregister_loop({json.dumps(safety_id)}, {json.dumps(reason)})
print("unregistered")
'''
    _run_python(code)


def get_status_report(friendly: bool = True) -> str:
    """Minimal standalone-friendly status report.

    When the full external Loop Safety Registry (loop_guard / loop_registry)
    is not present, this returns a helpful message instead of failing.
    External users or pure-packaged deployments get basic visibility.
    """
    SAFETY_DIR = _get_safety_dir()
    reg_file = SAFETY_DIR / "loop_registry.py"
    if reg_file.exists():
        # Delegate to the real one if available (via the guard for friendly output)
        try:
            guard = SAFETY_DIR / "loop_guard.py"
            if guard.exists() and friendly:
                out = _run_python(f'''
import sys
sys.path.insert(0, r"{SAFETY_DIR}")
import loop_guard
# loop_guard re-execs the registry with "status"
print("Delegating to external loop_guard status...")
''')
                # Fallback to direct if guard doesn't give nice output
                if "Delegating" in out:
                    pass
            # Direct call to registry for status
            code = f'''
import sys
sys.path.insert(0, r"{SAFETY_DIR}")
from loop_registry import get_status_report
print(get_status_report(friendly={friendly}))
'''
            return _run_python(code).strip()
        except Exception as e:
            return f"External registry present but failed to query: {e}. Falling back to standalone view."

    # Pure standalone mode
    if friendly:
        return (
            "Great news — running in standalone / external packaged mode.\n\n"
            "**Safety status:** No external Loop Safety Registry detected (loop_guard/loop_registry not found in SAFETY_DIR).\n"
            "Local governance (anti-runaway primitives, budget checks, Help Mode, discipline enforcement) are still active inside this HelixCore package.\n\n"
            "**What this means for you:** You are using the portable helixcore library outside a full grok-build environment. "
            "Long-running work will not be centrally registered for runaway protection unless you point HELIXCORE_SAFETY_DIR or install the safety scripts. "
            "Core patterns (phase handoffs, memory glue, pulses, closed-loop self-improvement) work fully.\n\n"
            "To enable full registry: copy or symlink the safety/ directory from a grok-build installation, "
            "or set the HELIXCORE_SAFETY_DIR environment variable before importing helixcore.\n"
            "(This is the ideal state for many external / library-only use cases — full power with minimal host dependencies.)"
        )
    else:
        return json.dumps({
            "mode": "standalone",
            "registry": "unavailable",
            "note": "No external loop_registry. Local anti-runaway and governance features remain functional."
        }, indent=2)

__all__ = [
    "register_orchestration_session",
    "heartbeat_orchestration",
    "finish_orchestration",
    "get_status_report",
]
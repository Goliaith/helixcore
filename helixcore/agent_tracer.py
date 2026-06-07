#!/usr/bin/env python3
"""
Lightweight Agent Tracer for the unified ~/.grok platform.

Designed to be 2026 OTel GenAI semantic conventions compatible (gen_ai.* attributes)
while remaining zero-dependency and local-first.

Usage:
    from agent_tracer import tracer, trace_span, emit_span, complete_span

    with trace_span("llm_call", {"gen_ai.model.name": "gpt-4o"}, task_slug="my-project"):
        # do work
        ...

    span_id = emit_span("governance_gate", {"action": "..."}, task_slug="my-project")
    ...
    complete_span(span_id, {"allowed": True})
"""

import json
import os
import time
import uuid
from pathlib import Path
from datetime import datetime, timezone
from contextlib import contextmanager
from typing import Optional, Dict, Any

HOME = Path(os.environ.get("USERPROFILE") or os.environ.get("HOME") or Path.home())
TRACE_DIR = HOME / ".grok" / "state" / "traces"

class AgentTracer:
    """Core tracer with JSONL persistence and simple in-process span correlation."""

    def __init__(self):
        TRACE_DIR.mkdir(parents=True, exist_ok=True)
        self._active_spans: Dict[str, dict] = {}  # span_id -> span dict

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def start_span(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
        task_slug: Optional[str] = None,
        parent_id: Optional[str] = None,
    ) -> str:
        span_id = str(uuid.uuid4())
        trace_id = parent_id or str(uuid.uuid4())  # simple propagation for now

        span = {
            "span_id": span_id,
            "trace_id": trace_id,
            "parent_id": parent_id,
            "name": name,
            "timestamp_start": self._now_iso(),
            "task_slug": task_slug,
            "attributes": attributes or {},
            "status": "in_progress",
        }
        self._active_spans[span_id] = span
        return span_id

    def end_span(self, span_id: str, attributes: Optional[Dict[str, Any]] = None):
        if span_id not in self._active_spans:
            return

        span = self._active_spans[span_id]
        span["timestamp_end"] = self._now_iso()

        try:
            start = datetime.fromisoformat(span["timestamp_start"])
            end = datetime.fromisoformat(span["timestamp_end"])
            span["duration_ms"] = (end - start).total_seconds() * 1000
        except Exception:
            span["duration_ms"] = None

        if attributes:
            span["attributes"].update(attributes)
        span["status"] = "ok"

        # Persist to task-scoped JSONL
        task_slug = span.get("task_slug") or "default"
        trace_file = TRACE_DIR / f"{task_slug}.jsonl"
        try:
            with open(trace_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(span, ensure_ascii=False) + "\n")
        except Exception:
            pass  # never let tracing break the main flow

        del self._active_spans[span_id]

    @contextmanager
    def trace(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
        task_slug: Optional[str] = None,
    ):
        span_id = self.start_span(name, attributes, task_slug)
        try:
            yield span_id
        except Exception as e:
            self.end_span(span_id, {"error": str(e), "error.type": type(e).__name__})
            raise
        else:
            self.end_span(span_id)

# Global singleton for easy import
tracer = AgentTracer()

# Public convenience API (recommended for use in orchestrator_mcp (package) and skills)
def emit_span(name: str, attributes: Optional[Dict] = None, task_slug: Optional[str] = None, parent_id: Optional[str] = None) -> str:
    """Start a new span. Returns span_id for later completion."""
    return tracer.start_span(name, attributes, task_slug, parent_id)

def complete_span(span_id: str, attributes: Optional[Dict] = None):
    """End a span and persist it."""
    tracer.end_span(span_id, attributes)

@contextmanager
def trace_span(name: str, attributes: Optional[Dict] = None, task_slug: Optional[str] = None):
    """Context manager for clean tracing blocks."""
    with tracer.trace(name, attributes, task_slug) as sid:
        yield sid


# Optional: helper to load recent traces for a task (used by Guardian / pulse)
def get_recent_traces(task_slug: str, max_spans: int = 20) -> list:
    trace_file = TRACE_DIR / f"{task_slug}.jsonl"
    if not trace_file.exists():
        return []
    try:
        lines = trace_file.read_text(encoding="utf-8").strip().splitlines()
        spans = [json.loads(line) for line in lines[-max_spans:]]
        return spans
    except Exception:
        return []


# --- Simple Local Trace Viewer / Query Helpers (added as part of Gap #1) ---

def list_traces_for_task(task_slug: str, limit: int = 50) -> list:
    """Return a list of recent trace dicts for a given task_slug."""
    return get_recent_traces(task_slug, max_spans=limit)


def print_recent_traces(task_slug: str, limit: int = 10):
    """Pretty-print recent traces for a task_slug to the console (useful for debugging)."""
    traces = get_recent_traces(task_slug, max_spans=limit)
    if not traces:
        print(f"No traces found for task '{task_slug}'")
        return
    print(f"\n=== Recent Traces for {task_slug} (last {len(traces)}) ===")
    for t in traces:
        dur = t.get("duration_ms")
        dur_str = f"{dur:.1f}ms" if dur is not None else "N/A"
        print(f"[{t.get('timestamp_start', '')[:19]}] {t.get('name', 'unknown')} | {dur_str} | {t.get('status', '')}")
        if t.get("attributes"):
            print(f"    attrs: {t['attributes']}")
    print("=" * 50)

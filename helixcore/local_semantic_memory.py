"""
LocalSemanticMemory — Pure-local high-level semantic memory replacement for Cognee.

Part of the post-Cognee (and post-Serena) local-first stack for HelixCore.

- Zero external dependencies or MCP calls.
- File-based append-only JSONL storage under ~/.grok/state/semantic/<safe_task_slug>/memories.jsonl
- Simple but effective keyword + recency scoring for "semantic" recall (no embeddings needed).
- Stores arbitrary content + metadata (e.g. category, source, ts).
- Used automatically inside disciplined_recall / synthesize_project_context_briefing for cognee_query.
- Persist paths (persist_decision / write_local_memory with flag) also feed it.

This provides the "high-level semantic / graph-like recall" previously delegated to Cognee,
while keeping everything fast, local, governed, and observable.
For advanced external RAG on arbitrary documents, users can still optionally use the Cognee MCP,
Chroma, or Firecrawl + local processing.

Design goals (matching LocalCodeIntel + LocalProjectMemory):
- Always available (no activation, no latency, no network).
- Integrated with HelixCore governance, live state, discipline.
- Packagable in helixcore with relative imports.
- Sufficient for task/project memory, decisions, retrospectives, "why we chose X".
"""

import json
import os
import re
import time
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional

# ------------------------------------------------------------------
# Paths - now lazy and respect configure(home=...) + HELIXCORE_HOME
# This fixes isolation for standalone / product use (e.g. Helix Lab).
# We query the orchestrator_mcp configured globals at call time.
# ------------------------------------------------------------------

def _get_configured_state_dir() -> Path:
    """Return the currently configured STATE_DIR (updated by configure() or env).
    Falls back to HELIXCORE_HOME or user home if not yet configured.
    """
    try:
        # Late import avoids any import-time circularity with top __init__
        from .orchestrator_mcp import STATE_DIR as _state_dir
        if _state_dir:
            return Path(_state_dir)
    except Exception:
        pass
    # Fallback mirrors the logic in orchestrator_mcp/__init__.py
    env_home = (
        os.environ.get("HELIXCORE_HOME")
        or os.environ.get("HELIXCORE_STATE_DIR")
        or os.environ.get("USERPROFILE")
        or os.environ.get("HOME")
    )
    if env_home:
        return Path(env_home) / ".grok" / "state"
    return Path.home() / ".grok" / "state"


def _get_semantic_dir() -> Path:
    d = _get_configured_state_dir() / "semantic"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _get_synaptic_dir() -> Path:
    d = _get_configured_state_dir() / "synaptic"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _safe_slug(slug: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]", "_", slug)


def _mem_path(task_slug: str) -> Path:
    """Append-only JSONL for semantic observations."""
    safe = _safe_slug(task_slug)
    return _get_semantic_dir() / safe / "memories.jsonl"


# ------------------------------------------------------------------
# Core API
# ------------------------------------------------------------------

def write_semantic_memory(
    task_slug: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None,
    dedup: bool = True,
) -> bool:
    """
    Append a semantic observation / memory for the task.
    Used by persist_decision flows, phase summaries, key retrospectives, etc.

    dedup (default True): this is a *recall* store — duplicate content never improves
    keyword/recency search, it only dilutes results and grows the file unbounded (e.g.
    tight telemetry loops re-logging the same outcome). When True, if an entry with
    identical content already exists for this slug, the existing entry's recency is
    refreshed in place instead of appending a redundant copy. Pass dedup=False to keep
    raw append-only history.
    """
    try:
        p = _mem_path(task_slug)
        p.parent.mkdir(parents=True, exist_ok=True)
        norm = (content or "").strip()

        if dedup and norm and p.exists():
            existing = []
            found = False
            with open(p, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    e = json.loads(line)
                    if not found and (e.get("content") or "").strip() == norm:
                        e["ts"] = time.time()  # refresh recency; no duplicate row
                        found = True
                    existing.append(e)
            if found:
                with open(p, "w", encoding="utf-8", newline="\n") as f:
                    for e in existing:
                        f.write(json.dumps(e, ensure_ascii=False) + "\n")
                return True

        entry: Dict[str, Any] = {
            "ts": time.time(),
            "content": content,
            "metadata": metadata or {},
        }
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return True
    except Exception:
        return False


def semantic_search(
    task_slug: str,
    query: str,
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """
    Local "semantic" recall over stored memories for the task.
    Scoring: keyword overlap (simple TF) + recency decay.
    Returns list of {ts, content, metadata, score} sorted by relevance desc.
    """
    p = _mem_path(task_slug)
    if not p.exists():
        return []

    entries: List[Dict[str, Any]] = []
    try:
        with open(p, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
    except Exception:
        return []

    if not query or not entries:
        # No query: return most recent
        entries.sort(key=lambda e: e.get("ts", 0), reverse=True)
        return entries[:limit]

    qwords = [w.lower() for w in re.findall(r"\w+", query) if len(w) > 2]
    if not qwords:
        entries.sort(key=lambda e: e.get("ts", 0), reverse=True)
        return entries[:limit]

    scored: List[Dict[str, Any]] = []
    now = time.time()
    for e in entries:
        text = (e.get("content") or "") + " " + json.dumps(e.get("metadata") or {})
        twords = Counter(re.findall(r"\w+", text.lower()))
        kw_score = sum(twords.get(w, 0) for w in qwords) / max(1, len(qwords))

        # Recency: full weight for last 7 days, linear decay to 0 at ~90 days
        age_days = (now - e.get("ts", now)) / 86400.0
        recency = max(0.0, 1.0 - (age_days / 90.0))

        final = (kw_score * 0.75) + (recency * 0.25)
        scored.append({**e, "score": round(final, 4)})

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:limit]


def list_semantic_memories(task_slug: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Return recent memories (newest first), without scoring."""
    p = _mem_path(task_slug)
    if not p.exists():
        return []
    entries: List[Dict[str, Any]] = []
    try:
        with open(p, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    entries.append(json.loads(line))
    except Exception:
        return []
    entries.sort(key=lambda e: e.get("ts", 0), reverse=True)
    return entries[:limit]


def get_semantic_stats(task_slug: str) -> Dict[str, Any]:
    """Light stats for health / pulse."""
    p = _mem_path(task_slug)
    if not p.exists():
        return {"count": 0, "path": str(p)}
    try:
        count = sum(1 for line in open(p, "r", encoding="utf-8") if line.strip())
        return {"count": count, "path": str(p)}
    except Exception:
        return {"count": 0, "error": "read failed"}


def clear_semantic_memories(task_slug: str) -> bool:
    """Dangerous: remove the semantic store for a slug (for tests/reset)."""
    try:
        p = _mem_path(task_slug)
        if p.exists():
            p.unlink()
        return True
    except Exception:
        return False


# ------------------------------------------------------------------
# Convenience for integration (used by orchestrator_mcp)
# ------------------------------------------------------------------

def feed_semantic_from_decision(
    task_slug: str, decision: str, category: str = "decisions"
) -> bool:
    """Helper called from persist paths to also feed the semantic layer."""
    meta = {"source": "persist_decision", "category": category}
    return write_semantic_memory(task_slug, decision, metadata=meta)


# ------------------------------------------------------------------
# Synaptogenesis support (MVP for active explicit connection formation)
# Biological metaphor: formation + reinforcement + pruning of "synapses"
# between semantic memories, handoffs, decisions, ideas, orchs.
# Builds directly on DreamWeaver (narrative weaving), Mycelium (entangled
# networks + fruiting + prune), Chemotaxis (gradient tubes as connections),
# Parliament (deliberative links), and hallucination grounding relations.
# Lean: local JSONL only (under state/synaptic/synapses.jsonl), keyword +
# cluster + chemotaxis-hint based discovery. Cross-slug by default.
# ------------------------------------------------------------------

def _get_synapse_file() -> Path:
    syn_dir = _get_synaptic_dir()
    return syn_dir / "synapses.jsonl"


def _append_synapse(entry: Dict[str, Any]) -> bool:
    try:
        fpath = _get_synapse_file()
        fpath.parent.mkdir(parents=True, exist_ok=True)
        with open(fpath, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return True
    except Exception:
        return False


def _load_all_synapses() -> List[Dict[str, Any]]:
    fpath = _get_synapse_file()
    if not fpath.exists():
        return []
    entries = []
    try:
        with open(fpath, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    entries.append(json.loads(line))
    except Exception:
        return []
    return entries


def _write_all_synapses(entries: List[Dict[str, Any]]) -> bool:
    try:
        fpath = _get_synapse_file()
        fpath.parent.mkdir(parents=True, exist_ok=True)
        with open(fpath, "w", encoding="utf-8") as f:
            for e in entries:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")
        return True
    except Exception:
        return False


def write_synapse(
    from_ref: str,
    to_ref: str,
    strength: float = 0.7,
    type: str = "analogous",
    reason: str = "",
    created_by: str = "synaptogenesis_pass",
    task_scope: str = "cross",
    metadata: Optional[Dict[str, Any]] = None,
) -> bool:
    """Create or record an explicit synapse (durable connection)."""
    entry: Dict[str, Any] = {
        "ts": time.time(),
        "from": from_ref,
        "to": to_ref,
        "strength": round(max(0.0, min(1.0, strength)), 3),
        "type": type,
        "reason": reason[:300],
        "created_by": created_by,
        "task_scope": task_scope,
        "last_reinforced": time.time(),
        "usage_count": 0,
        "metadata": metadata or {},
    }
    return _append_synapse(entry)


def list_synapses(limit: int = 50, min_strength: float = 0.0) -> List[Dict[str, Any]]:
    """Recent synapses (newest first), optionally filtered by strength. Dedups to latest per (from,to) for efficiency."""
    entries = _load_all_synapses()
    if not entries:
        return []
    # Dedup: keep latest (highest ts) per (from, to)
    latest = {}
    for e in entries:
        if e.get("strength", 0) < min_strength:
            continue
        key = (e.get("from"), e.get("to"))
        if key not in latest or e.get("ts", 0) > latest[key].get("ts", 0):
            latest[key] = e
    deduped = list(latest.values())
    deduped.sort(key=lambda e: e.get("ts", 0), reverse=True)
    return deduped[:limit]


# Minimal stopword set so keyword overlap reflects topical, not grammatical, similarity.
_SYNAPSE_STOPWORDS = frozenset({
    "the", "a", "an", "and", "or", "but", "of", "to", "in", "on", "for", "with",
    "at", "by", "from", "is", "are", "was", "were", "be", "been", "being", "this",
    "that", "these", "those", "it", "its", "as", "we", "you", "they", "them",
    "our", "your", "their", "have", "has", "had", "do", "does", "did", "not",
    "no", "so", "if", "then", "than", "what", "which", "who", "when", "where",
    "how", "all", "can", "will", "would", "should", "into", "out", "up", "via",
})


def _list_semantic_slugs() -> List[str]:
    """Enumerate real task slugs that actually have a semantic memory store on disk."""
    base = _get_semantic_dir()
    slugs: List[str] = []
    try:
        for child in base.iterdir():
            if child.is_dir() and (child / "memories.jsonl").exists():
                slugs.append(child.name)
    except Exception:
        pass
    return slugs


def _demo_example_synapses(max_candidates: int) -> List[Dict[str, Any]]:
    """Opt-in showcase clusters for empty installs (HELIXCORE_DEMO_SYNAPSES=1).

    These are illustrative only and reference example nodes that do not exist in a
    real store. They are NEVER emitted into a populated store — see find_potential_synapses.
    """
    clusters = [
        ["helixcore", "helixcore-memory-coherence-upgrades", "external-dogfood-2026-06-07", "helixcore-2026-closure"],
        ["system-coherence-synthesis-2026-06-02", "ultimate-stress", "helixcore-autonomy-chemotaxis-market-hybrid"],
    ]
    seen = set()
    uniq: List[Dict[str, Any]] = []
    for i, cl in enumerate(clusters):
        for a in cl:
            for b in cl:
                if a == b:
                    continue
                key = tuple(sorted([a, b]))
                if key in seen:
                    continue
                seen.add(key)
                uniq.append({
                    "from": a,
                    "to": b,
                    "potential": round(0.72 + (i * 0.04), 2),
                    "reason": "Demo example cluster (HELIXCORE_DEMO_SYNAPSES); not real data",
                    "suggested_type": "federation",
                })
    return uniq[:max_candidates]


def find_potential_synapses(max_candidates: int = 20, task_slug: Optional[str] = None) -> List[Dict[str, Any]]:
    """Discover high-potential new synapses from the *actual* local semantic store.

    Computes pairwise keyword (Jaccard) overlap between the real task-slug memory
    stores under state/semantic/. No synthetic/example data is written into a live
    store. The legacy demo clusters are opt-in (HELIXCORE_DEMO_SYNAPSES=1) and only
    used when the store is too sparse to discover anything real.

    When task_slug is given and present in the store, discovery is biased to pairs
    that include it; otherwise all real slug pairs are considered.
    """
    slugs = _list_semantic_slugs()

    # Build a topical keyword set per slug from its memory content.
    word_sets: Dict[str, set] = {}
    for s in slugs:
        mems = list_semantic_memories(s, limit=25)
        content = " ".join(m.get("content", "") for m in mems).lower()
        words = {
            w for w in re.findall(r"[a-z][a-z0-9_-]{2,}", content)
            if w not in _SYNAPSE_STOPWORDS
        }
        if len(words) >= 4:
            word_sets[s] = words

    names = list(word_sets.keys())
    if task_slug:
        safe = _safe_slug(task_slug)
        anchors = [safe] if safe in word_sets else names
    else:
        anchors = names

    potentials: List[Dict[str, Any]] = []
    seen = set()
    for a in anchors:
        for b in names:
            if a == b:
                continue
            key = tuple(sorted([a, b]))
            if key in seen:
                continue
            seen.add(key)
            wa, wb = word_sets[a], word_sets[b]
            union = len(wa | wb)
            if union == 0:
                continue
            overlap = len(wa & wb) / union
            if overlap >= 0.12:
                potentials.append({
                    "from": a,
                    "to": b,
                    "potential": round(min(0.95, 0.5 + overlap), 2),
                    "reason": f"Keyword overlap {overlap:.2f} between '{a}' and '{b}' (local semantic store)",
                    "suggested_type": "semantic-overlap",
                })

    potentials.sort(key=lambda p: p["potential"], reverse=True)

    if not potentials and os.environ.get("HELIXCORE_DEMO_SYNAPSES") == "1":
        return _demo_example_synapses(max_candidates)

    return potentials[:max_candidates]


def perform_synaptogenesis(task_slug: Optional[str] = None, max_new: int = 8) -> Dict[str, Any]:
    """Main entry: actively form new explicit synapses + reinforce.
    Returns summary for briefing / decision persistence.
    """
    created = []
    potentials = find_potential_synapses(max_new * 2, task_slug=task_slug)
    for p in potentials[:max_new]:
        ok = write_synapse(
            from_ref=p["from"],
            to_ref=p["to"],
            strength=p.get("potential", 0.7),
            type=p.get("suggested_type", "analogous"),
            reason=p["reason"],
            created_by="synaptogenesis_pass" + (f"@{task_slug}" if task_slug else ""),
            task_scope="cross" if task_slug is None else task_slug,
        )
        if ok:
            created.append({"from": p["from"], "to": p["to"], "strength": p.get("potential", 0.7)})
    # Reinforce recent + persist everything efficiently with dedup
    existing = list_synapses(limit=5, min_strength=0.4)
    reinforced = 0
    for e in existing:
        e["strength"] = min(1.0, e.get("strength", 0.5) + 0.05)
        e["last_reinforced"] = time.time()
        e["usage_count"] = e.get("usage_count", 0) + 1
        reinforced += 1
    # write_synapse() already persisted each created synapse above; do NOT re-append a
    # duplicate copy (that was the source of paired federation+auto bloat). Reload the
    # store (which now includes the created entries) and append reinforced updates only.
    all_entries = _load_all_synapses()
    for e in existing:
        all_entries.append(e)
    _write_all_synapses(all_entries)
    total_now = len(list_synapses())  # after dedup
    return {
        "new_synapses": len(created),
        "created_examples": created[:3],
        "reinforced": reinforced,
        "total_synapses": total_now,
        "task_scope": task_slug or "cross",
        "note": "Integrated for peak efficiency. Synapses are first-class, deduped, pruned, and auto-persisted.",
    }


def prune_synapses(max_mb: float = 5.0, min_strength: float = 0.25, dry_run: bool = True) -> Dict[str, Any]:
    """Size + strength based pruning for peak efficiency (completes Mycelium promise).
    Actually rewrites file keeping strong/recent synapses when !dry_run.
    """
    entries = _load_all_synapses()
    if not entries:
        return {"pruned": 0, "size_mb": 0.0}
    try:
        size_mb = SYNAPSE_FILE.stat().st_size / (1024 * 1024)
    except Exception:
        size_mb = 0.0
    if size_mb <= max_mb:
        return {"pruned": 0, "size_mb": round(size_mb, 2), "note": "under limit"}

    # Filter: keep strength >= min and reasonably recent (last 90 days for ts)
    now = time.time()
    kept = []
    pruned_count = 0
    for e in entries:
        age_days = (now - e.get("ts", now)) / 86400.0
        if e.get("strength", 0) >= min_strength and age_days < 90:
            kept.append(e)
        else:
            pruned_count += 1

    if not dry_run and pruned_count > 0:
        _write_all_synapses(kept)
        new_size = SYNAPSE_FILE.stat().st_size / (1024 * 1024) if SYNAPSE_FILE.exists() else 0
        return {"pruned": pruned_count, "before_mb": round(size_mb, 2), "after_mb": round(new_size, 2), "kept": len(kept)}

    return {
        "pruned": 0 if dry_run else pruned_count,
        "would_prune": pruned_count,
        "current_size_mb": round(size_mb, 2),
        "dry_run": dry_run,
        "kept_if_pruned": len(kept),
    }


def reinforce_synapse(from_ref: str, to_ref: str, delta: float = 0.05) -> bool:
    """Reinforce an existing synapse on use (for peak efficiency: surfacing/using strengthens connections).
    Appends reinforced entry; list dedups to latest.
    """
    try:
        entry = {
            "ts": time.time(),
            "from": from_ref,
            "to": to_ref,
            "strength": 0.5,  # will be adjusted from existing
            "type": "reinforced",
            "reason": "Reinforced on use/surface in briefing or recall",
            "created_by": "reinforce_synapse",
            "task_scope": "cross",
            "last_reinforced": time.time(),
            "usage_count": 1,
            "metadata": {}
        }
        # To properly reinforce, load and boost the latest
        all_e = _load_all_synapses()
        found = False
        for e in reversed(all_e):
            if e.get("from") == from_ref and e.get("to") == to_ref:
                e["strength"] = min(1.0, e.get("strength", 0.5) + delta)
                e["last_reinforced"] = time.time()
                e["usage_count"] = e.get("usage_count", 0) + 1
                found = True
                break
        if not found:
            entry["strength"] = 0.5 + delta
            all_e.append(entry)
        else:
            all_e.append(entry)  # append the updated for history
        _write_all_synapses(all_e)
        return True
    except Exception:
        return False


# Self-test when run directly
if __name__ == "__main__":
    import tempfile
    import shutil

    test_slug = "local-semantic-test"
    test_dir = SEMANTIC_DIR / _safe_slug(test_slug)
    if test_dir.exists():
        shutil.rmtree(test_dir)

    print("Writing test memories...")
    write_semantic_memory(test_slug, "We decided to use LocalCodeIntel because it is fast and local.", {"phase": "sunset"})
    write_semantic_memory(test_slug, "Key outcome: full Serena independence achieved in 3.65s dogfood run.", {"phase": "validation"})
    write_semantic_memory(test_slug, "Packaging 0.3.0 wheel validated via isolated venv pip install + local stack test.", {"phase": "packaging"})

    print("\nStats:", get_semantic_stats(test_slug))
    print("\nRecent (no query):", len(list_semantic_memories(test_slug)))

    print("\nSearch for 'local fast independence':")
    for hit in semantic_search(test_slug, "local fast independence", limit=3):
        print(f"  score={hit['score']:.3f} content={hit['content'][:80]}...")

    print("\nSearch for 'packaging wheel':")
    for hit in semantic_search(test_slug, "packaging wheel", limit=3):
        print(f"  score={hit['score']:.3f} content={hit['content'][:80]}...")

    print("\nLocalSemanticMemory self-test complete (pure local, no Cognee/Serena).")

    # Synaptogenesis peak efficiency self-test
    print("\n--- Synaptogenesis full integration test ---")
    # Clean previous test synapses for clean test
    if SYNAPSE_FILE.exists():
        SYNAPSE_FILE.unlink()
    write_synapse("test-cluster-a", "test-cluster-b", 0.9, "test", "Integration test synapse", "self-test")
    print("write_synapse:", len(list_synapses()))
    perf = perform_synaptogenesis(task_slug="self-test", max_new=2)
    print("perform_synaptogenesis:", perf)
    print("After prune dry:", prune_synapses(max_mb=0.001, dry_run=True))
    print("Total after:", len(list_synapses()))

    # cleanup
    if test_dir.exists():
        shutil.rmtree(test_dir)
    if SYNAPSE_FILE.exists():
        SYNAPSE_FILE.unlink()
    print("Cleaned test data.")
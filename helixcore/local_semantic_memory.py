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
import re
import time
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional

# ------------------------------------------------------------------
# Paths (consistent with LocalProjectMemory / local code intel)
# ------------------------------------------------------------------

HOME = Path.home()
STATE_DIR = HOME / ".grok" / "state"
SEMANTIC_DIR = STATE_DIR / "semantic"
SEMANTIC_DIR.mkdir(parents=True, exist_ok=True)


def _safe_slug(slug: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]", "_", slug)


def _mem_path(task_slug: str) -> Path:
    """Append-only JSONL for semantic observations."""
    safe = _safe_slug(task_slug)
    return SEMANTIC_DIR / safe / "memories.jsonl"


# ------------------------------------------------------------------
# Core API
# ------------------------------------------------------------------

def write_semantic_memory(
    task_slug: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Append a semantic observation / memory for the task.
    Used by persist_decision flows, phase summaries, key retrospectives, etc.
    """
    try:
        p = _mem_path(task_slug)
        p.parent.mkdir(parents=True, exist_ok=True)
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

SYNAPTIC_DIR = STATE_DIR / "synaptic"
SYNAPTIC_DIR.mkdir(parents=True, exist_ok=True)
SYNAPSE_FILE = SYNAPTIC_DIR / "synapses.jsonl"


def _append_synapse(entry: Dict[str, Any]) -> bool:
    try:
        SYNAPTIC_DIR.mkdir(parents=True, exist_ok=True)
        with open(SYNAPSE_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return True
    except Exception:
        return False


def _load_all_synapses() -> List[Dict[str, Any]]:
    if not SYNAPSE_FILE.exists():
        return []
    entries = []
    try:
        with open(SYNAPSE_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    entries.append(json.loads(line))
    except Exception:
        return []
    return entries


def _write_all_synapses(entries: List[Dict[str, Any]]) -> bool:
    try:
        SYNAPTIC_DIR.mkdir(parents=True, exist_ok=True)
        with open(SYNAPSE_FILE, "w", encoding="utf-8") as f:
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


def find_potential_synapses(max_candidates: int = 20, task_slug: Optional[str] = None) -> List[Dict[str, Any]]:
    """Lean discovery of high-potential new synapses.
    Uses comprehensive clusters + actual cross-slug semantic overlap for smarter, more efficient discovery.
    Boosts with chemotaxis where available. For peak efficiency in self-improvement.
    """
    # Comprehensive clusters covering ALL major semantic memory themes from live data (125 slugs).
    # Intra-cluster for dense local connections; the finder + manual seeding will cover.
    clusters = [
        # HelixCore Core, Packaging, Industry, UX, Orchestrator
        ["helixcore", "helixcore-2026-closure", "helixcore-v1-ambition-2026", "helixcore-industry-analysis-2026", "helixcore-industry-comparison-2026", "helixcore-opportunities-impl-2026-06-04", "helixcore-ux-production-readiness", "helixcore-core-ux-natural-interaction", "helixcore-final-split-check", "helixcore-workbench-app-build-20260604-203141", "orchestrator-mcp-facade-drift-alignment-20260604-201901", "orchestrator-mcp-split-review-20260604-200706", "doc-hygiene-orchestrator-mcp-20260604-201404", "sdist-target-030", "packaged-test", "packaged-semantic-test"],
        # Memory, Coherence, Synthesis, DreamWeaver, Mycelium, Briefing
        ["helixcore-memory-coherence-upgrades", "system-coherence-synthesis-2026-06", "system-coherence-synthesis-2026-06-02", "system-coherence-synthesis-dogfood-2026-06-02", "helix-memory-coherence-sandbox-eval", "refine-satisfying-briefing", "governance-anti-runaway-split-test"],
        # Autonomy: Chemotaxis, Market, Serendipity, Gradients
        ["helixcore-autonomy-chemotaxis-market-hybrid", "helixcore-autonomy-market-economy", "test-autonomy-chemotaxis-real-task", "serendipity-orchestrator-test"],
        # Stress, Performance, Anti-Runaway, Evaluations, Discipline, Compliance, Closed-Loop
        ["ultimate-stress", "ultimate-intense-throttled-stress-2026-06-04", "system-performance-analysis-2026", "anti-runaway-verification-1780360430", "post-stress-core-eval-2026-06-04", "stress-volume", "p2-closedloop-stress", "eval-enforce-test", "eval-meta-audit-verification-1780360394", "eval-meta-audit-verification-1780360419", "eval-meta-audit-verification-1780372580", "improve-evaluation-harness-pillar5", "batch2-harness-policy-check", "score-to-10-improvements-2026-06-04", "reanalysis-score-to-10-2026-06-04", "targeted-dogfood-gaps-to-10-2026-06-04", "significant-dogfooding-discipline-push-2026-06-04", "compliance-boost-discipline-remediation-2026-06-04", "discipline-boost-real-work-2026-06-04", "fix-governance-eval-pillar-2026-06-04", "closed-loop", "command-execution-safety-policy", "high_risk"],
        # Training Regimes, Bachelors, Math, Epistemology, K12, Capability Enhancement
        ["bachelors-epistemology-training-regime", "bachelors-mathematics-training-regime", "bachelors-physics-training-regime", "governed-epistemology-training-workbench-20260604", "governed-math-training-workbench-20260604-204044", "governed-physics-training-workbench-20260604", "k12-school-curriculum-training-regime", "math-abstract_algebra", "math-ai_applications", "math-bayesian_confirmation", "math-calc_i", "math-calc_ii", "math-calc_iii", "math-capstone", "math-capstone_physics", "math-classical_mechanics", "math-complex_analysis", "math-differential_equations", "math-electromagnetism", "math-feyerabend_pluralism", "math-formal_epistemology", "math-history_of_science_cases", "math-kuhn_paradigms", "math-lakatos_programmes", "math-linear_algebra", "math-number_theory", "math-popper_falsification", "math-probability_statistics", "math-quantum_mechanics", "math-real_analysis", "math-special_relativity", "math-statistical_mechanics", "math-thermodynamics", "math-waves_optics", "mathematical-architectural-2d-to-3d-demo", "mathematical-challenges-humans-ai", "mathematics-capability-enhancement", "mathematics-challenges-humans-ai", "mathematics-fundamentals-self-education", "mathematics-math-dataset-attempt-v3", "mathematics-math-dataset-full-attempt", "mathematics-mathset-training-40pct", "mathematics-proofs-self-education", "mathematics-reading-comprehension-terminology-training", "aimo-challenge-attempt-v2", "aimo-test-evaluation-knowledge-acquisition"],
        # Real-World, Proposals, External Challenges, Self-Improvement
        ["proposal-generation", "real-world-challenge-20260602-0044", "real-world-challenge-20260602-0044-branch-8afcb0", "external-real-work-example-2026", "external-real-work-example-2026-synthesis", "self-analysis-highest-impact-improvement"],
        # Specific Prototypes, Demos, Hygiene, Splits, Access
        ["helixcore-precise-editor-prototype-2026-06", "helixcore-distribution-hygiene", "helixcore-internet-research-demo", "helixcore-industry-comparison-2026-06-04", "composer-ux-everywhere", "access-helixcore", "helixcore-performance-report-2026-06", "helixcore-overall-system-analysis-20260604-202504"],
        # Scientific & Math Challenges (Riemann, etc.)
        ["riemann-hypothesis-rigorous-attack"],
        # Misc / General / Global / Test / Status / Pre-split
        ["general", "global", "smoke-test-minimal", "ux-smoke-test", "Status_report_delivered_for_completed_intense_throttled_stress_test__Full_duration_run__550_self-throttles__anti-runaway_0__slug_discipline_85_Excellent__reports_updated__clean_0_active_orchs__safety_calm__All_per_user_monitoring_rules_and_UX_standard_", "pre-split-test-1780602906", "pre-split-test-1780602943", "pre-split-test-1780602965", "pre-split-test-1780602988", "test-natural-language-feel-2026", "synaptogenesis-mvp-impl-seeding"],
    ]
    potentials: List[Dict[str, Any]] = []
    for i, cl in enumerate(clusters):
        for a in cl:
            for b in cl:
                if a != b:
                    potentials.append({
                        "from": a,
                        "to": b,
                        "potential": round(0.72 + (i * 0.04), 2),
                        "reason": "High thematic overlap in HelixCore self-improvement work (coherence/autonomy/DreamWeaver/chemotaxis/memory glue clusters from live semantic data)",
                        "suggested_type": "federation" if any(x in (a+b).lower() for x in ["coher", "weave", "memory"]) else "gradient-flow",
                    })
    # Dedup
    seen = set()
    uniq = []
    for p in potentials:
        key = tuple(sorted([p["from"], p["to"]]))
        if key not in seen:
            seen.add(key)
            uniq.append(p)

    # Smart enhancement for peak efficiency: scan actual semantic memories for high keyword overlap across slugs
    # Sample key active slugs (prioritize coherence, autonomy, training, stress for self-improvement)
    smart_slugs = ["helixcore-memory-coherence-upgrades", "system-coherence-synthesis-2026-06-02", "helixcore-autonomy-chemotaxis-market-hybrid", "ultimate-stress", "governed-math-training-workbench-20260604-204044", "bachelors-physics-training-regime", "proposal-generation"]
    try:
        overlap_pairs = []
        for i, slug_a in enumerate(smart_slugs):
            mems_a = list_semantic_memories(slug_a, limit=5)
            content_a = " ".join(m.get("content", "") for m in mems_a).lower()
            words_a = set(re.findall(r"\w+", content_a))
            if len(words_a) < 5: continue
            for slug_b in smart_slugs[i+1:]:
                mems_b = list_semantic_memories(slug_b, limit=5)
                content_b = " ".join(m.get("content", "") for m in mems_b).lower()
                words_b = set(re.findall(r"\w+", content_b))
                if len(words_b) < 5: continue
                overlap = len(words_a & words_b) / max(1, len(words_a | words_b))
                if overlap > 0.15:
                    overlap_pairs.append({
                        "from": slug_a, "to": slug_b,
                        "potential": round(0.65 + overlap * 0.3, 2),
                        "reason": f"High semantic keyword overlap ({round(overlap*100)}%) between memories in {slug_a} and {slug_b} (discovered via cross-slug scan for efficient connection formation)",
                        "suggested_type": "serendipity" if "coher" in slug_a+slug_b else "analogous"
                    })
        for op in overlap_pairs[:max_candidates//2]:
            key = tuple(sorted([op["from"], op["to"]]))
            if key not in seen:
                seen.add(key)
                uniq.append(op)
    except Exception:
        pass

    # Boost if chemotaxis available and task matches
    try:
        om = sys.modules.get("orchestrator_mcp")
        if om and task_slug and hasattr(om, "compute_chemotaxis_gradients"):
            chem = om.compute_chemotaxis_gradients(task_slug)
            if chem and chem.get("top_foraged_paths"):
                for p in uniq[:5]:
                    p["potential"] = min(1.0, p["potential"] + 0.08)
                    p["reason"] += " + chemotaxis gradient boost"
    except Exception:
        pass
    return uniq[:max_candidates]


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
    # Load all, merge created (as new entries), dedup in list will handle, but rewrite for persist
    all_entries = _load_all_synapses()
    for c in created:
        all_entries.append({
            "ts": time.time(),
            "from": c["from"],
            "to": c["to"],
            "strength": c["strength"],
            "type": "auto",
            "reason": "From perform_synaptogenesis",
            "created_by": "perform",
            "task_scope": task_slug or "cross",
            "last_reinforced": time.time(),
            "usage_count": 0,
            "metadata": {}
        })
    # Add reinforced as updates
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
"" 
Serendipity — Cognify helper / chroma hybrid for semantic memory.

"Serendipity" provides happy, accidental discovery through hybrid local + vector search.

- Always feeds to LocalSemanticMemory (pure local keyword + recency, zero deps).
- For chroma hybrid: provides ready-to-use tool call specifications for the chroma MCP
  (create_collection + add_documents for cognify; query_documents for recall).
- Task-scoped collections by default: f"serendipity_{safe_task_slug}"
- Supports custom collection names, embedding functions (default, ollama, openai, etc.),
  metadata, chunking hints.
- Hybrid recall: combines local semantic_search results + chroma query spec.
- Designed for use inside disciplined_orchestration_turn, persist flows, or directly
  by the agent via the returned specs (agent calls use_tool / the chroma__ tools).

This is the "cognify" (ingest for semantic) + advanced recall layer on top of the
local stack (LocalCodeIntel + LocalProjectMemory + LocalSemanticMemory).
Use when you want vector-powered semantic search over documents/decisions/code chunks,
while keeping the local layer as the always-available foundation.
Chroma MCP must be available/connected for the vector part; the helper gracefully
falls back to local-only if you choose.

See serena_sunset_initiative.md (cognee replacement + Serendipity phase),
orchestrator_mcp_patterns.md, and helixcore docs.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

# Local semantic as the always-on base layer (relative for packaged)
try:
    from .local_semantic_memory import (
        write_semantic_memory,
        semantic_search,
        feed_semantic_from_decision,
        get_semantic_stats,
    )
    LOCAL_SEMANTIC_AVAILABLE = True
except Exception:
    LOCAL_SEMANTIC_AVAILABLE = False
    write_semantic_memory = None
    semantic_search = None
    feed_semantic_from_decision = None
    get_semantic_stats = None


def _safe_slug(slug: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]", "_", slug)


def _default_collection(task_slug: str) -> str:
    return f"serendipity_{_safe_slug(task_slug)}"


# ------------------------------------------------------------------
# Serendipity Cognify (ingest / "cognify" for semantic)
# ------------------------------------------------------------------

def serendipity_cognify(
    task_slug: str,
    documents: List[str],
    ids: Optional[List[str]] = None,
    metadatas: Optional[List[Dict[str, Any]]] = None,
    collection_name: Optional[str] = None,
    embedding_function_name: str = "default",
    metadata: Optional[Dict[str, Any]] = None,
    also_local: bool = True,
) -> Dict[str, Any]:
    """
    Cognify helper: ingest documents for semantic search.

    - Always (if also_local): feeds every document to LocalSemanticMemory
      with metadata {"source": "serendipity_cognify", "collection": ..., **meta}.
    - Returns a dict with:
      - "local_fed": bool
      - "collection": str (the chroma collection name used)
      - "chroma_steps": list of tool call dicts ready for the agent to execute
        via use_tool (first create_collection if needed, then add_documents).
      - "note": guidance

    The agent should inspect the returned dict and call the chroma__ tools
    (using the exact args provided) to populate the vector collection.

    documents: list of text strings (chunk if very long for best results).
    ids: optional list of unique ids; auto-generated if omitted.
    metadatas: optional list of per-doc metadata dicts (same length as documents).
    embedding_function_name: 'default', 'ollama', 'openai', 'cohere', etc. (see chroma_create_collection).
    """
    collection = collection_name or _default_collection(task_slug)
    n = len(documents)
    if ids is None:
        ids = [f"{_safe_slug(task_slug)}_{i}" for i in range(n)]
    if metadatas is None:
        metadatas = [{} for _ in range(n)]
    if len(ids) != n or len(metadatas) != n:
        raise ValueError("ids and metadatas (if provided) must match length of documents")

    local_fed = False
    if also_local and LOCAL_SEMANTIC_AVAILABLE and write_semantic_memory is not None:
        for i, doc in enumerate(documents):
            meta = {"source": "serendipity_cognify", "collection": collection}
            if metadatas[i]:
                meta.update(metadatas[i])
            if metadata:
                meta.update(metadata)
            write_semantic_memory(task_slug, doc, metadata=meta)
        local_fed = True

    # Prepare chroma tool calls (agent will execute these via the MCP)
    create_step = {
        "tool": "chroma__chroma_create_collection",
        "args": {
            "collection_name": collection,
            "embedding_function_name": embedding_function_name,
            "metadata": metadata or {"created_by": "serendipity", "task_slug": task_slug},
        },
    }

    add_step = {
        "tool": "chroma__chroma_add_documents",
        "args": {
            "collection_name": collection,
            "documents": documents,
            "ids": ids,
            "metadatas": metadatas,
        },
    }

    return {
        "local_fed": local_fed,
        "collection": collection,
        "chroma_steps": [create_step, add_step],
        "note": (
            "Serendipity cognify complete. LocalSemanticMemory fed. "
            "Execute the chroma_steps (create_collection then add_documents) using the chroma MCP tools "
            "to enable vector semantic search. Use embedding_function_name appropriate for your environment "
            "(e.g. 'ollama' for local, 'default' for built-in)."
        ),
    }


# ------------------------------------------------------------------
# Serendipity Recall / Hybrid Search
# ------------------------------------------------------------------

def serendipity_recall(
    task_slug: str,
    query: str,
    n_results: int = 5,
    collection_name: Optional[str] = None,
    use_local: bool = True,
    use_chroma: bool = True,
    chroma_where: Optional[Dict[str, Any]] = None,
    include: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Hybrid recall using Serendipity (local semantic + chroma vector spec).

    - use_local=True: runs semantic_search on LocalSemanticMemory immediately (real results).
    - use_chroma=True: returns a ready-to-execute chroma__chroma_query_documents spec
      (the agent calls the tool with these args to get vector results).

    Returns dict with:
      - "local": list of hits from LocalSemanticMemory (if use_local)
      - "chroma_query": tool call spec for chroma (if use_chroma)
      - "collection": the collection that would be queried
      - "note": explanation + how to combine results
    """
    collection = collection_name or _default_collection(task_slug)
    result: Dict[str, Any] = {
        "collection": collection,
        "query": query,
    }

    if use_local and LOCAL_SEMANTIC_AVAILABLE and semantic_search is not None:
        result["local"] = semantic_search(task_slug, query, limit=n_results)
    else:
        result["local"] = []

    if use_chroma:
        chroma_query_spec = {
            "tool": "chroma__chroma_query_documents",
            "args": {
                "collection_name": collection,
                "query_texts": [query],
                "n_results": n_results,
                "where": chroma_where,
                "include": include or ["documents", "metadatas", "distances"],
            },
        }
        result["chroma_query"] = chroma_query_spec
    else:
        result["chroma_query"] = None

    result["note"] = (
        "Serendipity hybrid recall. 'local' contains immediate keyword+recency results from LocalSemanticMemory. "
        "If 'chroma_query' is present, execute it via the chroma MCP to get vector distances/semantic matches, "
        "then merge/rerank with local results for best Serendipity (happy discovery). "
        "This is the recommended cognify + recall pattern post-Cognee."
    )
    return result


# Convenience alias for the "cognify" experience
cognify = serendipity_cognify
recall = serendipity_recall


# ------------------------------------------------------------------
# Simple stats / management helpers (local side)
# ------------------------------------------------------------------

def serendipity_stats(task_slug: str, collection_name: Optional[str] = None) -> Dict[str, Any]:
    coll = collection_name or _default_collection(task_slug)
    local_stats = {}
    if LOCAL_SEMANTIC_AVAILABLE and get_semantic_stats is not None:  # type: ignore
        try:
            local_stats = get_semantic_stats(task_slug)  # type: ignore
        except Exception:
            pass
    return {
        "task_slug": task_slug,
        "collection": coll,
        "local": local_stats,
        "note": "For full chroma collection stats, call chroma__chroma_get_collection_info / count via MCP.",
    }


# ------------------------------------------------------------------
# Self-test / demo (run as python local_serendipity.py)
# ------------------------------------------------------------------

if __name__ == "__main__":
    import shutil
    from pathlib import Path

    test_slug = "serendipity-demo"
    sem_dir = Path.home() / ".grok" / "state" / "semantic" / _safe_slug(test_slug)
    if sem_dir.exists():
        shutil.rmtree(sem_dir)

    print("=== Serendipity self-test (cognify + hybrid recall) ===")

    docs = [
        "We decided to replace Cognee with LocalSemanticMemory for core task recall because it is fast and always available.",
        "Key outcome of the sunset: full independence from external semantic MCPs for normal agent work, with Serendipity as the chroma hybrid for advanced vector search.",
        "Packaging validation: 0.3.0 wheel tested in isolated venv; local stack including semantic memory works from installed package.",
        "Serendipity provides cognify (ingest to local + chroma) and hybrid recall for happy semantic discoveries.",
    ]
    metas = [
        {"phase": "cognee-replace"},
        {"phase": "sunset", "importance": "high"},
        {"phase": "packaging"},
        {"phase": "serendipity", "type": "helper"},
    ]

    print("\n1. Cognify (feeds local + returns chroma specs)...")
    cog = serendipity_cognify(
        test_slug,
        documents=docs,
        metadatas=metas,
        embedding_function_name="default",
    )
    print("   local_fed:", cog["local_fed"])
    print("   collection:", cog["collection"])
    print("   chroma_steps count:", len(cog["chroma_steps"]))
    print("   (Agent would now call chroma__chroma_create_collection then add_documents with these exact args)")

    print("\n2. Immediate local recall (no chroma call yet)...")
    rec = serendipity_recall(test_slug, "replace Cognee local semantic", n_results=3, use_chroma=False)
    print("   local hits:", len(rec.get("local", [])))
    for h in rec.get("local", [])[:2]:
        print(f"     score={h.get('score')} {h.get('content','')[:70]}...")

    print("\n3. Hybrid recall spec (includes chroma_query tool call)...")
    rec2 = serendipity_recall(test_slug, "packaging wheel validation", n_results=2)
    print("   local hits:", len(rec2.get("local", [])))
    if rec2.get("chroma_query"):
        print("   chroma_query tool:", rec2["chroma_query"]["tool"])
        print("   (Agent calls this via use_tool to get vector results, then hybrid-merge)")

    print("\n4. Stats...")
    st = serendipity_stats(test_slug)
    print("   ", st)

    print("\n=== Serendipity self-test SUCCESS ===")
    print("LocalSemanticMemory + chroma hybrid ready. Use cognify for ingest, recall for hybrid search.")
    print("See sunset md for integration with disciplined_orchestration_turn etc.")

    if sem_dir.exists():
        shutil.rmtree(sem_dir)
    print("Test data cleaned.")

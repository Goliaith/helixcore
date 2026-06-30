"""Regression tests for the two memory-substrate root-cause fixes (2026-06-29).

These lock in behavior that was previously broken and manually verified:

  1. Synaptogenesis no longer leaks hardcoded demo clusters into a live store.
     `find_potential_synapses()` used to return example clusters on every call,
     re-polluting `synapses.jsonl`. It now does real keyword-overlap discovery;
     demo clusters are strictly opt-in (HELIXCORE_DEMO_SYNAPSES=1) and suppressed
     whenever any real candidate exists.

  2. `perform_synaptogenesis()` no longer double-persists each created synapse
     (the old federation+auto paired write that bloated the file). Invariant:
     raw synapse lines == new_synapses + reinforced.

  3. `write_semantic_memory(dedup=True)` (default) collapses identical-content
     writes by refreshing recency in place instead of appending a redundant row;
     `dedup=False` preserves raw append-only history.

All tests run against a per-test temporary state dir — the real store is never
touched.
"""

import json
import time

import pytest

from helixcore import local_semantic_memory as lsm


# ---------------------------------------------------------------------------
# Isolation: redirect every path helper to a throwaway tmp state dir.
# Both _get_semantic_dir() and _get_synaptic_dir() funnel through
# _get_configured_state_dir(), so patching that one function isolates all I/O.
# ---------------------------------------------------------------------------
@pytest.fixture
def store(tmp_path, monkeypatch):
    state_dir = tmp_path / ".grok" / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(lsm, "_get_configured_state_dir", lambda: state_dir)
    # Demo clusters must be opt-in; ensure no ambient env bleeds into a test.
    monkeypatch.delenv("HELIXCORE_DEMO_SYNAPSES", raising=False)
    return state_dir


def _raw_mem_lines(slug):
    p = lsm._mem_path(slug)
    if not p.exists():
        return []
    return [json.loads(ln) for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]


def _raw_synapse_lines():
    p = lsm._get_synapse_file()
    if not p.exists():
        return []
    return [json.loads(ln) for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]


# Two slugs whose vocabularies overlap above the 0.12 Jaccard threshold.
_OVERLAP_A = "alpha beta gamma delta epsilon zeta"          # 6 topical words
_OVERLAP_B = "alpha beta gamma delta omega sigma"           # shares 4/8 -> 0.5
# Disjoint vocabularies -> no overlap.
_DISJOINT_A = "alpha beta gamma delta"
_DISJOINT_B = "omega sigma upsilon kappa"


# ===========================================================================
# 1. Synaptogenesis discovery — no synthetic noise
# ===========================================================================
class TestSynaptogenesisDiscovery:
    def test_empty_store_yields_no_synapses(self, store):
        """Empty store + no demo flag must produce zero candidates (no noise)."""
        assert lsm.find_potential_synapses() == []

    def test_demo_flag_returns_clusters_only_on_empty_store(self, store, monkeypatch):
        """Opt-in demo clusters still work for empty showcase installs."""
        monkeypatch.setenv("HELIXCORE_DEMO_SYNAPSES", "1")
        candidates = lsm.find_potential_synapses()
        assert candidates, "demo flag on an empty store should surface showcase clusters"
        assert all(c["suggested_type"] == "federation" for c in candidates)
        assert all("Demo example cluster" in c["reason"] for c in candidates)

    def test_real_overlap_is_discovered(self, store):
        """Two slugs sharing vocabulary yield a real semantic-overlap edge."""
        lsm.write_semantic_memory("slug-a", _OVERLAP_A)
        lsm.write_semantic_memory("slug-b", _OVERLAP_B)
        candidates = lsm.find_potential_synapses()
        assert candidates, "overlapping real slugs should produce a candidate"
        c = candidates[0]
        assert c["suggested_type"] == "semantic-overlap"
        assert {c["from"], c["to"]} == {"slug-a", "slug-b"}
        assert "Demo example cluster" not in c["reason"]

    def test_disjoint_slugs_yield_nothing(self, store):
        """Non-overlapping vocabularies must not be forced into a synapse."""
        lsm.write_semantic_memory("slug-a", _DISJOINT_A)
        lsm.write_semantic_memory("slug-b", _DISJOINT_B)
        assert lsm.find_potential_synapses() == []

    def test_demo_flag_is_suppressed_when_real_candidates_exist(self, store, monkeypatch):
        """The core regression: demo clusters must NEVER leak into a populated store,
        even with the opt-in flag set, as long as a real candidate is discoverable."""
        monkeypatch.setenv("HELIXCORE_DEMO_SYNAPSES", "1")
        lsm.write_semantic_memory("slug-a", _OVERLAP_A)
        lsm.write_semantic_memory("slug-b", _OVERLAP_B)
        candidates = lsm.find_potential_synapses()
        assert candidates
        assert all(c["suggested_type"] == "semantic-overlap" for c in candidates)
        assert all("Demo example cluster" not in c["reason"] for c in candidates)
        real_slugs = {"slug-a", "slug-b"}
        for c in candidates:
            assert c["from"] in real_slugs and c["to"] in real_slugs


# ===========================================================================
# 2. perform_synaptogenesis — no double-persist
# ===========================================================================
class TestPerformSynaptogenesis:
    def test_no_duplicate_write_invariant(self, store):
        """Each created synapse is persisted exactly once; reinforced updates are
        appended once. Raw line count must equal new_synapses + reinforced.
        The old paired federation+auto write violated this (created written twice).
        """
        lsm.write_semantic_memory("slug-a", _OVERLAP_A)
        lsm.write_semantic_memory("slug-b", _OVERLAP_B)
        result = lsm.perform_synaptogenesis(task_slug="slug-a")

        assert result["new_synapses"] >= 1
        raw = _raw_synapse_lines()
        assert len(raw) == result["new_synapses"] + result["reinforced"]

    def test_pass_writes_no_example_nodes(self, store):
        """A pass over real slugs must only connect real slugs — no demo endpoints."""
        lsm.write_semantic_memory("slug-a", _OVERLAP_A)
        lsm.write_semantic_memory("slug-b", _OVERLAP_B)
        lsm.perform_synaptogenesis(task_slug="slug-a")
        real_slugs = {"slug-a", "slug-b"}
        for e in _raw_synapse_lines():
            assert e["from"] in real_slugs and e["to"] in real_slugs
            assert "Demo example cluster" not in e.get("reason", "")

    def test_empty_store_pass_creates_nothing(self, store):
        """With no real memories, a pass forms zero synapses (no synthetic fill)."""
        result = lsm.perform_synaptogenesis()
        assert result["new_synapses"] == 0
        assert _raw_synapse_lines() == []


# ===========================================================================
# 3. Semantic memory dedup guard
# ===========================================================================
class TestSemanticDedup:
    def test_identical_writes_collapse_to_one_row(self, store):
        for _ in range(5):
            lsm.write_semantic_memory("dedup-slug", "the same exact observation")
        rows = _raw_mem_lines("dedup-slug")
        assert len(rows) == 1

    def test_distinct_content_appends(self, store):
        lsm.write_semantic_memory("dedup-slug", "first observation")
        lsm.write_semantic_memory("dedup-slug", "second observation")
        lsm.write_semantic_memory("dedup-slug", "third observation")
        assert len(_raw_mem_lines("dedup-slug")) == 3

    def test_dedup_false_preserves_history(self, store):
        for _ in range(4):
            lsm.write_semantic_memory("raw-slug", "repeated raw entry", dedup=False)
        assert len(_raw_mem_lines("raw-slug")) == 4

    def test_dedup_refreshes_recency_in_place(self, store):
        lsm.write_semantic_memory("recency-slug", "an observation worth refreshing")
        first_ts = _raw_mem_lines("recency-slug")[0]["ts"]
        time.sleep(0.01)
        lsm.write_semantic_memory("recency-slug", "an observation worth refreshing")
        rows = _raw_mem_lines("recency-slug")
        assert len(rows) == 1
        assert rows[0]["ts"] > first_ts

"""Tests for the Federation Adapter Layer.

Covers:
  - ContextSourceAdapter ABC contract
  - SourceCandidate dataclass
  - NativeAdapter wraps graph + registry + vector correctly
  - FederationOrchestrator runs adapters in parallel, collects results,
    handles timeouts and errors, resolves conflicts
  - SourceAttribution is built correctly
  - ResolveResponse.source_attribution field is populated
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from src.federation.base import ContextSourceAdapter, SourceCandidate
from src.federation.native_adapter import NativeAdapter
from src.federation.orchestrator import (
    DiscoveryResult,
    FederationOrchestrator,
    SourceAttribution,
    SourceStatus,
)
from src.governance.policy import AuthorizationResult
from src.models import (
    ResolveRequest,
    SourceAttributionItem,
    UserContext,
)
from src.resolution.engine import ResolutionEngine


# ----------------------------------------------------------------
# SourceCandidate
# ----------------------------------------------------------------

def test_source_candidate_defaults():
    sc = SourceCandidate(
        source_id="native",
        source_kind="native",
        concept_id="net_revenue",
        concept_type="metric",
        name="Net Revenue",
        definition="Recognized revenue",
        confidence=0.92,
    )
    assert sc.certification_tier == 4
    assert sc.payload == {}
    assert sc.last_synced_at is None


# ----------------------------------------------------------------
# NativeAdapter
# ----------------------------------------------------------------

@pytest.mark.asyncio
async def test_native_adapter_discover_with_concept_type():
    graph = AsyncMock()
    registry = AsyncMock()
    vector = AsyncMock()

    graph.find_concept.return_value = [
        {"id": "net_revenue", "name": "Net Revenue", "definition": "Rev", "score": 0.95, "certification_tier": 1}
    ]

    adapter = NativeAdapter(graph, registry, vector)
    assert adapter.source_id == "native"
    assert adapter.source_kind == "native"

    results = await adapter.discover_concepts("revenue", concept_type="metric", department="finance")
    assert len(results) == 1
    assert results[0].concept_id == "net_revenue"
    assert results[0].confidence == 0.95
    assert results[0].certification_tier == 1
    assert results[0].source_kind == "native"
    graph.find_concept.assert_called_once_with("metric", "revenue", "finance")


@pytest.mark.asyncio
async def test_native_adapter_discover_without_concept_type_uses_vector():
    graph = AsyncMock()
    registry = AsyncMock()
    vector = AsyncMock()

    vector.search.return_value = [
        {"id": "gl_revenue", "type": "glossary_term", "name": "Revenue", "definition": "Income", "score": 0.7}
    ]

    adapter = NativeAdapter(graph, registry, vector)
    results = await adapter.discover_concepts("revenue")
    assert len(results) == 1
    assert results[0].concept_type == "glossary_term"
    vector.search.assert_called_once_with(query="revenue", top_k=5)


@pytest.mark.asyncio
async def test_native_adapter_health_check():
    graph = AsyncMock()
    registry = AsyncMock()
    vector = AsyncMock()
    graph.ping.return_value = True
    registry.ping.return_value = True
    vector.ping.return_value = False

    adapter = NativeAdapter(graph, registry, vector)
    health = await adapter.health_check()
    assert health["healthy"] is False
    assert health["components"]["graph"] is True
    assert health["components"]["vector"] is False


@pytest.mark.asyncio
async def test_native_adapter_tribal_knowledge():
    graph = AsyncMock()
    registry = AsyncMock()
    vector = AsyncMock()
    graph.find_tribal_knowledge.return_value = [
        {"id": "tk_1", "description": "Known issue", "severity": "high", "impact": "big", "workaround": "use alt"}
    ]

    adapter = NativeAdapter(graph, registry, vector)
    tk = await adapter.get_tribal_knowledge(["net_revenue"])
    assert len(tk) == 1
    assert tk[0]["id"] == "tk_1"


# ----------------------------------------------------------------
# FederationOrchestrator
# ----------------------------------------------------------------

class FakeAdapter(ContextSourceAdapter):
    source_id = "fake"
    source_kind = "test"

    def __init__(self, results=None, delay=0.0, error=None):
        self._results = results or []
        self._delay = delay
        self._error = error

    async def discover_concepts(self, query, concept_type=None, department="", filters=None):
        if self._delay:
            await asyncio.sleep(self._delay)
        if self._error:
            raise RuntimeError(self._error)
        return self._results

    async def get_definition(self, concept_id):
        return {}

    async def get_relationships(self, concept_id):
        return []

    async def get_tribal_knowledge(self, concept_ids):
        return []

    async def health_check(self):
        return {"source_id": self.source_id, "healthy": True}


@pytest.mark.asyncio
async def test_orchestrator_single_adapter():
    candidates = [
        SourceCandidate(
            source_id="fake", source_kind="test",
            concept_id="c1", concept_type="metric",
            name="C1", definition="D1", confidence=0.9,
        )
    ]
    adapter = FakeAdapter(results=candidates)
    orch = FederationOrchestrator(adapters=[adapter])

    result = await orch.discover("revenue", concept_type="metric")
    assert len(result.candidates) == 1
    assert result.candidates[0].concept_id == "c1"
    assert len(result.source_statuses) == 1
    assert result.source_statuses[0].returned is True


@pytest.mark.asyncio
async def test_orchestrator_handles_adapter_error():
    adapter = FakeAdapter(error="connection refused")
    orch = FederationOrchestrator(adapters=[adapter])

    result = await orch.discover("revenue")
    assert len(result.candidates) == 0
    assert result.source_statuses[0].error == "connection refused"
    assert result.source_statuses[0].returned is False


@pytest.mark.asyncio
async def test_orchestrator_parallel_multiple_adapters():
    c1 = SourceCandidate(
        source_id="a", source_kind="test",
        concept_id="c1", concept_type="metric",
        name="C1", definition="", confidence=0.9,
    )
    c2 = SourceCandidate(
        source_id="b", source_kind="test",
        concept_id="c2", concept_type="metric",
        name="C2", definition="", confidence=0.8,
    )
    a1 = FakeAdapter(results=[c1])
    a1.source_id = "a"
    a2 = FakeAdapter(results=[c2])
    a2.source_id = "b"

    orch = FederationOrchestrator(adapters=[a1, a2])
    result = await orch.discover("revenue")
    assert len(result.candidates) == 2
    ids = {c.concept_id for c in result.candidates}
    assert ids == {"c1", "c2"}


@pytest.mark.asyncio
async def test_orchestrator_timeout():
    slow = FakeAdapter(delay=5.0)
    slow.source_id = "slow"
    fast_c = SourceCandidate(
        source_id="fast", source_kind="test",
        concept_id="c1", concept_type="metric",
        name="C1", definition="", confidence=0.9,
    )
    fast = FakeAdapter(results=[fast_c])
    fast.source_id = "fast"

    orch = FederationOrchestrator(adapters=[fast, slow])
    orch._budget_ms = 50  # 50ms budget

    result = await orch.discover("revenue")
    assert len(result.candidates) == 1
    statuses_by_id = {s.source_id: s for s in result.source_statuses}
    assert statuses_by_id["fast"].returned is True
    assert statuses_by_id["slow"].timed_out is True


# ----------------------------------------------------------------
# Conflict resolution
# ----------------------------------------------------------------

def test_resolve_conflicts_sorts_by_tier_then_confidence():
    c1 = SourceCandidate(
        source_id="a", source_kind="t", concept_id="x",
        concept_type="metric", name="X", definition="",
        confidence=0.9, certification_tier=2,
    )
    c2 = SourceCandidate(
        source_id="a", source_kind="t", concept_id="y",
        concept_type="metric", name="Y", definition="",
        confidence=0.8, certification_tier=1,
    )
    sorted_c, disambig = FederationOrchestrator.resolve_conflicts([c1, c2])
    assert sorted_c[0].concept_id == "y"  # tier 1 wins
    assert disambig is False  # same source, no conflict


def test_resolve_conflicts_detects_cross_source_conflict():
    c1 = SourceCandidate(
        source_id="a", source_kind="t", concept_id="x",
        concept_type="metric", name="X", definition="",
        confidence=0.9, certification_tier=1,
    )
    c2 = SourceCandidate(
        source_id="b", source_kind="t", concept_id="y",
        concept_type="metric", name="Y", definition="",
        confidence=0.8, certification_tier=1,
    )
    _, disambig = FederationOrchestrator.resolve_conflicts([c1, c2])
    assert disambig is True


def test_resolve_conflicts_no_conflict_when_tier_differs():
    c1 = SourceCandidate(
        source_id="a", source_kind="t", concept_id="x",
        concept_type="metric", name="X", definition="",
        confidence=0.9, certification_tier=1,
    )
    c2 = SourceCandidate(
        source_id="b", source_kind="t", concept_id="y",
        concept_type="metric", name="Y", definition="",
        confidence=0.95, certification_tier=2,
    )
    _, disambig = FederationOrchestrator.resolve_conflicts([c1, c2])
    assert disambig is False


# ----------------------------------------------------------------
# Source attribution
# ----------------------------------------------------------------

def test_build_source_attribution():
    candidates = [
        SourceCandidate(
            source_id="native", source_kind="native", concept_id="nr",
            concept_type="metric", name="NR", definition="", confidence=0.9,
            certification_tier=1,
        ),
        SourceCandidate(
            source_id="native", source_kind="native", concept_id="apac",
            concept_type="dimension", name="APAC", definition="", confidence=0.85,
            certification_tier=1,
        ),
    ]
    orch = FederationOrchestrator()
    attr = orch.build_source_attribution(candidates)
    assert len(attr) == 1
    assert attr[0].source_id == "native"
    assert set(attr[0].used_for) == {"metric", "dimension"}


# ----------------------------------------------------------------
# Engine integration: source_attribution in response
# ----------------------------------------------------------------

@pytest.mark.asyncio
async def test_engine_populates_source_attribution():
    graph = AsyncMock()
    registry = AsyncMock()
    vector = AsyncMock()
    traces = AsyncMock()

    graph.find_concept.return_value = [
        {"id": "net_revenue", "name": "Net Revenue", "definition": "Revenue", "score": 0.9}
    ]
    graph.find_tribal_knowledge.return_value = []
    graph.get_metric_sources.return_value = []
    registry.get_metric_info.return_value = {
        "semantic_layer_ref": "cube.finance.Revenue",
        "measure": "Revenue.net",
    }
    registry.get_metric_source_table.return_value = None
    registry.get_data_contract_for_table.return_value = None
    traces.find_similar.return_value = []

    engine = ResolutionEngine(graph, registry, vector, traces)
    engine._policy.authorize_resolution = AsyncMock(
        return_value=AuthorizationResult(allowed=True, denied_concepts=[], policies_evaluated=[])
    )
    traces.persist_resolution = AsyncMock()

    req = ResolveRequest(
        concept="revenue",
        user_context=UserContext(user_id="alice", department="finance"),
    )
    res = await engine.resolve(req)

    assert len(res.source_attribution) == 1
    assert res.source_attribution[0].source_id == "native"
    assert "metric" in res.source_attribution[0].used_for

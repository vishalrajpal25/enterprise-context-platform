"""Tests for precedent corrections applied as hard overrides.

Covers:
  - PrecedentEngine.find_precedents lifts structured corrections into
    Precedent.correction.
  - PrecedentEngine.compute_overrides filters by similarity floor,
    department match, and active concept_type.
  - ResolutionEngine.resolve swaps the resolved concept, sets confidence
    to 1.0 for the overridden concept, and records a DAG step.
  - Conflicting corrections (same concept_type, different targets) yield
    status == "disambiguation_required" with both candidates visible.
  - GOLDEN: resolve query X, mark as corrected with structured details,
    resolve similar query Y, assert correction was applied.
"""
from __future__ import annotations

import json
from unittest.mock import AsyncMock

import pytest

from src.governance.policy import AuthorizationResult
from src.models import (
    CorrectionDetail,
    ParsedIntent,
    Precedent,
    PrecedentCorrection,
    ResolveRequest,
    UserContext,
)
from src.resolution.engine import ResolutionEngine
from src.resolution.precedent import (
    MIN_OVERRIDE_SIMILARITY,
    PrecedentEngine,
    _extract_correction,
)


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

def _trace_row(
    *,
    query_id: str,
    similarity: float,
    department: str,
    concept_type: str,
    preferred_resolved_id: str,
    feedback_status: str = "corrected",
    preferred_resolved_name: str = "",
    note: str = "",
    feedback_at: str = "2026-03-12T10:00:00",
) -> dict:
    """Build a fake trace row in the shape `find_similar` returns."""
    return {
        "query_id": query_id,
        "user_context": {"user_id": "u", "department": department},
        "original_query": "what was apac revenue last quarter",
        "feedback_status": feedback_status,
        "correction_details": {
            "structured": {
                "concept_type": concept_type,
                "preferred_resolved_id": preferred_resolved_id,
                "preferred_resolved_name": preferred_resolved_name,
                "note": note,
            }
        },
        "feedback_at": feedback_at,
        "confidence": {"overall": 0.9},
        "definitions_selected": {},
        "started_at": "2026-03-12T09:00:00",
        "similarity": similarity,
    }


def _make_engine(graph_results=None, registry_metric_info=None) -> ResolutionEngine:
    graph = AsyncMock()
    registry = AsyncMock()
    vector = AsyncMock()
    traces = AsyncMock()

    graph.find_concept.return_value = graph_results or [
        {
            "id": "gross_revenue",
            "name": "Gross Revenue",
            "definition": "Total invoiced revenue",
            "score": 0.82,
        }
    ]
    graph.find_tribal_knowledge.return_value = []
    graph.get_metric_sources.return_value = []
    graph.get_dimension_values.return_value = {}
    registry.get_metric_info.return_value = registry_metric_info or {
        "semantic_layer_ref": "cube.finance.Revenue",
        "measure": "Revenue.gross",
    }
    registry.get_metric_source_table.return_value = None
    registry.get_data_contract_for_table.return_value = None

    engine = ResolutionEngine(graph, registry, vector, traces)
    engine._policy.authorize_resolution = AsyncMock(
        return_value=AuthorizationResult(
            allowed=True, denied_concepts=[], policies_evaluated=[]
        )
    )
    return engine


# ----------------------------------------------------------------------
# _extract_correction
# ----------------------------------------------------------------------

def test_extract_correction_from_dict():
    row = _trace_row(
        query_id="rs_a",
        similarity=0.91,
        department="finance",
        concept_type="metric",
        preferred_resolved_id="net_revenue",
        preferred_resolved_name="Net Revenue",
        note="ASC 606 alignment",
    )
    corr = _extract_correction(row, similarity=0.91)
    assert corr is not None
    assert corr.concept_type == "metric"
    assert corr.preferred_resolved_id == "net_revenue"
    assert corr.preferred_resolved_name == "Net Revenue"
    assert corr.department == "finance"
    assert corr.corrected_at == "2026-03-12T10:00:00"
    assert corr.note == "ASC 606 alignment"


def test_extract_correction_from_json_string():
    """JSONB columns can come back as strings — _extract_correction must decode."""
    row = _trace_row(
        query_id="rs_b",
        similarity=0.9,
        department="sales",
        concept_type="dimension",
        preferred_resolved_id="region_apac_sales",
    )
    row["correction_details"] = json.dumps(row["correction_details"])
    row["user_context"] = json.dumps(row["user_context"])
    corr = _extract_correction(row, similarity=0.9)
    assert corr is not None
    assert corr.preferred_resolved_id == "region_apac_sales"
    assert corr.department == "sales"


def test_extract_correction_returns_none_for_legacy_string():
    row = _trace_row(
        query_id="rs_c",
        similarity=0.9,
        department="finance",
        concept_type="metric",
        preferred_resolved_id="net_revenue",
    )
    row["correction_details"] = {"details": "old freeform note"}
    assert _extract_correction(row, 0.9) is None


def test_extract_correction_requires_concept_type_and_id():
    row = _trace_row(
        query_id="rs_d",
        similarity=0.9,
        department="finance",
        concept_type="",
        preferred_resolved_id="",
    )
    assert _extract_correction(row, 0.9) is None


# ----------------------------------------------------------------------
# PrecedentEngine.find_precedents
# ----------------------------------------------------------------------

@pytest.mark.asyncio
async def test_find_precedents_attaches_correction_for_corrected_rows():
    traces = AsyncMock()
    traces.find_similar.return_value = [
        _trace_row(
            query_id="rs_a",
            similarity=0.92,
            department="finance",
            concept_type="metric",
            preferred_resolved_id="net_revenue",
        )
    ]
    engine = PrecedentEngine(traces)
    out = await engine.find_precedents(
        query="apac revenue",
        intent=ParsedIntent(concepts={"metric": "revenue", "dimension": "apac"}),
        user_ctx=UserContext(user_id="alice", department="finance"),
    )
    assert len(out) == 1
    assert out[0].feedback == "corrected"
    assert out[0].correction is not None
    assert out[0].correction.preferred_resolved_id == "net_revenue"
    assert "HARD_OVERRIDE_CANDIDATE" in out[0].influence


@pytest.mark.asyncio
async def test_find_precedents_skips_below_similarity_floor():
    traces = AsyncMock()
    traces.find_similar.return_value = [
        _trace_row(
            query_id="rs_low",
            similarity=0.4,  # below MIN_PRECEDENT_SIMILARITY (0.55)
            department="finance",
            concept_type="metric",
            preferred_resolved_id="net_revenue",
        )
    ]
    engine = PrecedentEngine(traces)
    out = await engine.find_precedents(
        query="apac revenue",
        intent=ParsedIntent(concepts={"metric": "revenue"}),
        user_ctx=UserContext(user_id="alice", department="finance"),
    )
    assert out == []


# ----------------------------------------------------------------------
# compute_overrides — filtering rules
# ----------------------------------------------------------------------

def _precedent_with_correction(
    *, query_id="rs_x", similarity=0.91, concept_type="metric",
    preferred="net_revenue", department="finance",
) -> Precedent:
    return Precedent(
        query_id=query_id,
        similarity=similarity,
        original_query="q",
        feedback="corrected",
        influence="...",
        correction=PrecedentCorrection(
            concept_type=concept_type,
            preferred_resolved_id=preferred,
            preferred_resolved_name=preferred.replace("_", " ").title(),
            department=department,
            corrected_at="2026-03-12T10:00:00",
        ),
    )


def test_compute_overrides_eligibility_basic():
    p = _precedent_with_correction()
    intent = ParsedIntent(concepts={"metric": "revenue"})
    out = PrecedentEngine.compute_overrides(
        [p], UserContext(user_id="u", department="finance"), intent
    )
    assert "metric" in out
    assert out["metric"][0].correction.preferred_resolved_id == "net_revenue"


def test_compute_overrides_skips_when_similarity_at_or_below_floor():
    # Floor is strictly greater than MIN_OVERRIDE_SIMILARITY.
    p = _precedent_with_correction(similarity=MIN_OVERRIDE_SIMILARITY)
    out = PrecedentEngine.compute_overrides(
        [p],
        UserContext(user_id="u", department="finance"),
        ParsedIntent(concepts={"metric": "revenue"}),
    )
    assert out == {}


def test_compute_overrides_requires_department_match():
    p = _precedent_with_correction(department="finance")
    out = PrecedentEngine.compute_overrides(
        [p],
        UserContext(user_id="u", department="sales"),
        ParsedIntent(concepts={"metric": "revenue"}),
    )
    assert out == {}


def test_compute_overrides_skips_unrelated_concept_type():
    p = _precedent_with_correction(concept_type="dimension")
    out = PrecedentEngine.compute_overrides(
        [p],
        UserContext(user_id="u", department="finance"),
        ParsedIntent(concepts={"metric": "revenue"}),  # no dimension
    )
    assert out == {}


def test_compute_overrides_groups_conflicts_by_concept_type():
    p1 = _precedent_with_correction(query_id="rs_a", preferred="net_revenue")
    p2 = _precedent_with_correction(query_id="rs_b", preferred="gross_revenue")
    out = PrecedentEngine.compute_overrides(
        [p1, p2],
        UserContext(user_id="u", department="finance"),
        ParsedIntent(concepts={"metric": "revenue"}),
    )
    assert len(out["metric"]) == 2


# ----------------------------------------------------------------------
# ResolutionEngine — override is applied end-to-end
# ----------------------------------------------------------------------

@pytest.mark.asyncio
async def test_engine_applies_correction_override():
    """Graph would pick gross_revenue; correction forces net_revenue."""
    engine = _make_engine()
    engine.traces.persist_resolution = AsyncMock()

    correction_row = _trace_row(
        query_id="rs_correction",
        similarity=0.91,
        department="finance",
        concept_type="metric",
        preferred_resolved_id="net_revenue",
        preferred_resolved_name="Net Revenue",
        note="ASC 606 — finance always uses recognized revenue",
    )
    engine.traces.find_similar = AsyncMock(return_value=[correction_row])

    req = ResolveRequest(
        concept="revenue",
        user_context=UserContext(user_id="alice", department="finance"),
    )
    res = await engine.resolve(req)

    metric = res.resolved_concepts["metric"]
    assert metric.resolved_id == "net_revenue"
    assert metric.confidence == 1.0
    assert "Applied correction from rs_correction" in metric.reasoning

    # Definition-level confidence reflects the 1.0 swap.
    assert res.confidence.definition == 1.0
    assert res.status == "complete"

    # DAG carries an explicit override step.
    override_steps = [s for s in res.resolution_dag if s.step == "override_metric"]
    assert len(override_steps) == 1
    assert override_steps[0].method == "precedent_correction"
    assert override_steps[0].output["applied"] is True
    assert override_steps[0].output["resolved_id"] == "net_revenue"
    assert "Applied correction from rs_correction" in override_steps[0].reasoning


@pytest.mark.asyncio
async def test_engine_disambiguates_on_conflicting_corrections():
    engine = _make_engine()
    engine.traces.persist_resolution = AsyncMock()

    rows = [
        _trace_row(
            query_id="rs_one",
            similarity=0.92,
            department="finance",
            concept_type="metric",
            preferred_resolved_id="net_revenue",
        ),
        _trace_row(
            query_id="rs_two",
            similarity=0.90,
            department="finance",
            concept_type="metric",
            preferred_resolved_id="gross_revenue",
            feedback_at="2026-03-15T10:00:00",
        ),
    ]
    engine.traces.find_similar = AsyncMock(return_value=rows)

    req = ResolveRequest(
        concept="revenue",
        user_context=UserContext(user_id="alice", department="finance"),
    )
    res = await engine.resolve(req)

    assert res.status == "disambiguation_required"
    # Both correction precedents must be visible to the caller.
    assert {p.query_id for p in res.precedents_used} >= {"rs_one", "rs_two"}
    # The conflict step is recorded in the DAG.
    conflict_steps = [
        s for s in res.resolution_dag
        if s.step == "override_metric" and s.output.get("conflict") is True
    ]
    assert len(conflict_steps) == 1


@pytest.mark.asyncio
async def test_engine_no_override_when_department_mismatches():
    engine = _make_engine()
    engine.traces.persist_resolution = AsyncMock()

    # Correction was made in a finance session — caller is in sales.
    engine.traces.find_similar = AsyncMock(return_value=[
        _trace_row(
            query_id="rs_finance_only",
            similarity=0.91,
            department="finance",
            concept_type="metric",
            preferred_resolved_id="net_revenue",
        )
    ])

    req = ResolveRequest(
        concept="revenue",
        user_context=UserContext(user_id="bob", department="sales"),
    )
    res = await engine.resolve(req)

    metric = res.resolved_concepts["metric"]
    # Falls through to graph result (gross_revenue from _make_engine default).
    assert metric.resolved_id == "gross_revenue"
    override_steps = [s for s in res.resolution_dag if s.step == "override_metric"]
    assert override_steps == []


# ----------------------------------------------------------------------
# GOLDEN scenario — round-trip simulating record_feedback then re-resolve.
# ----------------------------------------------------------------------

@pytest.mark.asyncio
async def test_golden_correction_round_trip():
    """Simulate: resolve X, mark corrected with structured detail, resolve Y, override applies.

    This exercises CorrectionDetail → record_feedback persistence shape →
    find_similar payload → PrecedentEngine → engine override. The trace
    store is mocked to capture the correction_details JSON written, then
    replayed verbatim into the next resolve call's find_similar response.
    """
    engine = _make_engine()
    engine.traces.persist_resolution = AsyncMock()

    # First resolve: no precedents.
    engine.traces.find_similar = AsyncMock(return_value=[])
    res1 = await engine.resolve(ResolveRequest(
        concept="revenue last quarter",
        user_context=UserContext(user_id="alice", department="finance"),
    ))
    assert res1.resolved_concepts["metric"].resolved_id == "gross_revenue"

    # Capture what record_feedback would persist for a structured correction.
    captured: dict = {}

    async def fake_record(resolution_id, feedback, details):
        # Mirror the real TraceStore.record_feedback shape.
        if isinstance(details, CorrectionDetail):
            captured["correction_details"] = {"structured": details.model_dump()}
        else:
            captured["correction_details"] = {"details": details}
        captured["resolution_id"] = resolution_id
        captured["feedback_at"] = "2026-03-12T10:00:00"
        return True

    from src.models import FeedbackStatus
    engine.traces.record_feedback = AsyncMock(side_effect=fake_record)
    await engine.traces.record_feedback(
        res1.resolution_id,
        FeedbackStatus.CORRECTED,
        CorrectionDetail(
            concept_type="metric",
            preferred_resolved_id="net_revenue",
            preferred_resolved_name="Net Revenue",
            note="finance always uses ASC 606 recognized revenue",
        ),
    )

    # Second resolve: similar query, find_similar returns the persisted row.
    engine.traces.find_similar = AsyncMock(return_value=[
        {
            "query_id": captured["resolution_id"],
            "user_context": {"user_id": "alice", "department": "finance"},
            "original_query": "revenue last quarter",
            "feedback_status": "corrected",
            "correction_details": captured["correction_details"],
            "feedback_at": captured["feedback_at"],
            "confidence": {"overall": 0.85},
            "definitions_selected": {},
            "started_at": "2026-03-12T09:00:00",
            "similarity": 0.93,
        }
    ])

    res2 = await engine.resolve(ResolveRequest(
        concept="revenue this period",  # similar but not identical
        user_context=UserContext(user_id="alice", department="finance"),
    ))
    metric = res2.resolved_concepts["metric"]
    assert metric.resolved_id == "net_revenue"
    assert metric.confidence == 1.0
    assert res2.status == "complete"
    assert any(s.step == "override_metric" for s in res2.resolution_dag)

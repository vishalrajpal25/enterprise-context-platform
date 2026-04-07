from unittest.mock import AsyncMock

import pytest

from src.models import ResolveRequest, UserContext
from src.governance.policy import AuthorizationResult
from src.resolution.engine import ResolutionEngine


@pytest.mark.asyncio
async def test_deny_all_when_opa_denies_without_specific_concepts():
    graph = AsyncMock()
    registry = AsyncMock()
    vector = AsyncMock()
    traces = AsyncMock()

    graph.find_concept.return_value = [
        {"id": "net_revenue", "name": "Net Revenue", "definition": "Revenue", "score": 0.9}
    ]
    graph.find_tribal_knowledge.return_value = []
    registry.get_metric_info.return_value = {
        "semantic_layer_ref": "cube.finance.Revenue",
        "measure": "Revenue.net",
    }

    engine = ResolutionEngine(graph, registry, vector, traces)
    engine._policy.authorize_resolution = AsyncMock(
        return_value=AuthorizationResult(allowed=False, denied_concepts=[])
    )

    req = ResolveRequest(
        concept="revenue",
        user_context=UserContext(user_id="alice", department="finance", role="analyst"),
    )
    res = await engine.resolve(req)

    assert res.access_granted is False
    assert res.resolved_concepts == {}
    assert res.execution_plan == []
    assert "metric" in res.filtered_concepts
    assert res.confidence.authorization == 0.0

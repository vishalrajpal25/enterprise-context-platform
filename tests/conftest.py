import pytest
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

from src.models import ResolveResponse, Confidence


def sample_trace_session():
    return {
        "query_id": "rs_demo_1",
        "user_id": "demo_user",
        "status": "complete",
        "execution_plan": [
            {
                "target": "cube.finance.Revenue",
                "method": "semantic_layer_call",
                "parameters": {"measures": ["Revenue.net"]},
            }
        ],
        "confidence": {
            "overall": 0.85,
            "definition": 0.85,
            "data_quality": 0.9,
            "temporal_validity": 0.95,
            "authorization": 1.0,
            "completeness": 0.9,
        },
        "original_query": "APAC revenue",
    }


@pytest.fixture
def client(monkeypatch):
    import src.main as main

    @asynccontextmanager
    async def fake_lifespan(app):
        main.engine = MagicMock()

        async def do_resolve(req):
            return ResolveResponse(
                resolution_id="rs_test_1",
                status="complete",
                confidence=Confidence(
                    overall=0.9,
                    definition=0.9,
                    data_quality=0.9,
                    temporal_validity=0.9,
                    authorization=1.0,
                    completeness=0.9,
                ),
            )

        main.engine.resolve = AsyncMock(side_effect=do_resolve)
        main.traces.get_session = AsyncMock(return_value=sample_trace_session())
        main.traces.record_feedback = AsyncMock(return_value=True)
        main.graph.ping = AsyncMock(return_value=False)
        main.registry.ping = AsyncMock(return_value=False)
        main.vector.ping = AsyncMock(return_value=False)
        main.traces.ping = AsyncMock(return_value=False)
        main.audit.ping = AsyncMock(return_value=False)
        main.policy.ping = AsyncMock(return_value=False)
        yield

    monkeypatch.setattr(main.app.router, "lifespan_context", fake_lifespan)
    from starlette.testclient import TestClient

    with TestClient(main.app, raise_server_exceptions=True) as tc:
        yield tc

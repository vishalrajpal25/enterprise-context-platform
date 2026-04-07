import pytest

from src.config import settings
from src.semantic.cube_executor import run_execution_plan


@pytest.mark.asyncio
async def test_run_execution_plan_dry_run(monkeypatch):
    monkeypatch.setattr(settings, "cube_api_url", "")
    results, prov = await run_execution_plan(
        [{"method": "semantic_layer_call", "parameters": {"measures": ["M.a"]}}],
        {},
    )
    assert results["status"] == "not_configured"
    assert prov["cube_api_configured"] is False

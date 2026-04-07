"""Execute ECP execution plans against the Cube.js REST API (/cubejs-api/v1/load)."""
from __future__ import annotations

import logging
from typing import Any

import httpx

from src.config import settings

logger = logging.getLogger(__name__)


def _normalize_cube_base(url: str) -> str:
    u = url.rstrip("/")
    if u.endswith("/v1"):
        return u
    if "/cubejs-api" in u:
        return u if u.endswith("/v1") else u + "/v1"
    return u + "/cubejs-api/v1"


def _step_to_cube_query(step: dict[str, Any], extra_params: dict[str, Any]) -> dict[str, Any]:
    # Treat execution plan as authoritative: do not let caller override measures.
    params = dict(step.get("parameters") or {})
    extra_filters = extra_params.get("filters") if isinstance(extra_params, dict) else None
    if isinstance(extra_filters, dict):
        step_filters = params.get("filters")
        if isinstance(step_filters, dict):
            merged_filters = dict(step_filters)
            merged_filters.update(extra_filters)
            params["filters"] = merged_filters
    measures = params.get("measures") or []
    query: dict[str, Any] = {"measures": measures}
    filters = params.get("filters") or {}
    if isinstance(filters, dict):
        dr = filters.get("date_range")
        if isinstance(dr, dict) and dr.get("dimension"):
            query.setdefault("timeDimensions", []).append(
                {
                    "dimension": dr["dimension"],
                    "dateRange": dr.get("range") or dr.get("dateRange") or "Last quarter",
                }
            )
        region_vals = filters.get("region")
        if region_vals:
            member = params.get("region_member") or "Regions.name"
            vals = region_vals if isinstance(region_vals, list) else [region_vals]
            query.setdefault("filters", []).append(
                {"member": member, "operator": "equals", "values": vals}
            )
    return query


async def run_execution_plan(
    steps: list[dict[str, Any]],
    extra_params: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    Run each semantic_layer_call step against Cube. If ECP_CUBE_API_URL is unset,
    returns a dry-run payload (no network).
    """
    if not settings.cube_api_url:
        return (
            {
                "status": "not_configured",
                "message": (
                    "Set ECP_CUBE_API_URL (e.g. http://localhost:4000/cubejs-api/v1). "
                    "Optional: ECP_CUBE_API_SECRET for Authorization header."
                ),
                "steps": steps,
                "parameters": extra_params,
            },
            {"mode": "dry_run", "cube_api_configured": False},
        )

    base = _normalize_cube_base(settings.cube_api_url)
    headers: dict[str, str] = {}
    if settings.cube_api_secret:
        headers["Authorization"] = settings.cube_api_secret

    out: list[dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=120.0) as client:
        for step in steps:
            if step.get("method") != "semantic_layer_call":
                out.append({"skipped": True, "reason": "not_semantic_layer_call", "step": step})
                continue
            cube_query = _step_to_cube_query(step, extra_params)
            url = f"{base}/load"
            try:
                resp = await client.post(url, json={"query": cube_query}, headers=headers)
                resp.raise_for_status()
                body = resp.json()
            except Exception as e:
                logger.warning("Cube load failed: %s", e)
                out.append({"error": str(e), "cube_query": cube_query, "step": step})
                continue
            out.append({"cube_query": cube_query, "data": body.get("data"), "annotation": body.get("annotation")})

    return (
        {"status": "ok", "results": out},
        {"mode": "live", "cube_api_base": base},
    )

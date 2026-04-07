"""Golden Query Suite: reference answers for certified metrics.

Loads reference queries from golden_queries.yaml, runs them against /resolve,
and compares results to expected resolutions. Used for nightly eval runs and
online sampling of production resolutions.
"""
from __future__ import annotations
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
import yaml
from pydantic import BaseModel, Field


GOLDEN_QUERIES_PATH = Path(__file__).parent / "golden_queries.yaml"


class GoldenQueryResult(BaseModel):
    query_name: str
    passed: bool
    expected_status: str
    actual_status: str
    expected_concepts: dict[str, str] = Field(default_factory=dict)
    actual_concepts: dict[str, str] = Field(default_factory=dict)
    confidence: float = 0.0
    mismatches: list[str] = Field(default_factory=list)
    latency_ms: float = 0.0


class GoldenQuerySuiteResult(BaseModel):
    run_at: datetime = Field(default_factory=datetime.utcnow)
    total: int = 0
    passed: int = 0
    failed: int = 0
    accuracy_pct: float = 0.0
    results: list[GoldenQueryResult] = Field(default_factory=list)


def load_golden_queries(path: Path | None = None) -> list[dict[str, Any]]:
    """Load golden query definitions from YAML."""
    p = path or GOLDEN_QUERIES_PATH
    if not p.exists():
        return []
    with open(p) as f:
        data = yaml.safe_load(f)
    return data.get("golden_queries", [])


async def run_golden_queries(
    base_url: str = "http://localhost:8080",
    path: Path | None = None,
) -> GoldenQuerySuiteResult:
    """Execute the golden query suite against a running ECP instance."""
    queries = load_golden_queries(path)
    suite = GoldenQuerySuiteResult(total=len(queries))

    async with httpx.AsyncClient(timeout=30.0) as client:
        for gq in queries:
            result = await _run_single(client, base_url, gq)
            suite.results.append(result)
            if result.passed:
                suite.passed += 1
            else:
                suite.failed += 1

    suite.accuracy_pct = (suite.passed / suite.total * 100) if suite.total else 0.0
    return suite


async def _run_single(
    client: httpx.AsyncClient,
    base_url: str,
    gq: dict[str, Any],
) -> GoldenQueryResult:
    """Run a single golden query and compare to expected resolution."""
    import time

    payload = {
        "concept": gq["query"],
        "user_context": gq.get("user_context", {
            "user_id": "golden_eval",
            "department": gq.get("department", "finance"),
            "role": "analyst",
        }),
    }

    start = time.monotonic()
    try:
        resp = await client.post(f"{base_url}/api/v1/resolve", json=payload)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return GoldenQueryResult(
            query_name=gq.get("name", gq["query"]),
            passed=False,
            expected_status=gq.get("expected_status", "complete"),
            actual_status="error",
            mismatches=[f"HTTP error: {e}"],
            latency_ms=(time.monotonic() - start) * 1000,
        )

    latency = (time.monotonic() - start) * 1000

    # Extract actual resolved concept IDs
    actual_concepts = {
        k: v.get("resolved_id", "")
        for k, v in data.get("resolved_concepts", {}).items()
    }
    expected_concepts = gq.get("expected_concepts", {})
    expected_status = gq.get("expected_status", "complete")

    mismatches: list[str] = []
    if data.get("status") != expected_status:
        mismatches.append(f"status: expected={expected_status} actual={data.get('status')}")

    for concept_type, expected_id in expected_concepts.items():
        actual_id = actual_concepts.get(concept_type, "")
        if actual_id != expected_id:
            mismatches.append(
                f"{concept_type}: expected={expected_id} actual={actual_id}"
            )

    return GoldenQueryResult(
        query_name=gq.get("name", gq["query"]),
        passed=len(mismatches) == 0,
        expected_status=expected_status,
        actual_status=data.get("status", "unknown"),
        expected_concepts=expected_concepts,
        actual_concepts=actual_concepts,
        confidence=data.get("confidence", {}).get("overall", 0.0),
        mismatches=mismatches,
        latency_ms=latency,
    )

#!/usr/bin/env python3
"""Simple concurrent load smoke for /resolve with pass/fail thresholds."""
from __future__ import annotations

import asyncio
import statistics
import sys
import time

import httpx


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    idx = int((len(values) - 1) * p)
    return values[idx]


async def worker(
    client: httpx.AsyncClient,
    base_url: str,
    requests_per_worker: int,
    latencies_ms: list[float],
    errors: list[str],
    api_key: str,
    retries: int,
) -> None:
    headers = {"x-ecp-user-id": "load_tester", "x-ecp-department": "finance", "x-ecp-role": "analyst"}
    if api_key:
        headers["x-ecp-api-key"] = api_key
    payload = {"concept": "What was APAC revenue last quarter?", "user_context": None}
    for _ in range(requests_per_worker):
        attempts = 0
        while True:
            attempts += 1
            start = time.monotonic()
            try:
                resp = await client.post(f"{base_url}/api/v1/resolve", json=payload, headers=headers)
                elapsed = (time.monotonic() - start) * 1000
                latencies_ms.append(elapsed)
                if resp.status_code >= 400:
                    if attempts <= retries:
                        continue
                    errors.append(f"http_{resp.status_code}")
                break
            except Exception as e:  # noqa: BLE001
                if attempts <= retries:
                    continue
                errors.append(str(e))
                break


async def main() -> int:
    base_url = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8080").rstrip("/")
    total_requests = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    concurrency = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    p95_budget_ms = float(sys.argv[4]) if len(sys.argv) > 4 else 1500.0
    api_key = sys.argv[5] if len(sys.argv) > 5 else ""
    max_error_rate = float(sys.argv[6]) if len(sys.argv) > 6 else 5.0
    retries = int(sys.argv[7]) if len(sys.argv) > 7 else 1

    per_worker = max(1, total_requests // concurrency)
    latencies: list[float] = []
    errors: list[str] = []

    async with httpx.AsyncClient(timeout=30.0) as client:
        tasks = [
            worker(client, base_url, per_worker, latencies, errors, api_key, retries)
            for _ in range(concurrency)
        ]
        await asyncio.gather(*tasks)

    effective_requests = len(latencies)
    error_rate = (len(errors) / effective_requests * 100.0) if effective_requests else 100.0
    p95 = percentile(latencies, 0.95)
    p50 = percentile(latencies, 0.50)
    avg = statistics.fmean(latencies) if latencies else 0.0

    print(
        f"Load smoke: requests={effective_requests} concurrency={concurrency} "
        f"p50={p50:.1f}ms p95={p95:.1f}ms avg={avg:.1f}ms error_rate={error_rate:.2f}%"
    )
    if errors:
        print(f"Sample errors ({min(5, len(errors))}/{len(errors)}): {errors[:5]}")

    if p95 > p95_budget_ms or error_rate > max_error_rate:
        print(
            f"FAILED: p95 {p95:.1f}ms (budget {p95_budget_ms:.1f}ms) "
            f"or error_rate {error_rate:.2f}% (>{max_error_rate:.2f}%)"
        )
        return 1
    print("PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

"""SSE telemetry stream endpoint tests.

The bus is exhaustively tested in test_telemetry_bus.py. Here we verify:
1. The endpoint is registered and returns text/event-stream.
2. The `: connected` prelude arrives.
3. TelemetryEvent.to_sse() round-trips through the same wire format the
   observer TypeScript side parses.
4. The bus delivers events through subscribe() in the same shape the SSE
   handler would yield.
"""
from __future__ import annotations

import asyncio
import json

import pytest

from src.telemetry import (
    TelemetryEvent,
    TelemetryStage,
    TelemetryStatus,
    bus as telemetry_bus,
)


def test_event_sse_frame_matches_observer_contract():
    ev = TelemetryEvent(
        resolution_id="rs_x",
        stage=TelemetryStage.PARSE_INTENT,
        status=TelemetryStatus.OK,
        latency_ms=4.2,
        payload_summary={"query": "revenue"},
    )
    frame = ev.to_sse()
    assert frame.startswith("data: ")
    assert frame.endswith("\n\n")
    payload = json.loads(frame[len("data: "):-len("\n\n")])
    assert payload["resolution_id"] == "rs_x"
    assert payload["stage"] == "parse_intent"
    assert payload["status"] == "ok"
    assert payload["latency_ms"] == 4.2
    assert payload["payload_summary"] == {"query": "revenue"}


@pytest.mark.asyncio
async def test_bus_publish_reaches_subscriber_like_sse_handler():
    collected: list[str] = []

    async def _consume():
        async for ev in telemetry_bus.subscribe():
            collected.append(ev.to_sse())
            if len(collected) >= 2:
                return

    task = asyncio.create_task(_consume())
    while telemetry_bus.subscriber_count == 0:
        await asyncio.sleep(0)
    await telemetry_bus.publish(TelemetryEvent(
        resolution_id="rs_a",
        stage=TelemetryStage.PARSE_INTENT,
        status=TelemetryStatus.OK,
    ))
    await telemetry_bus.publish(TelemetryEvent(
        resolution_id="rs_b",
        stage=TelemetryStage.AUTHZ,
        status=TelemetryStatus.DENIED,
    ))
    await asyncio.wait_for(task, timeout=1.0)

    assert len(collected) == 2
    payloads = [json.loads(f[len("data: "):-len("\n\n")]) for f in collected]
    assert payloads[0]["resolution_id"] == "rs_a"
    assert payloads[1]["stage"] == "authz"
    assert payloads[1]["status"] == "denied"


def test_stream_endpoint_registered_and_streams(client):
    """Hit the endpoint through TestClient to prove it's wired and returns
    the right content-type with the `: connected` prelude."""
    with client.stream(
        "GET",
        "/api/v1/telemetry/stream",
        headers={"accept": "text/event-stream"},
    ) as resp:
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/event-stream")

        first_bytes = ""
        for chunk in resp.iter_text():
            first_bytes += chunk
            if '"connected"' in first_bytes:
                break

        assert '"type":"connected"' in first_bytes or '"type": "connected"' in first_bytes

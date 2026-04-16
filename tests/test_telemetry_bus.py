"""TelemetryBus contract tests.

Pin down the three invariants that protect the resolution path:
1. publish() with no subscribers is a no-op and never blocks.
2. publish() fans out to every subscriber.
3. A slow subscriber hitting queue-full drops its oldest event (not the
   newest) and never applies backpressure to the publisher.
"""
from __future__ import annotations

import asyncio

import pytest

from src.telemetry.bus import TelemetryBus
from src.telemetry.events import (
    TelemetryEvent,
    TelemetryStage,
    TelemetryStatus,
    truncate_payload,
)


def _event(
    resolution_id: str = "rs_test",
    stage: TelemetryStage = TelemetryStage.PARSE_INTENT,
) -> TelemetryEvent:
    return TelemetryEvent(
        resolution_id=resolution_id,
        stage=stage,
        status=TelemetryStatus.OK,
        latency_ms=1.0,
    )


@pytest.mark.asyncio
async def test_publish_without_subscribers_does_not_block():
    bus = TelemetryBus()
    await asyncio.wait_for(bus.publish(_event()), timeout=0.1)
    assert bus.subscriber_count == 0


@pytest.mark.asyncio
async def test_fanout_to_multiple_subscribers():
    bus = TelemetryBus()
    received_a: list[TelemetryEvent] = []
    received_b: list[TelemetryEvent] = []

    async def collect(target: list[TelemetryEvent], n: int) -> None:
        async for ev in bus.subscribe():
            target.append(ev)
            if len(target) >= n:
                break

    task_a = asyncio.create_task(collect(received_a, 3))
    task_b = asyncio.create_task(collect(received_b, 3))
    while bus.subscriber_count < 2:
        await asyncio.sleep(0)

    for i in range(3):
        await bus.publish(_event(resolution_id=f"rs_{i}"))

    await asyncio.wait_for(asyncio.gather(task_a, task_b), timeout=1.0)
    assert [e.resolution_id for e in received_a] == ["rs_0", "rs_1", "rs_2"]
    assert [e.resolution_id for e in received_b] == ["rs_0", "rs_1", "rs_2"]


@pytest.mark.asyncio
async def test_overflow_drops_oldest_not_newest():
    bus = TelemetryBus(queue_maxsize=2)
    seen: list[TelemetryEvent] = []

    async def slow_consumer():
        async for ev in bus.subscribe():
            seen.append(ev)
            if len(seen) >= 2:
                break

    task = asyncio.create_task(slow_consumer())
    while bus.subscriber_count < 1:
        await asyncio.sleep(0)

    for i in range(5):
        await bus.publish(_event(resolution_id=f"rs_{i}"))

    await asyncio.wait_for(task, timeout=1.0)
    assert [e.resolution_id for e in seen] == ["rs_3", "rs_4"]


@pytest.mark.asyncio
async def test_subscriber_cleanup_on_generator_close():
    bus = TelemetryBus()
    agen = bus.subscribe()

    async def consume_once():
        await agen.__anext__()

    task = asyncio.create_task(consume_once())
    while bus.subscriber_count < 1:
        await asyncio.sleep(0)
    await bus.publish(_event())
    await asyncio.wait_for(task, timeout=1.0)

    await agen.aclose()
    await asyncio.sleep(0)
    assert bus.subscriber_count == 0


def test_truncate_payload_caps_long_strings():
    s = "x" * 600
    result = truncate_payload(s)
    assert isinstance(result, str)
    assert result.startswith("x" * 500)
    assert "[+100 chars]" in result


def test_truncate_payload_caps_long_arrays():
    arr = list(range(25))
    result = truncate_payload(arr)
    assert isinstance(result, list)
    assert result[:10] == list(range(10))
    assert result[-1] == "...[+15 items]"


def test_truncate_payload_recurses_into_nested_dicts():
    payload = {"a": {"b": "y" * 700, "c": list(range(20))}}
    out = truncate_payload(payload)
    assert "[+200 chars]" in out["a"]["b"]
    assert out["a"]["c"][-1] == "...[+10 items]"


def test_truncate_payload_preserves_primitives():
    assert truncate_payload(None) is None
    assert truncate_payload(True) is True
    assert truncate_payload(42) == 42
    assert truncate_payload(3.14) == 3.14

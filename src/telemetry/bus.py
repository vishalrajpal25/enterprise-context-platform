"""In-process telemetry bus.

Fire-and-forget publish, fan-out to N subscribers. Each subscriber has a
bounded `asyncio.Queue`; if it fills up we drop the oldest event so a slow
observer can never backpressure the resolution path.

TODO(multi-node): swap for a Redis pub/sub or NATS implementation behind
the same TelemetryTransport protocol.
"""
from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from typing import Protocol

from src.telemetry.events import TelemetryEvent

logger = logging.getLogger(__name__)

_DEFAULT_QUEUE_MAXSIZE = 1024


class TelemetryTransport(Protocol):
    async def publish(self, event: TelemetryEvent) -> None: ...
    def subscribe(self) -> AsyncIterator[TelemetryEvent]: ...


class TelemetryBus:
    """Async fan-out bus. Single-process, in-memory."""

    def __init__(self, queue_maxsize: int = _DEFAULT_QUEUE_MAXSIZE) -> None:
        self._queue_maxsize = queue_maxsize
        self._subscribers: set[asyncio.Queue[TelemetryEvent]] = set()
        self._lock = asyncio.Lock()

    async def publish(self, event: TelemetryEvent) -> None:
        """Broadcast to every subscriber. Never blocks, never raises.

        If a subscriber queue is full we drop its oldest event to make room.
        """
        if not self._subscribers:
            return
        for queue in list(self._subscribers):
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
                try:
                    queue.put_nowait(event)
                except asyncio.QueueFull:
                    pass
            except Exception as exc:
                logger.warning("telemetry publish to subscriber failed: %s", exc)

    async def subscribe(self) -> AsyncIterator[TelemetryEvent]:
        """Yield events forever. Cleans up the queue on generator close."""
        queue: asyncio.Queue[TelemetryEvent] = asyncio.Queue(
            maxsize=self._queue_maxsize
        )
        async with self._lock:
            self._subscribers.add(queue)
        try:
            while True:
                event = await queue.get()
                yield event
        finally:
            async with self._lock:
                self._subscribers.discard(queue)

    @property
    def subscriber_count(self) -> int:
        return len(self._subscribers)


bus = TelemetryBus()


async def safe_publish(event: TelemetryEvent) -> None:
    """Fire-and-forget wrapper: publish failures must never bubble up."""
    try:
        await bus.publish(event)
    except Exception as exc:  # pragma: no cover
        logger.warning("telemetry safe_publish swallowed error: %s", exc)

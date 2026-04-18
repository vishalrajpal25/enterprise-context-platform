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


_DEFAULT_RING_SIZE = 500


class TelemetryBus:
    """Async fan-out bus. Single-process, in-memory."""

    def __init__(
        self,
        queue_maxsize: int = _DEFAULT_QUEUE_MAXSIZE,
        ring_size: int = _DEFAULT_RING_SIZE,
    ) -> None:
        self._queue_maxsize = queue_maxsize
        self._subscribers: set[asyncio.Queue[TelemetryEvent]] = set()
        self._lock = asyncio.Lock()
        # Ring buffer of recent events for polling clients.
        self._ring: list[TelemetryEvent] = []
        self._ring_size = ring_size
        self._seq = 0  # monotonic sequence counter

    async def publish(self, event: TelemetryEvent) -> None:
        """Broadcast to every subscriber. Never blocks, never raises.

        If a subscriber queue is full we drop its oldest event to make room.
        """
        # Always append to ring buffer (even with no subscribers).
        self._seq += 1
        if len(self._ring) >= self._ring_size:
            self._ring.pop(0)
        self._ring.append(event)

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

    def recent(self, after_seq: int = 0, user_id: str | None = None) -> tuple[int, list[TelemetryEvent]]:
        """Return (current_seq, events_after_seq), optionally filtered by user_id.

        Clients pass the last seq they saw; we return only newer events.
        """
        # Find events newer than after_seq
        start_idx = max(0, len(self._ring) - (self._seq - after_seq))
        events = self._ring[start_idx:]

        if user_id:
            # Track which resolution_ids belong to the user
            user_rids: set[str] = set()
            filtered: list[TelemetryEvent] = []
            for ev in events:
                if ev.stage == "resolution_start":
                    if ev.payload_summary.get("user_id") == user_id:
                        user_rids.add(ev.resolution_id)
                if ev.resolution_id in user_rids:
                    filtered.append(ev)
            events = filtered

        return self._seq, events

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

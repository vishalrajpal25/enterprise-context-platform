"""Telemetry event schema and no-op bus.

Defines the event shape that resolution and federation stages emit.
The bus collects subscribers; publish() fans out to each. With zero
subscribers, publish() is a no-op and never blocks.

This module is the coordination point between the federation layer
(Session C) and the observer UI (Session D). Session D may add a
real async bus; this stub ensures federation code compiles and runs
without blocking on that work.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Awaitable

logger = logging.getLogger(__name__)


class TelemetryStage(str, Enum):
    RESOLUTION_START = "resolution_start"
    PARSE_INTENT = "parse_intent"
    RESOLVE_CONCEPT = "resolve_concept"
    TRIBAL_CHECK = "tribal_check"
    PRECEDENT = "precedent"
    FEDERATION_DISCOVER = "federation_discover"
    FEDERATION_MERGE = "federation_merge"
    AUTHZ = "authz"
    BUILD_PLAN = "build_plan"
    PERSIST_TRACE = "persist_trace"
    RESOLUTION_END = "resolution_end"


class TelemetryStatus(str, Enum):
    STARTED = "started"
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"
    DENIED = "denied"
    TIMEOUT = "timeout"


@dataclass
class TelemetryEvent:
    resolution_id: str = ""
    stage: TelemetryStage = TelemetryStage.RESOLUTION_START
    status: TelemetryStatus = TelemetryStatus.OK
    latency_ms: float = 0.0
    payload_summary: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# Type alias for subscribers
Subscriber = Callable[[TelemetryEvent], Awaitable[None]]


class TelemetryBus:
    """In-process fan-out bus for telemetry events.

    No-op when no subscribers are registered. Publish never blocks the
    caller — subscriber errors are logged and swallowed.
    """

    def __init__(self) -> None:
        self._subscribers: list[Subscriber] = []

    def subscribe(self, handler: Subscriber) -> None:
        self._subscribers.append(handler)

    async def publish(self, event: TelemetryEvent) -> None:
        for sub in self._subscribers:
            try:
                await sub(event)
            except Exception as exc:
                logger.debug("telemetry subscriber error (swallowed): %s", exc)


# Module-level singleton
bus = TelemetryBus()


def truncate_payload(data: dict, max_chars: int = 500) -> dict:
    """Trim large values for telemetry payloads."""
    result: dict[str, Any] = {}
    for k, v in data.items():
        s = str(v)
        result[k] = s[:max_chars] if len(s) > max_chars else v
    return result

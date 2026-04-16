"""Telemetry event schema.

Single source of truth for the observer wire format. Mirrored by hand in
observer/src/types/events.ts — keep the two in sync. Federation adapters
publish `adapter_call` / `federation_discover` / `federation_merge` events
against the same schema.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class TelemetryStage(str, Enum):
    PARSE_INTENT = "parse_intent"
    RESOLVE_CONCEPT = "resolve_concept"
    TRIBAL_CHECK = "tribal_check"
    AUTHZ = "authz"
    PRECEDENT = "precedent"
    BUILD_PLAN = "build_plan"
    PERSIST_TRACE = "persist_trace"
    # Federation (Session C)
    FEDERATION_DISCOVER = "federation_discover"
    FEDERATION_MERGE = "federation_merge"
    # Nested / cross-cutting
    ADAPTER_CALL = "adapter_call"
    STORE_CALL = "store_call"
    # Top-level markers
    RESOLUTION_START = "resolution_start"
    RESOLUTION_END = "resolution_end"


class TelemetryStore(str, Enum):
    NEO4J = "neo4j"
    PGVECTOR = "pgvector"
    POSTGRES = "postgres"
    OPA = "opa"
    CUBE = "cube"
    ANTHROPIC = "anthropic"
    VOYAGE = "voyage"
    OPENAI = "openai"
    TRACE_STORE = "trace_store"


class TelemetryStatus(str, Enum):
    STARTED = "started"
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"
    TIMEOUT = "timeout"
    DENIED = "denied"


_STRING_CAP = 500
_ARRAY_CAP = 10


def truncate_payload(
    value: Any, *, string_cap: int = _STRING_CAP, array_cap: int = _ARRAY_CAP
) -> Any:
    """Recursively cap strings at 500 chars and arrays at 10 items.

    Observer payloads must never leak full definitions, full graph results,
    or secrets. Every publisher pipes payload_summary through this.
    """
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        if len(value) <= string_cap:
            return value
        return value[:string_cap] + f"...[+{len(value) - string_cap} chars]"
    if isinstance(value, (list, tuple)):
        truncated = [
            truncate_payload(v, string_cap=string_cap, array_cap=array_cap)
            for v in value[:array_cap]
        ]
        if len(value) > array_cap:
            truncated.append(f"...[+{len(value) - array_cap} items]")
        return truncated
    if isinstance(value, dict):
        return {
            k: truncate_payload(v, string_cap=string_cap, array_cap=array_cap)
            for k, v in value.items()
        }
    s = str(value)
    if len(s) <= string_cap:
        return s
    return s[:string_cap] + f"...[+{len(s) - string_cap} chars]"


class TelemetryEvent(BaseModel):
    """A single event on the telemetry bus.

    Events are fire-and-forget: publishers never block on slow subscribers
    and observer crashes never affect ECP.
    """

    resolution_id: str
    stage: TelemetryStage
    status: TelemetryStatus
    store: TelemetryStore | None = None
    latency_ms: float = 0.0
    payload_summary: dict[str, Any] = Field(default_factory=dict)
    ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    parent_stage: TelemetryStage | None = None
    source_id: str | None = None

    def to_sse(self) -> str:
        return f"data: {self.model_dump_json()}\n\n"

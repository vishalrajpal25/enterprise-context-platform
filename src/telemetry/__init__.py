"""Telemetry event bus and schema for observability.

Provides a fire-and-forget event bus that the resolution engine and
federation orchestrator use to publish stage-level events. Subscribers
(SSE endpoint, metrics, logging) receive events without blocking the
critical path.

The bus is no-op until a subscriber is wired up — calling publish()
with no subscribers is free.
"""

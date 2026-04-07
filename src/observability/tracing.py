"""OpenTelemetry instrumentation for resolution steps.

Provides a decorator that wraps async resolution methods with OTel spans,
capturing timing, status, and key attributes. Falls back gracefully when
the OpenTelemetry SDK is not installed.
"""
from __future__ import annotations
import functools
from typing import Any, Callable, TypeVar, ParamSpec

P = ParamSpec("P")
R = TypeVar("R")

# Try to import OpenTelemetry; fall back to no-op if not installed.
try:
    from opentelemetry import trace
    from opentelemetry.trace import StatusCode
    _tracer = trace.get_tracer("ecp.resolution")
    _OTEL_AVAILABLE = True
except ImportError:
    _OTEL_AVAILABLE = False
    _tracer = None


def traced(
    span_name: str | None = None,
    attributes: dict[str, Any] | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator that wraps an async function in an OpenTelemetry span.

    Usage::

        @traced("resolve_metric", attributes={"step": "resolve"})
        async def _resolve_orchestrator(self, ...):
            ...

    If OTel is not installed, the decorator is a transparent pass-through.
    """
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        if not _OTEL_AVAILABLE:
            return func

        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            name = span_name or func.__qualname__
            with _tracer.start_as_current_span(name) as span:
                if attributes:
                    for k, v in attributes.items():
                        span.set_attribute(k, v)
                try:
                    result = await func(*args, **kwargs)
                    span.set_status(StatusCode.OK)
                    return result
                except Exception as exc:
                    span.set_status(StatusCode.ERROR, str(exc))
                    span.record_exception(exc)
                    raise

        return wrapper  # type: ignore[return-value]
    return decorator


def record_span_attribute(key: str, value: Any) -> None:
    """Set an attribute on the current span (no-op if OTel unavailable)."""
    if _OTEL_AVAILABLE:
        span = trace.get_current_span()
        if span:
            span.set_attribute(key, value)

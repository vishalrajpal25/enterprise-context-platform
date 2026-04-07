"""Prometheus metrics for ECP resolution engine.

Exposes counters, histograms, and gauges for key operational signals.
Uses the prometheus_client library if available; degrades to no-ops otherwise.
"""
from __future__ import annotations
from typing import Any

try:
    from prometheus_client import Counter, Histogram, Gauge  # noqa: F401
    _PROM_AVAILABLE = True
except ImportError:
    _PROM_AVAILABLE = False


class _NoOpMetric:
    """Stand-in when prometheus_client is not installed."""
    def labels(self, *_a: Any, **_kw: Any) -> "_NoOpMetric":
        return self
    def inc(self, *_a: Any, **_kw: Any) -> None: ...
    def dec(self, *_a: Any, **_kw: Any) -> None: ...
    def set(self, *_a: Any, **_kw: Any) -> None: ...
    def observe(self, *_a: Any, **_kw: Any) -> None: ...


def _counter(name: str, doc: str, labels: list[str] | None = None) -> Any:
    if _PROM_AVAILABLE:
        return Counter(name, doc, labels or [])
    return _NoOpMetric()


def _histogram(name: str, doc: str, labels: list[str] | None = None, buckets: list[float] | None = None) -> Any:
    if _PROM_AVAILABLE:
        kw: dict[str, Any] = {}
        if buckets:
            kw["buckets"] = buckets
        return Histogram(name, doc, labels or [], **kw)
    return _NoOpMetric()


def _gauge(name: str, doc: str, labels: list[str] | None = None) -> Any:
    if _PROM_AVAILABLE:
        return Gauge(name, doc, labels or [])
    return _NoOpMetric()


# --- Resolution latency ---
resolution_latency = _histogram(
    "ecp_resolution_latency_seconds",
    "End-to-end resolution latency in seconds",
    labels=["mode", "status"],
    buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0],
)

# --- Cache hit rate ---
cache_hits_total = _counter(
    "ecp_cache_hits_total",
    "Total cache hits during resolution",
    labels=["cache_level"],
)
cache_misses_total = _counter(
    "ecp_cache_misses_total",
    "Total cache misses during resolution",
    labels=["cache_level"],
)

# --- Disambiguation rate ---
disambiguation_total = _counter(
    "ecp_disambiguation_total",
    "Total resolutions requiring disambiguation",
)
resolutions_total = _counter(
    "ecp_resolutions_total",
    "Total resolutions attempted",
    labels=["mode", "status"],
)

# --- Confidence distribution ---
confidence_distribution = _histogram(
    "ecp_confidence_score",
    "Distribution of overall confidence scores",
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
)

# --- Feedback rate ---
feedback_total = _counter(
    "ecp_feedback_total",
    "Total feedback submissions",
    labels=["feedback_type"],
)

# --- Active resolutions ---
active_resolutions = _gauge(
    "ecp_active_resolutions",
    "Number of currently in-flight resolutions",
)

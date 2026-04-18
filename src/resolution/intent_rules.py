"""Rule-based intent parser. Used by orchestrator mode and as the
fallback path for intelligent mode when no LLM key is configured.

Kept as a module-level function (not a method on ResolutionEngine) so
neural.py can call it without instantiating an engine — that previous
arrangement passed self=None and was a footgun.
"""
from __future__ import annotations

import re

from src.models import ParsedIntent


METRIC_KEYWORDS: dict[str, str] = {
    "free cash flow yield": "fcf_yield",
    "fcf yield": "fcf_yield",
    "cash flow yield": "fcf_yield",
    "revenue": "revenue", "sales": "revenue", "income": "revenue",
    "cost": "cost", "expense": "cost", "spend": "cost",
    "headcount": "headcount", "employees": "headcount", "staff": "headcount",
    "churn rate": "churn_rate",
    "churn": "churn", "attrition": "churn",
    "retention": "retention",
}

REGION_KEYWORDS: list[str] = [
    "apac", "emea", "americas", "latam", "na", "global",
]

TIME_KEYWORDS: dict[str, str] = {
    "last quarter": "last_quarter",
    "this quarter": "current_quarter",
    "previous quarter": "last_quarter",
    "current quarter": "current_quarter",
    "last year": "last_year",
    "this year": "current_year",
    "year to date": "year_to_date",
    "ytd": "year_to_date",
    "month to date": "month_to_date",
    "mtd": "month_to_date",
}

COMPARISON_KEYWORDS: tuple[str, ...] = ("compare", "vs", "versus", "budget", "target")

SCOPE_KEYWORDS: dict[str, str] = {
    "my tech book": "book",
    "my book": "book",
    "tech book": "book",
    "my portfolio": "book",
    "book of business": "book",
    "my accounts": "book",
}

ADJUSTMENT_KEYWORDS: dict[str, str] = {
    "peer-adjusted": "peer_adjusted",
    "peer adjusted": "peer_adjusted",
    "vs peers": "peer_adjusted",
    "relative to peers": "peer_adjusted",
    "peer comparison": "peer_adjusted",
}

# Regex for "last N quarters" pattern
_LAST_N_QUARTERS_RE = re.compile(r"last (\d+) quarters?")
# Regex for absolute quarter references like "Q4 2019" or "Q1 2025"
_ABSOLUTE_QUARTER_RE = re.compile(r"q([1-4])\s*(\d{4})", re.IGNORECASE)


def parse_intent_rules(query: str) -> ParsedIntent:
    """Extract structured intent from a natural-language query using rules only.

    Deterministic and free — used when no LLM is configured or for fast paths.
    """
    query_lower = query.lower()
    concepts: dict[str, str] = {}

    # Metric: longest match first so "free cash flow yield" beats "revenue"
    for keyword in sorted(METRIC_KEYWORDS.keys(), key=len, reverse=True):
        if keyword in query_lower:
            concepts["metric"] = METRIC_KEYWORDS[keyword]
            break

    for region in REGION_KEYWORDS:
        if region in query_lower:
            concepts["dimension"] = region
            break

    # Time: check patterns in order — absolute quarter, last N quarters, fixed phrases
    m_abs = _ABSOLUTE_QUARTER_RE.search(query_lower)
    m = _LAST_N_QUARTERS_RE.search(query_lower)
    if m_abs:
        concepts["time"] = f"q{m_abs.group(1)}_{m_abs.group(2)}"
    elif m:
        concepts["time"] = f"last_{m.group(1)}_quarters"
    else:
        # Longest match first so "last quarter" beats "quarter".
        for phrase in sorted(TIME_KEYWORDS.keys(), key=len, reverse=True):
            if phrase in query_lower:
                concepts["time"] = TIME_KEYWORDS[phrase]
                break

    if any(w in query_lower for w in COMPARISON_KEYWORDS):
        concepts["comparison"] = "budget" if "budget" in query_lower else "prior_period"

    # Scope: longest match first so "my tech book" beats "my book"
    for phrase in sorted(SCOPE_KEYWORDS.keys(), key=len, reverse=True):
        if phrase in query_lower:
            concepts["scope"] = SCOPE_KEYWORDS[phrase]
            break

    # Adjustment: longest match first
    for phrase in sorted(ADJUSTMENT_KEYWORDS.keys(), key=len, reverse=True):
        if phrase in query_lower:
            concepts["adjustment"] = ADJUSTMENT_KEYWORDS[phrase]
            break

    intent_type = "comparison" if "comparison" in concepts else "lookup"
    complexity = "simple"
    if len(concepts) >= 4:
        complexity = "cross_domain"
    elif len(concepts) >= 3:
        complexity = "multi_metric"
    return ParsedIntent(concepts=concepts, intent_type=intent_type, complexity=complexity)

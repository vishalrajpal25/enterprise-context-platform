"""Rule-based intent parser. Used by orchestrator mode and as the
fallback path for intelligent mode when no LLM key is configured.

Kept as a module-level function (not a method on ResolutionEngine) so
neural.py can call it without instantiating an engine — that previous
arrangement passed self=None and was a footgun.
"""
from __future__ import annotations

from src.models import ParsedIntent


METRIC_KEYWORDS: dict[str, str] = {
    "revenue": "revenue", "sales": "revenue", "income": "revenue",
    "cost": "cost", "expense": "cost", "spend": "cost",
    "headcount": "headcount", "employees": "headcount", "staff": "headcount",
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


def parse_intent_rules(query: str) -> ParsedIntent:
    """Extract structured intent from a natural-language query using rules only.

    Deterministic and free — used when no LLM is configured or for fast paths.
    """
    query_lower = query.lower()
    concepts: dict[str, str] = {}

    for keyword, canonical in METRIC_KEYWORDS.items():
        if keyword in query_lower:
            concepts["metric"] = canonical
            break

    for region in REGION_KEYWORDS:
        if region in query_lower:
            concepts["dimension"] = region
            break

    # Longest match first so "last quarter" beats "quarter".
    for phrase in sorted(TIME_KEYWORDS.keys(), key=len, reverse=True):
        if phrase in query_lower:
            concepts["time"] = TIME_KEYWORDS[phrase]
            break

    if any(w in query_lower for w in COMPARISON_KEYWORDS):
        concepts["comparison"] = "budget" if "budget" in query_lower else "prior_period"

    intent_type = "comparison" if "comparison" in concepts else "lookup"
    return ParsedIntent(concepts=concepts, intent_type=intent_type, complexity="simple")

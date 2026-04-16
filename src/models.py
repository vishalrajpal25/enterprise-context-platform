from __future__ import annotations
from pydantic import BaseModel, Field
from enum import Enum
from typing import Any


# ============================================================
# Resolution Request / Response
# ============================================================

class UserContext(BaseModel):
    user_id: str
    department: str = ""
    role: str = ""
    allowed_domains: list[str] = Field(default_factory=list)
    allowed_regions: list[str] = Field(default_factory=list)


class ResolveRequest(BaseModel):
    concept: str = Field(min_length=1, max_length=1000)  # "APAC revenue last quarter"
    user_context: UserContext | None = None


class Confidence(BaseModel):
    definition: float = 0.0            # How sure are we about the definition used
    data_quality: float = 0.0          # Quality of underlying data
    temporal_validity: float = 0.0     # Is data fresh and within valid range
    authorization: float = 0.0         # Does user have access
    completeness: float = 0.0          # Are all required data sources available
    overall: float = 0.0               # Weighted composite


class ResolvedConcept(BaseModel):
    concept_type: str                  # "metric", "dimension", "time", etc.
    raw_value: str                     # What the user said
    resolved_id: str                   # Canonical ID in the knowledge graph
    resolved_name: str                 # Human-readable name
    definition: str                    # Full definition text
    confidence: float                  # Concept-level confidence
    reasoning: str                     # Why this resolution was chosen


class TribalWarning(BaseModel):
    id: str
    description: str
    severity: str                      # "high", "medium", "low"
    impact: str
    workaround: str = ""


class PrecedentCorrection(BaseModel):
    """Detail of a correction precedent ready to apply as a hard override.

    Carries enough context for the engine to swap the resolved concept
    AND for the DAG step to record a human-readable reasoning string.
    """
    concept_type: str
    preferred_resolved_id: str
    preferred_resolved_name: str = ""
    department: str = ""
    corrected_at: str = ""             # ISO 8601, formatted by PrecedentEngine
    note: str = ""


class Precedent(BaseModel):
    query_id: str
    similarity: float
    original_query: str
    feedback: str                      # "accepted", "corrected", "rejected", "pending"
    influence: str                     # How this precedent affects current resolution
    # Populated when the precedent represents an actionable correction
    # propagating into the current resolution as a hard override.
    correction: PrecedentCorrection | None = None


class ExecutionStep(BaseModel):
    target: str                        # "cube.finance.Revenue.netRevenue"
    method: str                        # "semantic_layer_call"
    parameters: dict[str, Any] = Field(default_factory=dict)


class ResolutionDAGStep(BaseModel):
    step: str
    method: str
    input: dict[str, Any] = Field(default_factory=dict)
    output: dict[str, Any] = Field(default_factory=dict)
    reasoning: str = ""
    latency_ms: float = 0.0


class SourceAttributionItem(BaseModel):
    """Which federated source contributed to this resolution."""
    source_id: str
    source_kind: str                   # "native", "fabric_iq", "snowflake_sva", etc.
    certification_tier: int = 4
    used_for: list[str] = Field(default_factory=list)  # concept types this source provided


class ResolveResponse(BaseModel):
    resolution_id: str
    status: str                        # "resolved", "disambiguation_required", "failed"
    resolved_concepts: dict[str, ResolvedConcept] = Field(default_factory=dict)
    execution_plan: list[ExecutionStep] = Field(default_factory=list)
    confidence: Confidence = Field(default_factory=Confidence)
    warnings: list[TribalWarning] = Field(default_factory=list)
    precedents_used: list[Precedent] = Field(default_factory=list)
    resolution_dag: list[ResolutionDAGStep] = Field(default_factory=list)
    # Federation source attribution (v4)
    source_attribution: list[SourceAttributionItem] = Field(default_factory=list)
    # Governance / authorization fields
    policies_evaluated: list[str] = Field(default_factory=list)
    access_granted: bool = True
    filtered_concepts: list[str] = Field(default_factory=list)


# ============================================================
# Execution Request / Response
# ============================================================

class ExecuteRequest(BaseModel):
    resolution_id: str
    parameters: dict[str, Any] = Field(default_factory=dict, max_length=50)


class ExecuteResponse(BaseModel):
    results: dict[str, Any] = Field(default_factory=dict)
    confidence: Confidence = Field(default_factory=Confidence)
    warnings: list[TribalWarning] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)


# ============================================================
# Feedback
# ============================================================

class FeedbackStatus(str, Enum):
    ACCEPTED = "accepted"
    CORRECTED = "corrected"
    REJECTED = "rejected"


class CorrectionDetail(BaseModel):
    """Structured correction payload for `feedback == corrected`.

    A structured correction lets the Precedent Engine apply the user's
    fix as a hard override on similar future queries. `concept_type` and
    `preferred_resolved_id` are required for the override to fire; `note`
    is freeform context shown in the audit trail.
    """
    concept_type: str = Field(min_length=1, max_length=50)
    preferred_resolved_id: str = Field(min_length=1, max_length=200)
    preferred_resolved_name: str = Field(default="", max_length=200)
    note: str = Field(default="", max_length=2000)


class FeedbackRequest(BaseModel):
    resolution_id: str
    feedback: FeedbackStatus
    # Either a freeform string (legacy) or a structured CorrectionDetail.
    # Structured corrections enable hard-override propagation; string
    # corrections are kept for backward compatibility but do not override.
    correction_details: str | CorrectionDetail = Field(default="")


# ============================================================
# Search
# ============================================================

class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    asset_types: list[str] = Field(default_factory=list)
    limit: int = Field(default=10, ge=1, le=100)


class SearchResult(BaseModel):
    id: str
    type: str
    name: str
    description: str
    score: float


# ============================================================
# Intent (output of neural perception layer)
# ============================================================

class ParsedIntent(BaseModel):
    concepts: dict[str, str] = Field(default_factory=dict)
    # {"metric": "revenue", "dimension": "APAC", "time": "last quarter"}
    intent_type: str = "lookup"        # "lookup", "comparison", "trend", "anomaly"
    complexity: str = "simple"         # "simple", "multi_metric", "cross_domain", "novel"

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


class Precedent(BaseModel):
    query_id: str
    similarity: float
    original_query: str
    feedback: str                      # "accepted", "corrected", "rejected", "pending"
    influence: str                     # How this precedent affects current resolution


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


class ResolveResponse(BaseModel):
    resolution_id: str
    status: str                        # "resolved", "disambiguation_required", "failed"
    resolved_concepts: dict[str, ResolvedConcept] = Field(default_factory=dict)
    execution_plan: list[ExecutionStep] = Field(default_factory=list)
    confidence: Confidence = Field(default_factory=Confidence)
    warnings: list[TribalWarning] = Field(default_factory=list)
    precedents_used: list[Precedent] = Field(default_factory=list)
    resolution_dag: list[ResolutionDAGStep] = Field(default_factory=list)
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


class FeedbackRequest(BaseModel):
    resolution_id: str
    feedback: FeedbackStatus
    correction_details: str = Field(default="", max_length=4000)


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

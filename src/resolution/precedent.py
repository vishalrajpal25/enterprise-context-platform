"""Precedent Engine. Finds similar past resolutions to inform current ones.

Uses the trace store's cosine search (when embeddings are available) or
ILIKE fallback. Each precedent carries its real similarity score from the
underlying retrieval, not a hardcoded constant.

Correction precedents (feedback == "corrected") with a structured
`CorrectionDetail` payload are surfaced as `Precedent.correction` so the
ResolutionEngine can apply them as **hard overrides** rather than passive
hints. See `compute_overrides` and `find_precedents` below.
"""
from __future__ import annotations

import json
from typing import Any

from src.models import (
    ParsedIntent,
    Precedent,
    PrecedentCorrection,
    UserContext,
)
from src.traces.store import TraceStore


# Anything below this is dropped — too dissimilar to inform the current
# resolution. Calibrated for OpenAI text-embedding-3-small cosine.
MIN_PRECEDENT_SIMILARITY = 0.55

# Stricter floor for **hard overrides**. A correction propagates as a fact,
# so we want very high confidence the precedent is actually about the same
# question before swapping the resolver's choice.
MIN_OVERRIDE_SIMILARITY = 0.85


def _coerce_jsonable(value: Any) -> Any:
    """Best-effort decode of JSONB columns returned as strings or dicts."""
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (TypeError, ValueError):
            return None
    return None


def _extract_correction(row: dict, similarity: float) -> PrecedentCorrection | None:
    """Build a PrecedentCorrection from a stored trace row, if structured.

    Rows whose `correction_details` was persisted as the structured form
    (`{"structured": {...}}`) are eligible for hard override. Legacy string
    corrections (`{"details": "..."}`) carry no actionable target and are
    skipped.
    """
    details = _coerce_jsonable(row.get("correction_details"))
    if not isinstance(details, dict):
        return None
    structured = details.get("structured")
    if not isinstance(structured, dict):
        return None

    concept_type = (structured.get("concept_type") or "").strip()
    preferred_id = (structured.get("preferred_resolved_id") or "").strip()
    if not concept_type or not preferred_id:
        return None

    user_ctx = _coerce_jsonable(row.get("user_context")) or {}
    department = str(user_ctx.get("department") or "").strip()

    corrected_at = row.get("feedback_at") or ""
    if not isinstance(corrected_at, str):
        corrected_at = str(corrected_at)

    return PrecedentCorrection(
        concept_type=concept_type,
        preferred_resolved_id=preferred_id,
        preferred_resolved_name=structured.get("preferred_resolved_name", "") or "",
        department=department,
        corrected_at=corrected_at,
        note=structured.get("note", "") or "",
    )


class PrecedentEngine:
    def __init__(self, trace_store: TraceStore):
        self.traces = trace_store

    async def find_precedents(
        self, query: str, intent: ParsedIntent, user_ctx: UserContext, top_k: int = 5
    ) -> list[Precedent]:
        """Return up to top_k precedents above the similarity floor.

        For corrected precedents, attempts to attach a structured
        `PrecedentCorrection` so the engine can decide whether to apply
        the correction as a hard override.
        """
        search_terms = " ".join(intent.concepts.values()) or query

        similar = await self.traces.find_similar(
            query=search_terms, department=user_ctx.department, limit=top_k
        )

        precedents: list[Precedent] = []
        for r in similar:
            similarity = float(r.get("similarity") or 0.0)
            if similarity < MIN_PRECEDENT_SIMILARITY:
                continue

            feedback = r.get("feedback_status", "pending") or "pending"
            correction: PrecedentCorrection | None = None
            if feedback == "corrected":
                correction = _extract_correction(r, similarity)
                if correction:
                    influence = (
                        f"HARD_OVERRIDE_CANDIDATE: {correction.concept_type} → "
                        f"{correction.preferred_resolved_id} (sim={similarity:.2f})."
                    )
                else:
                    influence = (
                        "HARD_CONSTRAINT: Previous resolution was corrected "
                        "but no structured target was supplied."
                    )
            elif feedback == "accepted":
                influence = (
                    f"CONFIDENCE_BOOST: Similar query (sim={similarity:.2f}) resolved and accepted."
                )
            elif feedback == "rejected":
                influence = "AVOID: Similar resolution was rejected."
            else:
                influence = (
                    f"INFORMATIONAL: Similar query (sim={similarity:.2f}) exists, no feedback yet."
                )

            precedents.append(Precedent(
                query_id=r["query_id"],
                similarity=similarity,
                original_query=r["original_query"],
                feedback=feedback,
                influence=influence,
                correction=correction,
            ))

        return precedents

    @staticmethod
    def compute_overrides(
        precedents: list[Precedent],
        user_ctx: UserContext,
        intent: ParsedIntent,
    ) -> dict[str, list[Precedent]]:
        """Group eligible correction precedents by concept_type.

        A correction is eligible to override iff:
          - feedback == "corrected"
          - similarity > MIN_OVERRIDE_SIMILARITY (0.85)
          - precedent's user.department matches caller's user.department
          - the correction's concept_type is one being resolved now

        Returns a {concept_type: [Precedent, ...]} mapping. Concept types
        with multiple distinct preferred_resolved_id values represent a
        conflict and the engine must fall back to disambiguation.
        """
        eligible: dict[str, list[Precedent]] = {}
        caller_dept = (user_ctx.department or "").strip().lower()
        active_concepts = set(intent.concepts.keys())

        for p in precedents:
            if p.feedback != "corrected" or p.correction is None:
                continue
            if p.similarity <= MIN_OVERRIDE_SIMILARITY:
                continue
            precedent_dept = (p.correction.department or "").strip().lower()
            # Department must match. An empty caller dept never matches a
            # populated precedent dept (and vice-versa) — corrections are
            # scoped to a department by design.
            if not caller_dept or caller_dept != precedent_dept:
                continue
            if p.correction.concept_type not in active_concepts:
                continue
            eligible.setdefault(p.correction.concept_type, []).append(p)

        return eligible

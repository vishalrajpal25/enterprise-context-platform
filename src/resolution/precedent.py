"""Precedent Engine. Finds similar past resolutions to inform current ones.

Uses the trace store's cosine search (when embeddings are available) or
ILIKE fallback. Each precedent carries its real similarity score from the
underlying retrieval, not a hardcoded constant.
"""
from src.models import ParsedIntent, UserContext, Precedent
from src.traces.store import TraceStore


# Anything below this is dropped — too dissimilar to inform the current
# resolution. Calibrated for OpenAI text-embedding-3-small cosine.
MIN_PRECEDENT_SIMILARITY = 0.55


class PrecedentEngine:
    def __init__(self, trace_store: TraceStore):
        self.traces = trace_store

    async def find_precedents(
        self, query: str, intent: ParsedIntent, user_ctx: UserContext, top_k: int = 5
    ) -> list[Precedent]:
        """Return up to top_k precedents above the similarity floor."""
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
            if feedback == "corrected":
                influence = "HARD_CONSTRAINT: Previous resolution was corrected. Apply correction."
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
            ))

        return precedents

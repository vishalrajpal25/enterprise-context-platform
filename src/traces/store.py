"""Decision Trace Graph. Persists every resolution for precedent search and learning."""
import json
import logging
from typing import Any

import asyncpg

from src.config import settings
from src.context.embeddings import embeddings, format_vector_literal
from src.models import (
    CorrectionDetail,
    FeedbackStatus,
    ParsedIntent,
    ResolveRequest,
    ResolveResponse,
)

logger = logging.getLogger(__name__)


def _row_to_jsonable(row: asyncpg.Record) -> dict[str, Any]:
    d = dict(row)
    for k, v in list(d.items()):
        if hasattr(v, "isoformat"):
            d[k] = v.isoformat()
    return d


class TraceStore:
    def __init__(self):
        self._pool = None

    async def connect(self):
        self._pool = await asyncpg.create_pool(settings.postgres_dsn, min_size=2, max_size=10)

    async def close(self):
        if self._pool:
            await self._pool.close()

    async def ping(self) -> bool:
        if not self._pool:
            return False
        try:
            async with self._pool.acquire() as conn:
                value = await conn.fetchval("SELECT 1")
                return value == 1
        except Exception:
            return False

    async def get_session(self, query_id: str) -> dict[str, Any] | None:
        """Load a persisted resolution session by id (for execute and provenance)."""
        if not self._pool:
            return None
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT query_id, user_id, user_context, original_query, parsed_intent,
                       resolution_dag, stores_queried, definitions_selected, precedents_used,
                       execution_plan, status, confidence, result, started_at,
                       feedback_status
                FROM resolution_sessions
                WHERE query_id = $1
                """,
                query_id,
            )
            if not row:
                return None
            return _row_to_jsonable(row)

    async def persist_resolution(
        self, resolution_id: str, request: ResolveRequest, response: ResolveResponse,
        intent: ParsedIntent,
    ):
        """Save a complete resolution trace. Called after every successful resolution.

        Also writes a row to resolution_embeddings (query + intent vectors)
        when an embedding service is available, so find_similar() can do real
        cosine search instead of ILIKE.
        """
        # Compute which stores were actually queried during this resolution.
        # We infer from the DAG step methods rather than wiring per-call hooks —
        # this is honest because the DAG itself drives execution.
        stores_queried = self._infer_stores_queried(response)

        async with self._pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO resolution_sessions
                    (query_id, user_id, user_context, original_query, parsed_intent,
                     resolution_dag, stores_queried, definitions_selected, precedents_used,
                     execution_plan, status, confidence, result)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            """,
                resolution_id,
                request.user_context.user_id if request.user_context else "anonymous",
                json.dumps(request.user_context.model_dump() if request.user_context else {}),
                request.concept,
                json.dumps(intent.model_dump()),
                json.dumps([s.model_dump() for s in response.resolution_dag]),
                json.dumps(stores_queried),
                json.dumps({k: v.model_dump() for k, v in response.resolved_concepts.items()}),
                json.dumps([p.model_dump() for p in response.precedents_used]),
                json.dumps([s.model_dump() for s in response.execution_plan]),
                response.status,
                json.dumps(response.confidence.model_dump()),
                json.dumps({k: v.model_dump() for k, v in response.resolved_concepts.items()}),
            )

        # Embedding write (best-effort, never blocks the resolution).
        if embeddings.is_available():
            try:
                intent_summary = " ".join(intent.concepts.values()) if intent.concepts else request.concept
                vecs = await embeddings.embed_batch([request.concept, intent_summary])
                if vecs and len(vecs) == 2 and vecs[0] is not None and vecs[1] is not None:
                    qv = format_vector_literal(vecs[0])
                    iv = format_vector_literal(vecs[1])
                    async with self._pool.acquire() as conn:
                        await conn.execute(
                            """
                            INSERT INTO resolution_embeddings
                                (query_id, query_embedding, intent_embedding)
                            VALUES ($1, $2::vector, $3::vector)
                            ON CONFLICT (query_id) DO UPDATE
                              SET query_embedding = EXCLUDED.query_embedding,
                                  intent_embedding = EXCLUDED.intent_embedding
                            """,
                            resolution_id, qv, iv,
                        )
            except Exception as exc:
                logger.warning("trace embedding write failed for %s: %s", resolution_id, exc)

    @staticmethod
    def _infer_stores_queried(response: ResolveResponse) -> list[str]:
        stores: set[str] = set()
        for step in response.resolution_dag:
            method = (step.method or "").lower()
            if "graph" in method or "opa" in method:
                if "graph" in method:
                    stores.add("neo4j")
                if "opa" in method:
                    stores.add("opa")
            if "vector" in method or "embedding" in method:
                stores.add("pgvector")
            if "orchestrator" in method or "intelligent" in method:
                stores.add("postgres_registry")
        if response.execution_plan:
            stores.add("cube_semantic_layer")
        if response.precedents_used:
            stores.add("trace_store")
        return sorted(stores)

    async def persist_failure(self, resolution_id: str, request: ResolveRequest, error: str):
        async with self._pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO resolution_sessions
                    (query_id, user_id, user_context, original_query, parsed_intent,
                     resolution_dag, stores_queried, definitions_selected,
                     execution_plan, status, confidence, result)
                VALUES ($1, $2, $3, $4, '{}', '[]', '[]', '{}', '[]', 'failed', '{}', $5)
            """,
                resolution_id,
                request.user_context.user_id if request.user_context else "anonymous",
                json.dumps(request.user_context.model_dump() if request.user_context else {}),
                request.concept,
                json.dumps({"error": error}),
            )

    async def record_feedback(
        self,
        resolution_id: str,
        feedback: FeedbackStatus,
        details: str | CorrectionDetail = "",
    ) -> bool:
        # Persist structured corrections as-is so PrecedentEngine can
        # read concept_type and preferred_resolved_id back at lookup
        # time. Legacy string corrections are wrapped under "details".
        if isinstance(details, CorrectionDetail):
            payload = {"structured": details.model_dump()}
        else:
            payload = {"details": details}
        async with self._pool.acquire() as conn:
            updated = await conn.execute("""
                UPDATE resolution_sessions
                SET feedback_status = $2, feedback_at = NOW(), correction_details = $3
                WHERE query_id = $1
            """, resolution_id, feedback.value, json.dumps(payload))
            return not updated.endswith(" 0")

    async def find_similar(self, query: str, department: str = "", limit: int = 10) -> list[dict]:
        """Find similar past resolutions.

        Cosine search over query_embedding when an embedding service is
        available; ILIKE fallback otherwise. Each row carries a `similarity`
        field in [0, 1] so callers (PrecedentEngine) get a real signal.

        Includes user_context, correction_details, and feedback_at so the
        PrecedentEngine can apply department-matched correction overrides.
        """
        if embeddings.is_available():
            try:
                vec = await embeddings.embed_text(query)
                if vec is not None:
                    return await self._cosine_find_similar(vec, limit)
            except Exception as exc:
                logger.warning("trace cosine search failed, falling back to ILIKE: %s", exc)

        async with self._pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT query_id, user_context, original_query, feedback_status,
                       correction_details, feedback_at, confidence,
                       definitions_selected, started_at,
                       0.65::float AS similarity
                FROM resolution_sessions
                WHERE status = 'complete'
                  AND original_query ILIKE $1
                ORDER BY started_at DESC
                LIMIT $2
            """, f"%{query}%", limit)
            return [_row_to_jsonable(r) for r in rows]

    async def _cosine_find_similar(self, query_vec: list[float], limit: int) -> list[dict]:
        vec_literal = format_vector_literal(query_vec)
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT s.query_id, s.user_context, s.original_query,
                       s.feedback_status, s.correction_details, s.feedback_at,
                       s.confidence, s.definitions_selected, s.started_at,
                       (1 - (e.query_embedding <=> $1::vector))::float AS similarity
                FROM resolution_sessions s
                JOIN resolution_embeddings e ON e.query_id = s.query_id
                WHERE s.status = 'complete' AND e.query_embedding IS NOT NULL
                ORDER BY e.query_embedding <=> $1::vector
                LIMIT $2
                """,
                vec_literal, limit,
            )
            return [_row_to_jsonable(r) for r in rows]

"""Vector store for semantic search.

Real pgvector cosine search when an embedding service is available; falls
back to ILIKE text search when not. The fallback is honest: it's logged at
startup and the response is the same shape, but precedent boost and "fuzzy"
synonym matches will be weaker.

Schema: src/context/vector_assets table is created lazily on first connect.
It stores the asset_id, type, name, definition, and a 1536-dim embedding
of the searchable text. Populated by scripts/seed_data.py.
"""
from __future__ import annotations

import logging

import asyncpg

from src.config import settings
from src.context.embeddings import embeddings, format_vector_literal

logger = logging.getLogger(__name__)


def _create_asset_vectors_sql() -> str:
    """Build the asset_vectors DDL using the configured embedding dimension."""
    return f"""
    CREATE TABLE IF NOT EXISTS asset_vectors (
        asset_id VARCHAR(50) PRIMARY KEY REFERENCES assets(id) ON DELETE CASCADE,
        asset_type VARCHAR(50) NOT NULL,
        name TEXT NOT NULL,
        definition TEXT NOT NULL,
        embedding vector({settings.embedding_dim}),
        updated_at TIMESTAMP DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_asset_vectors_type ON asset_vectors(asset_type);
    """


class VectorClient:
    def __init__(self):
        self._pool = None

    async def connect(self):
        self._pool = await asyncpg.create_pool(settings.postgres_dsn, min_size=2, max_size=10)
        async with self._pool.acquire() as conn:
            await conn.execute(_create_asset_vectors_sql())
        embeddings.warn_if_unavailable_once()

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

    async def search(self, query: str, filter_type: str = None, top_k: int = 5) -> list[dict]:
        """Semantic search over context embeddings.

        Path 1 (preferred): real pgvector cosine search using OpenAI embeddings.
        Path 2 (fallback):  ILIKE text search when no embedding key is set or
                            when the asset_vectors table is empty.
        """
        if embeddings.is_available():
            try:
                vec = await embeddings.embed_text(query)
                if vec is not None:
                    rows = await self._cosine_search(vec, filter_type, top_k)
                    if rows:
                        return rows
            except Exception as exc:
                logger.warning("vector cosine search failed, falling back to ILIKE: %s", exc)

        return await self._ilike_search(query, filter_type, top_k)

    async def _cosine_search(
        self, query_vec: list[float], filter_type: str | None, top_k: int
    ) -> list[dict]:
        vec_literal = format_vector_literal(query_vec)
        async with self._pool.acquire() as conn:
            if filter_type:
                rows = await conn.fetch(
                    """
                    SELECT asset_id AS id, asset_type AS type, name,
                           definition,
                           1 - (embedding <=> $1::vector) AS score
                    FROM asset_vectors
                    WHERE embedding IS NOT NULL AND asset_type = $2
                    ORDER BY embedding <=> $1::vector
                    LIMIT $3
                    """,
                    vec_literal, filter_type, top_k,
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT asset_id AS id, asset_type AS type, name,
                           definition,
                           1 - (embedding <=> $1::vector) AS score
                    FROM asset_vectors
                    WHERE embedding IS NOT NULL
                    ORDER BY embedding <=> $1::vector
                    LIMIT $2
                    """,
                    vec_literal, top_k,
                )
            return [dict(r) for r in rows]

    async def _ilike_search(
        self, query: str, filter_type: str | None, top_k: int
    ) -> list[dict]:
        async with self._pool.acquire() as conn:
            if filter_type:
                rows = await conn.fetch(
                    """
                    SELECT id, type,
                           content->>'canonical_name' AS name,
                           content->>'definition' AS definition,
                           0.65 AS score
                    FROM assets
                    WHERE content::text ILIKE $1
                      AND type = $2
                    LIMIT $3
                    """,
                    f"%{query}%", filter_type, top_k,
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT id, type,
                           content->>'canonical_name' AS name,
                           content->>'definition' AS definition,
                           0.65 AS score
                    FROM assets
                    WHERE content::text ILIKE $1
                    LIMIT $2
                    """,
                    f"%{query}%", top_k,
                )
            return [dict(r) for r in rows]

    async def upsert_asset_vector(
        self,
        asset_id: str,
        asset_type: str,
        name: str,
        definition: str,
        embedding: list[float] | None,
    ) -> None:
        """Upsert one asset vector. Called by scripts/seed_data.py."""
        if not self._pool:
            raise RuntimeError("VectorClient not connected")
        vec_literal = format_vector_literal(embedding) if embedding is not None else None
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO asset_vectors (asset_id, asset_type, name, definition, embedding, updated_at)
                VALUES ($1, $2, $3, $4, $5::vector, NOW())
                ON CONFLICT (asset_id) DO UPDATE
                  SET asset_type = EXCLUDED.asset_type,
                      name = EXCLUDED.name,
                      definition = EXCLUDED.definition,
                      embedding = EXCLUDED.embedding,
                      updated_at = NOW()
                """,
                asset_id, asset_type, name, definition, vec_literal,
            )

"""Embedding service.

Provider-flexible. Reads ECP_EMBEDDING_PROVIDER from settings:
  - "voyage" (default) → Voyage AI, Anthropic's recommended embeddings
                         partner. Free tier covers the demo lifetime.
                         Default model: voyage-3-lite (1024 dims).
  - "openai"           → OpenAI text-embedding-3-small (1536 dims).
  - "none"             → No embeddings; vector search and precedent
                         similarity degrade to ILIKE text search.

The active embedding dimension is read from settings.embedding_dim and
must match the pgvector column dimension created by scripts/init_db.py.
A single env var change swaps providers cleanly.

Behavior contract: never fake an embedding. embed_text/embed_batch return
None on the unavailable path so callers can fall back honestly.
"""
from __future__ import annotations

import logging
from typing import Iterable

from src.config import settings

logger = logging.getLogger(__name__)


# Default model per provider when ECP_EMBEDDING_MODEL is unset.
DEFAULT_MODELS: dict[str, str] = {
    "voyage": "voyage-3-lite",
    "openai": "text-embedding-3-small",
}


class EmbeddingService:
    """Provider-aware embedding service with degrade-to-None fallback."""

    def __init__(self) -> None:
        self._client = None
        self._warned_unavailable = False
        self._provider = (settings.embedding_provider or "none").lower()
        self._model = settings.embedding_model or DEFAULT_MODELS.get(self._provider, "")
        self._dim = settings.embedding_dim

    @property
    def provider(self) -> str:
        return self._provider

    @property
    def model(self) -> str:
        return self._model

    @property
    def dim(self) -> int:
        return self._dim

    def is_available(self) -> bool:
        if self._provider == "voyage":
            return bool(settings.voyage_api_key)
        if self._provider == "openai":
            return bool(settings.openai_api_key)
        return False

    def warn_if_unavailable_once(self) -> None:
        """Log a single startup warning when no embedding provider is wired."""
        if self.is_available() or self._warned_unavailable:
            return
        self._warned_unavailable = True
        if self._provider == "none":
            logger.warning(
                "ECP embedding provider = 'none'. Vector search and precedent "
                "similarity will use ILIKE text search. Set "
                "ECP_EMBEDDING_PROVIDER=voyage (or openai) and provide the "
                "matching API key to enable real embedding-based retrieval."
            )
        else:
            key_var = "ECP_VOYAGE_API_KEY" if self._provider == "voyage" else "ECP_OPENAI_API_KEY"
            logger.warning(
                "ECP embedding provider = %r but %s is not set. Falling back "
                "to ILIKE text search. Add the key to enable cosine retrieval.",
                self._provider, key_var,
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def embed_text(self, text: str) -> list[float] | None:
        if not text:
            return None
        if self._provider == "voyage":
            return await self._voyage_embed_one(text)
        if self._provider == "openai":
            return await self._openai_embed_one(text)
        return None

    async def embed_batch(self, texts: Iterable[str]) -> list[list[float] | None]:
        items = [t for t in texts if t]
        if not items:
            return []
        if self._provider == "voyage":
            return await self._voyage_embed_batch(items)
        if self._provider == "openai":
            return await self._openai_embed_batch(items)
        return [None for _ in items]

    # ------------------------------------------------------------------
    # Voyage path
    # ------------------------------------------------------------------

    async def _voyage_embed_batch(self, items: list[str]) -> list[list[float] | None]:
        if not settings.voyage_api_key:
            return [None for _ in items]
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    "https://api.voyageai.com/v1/embeddings",
                    headers={
                        "Authorization": f"Bearer {settings.voyage_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self._model or "voyage-3-lite",
                        "input": items,
                        "input_type": "document",
                    },
                )
                resp.raise_for_status()
                body = resp.json()
                ordered = sorted(body.get("data", []), key=lambda d: d["index"])
                return [list(d["embedding"]) for d in ordered]
        except Exception as exc:
            logger.warning("voyage embed_batch failed: %s", exc)
            return [None for _ in items]

    async def _voyage_embed_one(self, text: str) -> list[float] | None:
        result = await self._voyage_embed_batch([text])
        return result[0] if result else None

    # ------------------------------------------------------------------
    # OpenAI path
    # ------------------------------------------------------------------

    def _get_openai_client(self):
        if self._client is not None:
            return self._client
        if not settings.openai_api_key:
            return None
        try:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        except Exception as exc:
            logger.warning("OpenAI client init failed: %s", exc)
            self._client = None
        return self._client

    async def _openai_embed_one(self, text: str) -> list[float] | None:
        client = self._get_openai_client()
        if client is None:
            return None
        try:
            resp = await client.embeddings.create(
                model=self._model or "text-embedding-3-small",
                input=text,
            )
            return list(resp.data[0].embedding)
        except Exception as exc:
            logger.warning("openai embed_text failed: %s", exc)
            return None

    async def _openai_embed_batch(self, items: list[str]) -> list[list[float] | None]:
        client = self._get_openai_client()
        if client is None:
            return [None for _ in items]
        try:
            resp = await client.embeddings.create(
                model=self._model or "text-embedding-3-small",
                input=items,
            )
            ordered = sorted(resp.data, key=lambda d: d.index)
            return [list(d.embedding) for d in ordered]
        except Exception as exc:
            logger.warning("openai embed_batch failed: %s", exc)
            return [None for _ in items]


# Module-level singleton — imported by vector.py, traces/store.py, seed_data.py.
embeddings = EmbeddingService()


def format_vector_literal(vec: list[float]) -> str:
    """Format a Python list as a pgvector literal string: '[0.1,0.2,...]'."""
    return "[" + ",".join(f"{x:.7f}" for x in vec) + "]"

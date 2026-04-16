"""Native adapter — wraps ECP's own Neo4j + PostgreSQL + pgvector stores.

This adapter is always present regardless of operating mode (standalone,
hybrid, federation). It delegates to the existing GraphClient,
RegistryClient, and VectorClient, mapping their return shapes into the
standard SourceCandidate contract so the FederationOrchestrator can treat
Native identically to any external adapter.

This is a **refactor, not a behavior change**. The resolution paths
through graph, registry, and vector are unchanged; only the call-site
in the engine shifts from direct calls to orchestrator → NativeAdapter.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from src.context.graph import GraphClient
from src.context.registry import RegistryClient
from src.context.vector import VectorClient
from src.federation.base import ContextSourceAdapter, SourceCandidate


class NativeAdapter(ContextSourceAdapter):
    source_id: str = "native"
    source_kind: str = "native"

    def __init__(
        self,
        graph: GraphClient,
        registry: RegistryClient,
        vector: VectorClient,
    ) -> None:
        self.graph = graph
        self.registry = registry
        self.vector = vector

    async def discover_concepts(
        self,
        query: str,
        concept_type: str | None = None,
        department: str = "",
        filters: dict | None = None,
    ) -> list[SourceCandidate]:
        """Search graph (primary) with vector fallback.

        Maps the existing graph.find_concept return shape into
        SourceCandidate. When concept_type is None, does a broad vector
        search instead.
        """
        candidates: list[SourceCandidate] = []

        if concept_type:
            rows = await self.graph.find_concept(concept_type, query, department)
            for row in rows:
                candidates.append(SourceCandidate(
                    source_id=self.source_id,
                    source_kind=self.source_kind,
                    concept_id=row["id"],
                    concept_type=concept_type,
                    name=row.get("name", row["id"]),
                    definition=row.get("definition", ""),
                    confidence=float(row.get("score", 0.5)),
                    certification_tier=int(row.get("certification_tier") or 4),
                    last_synced_at=datetime.now(timezone.utc),
                    payload=row,
                ))
        else:
            rows = await self.vector.search(query=query, top_k=5)
            for row in rows:
                candidates.append(SourceCandidate(
                    source_id=self.source_id,
                    source_kind=self.source_kind,
                    concept_id=row["id"],
                    concept_type=row.get("type", "unknown"),
                    name=row.get("name", row["id"]),
                    definition=row.get("definition", ""),
                    confidence=float(row.get("score", 0.5)),
                    last_synced_at=datetime.now(timezone.utc),
                    payload=row,
                ))

        return candidates

    async def get_definition(self, concept_id: str) -> dict:
        asset = await self.registry.get_asset(concept_id)
        if asset:
            return asset
        ctx = await self.graph.get_concept_context(concept_id, "")
        return ctx or {}

    async def get_relationships(self, concept_id: str) -> list[dict]:
        return await self.graph.get_metric_sources(concept_id)

    async def get_tribal_knowledge(self, concept_ids: list[str]) -> list[dict]:
        return await self.graph.find_tribal_knowledge(concept_ids)

    async def health_check(self) -> dict:
        graph_ok = await self.graph.ping()
        registry_ok = await self.registry.ping()
        vector_ok = await self.vector.ping()
        return {
            "source_id": self.source_id,
            "healthy": graph_ok and registry_ok and vector_ok,
            "components": {
                "graph": graph_ok,
                "registry": registry_ok,
                "vector": vector_ok,
            },
        }

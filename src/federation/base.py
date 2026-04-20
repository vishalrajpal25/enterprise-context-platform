"""Base class for all federated context source adapters.

Every context source — ECP's own stores (Native), Microsoft Fabric IQ,
Snowflake SVA, Glean, Atlan, dbt — implements this ABC. The
FederationOrchestrator calls these methods in parallel and merges results
with source attribution.

"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class SourceCandidate:
    """A concept candidate returned by an adapter's discover_concepts().

    Carries full source attribution so the orchestrator can merge, score,
    and trace back to whichever adapter produced the result.
    """
    source_id: str
    source_kind: str               # "native", "fabric_iq", "snowflake_sva", "glean", "atlan", "dbt"
    concept_id: str
    concept_type: str              # "metric", "dimension", "entity", etc.
    name: str
    definition: str
    confidence: float
    certification_tier: int = 4
    last_synced_at: datetime | None = None
    payload: dict[str, Any] = field(default_factory=dict)


class ContextSourceAdapter(ABC):
    """Base class for all federated context source adapters."""

    source_id: str
    source_kind: str

    @abstractmethod
    async def discover_concepts(
        self, query: str, concept_type: str | None = None, department: str = "",
        filters: dict | None = None,
    ) -> list[SourceCandidate]:
        """Search this source for matching concepts."""

    @abstractmethod
    async def get_definition(self, concept_id: str) -> dict:
        """Get the canonical definition from this source."""

    @abstractmethod
    async def get_relationships(self, concept_id: str) -> list[dict]:
        """Get entity relationships from this source."""

    @abstractmethod
    async def get_tribal_knowledge(self, concept_ids: list[str]) -> list[dict]:
        """Get known issues affecting these concepts (if supported)."""

    @abstractmethod
    async def health_check(self) -> dict:
        """Check source availability and freshness."""

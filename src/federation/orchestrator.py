"""Federation Orchestrator.

Loads enabled adapters from the context_sources registry, runs
discover_concepts() in parallel with a budget, and returns merged
SourceCandidate results with source attribution.

Conflict resolution: certification tier first, then registry.precedence,
then disambiguation_required.

See docs/enterprise-context-platform-spec-v4.md §1.3 and §3.0.
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any

from src.federation.base import ContextSourceAdapter, SourceCandidate

logger = logging.getLogger(__name__)

FEDERATION_BUDGET_MS = int(os.environ.get("ECP_FEDERATION_BUDGET_MS", "300"))


@dataclass
class SourceStatus:
    """Per-adapter status after a discovery round."""
    source_id: str
    source_kind: str
    returned: bool = False
    timed_out: bool = False
    error: str | None = None
    latency_ms: float = 0.0
    candidate_count: int = 0


@dataclass
class DiscoveryResult:
    """Aggregated result from a parallel discovery across all adapters."""
    candidates: list[SourceCandidate] = field(default_factory=list)
    source_statuses: list[SourceStatus] = field(default_factory=list)
    total_latency_ms: float = 0.0


@dataclass
class SourceAttribution:
    """Per-source contribution summary, included in ResolveResponse."""
    source_id: str
    source_kind: str
    certification_tier: int
    used_for: list[str]


class FederationOrchestrator:
    """Runs federated discovery across all enabled adapters."""

    def __init__(self, adapters: list[ContextSourceAdapter] | None = None) -> None:
        self._adapters: list[ContextSourceAdapter] = adapters or []
        self._budget_ms = FEDERATION_BUDGET_MS

    def register_adapter(self, adapter: ContextSourceAdapter) -> None:
        self._adapters.append(adapter)

    @property
    def adapters(self) -> list[ContextSourceAdapter]:
        return list(self._adapters)

    async def discover(
        self,
        query: str,
        concept_type: str | None = None,
        department: str = "",
        filters: dict | None = None,
    ) -> DiscoveryResult:
        """Run discover_concepts() on all adapters in parallel with a budget.

        Adapters that exceed the budget are recorded as timed_out but
        their partial results are still collected if available.
        """
        if not self._adapters:
            return DiscoveryResult()

        start = time.monotonic()
        budget_s = self._budget_ms / 1000.0

        async def _run_one(adapter: ContextSourceAdapter) -> tuple[ContextSourceAdapter, list[SourceCandidate] | None, str | None]:
            try:
                results = await adapter.discover_concepts(
                    query=query,
                    concept_type=concept_type,
                    department=department,
                    filters=filters,
                )
                return adapter, results, None
            except Exception as exc:
                logger.warning(
                    "adapter %s (%s) discover failed: %s",
                    adapter.source_id, adapter.source_kind, exc,
                )
                return adapter, None, str(exc)

        tasks = {
            asyncio.ensure_future(_run_one(a)): a
            for a in self._adapters
        }

        done, pending = await asyncio.wait(
            tasks.keys(), timeout=budget_s, return_when=asyncio.ALL_COMPLETED
        )

        statuses: list[SourceStatus] = []
        all_candidates: list[SourceCandidate] = []
        elapsed = (time.monotonic() - start) * 1000

        for task in done:
            adapter, candidates, error = task.result()
            status = SourceStatus(
                source_id=adapter.source_id,
                source_kind=adapter.source_kind,
                returned=candidates is not None,
                error=error,
                latency_ms=elapsed,
                candidate_count=len(candidates) if candidates else 0,
            )
            statuses.append(status)
            if candidates:
                all_candidates.extend(candidates)

        for task in pending:
            adapter = tasks[task]
            task.cancel()
            statuses.append(SourceStatus(
                source_id=adapter.source_id,
                source_kind=adapter.source_kind,
                timed_out=True,
                latency_ms=self._budget_ms,
            ))

        return DiscoveryResult(
            candidates=all_candidates,
            source_statuses=statuses,
            total_latency_ms=elapsed,
        )

    @staticmethod
    def resolve_conflicts(
        candidates: list[SourceCandidate],
    ) -> tuple[list[SourceCandidate], bool]:
        """Simple conflict resolution: tier first, then confidence.

        Returns (sorted_candidates, needs_disambiguation). If two
        candidates from different sources have the same concept_type but
        different concept_id AND the same certification_tier, we flag
        disambiguation_required.

        TODO: Precedent-based conflict resolution (spec §3.0 step 4b)
        will be added when the Precedent Engine gains cross-adapter
        awareness. For now, tier + confidence is sufficient for the
        single-adapter (Native-only) default.
        """
        if not candidates:
            return [], False

        sorted_candidates = sorted(
            candidates,
            key=lambda c: (-c.certification_tier * -1, -c.confidence),
        )
        # Properly sort: lower tier number = higher priority, then higher confidence
        sorted_candidates = sorted(
            candidates,
            key=lambda c: (c.certification_tier, -c.confidence),
        )

        # Check for conflicts: same concept_type, different concept_id,
        # from different sources, same tier
        needs_disambig = False
        by_type: dict[str, list[SourceCandidate]] = {}
        for c in sorted_candidates:
            by_type.setdefault(c.concept_type, []).append(c)

        for concept_type, group in by_type.items():
            if len(group) < 2:
                continue
            sources = {c.source_id for c in group}
            if len(sources) < 2:
                continue
            best_tier = group[0].certification_tier
            top_tier_ids = {
                c.concept_id for c in group
                if c.certification_tier == best_tier
            }
            if len(top_tier_ids) > 1:
                needs_disambig = True
                break

        return sorted_candidates, needs_disambig

    def build_source_attribution(
        self,
        used_candidates: list[SourceCandidate],
    ) -> list[SourceAttribution]:
        """Build source_attribution from the candidates actually used."""
        by_source: dict[str, SourceAttribution] = {}
        for c in used_candidates:
            key = c.source_id
            if key not in by_source:
                by_source[key] = SourceAttribution(
                    source_id=c.source_id,
                    source_kind=c.source_kind,
                    certification_tier=c.certification_tier,
                    used_for=[],
                )
            if c.concept_type not in by_source[key].used_for:
                by_source[key].used_for.append(c.concept_type)
            # Use best (lowest) tier seen
            by_source[key].certification_tier = min(
                by_source[key].certification_tier,
                c.certification_tier,
            )
        return list(by_source.values())

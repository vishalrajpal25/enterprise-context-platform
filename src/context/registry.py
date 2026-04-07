"""Asset Registry (PostgreSQL). Stores semantic contracts, glossary terms, data contracts, tribal knowledge."""
import json

import asyncpg

from src.config import settings
from src.context import fiscal as fiscal_calendar


class RegistryClient:
    def __init__(self):
        self._pool = None
        self._fiscal_ctx: fiscal_calendar.FiscalContext | None = None

    async def connect(self):
        self._pool = await asyncpg.create_pool(settings.postgres_dsn, min_size=5, max_size=20)

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

    async def get_asset(self, asset_id: str) -> dict | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, type, version, content, metadata FROM assets WHERE id = $1", asset_id
            )
            return dict(row) if row else None

    async def search_assets(self, query: str, asset_type: str = None, limit: int = 10) -> list[dict]:
        async with self._pool.acquire() as conn:
            if asset_type:
                rows = await conn.fetch(
                    """
                    SELECT id, type, content->>'canonical_name' as name,
                           content->>'definition' as description
                    FROM assets
                    WHERE content::text ILIKE $1
                      AND type = $2
                    LIMIT $3
                    """,
                    f"%{query}%",
                    asset_type,
                    limit,
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT id, type, content->>'canonical_name' as name,
                           content->>'definition' as description
                    FROM assets
                    WHERE content::text ILIKE $1
                    LIMIT $2
                    """,
                    f"%{query}%",
                    limit,
                )
            return [dict(r) for r in rows]

    async def get_metric_info(self, metric_id: str) -> dict | None:
        """Get semantic layer reference for a metric."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT content->>'semantic_layer_ref' as semantic_layer_ref,
                       content->>'measure' as measure,
                       content->>'owner' as owner,
                       content->>'definition' as definition
                FROM assets
                WHERE type IN ('metric_definition', 'glossary_term', 'data_contract')
                  AND (
                    id = $1
                    OR content->>'name' = $1
                    OR content->>'canonical_name' = $1
                  )
                LIMIT 1
            """, metric_id)
            return dict(row) if row else None

    async def _load_fiscal_context(self) -> fiscal_calendar.FiscalContext:
        if self._fiscal_ctx is not None:
            return self._fiscal_ctx
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT content FROM assets WHERE type = 'calendar_config' LIMIT 1"
            )
        content: dict | None = None
        if row and row["content"] is not None:
            raw = row["content"]
            content = raw if isinstance(raw, dict) else json.loads(raw)
        self._fiscal_ctx = fiscal_calendar.FiscalContext.from_calendar_asset(content)
        return self._fiscal_ctx

    async def resolve_time_period(self, time_id: str) -> dict | None:
        """Resolve a canonical time identifier to an absolute date range.

        Uses the fiscal calendar config asset to determine the fiscal year
        start month, then computes the range relative to *the current wall
        clock* — never frozen seed dates.
        """
        ctx = await self._load_fiscal_context()
        return fiscal_calendar.resolve(time_id, ctx)

    async def get_data_contract_for_table(self, table_id: str) -> dict | None:
        """Look up the data contract asset whose source.table matches table_id.

        Accepts any of:
            fact_revenue_daily
            finance.fact_revenue_daily
            analytics.finance.fact_revenue_daily

        Python-side matching is simpler than a SQL expression that concatenates
        three ``->>`` fields — that triggered an asyncpg type-inference error
        on our Postgres 16. We load all contracts (there are a handful) and
        match locally. Correct for any reasonable data contract cardinality.
        """
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT content FROM assets WHERE type = 'data_contract'"
            )

        for row in rows:
            raw = row["content"]
            content = raw if isinstance(raw, dict) else json.loads(raw)
            src = content.get("source") or {}
            table = src.get("table") or ""
            schema = src.get("schema") or ""
            database = src.get("database") or ""
            candidates = {
                table,
                f"{schema}.{table}",
                f"{database}.{schema}.{table}",
            }
            if table_id in candidates:
                return content
        return None

    async def get_metric_source_table(self, metric_id: str) -> str | None:
        """Return the source_table string from a metric_definition asset.

        Accepts either the asset id (e.g. `mt_net_revenue`) or the canonical
        metric name as exposed by the graph (e.g. `net_revenue`). Without
        this dual lookup, confidence scoring would silently degrade to the
        conservative-default branch on every resolution.
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT content->>'source_table' AS source_table
                FROM assets
                WHERE type = 'metric_definition'
                  AND (
                    id = $1
                    OR content->>'name' = $1
                    OR content->>'canonical_name' = $1
                  )
                LIMIT 1
                """,
                metric_id,
            )
            return row["source_table"] if row and row["source_table"] else None

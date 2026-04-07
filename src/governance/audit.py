"""Audit log writer. Extends the trace store with authorization audit entries.

Every resolution persists user identity, authorization result, and policies
evaluated, ensuring a complete audit trail for compliance.
"""
from __future__ import annotations
import json

import asyncpg

from src.config import settings
from src.governance.policy import AuthorizationResult
from src.models import UserContext


class AuditLogger:
    """Persists authorization audit events to PostgreSQL."""

    def __init__(self) -> None:
        self._pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        self._pool = await asyncpg.create_pool(settings.postgres_dsn, min_size=1, max_size=5)
        async with self._pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id SERIAL PRIMARY KEY,
                    resolution_id VARCHAR(50),
                    user_id VARCHAR(100) NOT NULL,
                    user_department VARCHAR(100),
                    user_role VARCHAR(100),
                    action VARCHAR(50) NOT NULL,
                    access_granted BOOLEAN NOT NULL,
                    denied_concepts JSONB DEFAULT '[]',
                    policies_evaluated JSONB DEFAULT '[]',
                    reason TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)

    async def close(self) -> None:
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

    async def log_authorization(
        self,
        resolution_id: str,
        user_ctx: UserContext,
        auth_result: AuthorizationResult,
        action: str = "resolve",
    ) -> None:
        """Persist an authorization decision to the audit log."""
        if not self._pool:
            return
        async with self._pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO audit_log
                    (resolution_id, user_id, user_department, user_role,
                     action, access_granted, denied_concepts,
                     policies_evaluated, reason)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """,
                resolution_id,
                user_ctx.user_id,
                user_ctx.department,
                user_ctx.role,
                action,
                auth_result.allowed,
                json.dumps(auth_result.denied_concepts),
                json.dumps(auth_result.policies_evaluated),
                auth_result.reason,
            )

    async def log_search_filter(
        self,
        user_ctx: UserContext,
        requested_count: int,
        returned_count: int,
    ) -> None:
        """Log a search filtering event."""
        if not self._pool:
            return
        async with self._pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO audit_log
                    (user_id, user_department, user_role, action,
                     access_granted, reason)
                VALUES ($1, $2, $3, 'search_filter', true, $4)
            """,
                user_ctx.user_id,
                user_ctx.department,
                user_ctx.role,
                f"Returned {returned_count} of {requested_count} results after filtering",
            )

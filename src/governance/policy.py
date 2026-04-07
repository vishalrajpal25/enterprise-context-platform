"""OPA policy client for access control evaluation.

ECP inherits and enforces access control — it never invents its own.
Identity passes through from the agent platform (JWT/OAuth) via user_context,
and OPA evaluates policies against the user's identity, role, and domain.

When OPA is unavailable, the system defaults to allow (configurable).
"""
from __future__ import annotations
import os
from typing import Any

import httpx

from src.models import UserContext


OPA_URL = os.environ.get("ECP_OPA_URL", "http://localhost:8181")
OPA_DEFAULT_ALLOW = os.environ.get("ECP_OPA_DEFAULT_ALLOW", "false").lower() == "true"


class AuthorizationResult:
    __slots__ = ("allowed", "denied_concepts", "policies_evaluated", "reason")

    def __init__(
        self,
        allowed: bool = True,
        denied_concepts: list[str] | None = None,
        policies_evaluated: list[str] | None = None,
        reason: str = "",
    ) -> None:
        self.allowed = allowed
        self.denied_concepts = denied_concepts or []
        self.policies_evaluated = policies_evaluated or []
        self.reason = reason


class OPAPolicyClient:
    """Evaluates access policies via Open Policy Agent."""

    def __init__(self, opa_url: str = OPA_URL) -> None:
        self._opa_url = opa_url.rstrip("/")

    async def ping(self) -> bool:
        """Best-effort OPA availability check."""
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                resp = await client.get(f"{self._opa_url}/health")
                return resp.status_code < 500
        except Exception:
            return False

    async def authorize_resolution(
        self,
        user_ctx: UserContext,
        resolved_concepts: dict[str, Any],
    ) -> AuthorizationResult:
        """Check whether the user may access each resolved concept.

        Calls OPA at POST /v1/data/ecp/authz with the user context and
        concept metadata. If OPA is unreachable, falls back to the
        configured default (allow or deny).

        Returns an AuthorizationResult indicating which concepts (if any)
        were denied, and which policies were evaluated.
        """
        input_doc = {
            "user": {
                "id": user_ctx.user_id,
                "department": user_ctx.department,
                "role": user_ctx.role,
                "allowed_domains": user_ctx.allowed_domains,
                "allowed_regions": user_ctx.allowed_regions,
            },
            "concepts": {
                k: {"resolved_id": v.resolved_id, "concept_type": v.concept_type}
                if hasattr(v, "resolved_id")
                else {"raw": str(v)}
                for k, v in resolved_concepts.items()
            },
        }

        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                resp = await client.post(
                    f"{self._opa_url}/v1/data/ecp/authz",
                    json={"input": input_doc},
                )
                resp.raise_for_status()
                body = resp.json()
                result = body.get("result", {})
                return AuthorizationResult(
                    allowed=result.get("allow", OPA_DEFAULT_ALLOW),
                    denied_concepts=result.get("denied_concepts", []),
                    policies_evaluated=result.get("policies_evaluated", []),
                    reason=result.get("reason", ""),
                )
        except Exception:
            # OPA unreachable — use configured default
            return AuthorizationResult(
                allowed=OPA_DEFAULT_ALLOW,
                policies_evaluated=["default_fallback"],
                reason="OPA unreachable, using default policy",
            )

    async def check_search_access(
        self,
        user_ctx: UserContext,
        asset_ids: list[str],
    ) -> list[str]:
        """Filter a list of asset IDs down to those the user may see.

        Returns the subset of asset_ids the user is authorized to access.
        Denied assets are silently omitted (not "access denied") to prevent
        information leakage.
        """
        input_doc = {
            "user": {
                "id": user_ctx.user_id,
                "department": user_ctx.department,
                "role": user_ctx.role,
                "allowed_domains": user_ctx.allowed_domains,
            },
            "asset_ids": asset_ids,
        }
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                resp = await client.post(
                    f"{self._opa_url}/v1/data/ecp/search_filter",
                    json={"input": input_doc},
                )
                resp.raise_for_status()
                body = resp.json()
                result = body.get("result", {})
                allowed_ids = result.get("allowed_ids")
                if isinstance(allowed_ids, list):
                    return allowed_ids
                return asset_ids if OPA_DEFAULT_ALLOW else []
        except Exception:
            # OPA unreachable — return all (or none, depending on policy)
            return asset_ids if OPA_DEFAULT_ALLOW else []

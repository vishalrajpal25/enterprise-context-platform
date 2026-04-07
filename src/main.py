"""Enterprise Context Platform - FastAPI Application"""
import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.config import settings
from src.context.embeddings import embeddings as embedding_service
from src.context.graph import GraphClient
from src.context.registry import RegistryClient
from src.context.vector import VectorClient
from src.governance.audit import AuditLogger
from src.governance.policy import OPAPolicyClient
from src.models import (
    Confidence,
    ExecuteRequest,
    ExecuteResponse,
    FeedbackRequest,
    ResolveRequest,
    ResolveResponse,
    SearchRequest,
    UserContext,
)
from src.resolution.engine import ResolutionEngine
from src.semantic.cube_executor import run_execution_plan
from src.traces.store import TraceStore

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def _print_startup_banner() -> None:
    mode = settings.resolution_mode.value
    has_anthropic = "yes" if settings.anthropic_api_key else "no"
    if embedding_service.is_available():
        embed_status = (
            f"{embedding_service.provider}/{embedding_service.model} "
            f"(dim={embedding_service.dim})"
        )
    else:
        embed_status = f"{embedding_service.provider} (ILIKE fallback)"
    bar = "=" * 70
    lines = [bar, " Enterprise Context Platform v3.0", bar]
    if settings.demo_mode:
        lines += [
            " DEMO MODE — public sandbox, NOT a production security boundary.",
            " OPA may be unconfigured. Do not store real data here.",
        ]
    lines += [
        f" resolution_mode = {mode}",
        f" anthropic_key   = {has_anthropic}",
        f" embeddings      = {embed_status}",
        f" cube_api        = {'configured' if settings.cube_api_url else 'dry-run'}",
        f" api_key_required= {'yes' if settings.api_key else 'no'}",
        bar,
    ]
    for line in lines:
        logger.info(line)


# Global clients (initialized on startup)
graph = GraphClient()
registry = RegistryClient()
vector = VectorClient()
traces = TraceStore()
audit = AuditLogger()
policy = OPAPolicyClient()
engine: ResolutionEngine | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global engine
    await graph.connect()
    await registry.connect()
    await vector.connect()
    await traces.connect()
    await audit.connect()
    engine = ResolutionEngine(graph, registry, vector, traces, audit)
    embedding_service.warn_if_unavailable_once()
    _print_startup_banner()
    yield
    await graph.close()
    await registry.close()
    await vector.close()
    await traces.close()
    await audit.close()


app = FastAPI(
    title="Enterprise Context Platform",
    version="3.0.0",
    description="Enterprise context layer for any AI system -- agents, copilots, workflows, applications",
    lifespan=lifespan,
)

# CORS — open in demo mode so the static demo page (hosted on GH Pages,
# Netlify, Vercel, or anywhere else) can call this API from the browser.
# In a real production deployment you'd restrict allow_origins to your
# trusted dashboards.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.demo_mode else [],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _confidence_from_trace(raw: object) -> Confidence:
    if raw is None:
        return Confidence()
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError:
            return Confidence()
    if isinstance(raw, dict):
        return Confidence(
            definition=float(raw.get("definition", 0) or 0),
            data_quality=float(raw.get("data_quality", 0) or 0),
            temporal_validity=float(raw.get("temporal_validity", 0) or 0),
            authorization=float(raw.get("authorization", 0) or 0),
            completeness=float(raw.get("completeness", 0) or 0),
            overall=float(raw.get("overall", 0) or 0),
        )
    return Confidence()


# ============================================================
# Core Endpoints (these map 1:1 to MCP tools)
# ============================================================


def _extract_user_context(request: ResolveRequest, http_request: Request) -> ResolveRequest:
    """Overlay user identity from HTTP headers onto the request if not already set."""
    if request.user_context and request.user_context.user_id != "anonymous":
        return request
    user_id = http_request.headers.get("x-ecp-user-id", "")
    department = http_request.headers.get("x-ecp-department", "")
    role = http_request.headers.get("x-ecp-role", "")
    if user_id:
        request.user_context = UserContext(
            user_id=user_id,
            department=department,
            role=role,
        )
    return request


def _extract_search_user_context(http_request: Request) -> UserContext:
    """Build UserContext from HTTP headers for search authorization."""
    return UserContext(
        user_id=http_request.headers.get("x-ecp-user-id", "anonymous"),
        department=http_request.headers.get("x-ecp-department", ""),
        role=http_request.headers.get("x-ecp-role", ""),
    )


def _require_api_key(http_request: Request) -> None:
    """Require API key when ECP_API_KEY is configured."""
    configured = settings.api_key.strip()
    if not configured:
        return
    provided = http_request.headers.get("x-ecp-api-key", "")
    if provided != configured:
        raise HTTPException(status_code=401, detail="Unauthorized: invalid API key")


def _enforce_session_owner(session: dict, http_request: Request) -> None:
    """Guard execute/provenance/feedback from cross-user access."""
    owner = str(session.get("user_id") or "").strip()
    if not owner:
        return
    caller = http_request.headers.get("x-ecp-user-id", "anonymous")
    if caller != owner:
        raise HTTPException(status_code=403, detail="Forbidden: resolution does not belong to caller")


@app.post("/api/v1/resolve", response_model=ResolveResponse)
async def resolve_concept(request: ResolveRequest, http_request: Request):
    """
    Resolve a business concept to canonical definition and execution plan.
    This is the primary entry point for AI systems.
    """
    _require_api_key(http_request)
    request = _extract_user_context(request, http_request)
    return await engine.resolve(request)


@app.post("/api/v1/execute", response_model=ExecuteResponse)
async def execute_query(request: ExecuteRequest, http_request: Request):
    """Execute a resolved query plan via the Semantic Layer (Cube.js when configured)."""
    _require_api_key(http_request)
    session = await traces.get_session(request.resolution_id)
    if not session:
        raise HTTPException(status_code=404, detail="Resolution not found")
    _enforce_session_owner(session, http_request)
    if session.get("status") != "complete":
        raise HTTPException(
            status_code=400,
            detail=f"Resolution status is {session.get('status')!r}; execute requires complete",
        )
    plan = session.get("execution_plan")
    if isinstance(plan, str):
        plan = json.loads(plan)
    if not plan:
        raise HTTPException(status_code=400, detail="No execution plan stored for this resolution")

    results, prov = await run_execution_plan(plan, request.parameters)
    confidence = _confidence_from_trace(session.get("confidence"))
    return ExecuteResponse(
        results=results,
        confidence=confidence,
        warnings=[],
        provenance={
            **prov,
            "resolution_id": request.resolution_id,
            "original_query": session.get("original_query"),
        },
    )


@app.post("/api/v1/feedback")
async def report_feedback(request: FeedbackRequest, http_request: Request):
    """Report feedback on a resolution. Feeds into Decision Trace Graph."""
    _require_api_key(http_request)
    session = await traces.get_session(request.resolution_id)
    if not session:
        raise HTTPException(status_code=404, detail="Resolution not found")
    _enforce_session_owner(session, http_request)
    updated = await traces.record_feedback(
        request.resolution_id,
        request.feedback,
        request.correction_details,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Resolution not found")
    return {"status": "recorded", "resolution_id": request.resolution_id}


@app.post("/api/v1/search")
async def search_context(request: SearchRequest, http_request: Request):
    """Search the Context Registry for definitions, tribal knowledge, data contracts."""
    _require_api_key(http_request)
    user_ctx = _extract_search_user_context(http_request)
    if settings.search_require_identity and user_ctx.user_id == "anonymous":
        await audit.log_search_filter(user_ctx, requested_count=0, returned_count=0)
        return {"results": []}

    results = await registry.search_assets(
        request.query,
        asset_type=request.asset_types[0] if request.asset_types else None,
        limit=request.limit,
    )
    requested_count = len(results)

    if results and user_ctx.user_id != "anonymous":
        asset_ids = [r["id"] for r in results if "id" in r]
        if asset_ids:
            allowed_ids = await policy.check_search_access(user_ctx, asset_ids)
            allowed_set = set(allowed_ids)
            results = [r for r in results if r.get("id") in allowed_set]
    await audit.log_search_filter(user_ctx, requested_count=requested_count, returned_count=len(results))

    return {"results": results}


@app.get("/api/v1/provenance/{resolution_id}")
async def get_provenance(resolution_id: str, http_request: Request):
    """Get full provenance for a past resolution."""
    _require_api_key(http_request)
    session = await traces.get_session(resolution_id)
    if not session:
        raise HTTPException(status_code=404, detail="Resolution not found")
    _enforce_session_owner(session, http_request)
    return session


# ============================================================
# Health
# ============================================================


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "mode": settings.resolution_mode.value,
        "demo_mode": settings.demo_mode,
        "version": "3.0.0",
        "embedding_available": embedding_service.is_available(),
    }


@app.get("/health/ready")
async def health_ready():
    checks = {
        "graph": await graph.ping(),
        "registry": await registry.ping(),
        "vector": await vector.ping(),
        "traces": await traces.ping(),
        "audit": await audit.ping(),
    }
    # OPA readiness is advisory when policy fallback is explicitly configured.
    checks["opa"] = await policy.ping()
    ready = all(v for k, v in checks.items() if k != "opa")
    status = "ready" if ready else "not_ready"
    return JSONResponse(
        status_code=200 if ready else 503,
        content={"status": status, "checks": checks, "demo_mode": settings.demo_mode},
    )


@app.get("/admin/keep-warm")
async def keep_warm():
    """Touch every backend so a single external HTTP ping (UptimeRobot, etc.)
    keeps the whole free-tier stack from auto-pausing.

    Public endpoint by design — only does cheap pings, never returns secrets,
    never accepts user data. Safe to hit from anywhere.
    """
    return {
        "ok": True,
        "checks": {
            "graph": await graph.ping(),
            "registry": await registry.ping(),
            "vector": await vector.ping(),
            "traces": await traces.ping(),
        },
        "demo_mode": settings.demo_mode,
    }

# CLAUDE.md - Enterprise Context Platform

## What This Is
Getting AI agents to answer questions correctly on enterprise data is hard, and it isn't a problem any single tool — graph, ontology, semantic layer, RAG — solves on its own. The meaning of the data lives outside the data: definitions that differ between departments, fiscal calendars nobody told the model about, tribal knowledge only the senior analyst remembers, decades of logic buried in old stored procedures.

ECP is the system that extracts that context from legacy systems, captures what people know, keeps it current, and serves it to agents (over MCP) with canonical definitions, fiscal-aware time, tribal warnings, an executable plan against the semantic layer, and a decision trace for every call. Context has to be maintained like a live service, not generated once and forgotten.

## Architecture
Agent -> MCP Server -> Resolution Engine (dual-mode) -> Context Registry (Neo4j + PostgreSQL + Vector) + Semantic Layer (Cube.js) + Decision Trace Graph (PostgreSQL)

## Key Principles
1. **Semantic Firewall**: Agents never touch raw data directly
2. **Agent Never Does Math**: LLMs reason, databases compute (deterministic via Semantic Layer)
3. **Context is the Product**: We wrap messy data with rich context, don't clean data first
4. **Manufacturing Not Art**: Factory model (Ingest > Synthesize > Ratify > Publish) scales from 10 to 1000 datasets
5. **Dual-mode Resolution**: Orchestrator (rule-based, stable) and Intelligent (neuro-symbolic, experimental), selected via ECP_RESOLUTION_MODE env var

## Tech Stack
- Python 3.11, FastAPI, asyncpg, neo4j async driver
- Neo4j 5.x (knowledge graph), PostgreSQL 16 + pgvector (asset registry + traces), Redis (cache)
- Anthropic Claude (Haiku 4.5) for neural intent parsing in intelligent mode
- Voyage AI (default) or OpenAI for embeddings — provider flexible via ECP_EMBEDDING_PROVIDER
- Docker Compose for local dev

## Running Locally
```bash
docker compose up -d
python scripts/init_db.py
python scripts/seed_data.py
uvicorn src.main:app --reload --port 8080
python scripts/demo.py  # runs canonical demo flow
```

## API Endpoints (map 1:1 to MCP tools)
- POST /api/v1/resolve - Resolve business concept to canonical definition + execution plan
- POST /api/v1/execute - Execute resolved query via Semantic Layer
- POST /api/v1/feedback - Report feedback on resolution (feeds Decision Trace Graph)
- POST /api/v1/search - Search Context Registry
- GET /api/v1/provenance/{id} - Get full provenance for past resolution
- GET /health - Health check with resolution mode

## Demo Scenario: Financial Data Company
Sample data models a Fortune 500 financial data company with:
- "Revenue" with 3 definitions (net/gross/run-rate) varying by department
- "APAC" with 2 region definitions (finance includes ANZ, sales excludes ANZ)
- Fiscal calendar (April start, so "last quarter" resolves to Q3-FY2025 = Oct-Dec 2025)
- Tribal knowledge: Q4 2019 APAC data gap, APAC cost center change in 2021, FX rate gotcha
- Data contracts with SLAs for fact_revenue_daily

## What Needs Building Next (priority order)
1. Real telemetry-based freshness (currently `temporal_validity` is derived from the data contract's freshness SLA, not observed lag — wire to Snowflake/dbt freshness metadata when available)
2. OSI Bridge for import/export of semantic definitions (dbt MetricFlow, Cube schema, LookML)
3. Drift detection service (currently a stub — diff Neo4j schema snapshots between scans, alert via webhook)
4. Tier-1 connector adapters (Snowflake INFORMATION_SCHEMA, dbt manifest.json) — replace the deleted v0.3 stubs with real, async implementations
5. MCP polish: packaged npm release, install docs

**Done in tree (v3.0):**
- Dual-mode resolution engine (orchestrator + intelligent), decision trace persisted on every call
- Real fiscal calendar resolver (computes from `datetime.now()` against the calendar config asset)
- Real graph match scoring (exact/prefix/substring + cert tier + department-variation match)
- Real confidence scoring from data contract SLAs (data_quality, completeness, freshness-derived temporal_validity)
- pgvector cosine search for asset retrieval, precedent retrieval, and trace embeddings — with honest ILIKE fallback when no embedding key is configured
- Real precedent similarity scoring from cosine, with `MIN_PRECEDENT_SIMILARITY` floor
- OPA policy enforcement (fail-closed by default), audit log on every authorization decision
- API key + per-session ownership guards on execute / feedback / provenance
- Anthropic Haiku-4.5 default for intelligent-mode intent parsing, OpenAI swappable
- MCP stdio server, `/execute` via Cube when `ECP_CUBE_API_URL` set (dry-run otherwise)
- pytest + golden eval CI job, security smoke, load smoke

## Coding Conventions
- Async everywhere (asyncpg, neo4j async driver)
- Pydantic v2 models for all request/response types
- Feature flags via ECP_ environment variables
- Every resolution persists a decision trace, no exceptions
- Type hints on all functions

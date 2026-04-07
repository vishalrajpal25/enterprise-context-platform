# CLAUDE.md - Enterprise Context Platform

**Version:** v4.0 (federation-first positioning)
**Previous:** v3.0 (standalone, live fiscal calendar + real scoring)

## What This Is
ECP is the **enterprise context layer** that gives any AI system — agents, copilots, workflows, applications — a trusted understanding of your business data. It **federates over your existing context investments** (Microsoft Fabric IQ, Snowflake SVA, Glean, Atlan, dbt), resolves conflicts between them, and gets smarter with every interaction.

Getting AI systems to answer questions correctly on enterprise data is hard, and it isn't a problem any single tool — graph, ontology, semantic layer, RAG — solves on its own. The meaning of the data lives outside the data: definitions that differ between departments, fiscal calendars nobody told the model about, tribal knowledge only the senior analyst remembers, decades of logic buried in old stored procedures.

ECP extracts that context from legacy systems, captures what people know, keeps it current, and serves it to AI systems (over MCP) with canonical definitions, fiscal-aware time, tribal warnings, an executable plan against the semantic layer, and a decision trace for every call. Context has to be maintained like a live service, not generated once and forgotten.

**Math vs Meaning:** Semantic layers do math. ECP does meaning. ECP tells the semantic layer *which* math to do, based on who is asking and what the enterprise context says is correct.

**Three operating modes:** Federation (over existing investments), Hybrid (mixed), Standalone (ECP brings its own full stack — current default for the demo).

## Architecture
AI System -> MCP Server -> Resolution Engine (dual-mode) -> Federation Adapter Layer (FabricIQ | SnowflakeSVA | Glean | Atlan | dbt | Native) -> Context Registry (Neo4j + PostgreSQL + Vector) + Semantic Layer (Cube.js) + Decision Trace Graph (PostgreSQL)

## Key Principles
1. **Semantic Firewall**: AI systems never touch raw data directly
2. **AI Reasons. Databases Compute.**: No AI system that calls ECP ever generates SQL or performs calculations. All computation happens in deterministic semantic layers.
3. **Context is the Product**: We wrap messy data with rich context, don't clean data first
4. **Manufacturing Not Art**: Factory model (Ingest > Synthesize > Ratify > Publish) scales from 10 to 1000 datasets
5. **Dual-mode Resolution**: Orchestrator (rule-based, stable) and Intelligent (neuro-symbolic, experimental), selected via ECP_RESOLUTION_MODE env var
6. **Federation-First Distribution**: ECP consumes context from wherever it already exists (Fabric IQ ontologies, Snowflake semantic views, Glean knowledge graphs, Atlan metadata, dbt metrics) and adds what none of them provide: cross-estate resolution, tribal knowledge, certification tiers, and decision trace learning.

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
1. **Federation Adapter Layer** (`src/federation/`) — base `ContextSourceAdapter` class plus concrete adapters: `FabricIQAdapter` (MCP), `SnowflakeSVAAdapter` (API), `GleanAdapter` (API), `AtlanAdapter` (MCP), `DbtAdapter` (OSI), `NativeAdapter` (always on). See `docs/enterprise-context-platform-spec-v4.md` §1.3.
2. **Conflict resolution logic** in the Resolution Engine: parallel discovery across adapters, source-attributed merging, certification-tier + precedent-based conflict resolution, `disambiguation_required` fallback. See spec-v4 §3.0 (Source-Aware Resolution).
3. Real telemetry-based freshness (currently `temporal_validity` is derived from the data contract's freshness SLA, not observed lag — wire to Snowflake/dbt freshness metadata when available)
4. OSI Bridge for import/export of semantic definitions (dbt MetricFlow, Cube schema, LookML)
5. Drift detection service (currently a stub — diff Neo4j schema snapshots between scans, alert via webhook)
6. Tier-1 connector adapters (Snowflake INFORMATION_SCHEMA, dbt manifest.json) — replace the deleted v0.3 stubs with real, async implementations
7. MCP polish: packaged npm release, install docs

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

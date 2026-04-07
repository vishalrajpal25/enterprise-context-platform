# Enterprise Context Platform

> The enterprise context layer that gives any AI system a trusted understanding of your business data. Federates over existing context investments (Microsoft IQ, Snowflake SVA, Glean, Atlan, dbt) or brings its own.

Getting AI systems to answer questions correctly on enterprise data is hard, and it's not a problem you can solve by picking the right database or the right retrieval trick. The meaning of the data lives outside the data — in definitions that differ between departments, in fiscal calendars nobody told the model about, in tribal knowledge that only the senior analyst remembers, in decades of logic buried in old stored procedures.

A knowledge graph can't fix this on its own. Neither can an ontology, or a semantic layer, or RAG. Each of those is useful, but each is a component. What's actually needed is a system that extracts this context from legacy systems, captures what people know, keeps it current as the business changes, and serves it to AI systems with enough provenance that the answers can be trusted.

ECP is that system. It's built around the idea that context has to be maintained like a live service, not generated once and forgotten. AI systems — agents, copilots, workflows, applications — talk to it over MCP and get back canonical definitions, time periods resolved against the real fiscal calendar, warnings from known issues, an execution plan against your semantic layer, and a decision trace for every call.

**Math vs Meaning:** Semantic layers do math. ECP does meaning. ECP tells the semantic layer *which* math to do, based on who is asking and what the enterprise context says is correct.

## Why no single tool solves this

Every category in the market right now is being sold as if it were the answer. Each one is genuinely useful, but each is a part.

- **Ontology.** A description of what concepts exist and how they relate. It's a document. It doesn't notice when finance quietly changes the definition of APAC in 2021. It doesn't get tribal knowledge out of the senior analyst's head before she retires. An ontology is a plan, not a worker.
- **Knowledge graph or graph database.** A storage engine that's good at relationships and traversals. It will happily store "APAC includes ANZ" and "APAC excludes ANZ" as equally valid facts and shrug when an agent asks which is right. A graph is a warehouse, not a factory.
- **Semantic layer** (Cube, dbt MetricFlow, LookML). Defines metrics deterministically so the math is consistent. But it assumes someone already figured out what the metrics should be, already resolved the conflicts, already accounted for the fiscal calendar and the 2019 data gap. It executes context; it doesn't manufacture it.
- **Data catalog.** Inventories what you have. It doesn't know what any of it actually means in the way an analyst who's been there ten years means it.
- **RAG.** Retrieves documents that look relevant and stuffs them into a prompt. It has no concept of canonical meaning, department-specific variation, fiscal time, data quality SLAs, or "this answer was corrected last week, apply the correction."

Each of these is real and useful inside a bigger thing. The bigger thing is not another noun. It's a system that uses all of them, continuously, with feedback and governance, to manufacture and maintain the context that agents need.

## Architecture

```
AI System (Claude / GPT / Copilot / agent / workflow / app)
   │  MCP stdio  /  REST  /  OSI
   ▼
ECP API (FastAPI)
   │
   ├─ Resolution Engine (orchestrator | intelligent)
   │
   ├─ Federation Adapter Layer (v4)
   │     ├─ FabricIQAdapter      (MCP)        — Microsoft Fabric IQ ontology
   │     ├─ SnowflakeSVAAdapter  (API)        — Snowflake Semantic Views
   │     ├─ GleanAdapter         (API)        — Glean Enterprise Graph
   │     ├─ AtlanAdapter         (MCP)        — Atlan metadata + lineage
   │     ├─ DbtAdapter           (OSI)        — dbt MetricFlow definitions
   │     └─ NativeAdapter        (always on)  — ECP's own stores below
   │
   ├─ Knowledge Graph (Neo4j) — relationships, variations, lineage
   ├─ Asset Registry (Postgres + JSONB) — versioned definitions, contracts, tribal knowledge
   ├─ Vector Store (Postgres + pgvector) — Voyage or OpenAI embeddings, with honest ILIKE fallback
   ├─ Decision Trace Store (Postgres) — every resolution, for learning and audit
   ├─ OPA Policy — fail-closed by default
   └─ Semantic Layer Executor (Cube.js REST) — deterministic computation against your warehouse
```

**Three operating modes:** Federation (federates over existing investments), Hybrid (federates where possible, brings its own for gaps), Standalone (default for the demo, ECP brings its own full stack).

## What's in the box (v3.0)

| Capability | Status | Source |
|---|---|---|
| Dual-mode resolution (orchestrator + intelligent) | real | [src/resolution/engine.py](src/resolution/engine.py) |
| Live fiscal calendar (`last_quarter` → `Q4-FY2026` from `datetime.now()`) | real | [src/context/fiscal.py](src/context/fiscal.py) |
| Real graph match scoring (exact / prefix / substring + cert tier + dept variation) | real | [src/context/graph.py](src/context/graph.py) |
| pgvector cosine search (assets + precedent traces) | real, with ILIKE fallback | [src/context/vector.py](src/context/vector.py), [src/traces/store.py](src/traces/store.py) |
| Confidence scoring from real data contract SLAs | real | `_contract_quality` in [src/resolution/engine.py](src/resolution/engine.py) |
| Tribal knowledge surfaced in every resolution | real | seed has 3 entries; [src/context/graph.py](src/context/graph.py) |
| OPA policy enforcement, fail-closed default | real | [src/governance/policy.py](src/governance/policy.py) |
| API key + per-session ownership guards | real | [src/main.py](src/main.py) |
| Audit log on every authorization decision | real | [src/governance/audit.py](src/governance/audit.py) |
| Decision trace persisted on every resolution | real | [src/traces/store.py](src/traces/store.py) |
| Cube.js execution (dry-run when unconfigured) | real | [src/semantic/cube_executor.py](src/semantic/cube_executor.py) |
| MCP stdio server | real | [src/protocol/mcp_server.mjs](src/protocol/mcp_server.mjs) |
| Anthropic Haiku-4.5 default for intent parsing | real, swappable to OpenAI | [src/resolution/neural.py](src/resolution/neural.py) |
| Voyage / OpenAI dual-provider embeddings | real, config-driven | [src/context/embeddings.py](src/context/embeddings.py) |
| Static touch-and-feel demo page | real | [docs/demo/index.html](docs/demo/index.html) |

## What's still aspirational

- Real telemetry-based freshness (currently uses the SLA from the data contract, not observed lag — see [CLAUDE.md](CLAUDE.md))
- Drift detection service (was a stub; removed in v3 until real)
- Snowflake / dbt / Looker connector adapters (the v0.x stubs were sync inside an async app — deleted in v3)
- OSI Bridge for import/export across semantic tools

We removed the broken or unimplemented surfaces rather than ship them dressed up.

## Quick start (local)

```bash
docker compose up -d
python scripts/init_db.py
python scripts/seed_data.py        # uses VOYAGE_API_KEY or OPENAI_API_KEY for embeddings if set
uvicorn src.main:app --reload --port 8080
python scripts/demo.py             # canonical resolution flow
```

Open [docs/demo/index.html](docs/demo/index.html) directly in a browser, or serve it with `python -m http.server` from `docs/demo/` — it talks to `http://localhost:8080` by default. Pass `?api=https://your-deploy.example.com` to point it elsewhere.

> In **federation mode**, configure adapters in `config/adapters.yaml` (planned in v4 — see `docs/enterprise-context-platform-spec-v4.md` §1.3). In **standalone mode** (default for the demo), ECP uses its own Neo4j + PostgreSQL stores via `NativeAdapter`.

### Environment variables

| Var | Default | Notes |
|---|---|---|
| `ECP_RESOLUTION_MODE` | `orchestrator` | `intelligent` enables LLM intent parsing |
| `ECP_DEMO_MODE` | `false` | Set `true` for public sandbox: prints banner, opens CORS |
| `ECP_API_KEY` | unset | When set, every API call needs `x-ecp-api-key` |
| `ECP_OPA_DEFAULT_ALLOW` | `false` (fail-closed) | Set `true` *only* for the public demo with no OPA |
| `ECP_SEARCH_REQUIRE_IDENTITY` | `true` | Anonymous search returns empty when true |
| `ECP_EMBEDDING_PROVIDER` | `voyage` | `voyage` \| `openai` \| `none` |
| `ECP_EMBEDDING_MODEL` | provider default | `voyage-3-lite` (1024d) or `text-embedding-3-small` (1536d) |
| `ECP_EMBEDDING_DIM` | `1024` | Must match the active provider; re-run `init_db.py` after changing |
| `ECP_VOYAGE_API_KEY` | unset | Free tier at voyageai.com — no card required |
| `ECP_OPENAI_API_KEY` | unset | Pay-per-use, ~$0.05 lifetime at demo scale |
| `ECP_ANTHROPIC_API_KEY` | unset | Used by intelligent mode for intent parsing |
| `ECP_LLM_MODEL` | `claude-haiku-4-5-20251001` | Override to `claude-sonnet-4-6` for harder reasoning |
| `ECP_CUBE_API_URL` | unset | When set, `/execute` calls Cube; else dry-run |
| `ECP_NEO4J_URI` / `ECP_POSTGRES_DSN` / `ECP_REDIS_URL` | local Docker | Override for hosted backends |

When no embedding key is set, the system logs a startup warning and degrades to ILIKE text search transparently. It never silently fakes a vector.

## Demo scenario

The seed models a Fortune 500 financial data company:

- **Revenue** has 3 definitions (net / gross / run-rate) varying by department
- **APAC** has 2 region definitions (finance includes ANZ, sales excludes ANZ)
- **Fiscal calendar** starts in April. "Last quarter" resolves *live* against `datetime.now()`
- **Tribal knowledge**: Q4 2019 APAC data gap, APAC cost-center change in 2021, FX rate gotcha
- **Data contracts** with real SLA values feeding confidence scoring
- New in v3: `headcount`, `cost`, `retention`, `region_americas` so the golden eval has full coverage

## API endpoints (1:1 with MCP tools)

| | |
|---|---|
| `POST /api/v1/resolve` | Resolve concept → canonical defs + execution plan + DAG + tribal warnings + confidence |
| `POST /api/v1/execute` | Run a stored resolution against Cube.js (or dry-run) |
| `POST /api/v1/feedback` | Record `accepted` / `corrected` / `rejected` — feeds precedent learning |
| `POST /api/v1/search` | Search the registry (cosine if embeddings available, ILIKE otherwise) |
| `GET  /api/v1/provenance/{id}` | Full DAG, stores queried, definitions selected, execution plan |
| `GET  /health` | `{status, mode, demo_mode, embedding_available}` |
| `GET  /health/ready` | All backend ping checks |
| `GET  /admin/keep-warm` | Cheap ping for UptimeRobot — keeps free-tier backends alive |

## Tests

```bash
uv pip install --python .venv/bin/python -e ".[dev]"
PYTHONPATH=. .venv/bin/python -m pytest tests/ -q
.venv/bin/ruff check src tests
```

CI runs ruff, pytest, the golden eval suite (13 reference queries), a security smoke (IDOR + API key), and a load smoke (p95 budget). See [.github/workflows/ci.yml](.github/workflows/ci.yml).

## Free public deploy

Hosting target: $0/month. The whole stack stays alive because a single UptimeRobot HTTP check pinging `/admin/keep-warm` every 5 minutes touches every backend.

1. **Render free** for the web service ([Dockerfile](Dockerfile) + [render.yaml](render.yaml))
2. **Neon free** Postgres (includes pgvector). Connection string → `ECP_POSTGRES_DSN` (with `sslmode=require`)
3. **Neo4j AuraDB Free**. Connection string → `ECP_NEO4J_URI` (`neo4j+s://…`)
4. **Upstash Redis free** *(optional, currently unused at runtime)*
5. **Voyage AI** — sign up at voyageai.com (no card), set `ECP_VOYAGE_API_KEY`. Or use OpenAI by setting `ECP_EMBEDDING_PROVIDER=openai` + `ECP_OPENAI_API_KEY`.
6. **Anthropic** — set `ECP_ANTHROPIC_API_KEY` to enable intelligent mode.
7. **UptimeRobot** — add an HTTP check on `https://<your-render>.onrender.com/admin/keep-warm` every 5 minutes.

First-deploy bootstrap (one-time):
1. Set `ECP_BOOTSTRAP_DB=true` and `ECP_AUTO_SEED_DEMO=true`, redeploy
2. Verify `https://<service>.onrender.com/health` returns `demo_mode: true`
3. Flip both flags back to `false`

Then point [docs/demo/index.html](docs/demo/index.html) at the live URL by opening it with `?api=https://<service>.onrender.com`, or fork the repo and host the page from GitHub Pages.

## License

Apache 2.0 — see [LICENSE](LICENSE). [CONTRIBUTING.md](CONTRIBUTING.md) for development workflow.

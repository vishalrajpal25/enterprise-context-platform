# Enterprise Context Platform

**The MCP server that resolves business meaning for AI systems.** Not an agent — a context layer that any AI system calls before it touches enterprise data.

Semantic layers do math. ECP does meaning. ECP tells the semantic layer *which* math to do, based on who is asking and what the enterprise context says is correct.

```
AI System (Claude / GPT / Copilot / agent / workflow)
   |  MCP (primary) / REST / gRPC
   v
Enterprise Context Platform          <-- one MCP server per estate
   |
   +-- Resolution Engine             resolves "APAC revenue last quarter" to canonical definitions
   +-- Federation Adapter Layer      fans out to your existing context stores
   +-- Knowledge Graph (Neo4j)       relationships, department variations, lineage
   +-- Asset Registry (Postgres)     versioned definitions, contracts, tribal knowledge
   +-- Vector Store (pgvector)       semantic search with ILIKE fallback
   +-- Decision Trace Store          every resolution persisted for learning and audit
   +-- OPA Policy Engine             fail-closed authorization
   +-- Semantic Layer (Cube.js)      deterministic computation against your warehouse
```

## The problem

Getting AI systems to answer questions correctly on enterprise data is hard. The meaning of the data lives *outside* the data: definitions that differ between departments, fiscal calendars nobody told the model about, tribal knowledge only the senior analyst remembers. No single tool (graph, ontology, semantic layer, RAG) solves this alone.

ECP extracts that context, keeps it current, and serves it to AI systems with canonical definitions, fiscal-aware time, tribal warnings, an execution plan, and a decision trace for every call.

## How it works

Register ECP as an MCP server. Your AI system gets six tools:

| MCP Tool | What it does |
|---|---|
| `set_persona` | Set user identity (department, role) for the session |
| `resolve_concept` | Resolve a business question to canonical definitions + execution plan |
| `execute_metric` | Run the resolved plan against the semantic layer |
| `search_context` | Search the context registry |
| `get_provenance` | Full decision DAG for any past resolution |
| `report_feedback` | Accept, correct, or reject a resolution (feeds learning) |

The agent never sees a table name, a SQL fragment, or a schema. That's the semantic firewall: **AI reasons, databases compute.**

## Same question, different correct answers

> **"What was APAC revenue last quarter?"**

| | Finance Analyst | Sales Director |
|---|---|---|
| **Metric** | Net Revenue (ASC 606, tier 1) | Gross Revenue (invoiced, tier 2) |
| **APAC** | Includes AU + NZ | Excludes AU + NZ |
| **Last quarter** | Q4-FY2026 (Jan-Mar, fiscal year starts April) | Q4-FY2026 (same) |
| **Warnings** | 3 tribal (data gap, cost center change, FX) | 2 tribal (data gap, FX) |
| **Confidence** | 0.90 | 0.90 |

Neither is wrong. Context is the product.

## Quick start

```bash
# Infrastructure
docker compose up -d          # Neo4j, Postgres+pgvector, Redis

# Initialize and seed
uv run python scripts/init_db.py
uv run python scripts/seed_data.py

# Start ECP
ECP_OPA_DEFAULT_ALLOW=true uv run python -m uvicorn src.main:app --reload --port 8080

# Start the Observer UI (optional, separate terminal)
cd observer && npm install && npm run dev    # http://localhost:5174

# Verify
bash scripts/demo_preflight.sh
```

### Claude Desktop integration

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "enterprise-context-platform": {
      "command": "node",
      "args": ["/path/to/enterprise-context-platform/src/protocol/mcp_server.mjs"],
      "env": {
        "ECP_BASE_URL": "http://127.0.0.1:8080",
        "ECP_API_KEY": ""
      }
    }
  }
}
```

Restart Claude Desktop. Say "I'm a finance analyst" then ask any business question.

## Enterprise demo scenarios

| Question | What it showcases |
|---|---|
| "What was APAC revenue last quarter?" | Department-specific metric + region + live fiscal calendar |
| "Revenue for APAC Q4 2019" | Tribal knowledge trap (data 15% underreported) |
| "APAC cost breakdown last quarter" | Tribal warning fires on non-revenue metric |
| "What is our headcount trend this year?" | Data contract SLA drives confidence (24h freshness) |
| "What's the churn rate this quarter vs last?" | Low-quality data source (48h freshness, temporal_validity 0.50) |
| "FCF yield for my tech book, peer-adjusted" | Cross-domain resolution (3 concepts, department-specific variations) |
| "Compare EMEA and Americas revenue YTD" | Comparison intent, region variation |

## Observer UI

The Observer (`observer/`) is a live visualization that shows every resolution stage in real time — what stores were queried, what concepts were resolved, what tribal warnings fired, and the full confidence breakdown. Run it alongside Claude Desktop to make the black box transparent.

```
+----------------------------+-----------------------------+
| Resolution Flow            | Detail Panel                |
|                            |                             |
| Parse Intent       2ms  +  | Resolved: net_revenue       |
| Resolve Concepts  50ms  +  | Definition: ASC 606...      |
| Tribal Check      25ms  !  | Reasoning: Graph match 1.00 |
| Precedent          3ms  +  |                             |
| Authorization      4ms  +  | Confidence Bars:            |
| Build Plan        15ms  +  | definition    [==========] 1.0  |
| Persist Trace      2ms  +  | data_quality  [=========.] 0.99 |
|                            | temporal      [==========] 1.0  |
| Total: 101ms | Conf: 0.90 | authorization [==========] 1.0  |
+----------------------------+-----------------------------+
| Recent: rs_...48b (0.90) | rs_...9cf (0.90) | ...       |
+-----------------------------------------------------------+
```

## Architecture

**Federation Adapter Layer (v4):** ECP federates over existing context investments. The Resolution Engine queries adapters in parallel with a latency budget; results are merged with source attribution; conflicts are resolved by certification tier, precedent, or disambiguation. Currently ships with `NativeAdapter` (Neo4j + Postgres); external adapters (Fabric IQ, Snowflake SVA, Glean, Atlan, dbt) are the ABC interface, ready to implement.

**Precedent learning:** Every resolution is persisted. When a user corrects a resolution, similar future queries apply the correction as a hard override (similarity > 0.85, department match). The system learns from every interaction without retraining a model.

**Governance:** OPA policy enforcement (fail-closed), per-session ownership guards (no cross-user access to traces), audit log on every authorization decision. ECP is not an access control layer — it's a policy evaluation point that federates entitlements from your existing systems.

## Tech stack

- Python 3.11, FastAPI, asyncpg, neo4j async driver
- Neo4j 5.x (knowledge graph), PostgreSQL 16 + pgvector (registry + traces), Redis (cache)
- Anthropic Claude Haiku 4.5 for neural intent parsing (optional, orchestrator mode is deterministic)
- Voyage AI or OpenAI for embeddings (optional, falls back to ILIKE)
- Node.js MCP SDK for the stdio server
- Vite + React + TypeScript for the Observer UI
- Docker Compose for local dev

## Environment variables

| Variable | Default | Notes |
|---|---|---|
| `ECP_RESOLUTION_MODE` | `orchestrator` | `intelligent` enables LLM intent parsing |
| `ECP_API_KEY` | unset | When set, every request needs `x-ecp-api-key` |
| `ECP_OPA_DEFAULT_ALLOW` | `false` | Set `true` only for demos without OPA deployed |
| `ECP_EMBEDDING_PROVIDER` | `voyage` | `voyage` / `openai` / `none` |
| `ECP_VOYAGE_API_KEY` | unset | Free tier at voyageai.com |
| `ECP_CUBE_API_URL` | unset | When set, `/execute` calls Cube; else dry-run |
| `ECP_NEO4J_URI` | `bolt://localhost:7687` | Override for hosted Neo4j (Aura) |
| `ECP_POSTGRES_DSN` | `postgresql://ecp:ecp_local_dev@localhost:5432/ecp` | Override for hosted Postgres (Neon) |

## API endpoints

| Endpoint | MCP Tool | Purpose |
|---|---|---|
| `POST /api/v1/resolve` | `resolve_concept` | Resolve concept to definitions + plan + DAG |
| `POST /api/v1/execute` | `execute_metric` | Run plan via semantic layer |
| `POST /api/v1/feedback` | `report_feedback` | Record feedback, feed learning loop |
| `POST /api/v1/search` | `search_context` | Search context registry |
| `GET /api/v1/provenance/{id}` | `get_provenance` | Full decision trace |
| `GET /api/v1/telemetry/stream` | — | SSE stream for Observer UI |
| `GET /health` | — | Health check |

## Deployment

See [docs/DEPLOY.md](docs/DEPLOY.md) for Render + Neon + Neo4j Aura deployment guide.

## Tests

```bash
uv run python -m pytest tests/ -q     # 54 tests
cd observer && npm test                 # 4 tests
cd observer && npm run build            # TypeScript + Vite build
```

## License

Apache 2.0 — see [LICENSE](LICENSE).

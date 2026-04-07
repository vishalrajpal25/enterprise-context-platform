# Enterprise Context Platform: Technical Architecture v4

**Version: 4.0 | April 2026 | Audience: Engineering & Architecture Teams | Status: Implementation-Ready (Phases 1-3), Research Preview (Phases 4-5)**

> **v4 positioning:** ECP is the enterprise context layer that gives any AI system -- agents, copilots, workflows, applications -- a trusted understanding of your business data. It federates over existing context investments (Microsoft Fabric IQ, Snowflake SVA, Glean, Atlan, dbt) via a Federation Adapter Layer, or runs standalone on its own stores. Semantic layers do math; ECP does meaning.

---

## 1. SYSTEM ARCHITECTURE

### 1.1 Component Stack

```
+------------------------------------------------------------------------+
|                     AI SYSTEM RUNTIME LAYER                            |
|        (Azure AI Foundry / Vertex AI / Bedrock / Frontier / Cowork /   |
|         Copilots / Workflow engines / AI-powered applications)         |
|                  AI system makes tool/function calls                   |
+---------------------------------+--------------------------------------+
                                  |
                                  | MCP / REST / gRPC
                                  |
+---------------------------------v--------------------------------------+
|                  INTELLIGENT RESOLUTION ENGINE                         |
|                  (Python 3.11 + FastAPI Service)                       |
|                                                                        |
|  +------------+  +-------------+  +------------+  +-----------+       |
|  | Neural     |  | Symbolic    |  | Precedent  |  | Query     |       |
|  | Perception |->| Reasoning   |->| Engine     |->| Planner   |       |
|  | (Intent,   |  | (Graph,     |  | (Decision  |  | (Compose, |       |
|  |  Matching) |  |  Rules,     |  |  Traces,   |  |  Optimize,|       |
|  |            |  |  Ontology)  |  |  Learning) |  |  Execute) |       |
|  +------------+  +-------------+  +------------+  +-----------+       |
|                                                                        |
|  +-------------------+  +-------------------+  +------------------+   |
|  | Authorizer (OPA)  |  | Validator         |  | Assembler        |   |
|  |                   |  | (Business Rules)  |  | (Provenance)     |   |
|  +-------------------+  +-------------------+  +------------------+   |
|                                                                        |
|  State: Resolution DAG (Redis) | Cache: L1/L2/L3 Multi-Level         |
+------------------------------------------------------------------------+
                                 |
                                 v
+------------------------------------------------------------------------+
|                    FEDERATION ADAPTER LAYER (NEW in v4)                |
|                                                                        |
|  +----------+ +----------+ +-------+ +-------+ +-----+ +-------------+|
|  | FabricIQ | | Snowflake| | Glean | | Atlan | | dbt | | Native      ||
|  | Adapter  | | SVA      | |       | |       | |     | | (always on) ||
|  | (MCP)    | | Adapter  | |       | |       | |     | |             ||
|  +----------+ +----------+ +-------+ +-------+ +-----+ +-------------+|
|                                                                        |
|  Parallel discovery | Source-attributed merging | Conflict resolution  |
+------------------------------------------------------------------------+
            |                  |                  |                |
            v                  v                  v                v
+----------------+  +----------------+  +----------------+  +----------+
| Knowledge Graph|  | Vector Store   |  | Asset Registry |  | Semantic |
| (Neo4j 5.x)   |  | (Pinecone)     |  | (PostgreSQL 15)|  | Layer    |
|                |  |                |  |                |  | (Cube.js)|
| - Entities     |  | - Embeddings   |  | - Glossary     |  |          |
| - Relationships|  | - Semantic     |  | - Contracts    |  | - Metrics|
| - Lineage DAG  |  |   Search       |  | - Tribal KB    |  | - Dims   |
| - Ontology     |  |                |  | - Policies     |  | - Exec   |
| - Temporal     |  |                |  | - Migration    |  |          |
|   Edges (NEW)  |  |                |  |   Records (NEW)|  |          |
+----------------+  +----------------+  +----------------+  +----+-----+
            |                  |                  |               |
            v                  v                  v               v
+------------------------------------------------------------------------+
|               DECISION TRACE GRAPH (NEW)                               |
|               (PostgreSQL + Neo4j Temporal Edges)                      |
|                                                                        |
|  - Resolution Sessions (full DAG of every resolution)                 |
|  - Human Overrides (corrections, exceptions, approvals)               |
|  - Precedent Links (similar resolutions connected)                    |
|  - Feedback Signals (accepted, rejected, corrected)                   |
|  - Drift Events (schema changes, validation failures)                 |
+------------------------------------------------------------------------+
            |
            v
+------------------------------------------------------------------------+
|               DRIFT DETECTION SERVICE (NEW)                            |
|               (Scheduled Jobs + Event-Driven Monitors)                 |
|                                                                        |
|  - Schema Change Monitors (Information Schema / Unity Catalog)        |
|  - Validation Runners (scheduled contract validation)                 |
|  - OSI Sync (import/export semantic definitions)                      |
|  - Alert Engine (notify contract owners on drift)                     |
+------------------------------------------------------------------------+
            |
            v
+------------------------------------------------------------------------+
|                       PHYSICAL DATA ESTATE                             |
|        Snowflake / Databricks / SQL Server / Oracle / etc.            |
+------------------------------------------------------------------------+
```

### 1.2 Technology Stack

| Layer | Component | Technology | Port/Protocol | Purpose |
|---|---|---|---|---|
| API Gateway | Load Balancer | Nginx/Envoy | 443/HTTPS | TLS termination, rate limiting |
| Orchestration | Resolution Engine | Python 3.11 + FastAPI | 8080/HTTP | Core neuro-symbolic logic |
| Orchestration | MCP Server | Node.js + MCP SDK | 3000/SSE | AI system integration (Frontier, Cowork, Copilots, custom) |
| Orchestration | OSI Bridge | Python 3.11 | 8082/HTTP | OSI import/export |
| Orchestration | State Store | Redis 7.x | 6379/Redis | Session state, multi-level cache |
| Context | Knowledge Graph | Neo4j 5.x Enterprise | 7687/Bolt | Relationships, lineage, temporal edges |
| Context | Vector Store | Pinecone Serverless | HTTPS/gRPC | Semantic search, fuzzy matching |
| Context | Asset Registry | PostgreSQL 15 | 5432/PostgreSQL | Structured metadata, decision traces |
| Compute | Semantic Layer | Cube.js 0.35+ | 4000/HTTP | Deterministic metric execution |
| Policy | Authorization | OPA 0.60+ | 8181/HTTP | Policy evaluation |
| Learning | Precedent Engine | Python + pgvector | Internal | Resolution trace similarity search |
| Monitoring | Drift Detection | Python + APScheduler | Internal | Schema monitoring, validation |
| Monitoring | Observability | Datadog/Prometheus | - | Metrics, traces, logs |

### 1.3 Federation Adapter Layer (NEW in v4)

The Federation Adapter Layer abstracts the difference between ECP's native stores and external context sources (Microsoft Fabric IQ, Snowflake SVA, Glean, Atlan, dbt). The Resolution Engine queries adapters in parallel; results are merged with source attribution; conflicts are resolved by certification tier, decision-trace precedent, or disambiguation prompt.

```python
class ContextSourceAdapter(ABC):
    """Base class for all federated context source adapters."""

    @abstractmethod
    async def discover_concepts(self, query: str, filters: dict = None) -> list[dict]:
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


# Concrete adapters:
# FabricIQAdapter      - Consumes Microsoft Fabric IQ ontology via MCP server
# SnowflakeSVAAdapter  - Consumes Snowflake Semantic Views via API
# GleanAdapter         - Consumes Glean Enterprise Graph for unstructured knowledge
# AtlanAdapter         - Consumes Atlan metadata and lineage via MCP server
# DbtAdapter           - Consumes dbt MetricFlow definitions via OSI
# NativeAdapter        - ECP's own Neo4j + PostgreSQL stores (always present)
```

**Operating modes:**
- **Federation:** Multiple external adapters + Native (for tribal knowledge, decision traces, certification tiers).
- **Hybrid:** A subset of external adapters + Native fills the gaps.
- **Standalone:** Only the Native adapter is active. ECP builds context via the Factory Model.

**Adapter discovery rules:** All configured adapters run in parallel. Each candidate result carries `source_id`, `source_kind`, `confidence`, and `last_synced_at`. The Resolution Engine then applies conflict resolution (see Section 3, Source-Aware Resolution).

### 1.4 Protocol Integration Layer (NEW)

```
+------------------------------------------------------------------------+
|                     PROTOCOL INTEGRATION LAYER                          |
|                                                                        |
|  MCP Server              OSI Bridge              REST/gRPC API         |
|  +------------------+   +------------------+   +------------------+   |
|  | resolve_concept  |   | import_from_     |   | POST /resolve    |   |
|  | execute_metric   |   |   snowflake_sva  |   | POST /execute    |   |
|  | get_provenance   |   | import_from_dbt  |   | GET /contract    |   |
|  | search_context   |   | export_osi_yaml  |   | GET /provenance  |   |
|  | report_feedback  |   | sync_definitions |   | POST /feedback   |   |
|  +------------------+   +------------------+   +------------------+   |
|                                                                        |
|  Any MCP-compatible      Any OSI-compatible      Any HTTP client       |
|  AI system (Claude,      tool (dbt, Looker,      (custom AI systems,   |
|  GPT, Copilot, custom)   ThoughtSpot, Sigma)     dashboards, workflows)|
+------------------------------------------------------------------------+
```

---

## 2. DATA MODELS

### 2.1 Knowledge Graph Schema (Neo4j) -- Updated

```cypher
// ============================================================
// CORE ENTITY TYPES (unchanged from v2)
// ============================================================

(:Entity {
  id: string,
  name: string,
  domain: string,         // "sales", "finance", "operations"
  description: string,
  created_at: datetime,
  updated_at: datetime
})

(:Attribute {
  id: string,
  name: string,
  data_type: string,
  nullable: boolean,
  pii: boolean
})

(:Metric {
  id: string,
  name: string,
  description: string,
  semantic_layer_ref: string,
  asset_registry_id: string,
  certification_tier: integer,
  owner: string
})

(:GlossaryTerm {
  id: string,
  canonical_name: string,
  asset_registry_id: string
})

(:Column {
  id: string,
  table_id: string,
  name: string,
  data_type: string
})

(:Table {
  id: string,
  schema: string,
  name: string,
  platform: string
})

(:TribalKnowledge {
  id: string,
  asset_registry_id: string,
  severity: string
})

// ============================================================
// NEW IN V3: TEMPORAL EDGES AND DECISION TRACES
// ============================================================

// Decision Trace Node (links resolutions to the knowledge graph)
(:ResolutionTrace {
  id: string,              // "rt_20260315_001"
  query_id: string,        // reference to resolution_sessions
  resolved_at: datetime,
  user_id: string,
  user_department: string,
  confidence_score: float,
  feedback: string,        // "accepted", "corrected", "rejected"
  correction_note: string  // if corrected, what changed
})

// Migration Record Node
(:MigrationEvent {
  id: string,
  event_type: string,      // "table_moved", "column_renamed",
                           // "source_deprecated", "schema_changed"
  source_platform: string,
  target_platform: string,
  occurred_at: datetime,
  description: string,
  impact_assessed: boolean
})

// ============================================================
// RELATIONSHIPS (updated)
// ============================================================

// Core relationships (unchanged)
(:Entity)-[:HAS_ATTRIBUTE]->(:Attribute)
(:Entity)-[:MAPS_TO {context: string}]->(:Entity)
(:Metric)-[:DEFINED_BY]->(:GlossaryTerm)
(:Metric)-[:USES_DIMENSION]->(:Attribute)
(:Metric)-[:COMPUTED_FROM]->(:Column)
(:Metric)-[:HAS_KNOWN_ISSUE]->(:TribalKnowledge)
(:Column)-[:BELONGS_TO]->(:Table)
(:Column)-[:TRANSFORMS_TO {logic: string}]->(:Column)
(:GlossaryTerm)-[:HAS_VARIATION {context: string}]->(:GlossaryTerm)

// NEW: Temporal relationships for decision traces
(:ResolutionTrace)-[:RESOLVED_METRIC]->(:Metric)
(:ResolutionTrace)-[:USED_DEFINITION]->(:GlossaryTerm)
(:ResolutionTrace)-[:SIMILAR_TO {
  similarity_score: float,
  similarity_method: string  // "embedding", "structural", "user_context"
}]->(:ResolutionTrace)

// NEW: Migration relationships
(:MigrationEvent)-[:AFFECTED_TABLE]->(:Table)
(:MigrationEvent)-[:AFFECTED_COLUMN]->(:Column)
(:MigrationEvent)-[:AFFECTED_CONTRACT]->(contract_node)

// NEW: Temporal validity on edges
// All COMPUTED_FROM and TRANSFORMS_TO edges now carry temporal validity
(:Metric)-[:COMPUTED_FROM {
  valid_from: datetime,
  valid_until: datetime,     // null = currently valid
  logic: string,
  migration_event_id: string // null if not migration-related
}]->(:Column)
```

### 2.2 Asset Registry Schema (PostgreSQL) -- Updated

```sql
-- ============================================================
-- CORE TABLES (unchanged from v2)
-- ============================================================

CREATE TABLE assets (
    id VARCHAR(50) PRIMARY KEY,
    type VARCHAR(50) NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    content JSONB NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),
    CONSTRAINT valid_type CHECK (type IN (
        'glossary_term', 'data_contract', 'validation_rule',
        'tribal_knowledge', 'policy', 'query_template',
        'migration_record'  -- NEW
    ))
);

CREATE INDEX idx_assets_type ON assets(type);
CREATE INDEX idx_assets_content_gin ON assets USING GIN(content);

-- ============================================================
-- NEW IN V3: DECISION TRACE TABLES
-- ============================================================

-- Resolution sessions (expanded from v2)
CREATE TABLE resolution_sessions (
    query_id VARCHAR(50) PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,
    user_context JSONB NOT NULL,       -- {department, role, allowed_regions, ...}
    original_query TEXT NOT NULL,
    parsed_intent JSONB NOT NULL,      -- NEW: structured intent from neural layer
    resolution_dag JSONB NOT NULL,     -- full resolution path
    stores_queried JSONB NOT NULL,     -- NEW: which stores were hit, latencies
    definitions_selected JSONB NOT NULL, -- NEW: which definitions chosen and why
    precedents_used JSONB,             -- NEW: which past resolutions informed this one
    execution_plan JSONB NOT NULL,
    status VARCHAR(20) NOT NULL,
    confidence JSONB NOT NULL,         -- NEW: multi-dimensional confidence
    -- {definition: 0.95, data_quality: 0.88, temporal: 0.92,
    --  authorization: 1.0, completeness: 0.90, overall: 0.93}
    result JSONB,
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    -- NEW: feedback fields
    feedback_status VARCHAR(20) DEFAULT 'pending',
    -- "pending", "accepted", "corrected", "rejected"
    feedback_at TIMESTAMP,
    feedback_by VARCHAR(100),
    correction_details JSONB,          -- what was wrong, what should have been used
    CONSTRAINT valid_status CHECK (status IN (
        'parsing', 'resolving', 'planning', 'authorizing',
        'executing', 'validating', 'complete', 'failed'
    ))
);

CREATE INDEX idx_resolution_user ON resolution_sessions(user_id);
CREATE INDEX idx_resolution_status ON resolution_sessions(status);
CREATE INDEX idx_resolution_feedback ON resolution_sessions(feedback_status);
CREATE INDEX idx_resolution_started ON resolution_sessions(started_at);

-- Resolution trace embeddings (for precedent search)
CREATE TABLE resolution_embeddings (
    query_id VARCHAR(50) PRIMARY KEY REFERENCES resolution_sessions(query_id),
    query_embedding vector(1536),      -- embedding of original query
    intent_embedding vector(1536),     -- embedding of parsed intent
    resolution_embedding vector(1536), -- embedding of resolution path
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_resolution_query_embed ON resolution_embeddings
    USING ivfflat (query_embedding vector_cosine_ops);
CREATE INDEX idx_resolution_intent_embed ON resolution_embeddings
    USING ivfflat (intent_embedding vector_cosine_ops);

-- ============================================================
-- NEW IN V3: DRIFT DETECTION TABLES
-- ============================================================

CREATE TABLE drift_events (
    id VARCHAR(50) PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    -- "schema_change", "validation_failure", "freshness_breach",
    -- "definition_conflict", "source_deprecated"
    platform VARCHAR(50) NOT NULL,     -- "snowflake", "databricks", "oracle"
    affected_object TEXT NOT NULL,      -- table/column/view identifier
    affected_contracts JSONB,          -- list of contract IDs impacted
    details JSONB NOT NULL,            -- change details
    detected_at TIMESTAMP DEFAULT NOW(),
    resolved_at TIMESTAMP,
    resolved_by VARCHAR(100),
    resolution_action TEXT,
    severity VARCHAR(20) NOT NULL,     -- "critical", "warning", "info"
    CONSTRAINT valid_severity CHECK (severity IN ('critical', 'warning', 'info'))
);

CREATE INDEX idx_drift_platform ON drift_events(platform);
CREATE INDEX idx_drift_severity ON drift_events(severity);
CREATE INDEX idx_drift_detected ON drift_events(detected_at);

-- Contract version history (for migration resilience)
CREATE TABLE contract_versions (
    id SERIAL PRIMARY KEY,
    asset_id VARCHAR(50) REFERENCES assets(id),
    version INTEGER NOT NULL,
    content JSONB NOT NULL,
    change_reason TEXT,                -- "migration", "correction", "update"
    migration_event_id VARCHAR(50),    -- reference to drift_events if applicable
    created_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(100),
    is_current BOOLEAN DEFAULT true
);

CREATE INDEX idx_contract_versions_asset ON contract_versions(asset_id);
CREATE INDEX idx_contract_versions_current ON contract_versions(is_current);


-- ============================================================
-- NEW IN V3: OSI INTERCHANGE TABLE
-- ============================================================

CREATE TABLE osi_sync_log (
    id SERIAL PRIMARY KEY,
    direction VARCHAR(10) NOT NULL,     -- "import", "export"
    source_tool VARCHAR(100) NOT NULL,  -- "snowflake_sva", "dbt_metricflow", "looker"
    definitions_synced INTEGER NOT NULL,
    conflicts_detected INTEGER DEFAULT 0,
    conflicts_resolved INTEGER DEFAULT 0,
    sync_at TIMESTAMP DEFAULT NOW(),
    details JSONB
);
```

### 2.3 Decision Trace Graph: Example Structures

```json
// Resolution session with full trace
{
  "query_id": "rs_20260315_042",
  "original_query": "What was APAC revenue last quarter compared to budget?",
  "parsed_intent": {
    "concepts": {
      "metric": {"raw": "revenue", "candidates": ["net_revenue", "gross_revenue"]},
      "dimension": {"raw": "APAC", "candidates": ["region_apac_finance", "region_apac_sales"]},
      "time": {"raw": "last quarter", "candidates": ["Q3-FY2025", "Q3-CY2025"]},
      "comparison": {"raw": "budget", "candidates": ["budget_net_revenue"]}
    },
    "intent_type": "comparison_query",
    "complexity": "multi_metric"
  },
  "resolution_dag": {
    "steps": [
      {
        "step": "resolve_revenue",
        "method": "graph_lookup + user_context",
        "input": {"term": "revenue", "user_dept": "finance"},
        "output": {"selected": "net_revenue", "confidence": 0.95},
        "reasoning": "User department is finance; net_revenue is canonical for finance context. 23 precedent resolutions confirm this pattern."
      },
      {
        "step": "resolve_apac",
        "method": "graph_lookup + variation_match",
        "input": {"term": "APAC", "context": "finance"},
        "output": {"selected": "region_apac_finance", "countries": ["JP","KR","SG","HK","TW","AU","NZ","IN","CN"]},
        "reasoning": "Finance context includes ANZ. Sales context excludes ANZ. Selected finance variation based on user context."
      },
      {
        "step": "resolve_last_quarter",
        "method": "calendar_config",
        "input": {"term": "last quarter", "fiscal_year_start": "April"},
        "output": {"selected": "Q3-FY2025", "date_range": ["2025-10-01", "2025-12-31"]},
        "reasoning": "Organization uses April fiscal year start. Current date is March 2026. Last fiscal quarter is Q3-FY2025."
      },
      {
        "step": "check_tribal_knowledge",
        "method": "vector_search + graph_traversal",
        "input": {"metric": "net_revenue", "region": "APAC", "period": "Q3-FY2025"},
        "output": {"issues_found": 0},
        "reasoning": "No known issues for APAC net_revenue in Q3-FY2025. (Note: Q4-FY2020 has known data gap.)"
      }
    ]
  },
  "precedents_used": [
    {
      "query_id": "rs_20260301_018",
      "similarity": 0.94,
      "original_query": "APAC revenue vs budget Q2",
      "outcome": "accepted",
      "influence": "Confirmed finance definition of APAC and net_revenue"
    }
  ],
  "confidence": {
    "definition": 0.95,
    "data_quality": 0.92,
    "temporal_validity": 0.98,
    "authorization": 1.0,
    "completeness": 0.90,
    "overall": 0.94
  }
}
```

---

## 3. INTELLIGENT RESOLUTION ENGINE

### 3.0 Source-Aware Resolution (NEW in v4)

When resolving a concept in federation or hybrid mode, the engine queries all configured adapters in the Federation Adapter Layer:

1. **Parallel discovery.** All adapters (`FabricIQAdapter`, `SnowflakeSVAAdapter`, `GleanAdapter`, `AtlanAdapter`, `DbtAdapter`, `NativeAdapter`) search simultaneously via `discover_concepts(query, filters)`.
2. **Result merging.** Candidates are collected with full source attribution: `(concept_id, source_id, source_kind, definition, confidence, last_synced_at)`.
3. **Conflict detection.** If two sources define the same logical concept differently (e.g., Fabric IQ says "Revenue = recognized" and Snowflake SVA says "Revenue = booked"), the candidates are flagged as a conflict cluster.
4. **Conflict resolution.** Apply, in order:
   - **Certification tier priority** (Tier 1 > Tier 2 > Tier 3 > Tier 4)
   - **Decision-trace precedent** (if a similar resolution was previously accepted, prefer that source)
   - **Disambiguation prompt** (if no clear winner, return `disambiguation_required` to the calling AI system with all candidates and their source attribution)
5. **Provenance tracking.** Every response includes `source_attribution[]` listing which adapter each definition, relationship, and tribal-knowledge fragment came from. The decision trace persists this for learning.

In standalone mode, only `NativeAdapter` runs and conflict resolution is a no-op.

### 3.1 Architecture

```
User Query: "What was APAC revenue last quarter compared to budget?"
                            |
                            v
+====================================================================+
|                    NEURAL PERCEPTION LAYER                          |
|                    (System 1: Fast, Intuitive)                      |
|                                                                     |
|  LLM Intent Parsing:                                               |
|    - Extract entities: metric, dimension, time, comparison         |
|    - Classify intent type: comparison_query                        |
|    - Generate candidate interpretations with initial confidence    |
|    - Produce query embedding for precedent search                  |
|                                                                     |
|  Vector Similarity Search (parallel):                              |
|    - Glossary terms matching "revenue" -> [net_revenue, gross_..] |
|    - Glossary terms matching "APAC" -> [region_apac_finance, ..]  |
|    - Tribal knowledge matching "APAC revenue" -> [known issues]   |
+====================================================================+
                            |
                            v
+====================================================================+
|                    SYMBOLIC REASONING LAYER                         |
|                    (System 2: Deliberate, Logical)                  |
|                                                                     |
|  Graph Traversal (Neo4j):                                          |
|    - Resolve "revenue" to metric node via DEFINED_BY edges         |
|    - Check HAS_VARIATION edges for context-specific definitions    |
|    - Traverse COMPUTED_FROM to find authoritative columns          |
|    - Check temporal validity on all edges (valid_from/valid_until) |
|    - Traverse MAPS_TO for cross-domain entity resolution           |
|                                                                     |
|  Ontology Inference:                                               |
|    - Apply domain constraints (finance context -> ASC 606 rules)  |
|    - Check consistency (APAC + net_revenue: compatible?)           |
|    - Resolve calendar config (fiscal vs. calendar quarter)         |
|                                                                     |
|  Rule Application:                                                 |
|    - Validation rules for the selected metric                      |
|    - Policy checks (does user have access to this data?)          |
|    - Business rules (revenue non-negative, variance bounds)        |
+====================================================================+
                            |
                            v
+====================================================================+
|                    PRECEDENT ENGINE (NEW)                            |
|                    (Learning from Past Resolutions)                  |
|                                                                     |
|  Query Decision Trace Graph:                                       |
|    - Embed current query and find top-k similar past resolutions   |
|    - Weight by: recency, same user, same department, feedback      |
|    - If high-confidence precedent exists AND was accepted:         |
|      -> Boost confidence in matching resolution path               |
|    - If similar query was corrected:                               |
|      -> Apply correction as hard constraint                        |
|    - If similar query was rejected:                                |
|      -> Avoid that resolution path, try alternatives               |
|                                                                     |
|  Practical now: embedding similarity + keyword matching            |
|  Research frontier: RL-optimized resolution path selection         |
+====================================================================+
                            |
                            v
+====================================================================+
|                    COMPOSITIONAL QUERY PLANNER                      |
|                    (Build the Execution Plan)                       |
|                                                                     |
|  For templated queries (80% of cases):                             |
|    - Select pre-approved query template from Asset Registry        |
|    - Fill in resolved parameters (metric, filters, time range)     |
|    - Map to Semantic Layer API calls (Cube.js)                     |
|                                                                     |
|  For novel queries (20% of cases):                                 |
|    - LLM-guided plan synthesis: compose Semantic Layer calls       |
|    - Validate plan against Semantic Layer capabilities             |
|    - If cross-platform: plan federated execution strategy          |
|    - Estimate cost and latency before execution                    |
|                                                                     |
|  Practical now: template matching + simple composition             |
|  Research frontier: LLM-guided program synthesis, RL-optimized     |
|  federated join ordering                                           |
+====================================================================+
                            |
                            v
+====================================================================+
|                    AUTHORIZE + EXECUTE + VALIDATE                    |
|                                                                     |
|  Authorize: OPA policy check against user context                  |
|  Execute: Semantic Layer calls (Cube.js API)                       |
|  Validate: Business rules, anomaly detection, bounds checking      |
|  Assemble: Construct response with full provenance                 |
|  Persist: Save resolution trace to Decision Trace Graph            |
+====================================================================+
```

### 3.2 Neural Perception Layer: Implementation

```python
class NeuralPerceptionLayer:
    """
    System 1: Fast, intuitive understanding of user intent.
    Uses LLM for parsing and vector store for semantic matching.
    """

    async def perceive(self, query: str, user_context: dict) -> PerceptionResult:
        # Parallel execution: LLM parsing + vector searches
        intent_task = self.parse_intent(query, user_context)
        embedding_task = self.embed_query(query)

        intent, query_embedding = await asyncio.gather(intent_task, embedding_task)

        # Parallel vector searches for each extracted concept
        concept_searches = []
        for concept_type, raw_value in intent.concepts.items():
            concept_searches.append(
                self.search_candidates(raw_value, concept_type, user_context)
            )

        candidate_sets = await asyncio.gather(*concept_searches)

        return PerceptionResult(
            intent=intent,
            query_embedding=query_embedding,
            candidates={
                concept_type: candidates
                for concept_type, candidates in zip(intent.concepts.keys(), candidate_sets)
            },
            initial_confidence=self.estimate_confidence(intent, candidate_sets)
        )

    async def parse_intent(self, query: str, user_context: dict) -> Intent:
        """
        LLM-based intent parsing. Extracts structured intent from natural language.
        Uses few-shot examples from successful past resolutions.
        """
        # Fetch recent successful resolutions as few-shot examples
        examples = await self.get_resolution_examples(user_context.get("department"))

        response = await self.llm.generate(
            system_prompt=INTENT_PARSING_PROMPT,
            user_prompt=f"""
            User: {user_context}
            Query: {query}

            Extract: metric, dimensions, time_range, comparison, aggregation
            Classify: intent_type (lookup, comparison, trend, anomaly, exploratory)
            Estimate: complexity (simple, multi_metric, cross_domain, novel)
            """,
            examples=examples,
            response_format=IntentSchema
        )
        return Intent.from_llm_response(response)

    async def search_candidates(
        self, raw_value: str, concept_type: str, user_context: dict
    ) -> list[Candidate]:
        """
        Vector similarity search for candidate concepts.
        Filters by concept type and user-accessible domains.
        """
        embedding = await self.embed(raw_value)
        results = await self.vector_store.query(
            vector=embedding,
            filter={
                "type": concept_type,
                "domain": {"$in": user_context.get("allowed_domains", [])}
            },
            top_k=5,
            include_metadata=True
        )
        return [
            Candidate(
                id=r.id,
                name=r.metadata["term"],
                asset_registry_id=r.metadata["asset_registry_id"],
                graph_node_id=r.metadata["graph_node_id"],
                similarity_score=r.score,
                domain=r.metadata["domain"]
            )
            for r in results
        ]
```

### 3.3 Symbolic Reasoning Layer: Implementation

```python
class SymbolicReasoningLayer:
    """
    System 2: Deliberate, logical reasoning over the knowledge graph.
    Resolves ambiguity using formal constraints and graph inference.
    """

    async def reason(
        self, perception: PerceptionResult, user_context: dict
    ) -> ReasoningResult:

        resolved_concepts = {}

        for concept_type, candidates in perception.candidates.items():
            resolved = await self.resolve_concept(
                concept_type, candidates, user_context, perception.intent
            )
            resolved_concepts[concept_type] = resolved

        # Check cross-concept consistency
        consistency = await self.check_consistency(resolved_concepts)
        if not consistency.is_consistent:
            resolved_concepts = await self.resolve_inconsistencies(
                resolved_concepts, consistency.conflicts
            )

        # Check tribal knowledge for resolved concepts
        tribal_warnings = await self.check_tribal_knowledge(resolved_concepts)

        return ReasoningResult(
            resolved_concepts=resolved_concepts,
            tribal_warnings=tribal_warnings,
            consistency=consistency
        )

    async def resolve_concept(
        self, concept_type: str, candidates: list[Candidate],
        user_context: dict, intent: Intent
    ) -> ResolvedConcept:
        """
        Graph-based concept resolution with ontology inference.

        This is where the symbolic reasoning happens:
        1. For each candidate, traverse graph to find full context
        2. Apply domain constraints based on user context
        3. Check temporal validity
        4. Score candidates based on graph evidence
        """
        scored_candidates = []

        for candidate in candidates:
            # Graph traversal: get full context for this candidate
            graph_context = await self.graph.query(f"""
                MATCH (n {{id: '{candidate.graph_node_id}'}})
                OPTIONAL MATCH (n)-[r1:DEFINED_BY]->(g:GlossaryTerm)
                OPTIONAL MATCH (g)-[r2:HAS_VARIATION {{context: '{user_context["department"]}'}}]->(v:GlossaryTerm)
                OPTIONAL MATCH (n)-[r3:COMPUTED_FROM]->(c:Column)-[:BELONGS_TO]->(t:Table)
                WHERE r3.valid_until IS NULL  // only currently valid sources
                OPTIONAL MATCH (n)-[r4:HAS_KNOWN_ISSUE]->(tk:TribalKnowledge)
                WHERE tk.active = true
                RETURN n, g, v, collect(distinct c) as columns,
                       collect(distinct t) as tables,
                       collect(distinct tk) as issues
            """)

            # Score based on: semantic similarity, graph evidence,
            # user context match, temporal validity
            score = self.score_candidate(
                candidate, graph_context, user_context, intent
            )
            scored_candidates.append((candidate, graph_context, score))

        # Select best candidate
        best = max(scored_candidates, key=lambda x: x[2])
        return ResolvedConcept(
            candidate=best[0],
            graph_context=best[1],
            confidence=best[2],
            reasoning=self.explain_selection(best, scored_candidates)
        )

    async def check_tribal_knowledge(
        self, resolved_concepts: dict
    ) -> list[TribalWarning]:
        """
        Search for known issues that affect the resolved concepts.
        Uses both vector search (for broad matching) and graph traversal
        (for precise relationship-based matching).
        """
        warnings = []

        # Build a scoped search from resolved concepts
        scope = self.build_scope(resolved_concepts)

        # Vector search: broad matching
        vector_results = await self.vector_store.query(
            vector=await self.embed(scope.to_search_string()),
            filter={"type": "tribal_knowledge"},
            top_k=10
        )

        # Graph traversal: precise relationship matching
        graph_results = await self.graph.query(f"""
            MATCH (tk:TribalKnowledge)-[:AFFECTS]->(n)
            WHERE n.id IN {scope.affected_node_ids}
            AND tk.active = true
            RETURN tk
        """)

        # Merge and deduplicate
        for tk in self.merge_results(vector_results, graph_results):
            warnings.append(TribalWarning(
                id=tk.id,
                description=tk.description,
                severity=tk.severity,
                impact=tk.impact,
                workaround=tk.workaround
            ))

        return warnings
```

### 3.4 Precedent Engine: Implementation (NEW)

```python
class PrecedentEngine:
    """
    Learns from past resolutions to improve future ones.

    Practical now: embedding similarity + feedback-weighted scoring.
    Research frontier: RL-optimized resolution path selection.
    """

    async def find_precedents(
        self, query_embedding: ndarray, intent: Intent, user_context: dict,
        top_k: int = 10
    ) -> list[Precedent]:
        """
        Find similar past resolutions and extract learning signals.
        """
        # Step 1: Embedding similarity search (fast, approximate)
        similar_resolutions = await self.db.execute("""
            SELECT rs.query_id, rs.original_query, rs.resolution_dag,
                   rs.definitions_selected, rs.feedback_status,
                   rs.correction_details, rs.confidence,
                   1 - (re.intent_embedding <=> $1) as similarity
            FROM resolution_embeddings re
            JOIN resolution_sessions rs ON rs.query_id = re.query_id
            WHERE rs.status = 'complete'
            AND 1 - (re.intent_embedding <=> $1) > 0.7  -- similarity threshold
            ORDER BY similarity DESC
            LIMIT $2
        """, intent_embedding, top_k * 2)  # oversample, then filter

        # Step 2: Apply structural filters (same concept types, similar complexity)
        filtered = [
            r for r in similar_resolutions
            if self.structural_match(r, intent)
        ]

        # Step 3: Score with feedback weighting
        scored = []
        for r in filtered[:top_k]:
            score = r.similarity

            # Boost accepted resolutions
            if r.feedback_status == "accepted":
                score *= 1.2

            # Strongly boost same-user or same-department
            if r.user_context.get("department") == user_context.get("department"):
                score *= 1.1

            # Penalize rejected resolutions
            if r.feedback_status == "rejected":
                score *= 0.5

            # Recency weighting (exponential decay)
            days_ago = (datetime.now() - r.completed_at).days
            recency_weight = math.exp(-0.01 * days_ago)
            score *= recency_weight

            scored.append(Precedent(
                query_id=r.query_id,
                similarity=score,
                original_query=r.original_query,
                resolution_path=r.resolution_dag,
                definitions_used=r.definitions_selected,
                feedback=r.feedback_status,
                correction=r.correction_details,
                influence=self.determine_influence(r)
            ))

        return sorted(scored, key=lambda p: p.similarity, reverse=True)

    def determine_influence(self, resolution) -> str:
        """
        Determine how this precedent should influence the current resolution.
        """
        if resolution.feedback_status == "corrected":
            return f"HARD_CONSTRAINT: Previous resolution was corrected. " \
                   f"Apply correction: {resolution.correction_details}"
        elif resolution.feedback_status == "accepted":
            return f"CONFIDENCE_BOOST: Similar query was resolved this way " \
                   f"and accepted by user."
        elif resolution.feedback_status == "rejected":
            return f"AVOID: Similar resolution was rejected. " \
                   f"Try alternative path."
        else:
            return "INFORMATIONAL: Similar query exists but no feedback yet."

    # ============================================================
    # RESEARCH FRONTIER: RL-Based Resolution Path Selection
    # ============================================================
    #
    # Future implementation: Train a policy network that selects
    # resolution strategies based on:
    # - Query characteristics (intent type, complexity, domain)
    # - User context (department, role, past behavior)
    # - Available context (which stores have relevant data)
    # - Past outcomes (feedback from Decision Trace Graph)
    #
    # The reward signal combines:
    # - Accuracy (was the resolution accepted?)
    # - Latency (how fast was the resolution?)
    # - Cost (how many store queries were needed?)
    #
    # This is directly inspired by the CLAUSE paper's
    # Lagrangian-Constrained Multi-Agent PPO approach,
    # adapted for enterprise context resolution.
    #
    # Implementation path:
    # 1. Collect 10,000+ resolution traces with feedback
    # 2. Train offline on historical traces
    # 3. Deploy with A/B testing against rule-based resolver
    # 4. Continuous online learning with safety constraints
```

### 3.5 Drift Detection Service: Implementation (NEW)

```python
class DriftDetectionService:
    """
    Monitors the physical data estate for changes that could
    invalidate Semantic Contracts. Runs as a background service.
    """

    async def run_detection_cycle(self):
        """
        Called on schedule (e.g., every 6 hours for active platforms,
        daily for stable platforms).
        """
        platforms = await self.get_monitored_platforms()

        for platform in platforms:
            try:
                # Step 1: Detect schema changes
                changes = await self.detect_schema_changes(platform)

                # Step 2: For each change, find affected contracts
                for change in changes:
                    affected = await self.find_affected_contracts(change)

                    if affected:
                        # Step 3: Record drift event
                        event = await self.record_drift_event(
                            change, affected, platform
                        )

                        # Step 4: Run validation for affected contracts
                        for contract in affected:
                            validation = await self.validate_contract(contract)
                            if not validation.passed:
                                event.severity = "critical"
                                await self.alert_contract_owner(contract, event)

                # Step 5: Run scheduled validation rules
                await self.run_validation_rules(platform)

            except Exception as e:
                logger.error(f"Drift detection failed for {platform}: {e}")

    async def detect_schema_changes(self, platform: Platform) -> list[SchemaChange]:
        """
        Compare current schema snapshot against last known snapshot.
        Platform-specific implementations.
        """
        if platform.type == "snowflake":
            return await self._detect_snowflake_changes(platform)
        elif platform.type == "databricks":
            return await self._detect_databricks_changes(platform)
        elif platform.type == "postgresql":
            return await self._detect_postgres_changes(platform)
        # ... other platforms

    async def _detect_snowflake_changes(self, platform) -> list[SchemaChange]:
        """
        Uses Snowflake's INFORMATION_SCHEMA and ACCESS_HISTORY
        to detect changes since last check.
        """
        last_check = await self.get_last_check_time(platform.id)

        changes = await platform.execute(f"""
            SELECT
                table_catalog, table_schema, table_name,
                column_name, data_type, is_nullable,
                comment
            FROM information_schema.columns
            WHERE last_altered > '{last_check}'
            ORDER BY last_altered DESC
        """)

        # Compare against stored snapshot
        snapshot = await self.get_schema_snapshot(platform.id)
        return self.diff_schemas(snapshot, changes)

    async def find_affected_contracts(
        self, change: SchemaChange
    ) -> list[Contract]:
        """
        Query the Knowledge Graph to find all Semantic Contracts
        that reference the changed table/column.
        """
        affected = await self.graph.query(f"""
            MATCH (c:Column {{table_id: '{change.table_id}'}})
            <-[:COMPUTED_FROM]-(m:Metric)
            RETURN m.asset_registry_id as contract_id, m.name as metric_name
        """)

        contracts = []
        for a in affected:
            contract = await self.asset_registry.get(a.contract_id)
            contracts.append(contract)

        return contracts
```

---

## 4. FACTORY MODEL (Updated)

### 4.1 Four-Phase Manufacturing Process

```
Phase 1: INGEST (Automated)
+-------------------------------------------------------------+
| Sources:                                                     |
|   - Database schemas (Information Schema, Unity Catalog)    |
|   - Stored procedures and views (parse SQL for logic)       |
|   - Query logs (identify usage patterns, consensus defs)    |
|   - Existing semantic layers:                               |
|     - Snowflake Semantic Views (import via API)     [NEW]   |
|     - dbt MetricFlow definitions (import YAML)      [NEW]   |
|     - OSI-compliant definitions (import YAML)        [NEW]   |
|   - Documentation (Confluence, SharePoint, wikis)           |
|   - Slack/Teams threads (with permission)                   |
|   - Decision Trace Graph (precedents from similar     [NEW]  |
|     datasets already onboarded)                              |
|                                                              |
| Output: Raw context artifacts per dataset                    |
+-------------------------------------------------------------+

Phase 2: SYNTHESIZE (Automated)
+-------------------------------------------------------------+
| Process:                                                     |
|   - LLM proposes definitions, identifies patterns           |
|   - Cross-reference against existing Context Registry       |
|   - Query Decision Trace Graph for precedents from   [NEW]  |
|     similar datasets (how were similar terms resolved?)      |
|   - Detect conflicts with existing definitions              |
|   - Generate confidence scores per proposed definition      |
|   - Produce draft Semantic Contract with provenance         |
|                                                              |
| Output: Draft Semantic Contracts with confidence scores      |
+-------------------------------------------------------------+

Phase 3: RATIFY (Human)
+-------------------------------------------------------------+
| Process:                                                     |
|   - SME reviews AI-generated proposals                      |
|   - Validates definitions, corrections fed back       [NEW]  |
|     to Decision Trace Graph as training signal               |
|   - Approves or modifies certification tier                 |
|   - Adds tribal knowledge not captured by automation        |
|   - 15-30 minutes per contract (review, not write)          |
|                                                              |
| Output: Ratified Semantic Contracts                          |
+-------------------------------------------------------------+

Phase 4: PUBLISH (Automated)
+-------------------------------------------------------------+
| Destinations:                                                |
|   - Context Registry (Knowledge Graph + Asset Registry)     |
|   - Semantic Layer (Cube.js metric definitions)             |
|   - Vector Store (embeddings for search)                    |
|   - MCP Server (available to AI systems)                    |
|   - OSI Export (YAML for dbt, Looker, ThoughtSpot)   [NEW]  |
|   - Decision Trace Graph (record the onboarding      [NEW]  |
|     as a precedent for future similar datasets)              |
|                                                              |
| Output: Live, queryable, AI-consumable context               |
+-------------------------------------------------------------+
```

---

## 5. RESEARCH FRONTIERS AND DISRUPTION POTENTIAL

### 5.1 Areas Under Active Research

| Area | Current State | Research Direction | Disruption Potential | Timeline |
|---|---|---|---|---|
| **Intelligent Resolution** | Rule-based orchestration | Neuro-symbolic reasoning with RL-optimized path selection (CLAUSE-style) | HIGH: Resolution that improves with every query without retraining | 6-18 months |
| **Compositional Query Planning** | Template-based | LLM-guided program synthesis for novel cross-domain queries | MEDIUM: Handle the long tail of queries no template covers | 6-12 months |
| **Federated Query Optimization** | Cost-based heuristics | Deep RL for join ordering across heterogeneous platforms (Coral-style) | HIGH: Optimal execution across Snowflake + Oracle + mainframe | 12-24 months |
| **Decision Trace Learning** | Feedback loops | Continuous online learning from AI system execution traces | HIGH: Context layer that writes its own semantic contracts | 12-18 months |
| **Tribal Knowledge Extraction** | LLM-based document analysis | Multi-modal extraction from Slack, video calls, code comments with active learning | MEDIUM: Systematically captures what only lives in heads | 6-12 months |
| **Calibrated Confidence** | Heuristic scoring | Conformal prediction for calibrated uncertainty bounds per response | MEDIUM: Statistical guarantees on confidence scores | 6-12 months |
| **Self-Healing Contracts** | Manual drift response | Contracts that auto-adapt when schema changes are detected, validated, and non-breaking | HIGH: Zero-maintenance context layer for migrating estates | 18-24 months |
| **Cross-Org Context Federation** | Not addressed | Secure context sharing between enterprises (e.g., supply chain data) | VERY HIGH: The "next-next" platform after intra-enterprise | 24+ months |

### 5.2 What Labs Would Do Differently

If this were a Stanford HAI or MIT CSAIL project, they would likely:

1. **Formalize the resolution problem as a POMDP** (Partially Observable Markov Decision Process). The agent has incomplete information about which definition is correct, takes actions (query stores, ask for clarification, select definition), and receives rewards (user feedback). This formalization enables rigorous policy optimization.

2. **Use graph neural networks for entity resolution** instead of Cypher queries. GNNs can learn entity representations that capture structural similarity across the knowledge graph, making cross-domain mapping more robust than hand-coded traversals.

3. **Apply conformal prediction for confidence calibration.** Instead of heuristic confidence scores, conformal prediction provides distribution-free guarantees: "with 90% probability, the true answer is within this set of interpretations."

4. **Build a benchmark dataset** for enterprise concept resolution. The field lacks a standard benchmark (like GLUE for NLU or JOB for query optimization). Creating one from anonymized resolution traces would accelerate research.

5. **Explore emergent ontology learning.** Rather than manually defining ontologies, use the accumulated decision traces to learn entity types, relationships, and constraints that the system discovers itself.

### 5.3 Practical Path: How to Get There

The architecture supports progressive intelligence:

**Phase 1 (Now):** Orchestrator pattern. Rule-based resolution. Template execution. Instrument everything for trace collection.

**Phase 2 (Months 4-6):** Add Precedent Engine. Embedding-based similarity search over decision traces. Feedback-weighted resolution. This is pure engineering, no ML research required.

**Phase 3 (Months 7-12):** Add compositional query planning for novel queries. Train lightweight classifiers on resolution traces for learned disambiguation. This requires moderate ML expertise.

**Phase 4 (Year 2):** Full neuro-symbolic resolution with RL-optimized path selection. Federated query optimization with deep RL. Self-healing contracts. This is research-frontier work but grounded in a massive corpus of traces collected in Phases 1-3.

The key insight: **you can't train intelligent resolution without resolution traces, and you can't collect resolution traces without a working system.** The orchestrator pattern is the necessary first step that creates the training data for the intelligent future.

---

## 6. IMPLEMENTATION NOTES

### 6.1 MCP Server Tool Definitions (Updated)

```javascript
const tools = [
  {
    name: "resolve_business_concept",
    description: "Resolve business concept to canonical definition and execution plan. " +
                 "Returns multi-dimensional confidence, provenance, and precedent information.",
    inputSchema: {
      type: "object",
      properties: {
        concept: {
          type: "string",
          description: "Business concept to resolve (e.g., 'APAC revenue')"
        },
        user_context: {
          type: "object",
          properties: {
            user_id: { type: "string" },
            department: { type: "string" },
            role: { type: "string" }
          }
        }
      },
      required: ["concept"]
    }
  },

  {
    name: "execute_metric_query",
    description: "Execute a metric query via the Semantic Layer with full provenance.",
    inputSchema: {
      type: "object",
      properties: {
        resolution_id: { type: "string" },
        parameters: { type: "object" }
      },
      required: ["resolution_id"]
    }
  },

  {
    name: "search_context",
    description: "Search the Context Registry for definitions, tribal knowledge, " +
                 "or data contracts related to a topic.",
    inputSchema: {
      type: "object",
      properties: {
        query: { type: "string" },
        asset_types: {
          type: "array",
          items: { type: "string" },
          description: "Filter by asset type: glossary_term, tribal_knowledge, data_contract, etc."
        }
      },
      required: ["query"]
    }
  },

  // NEW in v3
  {
    name: "report_feedback",
    description: "Report feedback on a resolution. Feeds into the Decision Trace Graph " +
                 "for continuous improvement.",
    inputSchema: {
      type: "object",
      properties: {
        resolution_id: { type: "string" },
        feedback: {
          type: "string",
          enum: ["accepted", "corrected", "rejected"]
        },
        correction_details: {
          type: "string",
          description: "If corrected, explain what should have been different"
        }
      },
      required: ["resolution_id", "feedback"]
    }
  },

  {
    name: "get_provenance",
    description: "Get full provenance for a past resolution, including resolution DAG, " +
                 "definitions used, precedents consulted, and confidence decomposition.",
    inputSchema: {
      type: "object",
      properties: {
        resolution_id: { type: "string" }
      },
      required: ["resolution_id"]
    }
  }
];
```

### 6.2 OSI Bridge: Import/Export (NEW)

```python
class OSIBridge:
    """
    Import and export semantic definitions in OSI-compliant YAML format.
    Enables bidirectional sync with Snowflake SVA, dbt MetricFlow,
    Looker, ThoughtSpot, and any OSI-compatible tool.
    """

    async def import_from_snowflake_sva(
        self, connection: SnowflakeConnection
    ) -> ImportResult:
        """
        Import Semantic View definitions from Snowflake SVA.
        Maps SVA metrics/dimensions to ECP Semantic Contracts.
        """
        semantic_views = await connection.execute("""
            SHOW SEMANTIC VIEWS IN SCHEMA {schema}
        """)

        imported = 0
        conflicts = 0

        for sv in semantic_views:
            # Get view details
            details = await connection.execute(f"""
                SHOW METRICS IN SEMANTIC VIEW {sv.name}
            """)

            for metric in details:
                # Check for existing definition
                existing = await self.asset_registry.find_by_name(
                    metric.name, type="glossary_term"
                )

                if existing and existing.definition != metric.comment:
                    # Conflict: Snowflake SVA defines it differently
                    conflicts += 1
                    await self.record_conflict(existing, metric, "snowflake_sva")
                else:
                    # Import as draft contract (requires ratification)
                    await self.create_draft_contract(metric, source="snowflake_sva")
                    imported += 1

        return ImportResult(imported=imported, conflicts=conflicts)

    async def export_osi_yaml(self, contract_ids: list[str] = None) -> str:
        """
        Export Semantic Contracts as OSI-compliant YAML.
        Any OSI-compatible tool can consume this.
        """
        contracts = await self.asset_registry.get_contracts(contract_ids)

        osi_definitions = []
        for contract in contracts:
            osi_def = {
                "name": contract.canonical_name,
                "type": "metric" if contract.type == "metric" else "dimension",
                "description": contract.definition,
                "expression": contract.formula,
                "dimensions": contract.dimensions,
                "filters": contract.default_filters,
                "metadata": {
                    "owner": contract.owner,
                    "certification_tier": contract.certification_tier,
                    "ecp_contract_id": contract.id,
                    "last_reviewed": contract.last_reviewed
                }
            }
            osi_definitions.append(osi_def)

        return yaml.dump({"osi_version": "1.0", "definitions": osi_definitions})
```

---

## 7. SUCCESS METRICS

| Metric | Phase 1 (30d) | Phase 2 (60d) | Phase 3 (90d) | Phase 4 (6mo) |
|---|---|---|---|---|
| Certified data products | 10 | 50 | 150 | 500 |
| Resolution accuracy (vs. SME reference) | 80% | 85% | 90% | 93%+ |
| Resolution latency (p95) | <2s | <1.5s | <1s | <500ms |
| Automation rate (contracts created w/o human edit) | 60% | 70% | 75% | 80%+ |
| Decision traces collected | - | 1,000 | 10,000 | 100,000 |
| Precedent hit rate | - | - | 30% | 60%+ |
| Schema drift events detected | - | - | 100% critical | 100% all |
| OSI definitions exported | - | 50 | 150 | 500 |
| AI systems supported via MCP | 1 | 2 | 3+ | 5+ |
| Resolution intelligence improvement (accuracy delta from traces) | - | - | +2% | +5%+ |

---

## 8. WHAT MAKES ECP v4 UNIQUE

No other solution combines all of these:

1. **Cross-estate semantic mediation** -- not locked to one platform
2. **Intelligent Resolution Engine** -- neuro-symbolic, not just lookup
3. **Semantic Firewall** -- AI systems never touch raw data
4. **AI Reasons. Databases Compute.** -- deterministic computation only
5. **Decision Trace Graph** -- learns from every resolution
6. **Factory Model** -- repeatable, scalable onboarding
7. **Certification Tiers** -- multi-level trust with provenance
8. **Tribal Knowledge** as first-class asset
9. **Drift Detection** -- survives estate evolution
10. **Protocol-Native** -- MCP, OSI, REST for any AI system
11. **Semantic Contracts** as the unit of work
12. **Research-ready architecture** -- designed for progressive intelligence
13. **Federation-first** -- consumes context from Microsoft IQ, Snowflake SVA, Glean, Atlan, dbt via their APIs/MCP servers. Makes every platform more valuable, competes with none.
14. **Three operating modes** -- Federation, Hybrid, Standalone -- works for any enterprise maturity level
15. **Connector Framework** -- tiered ingestion from heterogeneous estates
16. **Entitlements Architecture** -- inherited access control with OPA + audit
17. **Observability & Evals** -- tracing, metrics, golden query suites, hallucination circuit breakers

---

## 9. CONNECTOR ARCHITECTURE

### 9.1 Overview

The Connector Framework sits between the Factory Model Ingest phase and the physical data estate. It provides a uniform abstraction layer so that new systems can be onboarded through configuration rather than custom code.

### 9.2 Connector Tiers

| Tier | Name | Systems | Automation Level | Human Effort |
|---|---|---|---|---|
| 1 | Full Auto | Snowflake, Databricks, PostgreSQL, dbt, Looker | Schema, query logs, semantic defs, business logic extracted automatically | Review only |
| 2 | Semi-Auto | Oracle, SAP HANA, MongoDB, REST APIs | Schema and query logs extracted; semantic defs require SME validation | Moderate review |
| 3 | Manual + LLM | Mainframes, COBOL, flat files, spreadsheets | LLM-assisted SME interview produces structured templates | SME fills templates, LLM structures |

### 9.3 Connector Abstraction Layer

Every connector implements four extraction methods:

```
extract_schema()          → SchemaObject[]     (tables, columns, types)
extract_query_logs()      → QueryLogEntry[]    (SQL history, access patterns)
extract_semantic_defs()   → SemanticDefinition[] (metrics, dimensions from platform semantic layers)
extract_business_logic()  → BusinessLogicFragment[] (stored procs, views, triggers)
```

### 9.4 Connector Registry

The Connector Registry is a catalog of all connected systems:

- **System inventory:** Platform, tier, connection config (secrets redacted)
- **Last scan time:** When the connector last ran a full or incremental scan
- **Health status:** Healthy, degraded, unreachable, unknown
- **Coverage %:** Percentage of discovered objects that have been mapped to semantic contracts

### 9.5 Incremental Scanning

After the initial full scan, subsequent scans only process changes since the last scan time. This is achieved by:

- **Tier 1:** Querying `INFORMATION_SCHEMA` with `WHERE last_altered >= $since` (Snowflake) or equivalent
- **Tier 2:** Comparing schema snapshots using hash-based change detection
- **Tier 3:** Manual re-ingestion triggered by SME or drift detection alert

### 9.6 Manual Ingestion Path

For Tier 3 (non-connectable) systems, a structured template-based workflow:

1. SME receives a blank schema template (JSON) with fields for tables, columns, data types, business rules, known issues
2. SME fills in the template based on their knowledge of the system
3. LLM reviews the template, identifies gaps, suggests improvements, and normalizes naming
4. Validated template is ingested into the Context Registry as structured assets
5. Semantic definitions are proposed by LLM based on the template, sent to SME for ratification

---

## 10. ENTITLEMENTS ARCHITECTURE

### 10.1 Core Principle

**ECP inherits and enforces; it never invents access control.** Authorization decisions are made by existing enterprise identity systems (Active Directory, Okta, etc.) and evaluated by OPA policies. ECP passes through identity and applies the result.

### 10.2 Identity Pass-Through

```
AI System (Frontier/Cowork/Copilots/Custom)
    → JWT/OAuth token in Authorization header
        → ECP extracts user_context (user_id, department, role, allowed_domains, allowed_regions)
            → OPA evaluates policies against user_context + requested concepts
                → Semantic Layer enforces row-level security
```

### 10.3 Context-Level RBAC

OPA policies control access at the concept level:

- **Tier-based:** Only authorized users can access Tier 1 (regulatory) data
- **Domain-based:** Sales users cannot see HR metrics; finance users cannot see engineering costs
- **PII-based:** Concepts tagged as PII require elevated privileges
- **Region-based:** APAC data only accessible to users with APAC region clearance

### 10.4 Search Result Filtering

The `search_context` endpoint filters results through OPA before returning:

- Query results are checked against the user's authorization profile
- Denied results are silently omitted (return "not found," not "access denied") to prevent information leakage
- Audit log records the filtering event with counts

### 10.5 Namespace Isolation

Domain-based multi-tenancy for business unit separation:

- Each business unit (Sales, Finance, Operations) operates in a namespace
- Cross-namespace resolution requires explicit permission
- Namespace boundaries are enforced by OPA policies

### 10.6 Audit Trail

Every resolution persists:

- **User identity:** Who made the request (user_id, department, role)
- **Authorization result:** Allowed or denied, which policies were evaluated
- **Filtered concepts:** Which concepts were removed due to access control
- **Timestamp and action:** When the decision was made and what was requested

---

## 11. OBSERVABILITY

### 11.1 OpenTelemetry Instrumentation

Every resolution step is wrapped in an OpenTelemetry span:

- `parse_intent` — LLM or rule-based intent extraction
- `resolve_{concept_type}` — Per-concept resolution (graph lookup or neuro-symbolic)
- `check_tribal_knowledge` — Tribal knowledge scan
- `find_precedents` — Decision trace search
- `authorize` — OPA policy evaluation
- `build_execution_plan` — Semantic layer query planning

Spans carry attributes: `resolution_id`, `mode`, `user_department`, `confidence`, `concept_count`.

### 11.2 Hallucination Circuit Breakers

Three layers of hallucination prevention:

1. **Confidence threshold (< 0.7):** When overall confidence drops below 0.7, the engine returns `status="disambiguation_required"` with candidate options instead of a resolved answer. The calling AI system must prompt the user for clarification.
2. **Validation rule enforcement:** Business rules from data contracts are checked post-resolution. Violations trigger warnings or block execution.
3. **Drift-triggered re-validation:** When the Drift Detection Service detects a schema change affecting a resolved concept, in-flight resolutions are flagged for re-validation.

### 11.3 Prometheus Metrics

| Metric | Type | Labels | Purpose |
|---|---|---|---|
| `ecp_resolution_latency_seconds` | Histogram | mode, status | End-to-end resolution time |
| `ecp_cache_hits_total` | Counter | cache_level | Cache effectiveness |
| `ecp_disambiguation_total` | Counter | — | How often disambiguation is triggered |
| `ecp_resolutions_total` | Counter | mode, status | Total resolution volume |
| `ecp_confidence_score` | Histogram | — | Confidence distribution |
| `ecp_feedback_total` | Counter | feedback_type | Feedback submission rate |
| `ecp_active_resolutions` | Gauge | — | In-flight resolution count |

### 11.4 Trust Dashboard

Key metrics surfaced on the Trust Dashboard:

- **Accuracy:** Golden query pass rate (nightly) + online feedback acceptance rate
- **Coverage:** % of business concepts with certified semantic contracts
- **Freshness:** % of data sources within SLA freshness windows
- **Drift:** Active drift events by severity (critical, warning, info)
- **Certification:** Breakdown by tier (Tier 1 regulatory, Tier 2 executive, etc.)

---

## 12. EVAL FRAMEWORK

### 12.1 Golden Query Suite

A curated set of reference queries with expected resolutions for each certified metric:

- **10+ reference queries** covering the demo scenario (revenue variants, region resolution, time handling, comparison queries)
- **Expected outputs:** Specific resolved concept IDs, status, and minimum confidence
- **Scheduled nightly runs** against the staging environment
- **Accuracy tracking:** Pass rate trended over time to detect regressions

### 12.2 Online Evals

- **10% sampling:** 10% of production resolutions are evaluated asynchronously
- **Evaluation criteria:** Concept resolution matches golden references, confidence within expected range, no unexpected tribal knowledge gaps
- **Feedback trending:** Track accepted/corrected/rejected ratios over time, by department, by concept type
- **Alerting:** Accuracy drop > 5% in any 24-hour window triggers oncall alert

This is the layer that sits between OpenAI Frontier (agent execution) and Snowflake SVA (in-platform analytics). It is the deep, cross-estate, trustworthy context that makes enterprise AI -- agents, copilots, workflows, applications -- actually work.

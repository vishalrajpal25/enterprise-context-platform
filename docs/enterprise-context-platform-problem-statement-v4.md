# Enterprise Data Estate Readiness for AI

## Version 4.0 | April 2026

---

## Context & Market Validation

### Why This Problem Is Now Consensus

Between January and March 2026, the enterprise context layer thesis moved from emerging insight to industry consensus:

- **OpenAI** launched Frontier (Feb 5, 2026) with a "semantic layer for the enterprise" as its first pillar. Initial customers include Intuit, State Farm, Uber, HP, Oracle.
- **Anthropic** launched enterprise agents with MCP-connected context and Agent Skills as an open standard (Feb 24, 2026).
- **Snowflake** shipped Semantic View Autopilot (GA, Feb 2026) and announced Project SnowWork as an agentic enterprise control plane. Published "The Agent Context Layer for Trustworthy Data Agents" (March 2026).
- **Solid** raised $20M seed (Feb 2026) to build "context graphs" for enterprise AI, coining the term "Semantic Engineering."
- **Andreessen Horowitz** published "Your Data Agents Need Context" (March 2026), calling the context layer the defining category of the agentic era.
- **Foundation Capital** published "Context Graphs: AI's Trillion-Dollar Opportunity," arguing that decision traces are the next enterprise data asset.
- **Gartner** predicts context engineering will be in 80% of AI tools by 2028.
- **Open Semantic Interchange (OSI)** finalized its vendor-neutral spec for semantic layer constructs, with dbt Labs, Snowflake, Salesforce, Databricks, ThoughtSpot, and AtScale as members.

The problem is validated. The question is now: who builds the deepest, most scalable, most trustworthy implementation?

---

## Positioning

**Name:** Enterprise Context Platform (ECP)
**Category:** Enterprise Context Layer for AI
**Tagline:** Resolve. Trust. Learn.

**One-liner:** ECP is the enterprise context layer that gives any AI system -- agents, copilots, workflows, applications -- a trusted understanding of your business data. It federates over your existing context investments, resolves conflicts between them, and gets smarter with every interaction.

### Math vs Meaning

Semantic layers do math. ECP does meaning. ECP tells the semantic layer what math to do, based on who is asking and what the enterprise context says is correct.

### What ECP is NOT

- **Not a semantic layer.** dbt MetricFlow, Cube.js, Power BI compute metrics. ECP tells them WHICH metrics to compute.
- **Not a data catalog.** Atlan, Alation index metadata. ECP resolves meaning from metadata.
- **Not enterprise search.** Glean searches unstructured knowledge. ECP resolves structured data semantics.
- **Not an agent platform.** OpenAI Frontier, Anthropic Cowork orchestrate AI systems. ECP gives them context.
- **Not a data platform.** Snowflake, Databricks, Fabric store and compute data. ECP wraps them with meaning.

### Three Operating Modes

| Mode | When It Applies | What ECP Does |
|---|---|---|
| **Federation** | Enterprise has invested in Fabric IQ, Snowflake SVA, Glean, Atlan, dbt | Federates over them via MCP/API, resolves conflicts, adds trust + traces |
| **Hybrid** | Enterprise has partial investments | Federates where possible, brings its own stores for the gaps |
| **Standalone** | Enterprise has no existing context layer | Brings its own full stack, builds context via the Factory Model |

---

## The Problem: Technical Reality

You are advising a large enterprise (Fortune 500 financial data company -- similar to FactSet, Bloomberg, or Reuters) that has built a complex data estate over 15-20 years.

### Technical Reality

| Component | State |
|---|---|
| Databases | Tens of platforms across SQL Server, Oracle, Snowflake, PostgreSQL, legacy mainframes |
| Business Logic | Thousands of stored procedures containing embedded logic, some dating back 15+ years |
| Technical Debt | Views built on views; undocumented dependencies; inconsistent naming |
| ETL Pipelines | Transformation logic scattered across Databricks, Informatica, SSIS, dbt, custom scripts |
| Data Lakes | Semi-structured and unstructured data mixed with processed structured data |
| APIs | Multiple interfaces exposing data to internal and external consumers |
| Sources of Truth | Multiple, conflicting -- some sources claim truth, others compute it at runtime |

### Organizational Reality

| Challenge | Manifestation |
|---|---|
| Definition Variance | "Revenue" means different things to Sales, Finance, and Operations |
| Undocumented Jargon | Acronyms pervasive and inconsistently documented |
| Tribal Knowledge | The "right" way to query data is passed down verbally or lives in individuals' heads |
| Hidden Gotchas | Known data issues and workarounds not systematically captured |
| Fragmented Ownership | No single person understands the full estate |
| Scattered Documentation | Confluence, SharePoint, wikis, email threads, Slack -- mostly outdated |
| Estate in Motion | Active migrations, modernization, platform consolidation happening continuously |

### Business Pressure

- Leadership expects GenAI to "just work" on enterprise data -- they don't understand why it hallucinates or returns wrong answers
- Competitors moving fast; 12-18 month window to establish AI-driven data products
- Regulatory requirements demand accuracy, auditability, and explainability
- Traditional governance programs take 2-3 years and often fail before completion
- OpenAI Frontier, Salesforce Agentforce, and other platforms are selling "enterprise AI" but cannot deliver accuracy without the context layer underneath

---

## The Core Problem

AI systems fail on enterprise data not because of reasoning limitations, but because of missing context.

When a user asks an AI system "What was our APAC revenue last quarter?", the AI system doesn't know:

- Which definition of "revenue" to use (gross? net? recognized? booked?)
- What "APAC" means in this organization (includes China? excludes ANZ?)
- Whether "last quarter" is fiscal or calendar
- Which source system is authoritative for this metric
- That Q4 2019 data is incomplete due to a migration
- That APAC cost center definitions changed in 2021
- What stored procedure or view contains the "correct" calculation
- What joins, filters, and transformations are required
- How this same question was resolved last time and whether the user accepted that answer

This context exists -- but it's scattered across schemas, code, documentation, and people's heads. It was never designed to be machine-readable or AI-consumable.

**What existing solutions miss:**

- **OpenAI Frontier** connects systems but does not resolve what the data means. It is an agent execution platform, not a semantic mediation layer.
- **Snowflake Semantic View Autopilot** defines metrics within Snowflake but cannot span Oracle, SQL Server, and Databricks estates. It learns from SQL query patterns but not from tribal knowledge, Slack threads, or documentation.
- **Anthropic Cowork + MCP** provides protocol-level connectivity but no persistent semantic registry, no concept resolution, no certification tiers.
- **Solid** builds context graphs but has not published a resolution orchestration, factory model, or trust architecture.
- **dbt MetricFlow / AtScale** provide deterministic metric computation but only within the BI/analytics layer -- not across the full AI system interaction surface.

The traditional approach -- manual data cataloging, governance programs, stewardship councils -- takes 2-3 years and tens of millions of dollars. And it often fails before completion.

---

## The Business Goal

> Enable a scalable data access layer that is safe, accurate, and trustable -- on the existing legacy data estate -- in minimum possible time. The solution must serve any AI system -- agents, copilots, workflows, applications -- and either federate over existing context investments or bring its own.

### Requirement Breakdown

| Dimension | Requirement | Success Criteria |
|---|---|---|
| Scalable | Approach works for 10 datasets and still works for 1000; can't be artisanal | Linear cost scaling; consistent onboarding time per dataset |
| Safe | AI systems cannot return harmful, misleading, or unauthorized data | Zero unauthorized exposures; guardrails catch anomalies |
| Accurate | Answers correct per business definitions, not hallucinated | Match validated reference answers; SME approval |
| Trustable | Every answer explainable, auditable, traceable to authoritative sources | Full provenance on every response |
| Cross-Estate | Works across Snowflake, Databricks, Oracle, SQL Server, mainframes | No platform lock-in; federated resolution |
| Existing Estate | Cannot wait for multi-year modernization; must work with current systems | Incremental adoption; no data migration required |
| Migration-Resilient | Continues working as underlying data estate evolves | Drift detection; versioned contracts; backward compatibility |
| Minimum Time | Weeks to months, not years; leverage automation and smart prioritization | Initial value in 90 days |
| Protocol-Native | Exposes context via MCP, OSI, REST/gRPC for any AI system | Works with Frontier, Cowork, Claude Code, custom AI systems |

---

## Key Challenges to Address

### 1. The Context Gap
- How do you capture and represent the business context (definitions, rules, logic, exceptions) that AI systems need to answer questions correctly?
- How do you make this context queryable and injectable at runtime?
- How do you span multiple data platforms with conflicting definitions?

### 2. The Tribal Knowledge Problem
- How do you extract undocumented knowledge from people's heads, Slack threads, old emails, and code comments?
- How do you keep this knowledge current as the organization evolves?
- How do you distinguish between tribal knowledge that is correct vs. outdated assumptions?

### 3. The Scale Problem
- How do you avoid the "boil the ocean" trap of cataloging everything?
- What's the unit of work that can be manufactured repeatedly?
- How do you prioritize which data to make AI-ready first?

### 4. The Accuracy Problem (Intelligent Resolution)
- How does an AI system know which source, calculation, or definition is authoritative?
- How do you handle ambiguity when multiple valid interpretations exist?
- How do you prevent AI systems from using stale, deprecated, or incorrect data?
- **Can the resolution layer be intelligent -- not just an orchestrator, but a reasoning engine that learns from past resolutions, applies graph-based inference, and composes novel query strategies?**

### 5. The Trust Problem
- How do you provide provenance, confidence scores, and audit trails with every answer?
- How do you certify data for different use cases (internal analytics vs. external reporting vs. regulatory)?
- How do you explain to a regulator or executive exactly how an answer was derived?

### 6. The Safety Problem
- How do you prevent AI systems from accessing unauthorized data?
- How do you catch obviously wrong results before they reach users?
- How do you enforce business rules and constraints at query time?

### 7. The Maintenance Problem
- How do you keep the context layer in sync as the underlying data estate changes?
- How do you incorporate feedback when AI systems make mistakes?
- How do you handle versioning of definitions and logic over time?
- **How does the context layer learn over time through decision traces, resolution patterns, and human feedback?**

### 8. The Continuous Migration Problem (NEW)
- The physical data estate is not static. Tables get renamed, pipelines get migrated, sources get deprecated.
- How does the context layer detect drift in the underlying estate?
- How do semantic contracts maintain stability while the physical layer evolves underneath?
- How do you version contracts to maintain backward compatibility during migrations?

### 9. Scalability Across Heterogeneous Estates (NEW)
- Enterprises run dozens of platforms: Snowflake, Databricks, Oracle, SQL Server, SAP HANA, mainframes, flat files.
- Each platform has different APIs, schema conventions, and capabilities.
- How do you build a connector framework that scales across tiers of automation?
  - **Tier 1 (Full Auto):** Snowflake, Databricks, PostgreSQL — schema, query logs, semantic defs extracted automatically
  - **Tier 2 (Semi-Auto):** Oracle, SAP HANA, MongoDB — partial automation, SME validation required
  - **Tier 3 (Manual+LLM):** Mainframes, COBOL, flat files — LLM-assisted SME interviews produce structured templates
- How do incremental scans avoid re-processing the entire estate on every run?
- How do you track coverage: what percentage of a connected system's objects have semantic contracts?

### 10. Enterprise Governance (NEW)
- AI systems must respect existing access control — they cannot see data the requesting user wouldn't be authorized to access directly.
- Identity must pass through from the AI system (JWT/OAuth) to the semantic layer (row-level security).
- Access control must operate at the concept level, not just the table level: denying a user "revenue by cost center" while allowing "revenue by region."
- Denied concepts must return "not found" rather than "access denied" to prevent information leakage.
- Every resolution must produce a complete audit trail: who requested, what was authorized, which policies evaluated, what was filtered.
- Namespace isolation must support multi-tenancy across business units.

### 11. Observability & Trust (NEW)
- How do you instrument the resolution engine for end-to-end tracing (OpenTelemetry)?
- How do you prevent hallucination at the resolution layer?
  - **Confidence thresholds:** Below 0.7, return "disambiguation required" instead of a potentially wrong answer
  - **Validation rule enforcement:** Business rules from data contracts checked post-resolution
  - **Drift-triggered re-validation:** Schema changes invalidate cached resolutions
- How do you measure accuracy over time?
  - **Golden Query Suite:** Nightly runs of reference queries with expected resolutions
  - **Online evals:** Sample 10% of production resolutions, track accuracy trends
- How do you expose trust metrics (accuracy, coverage, freshness, drift, certification) on a dashboard?

---

## Constraints & Boundaries

### What We CAN Do
- Build new layers/services that sit between AI systems and the data estate
- Use LLMs and AI to accelerate extraction and synthesis
- Deploy new infrastructure (knowledge graphs, vector stores, semantic layers, APIs)
- Prioritize high-value data products over comprehensive coverage
- Implement human-in-the-loop validation for critical use cases
- Integrate with existing platforms (Snowflake SVA, dbt, Databricks Unity Catalog) rather than replace them
- Federate over existing enterprise context investments (Microsoft IQ, Snowflake SVA, Glean, Atlan, dbt) rather than replace them
- Expose context via industry-standard protocols (MCP, OSI, REST/gRPC)
- Leverage research in neuro-symbolic AI, learned query optimization, and graph neural networks for intelligent resolution

### What We CANNOT Do
- Wait for a 2-year data governance program
- Assume perfect data quality or complete documentation exists
- Require migration of data to new platforms
- Force organizational restructuring before delivering value
- Compete with OpenAI Frontier or Snowflake on their core turf (agent execution or in-platform analytics)

---

## Solution Principles

### Core Thesis

**Context is the product, not data.** The data already exists. What's missing is the machine-readable semantic contract that tells an AI system how to use that data correctly. We don't fix the data before use; we wrap messy data with rich context that enables correct interpretation.

### Architectural Principles

1. **The Semantic Firewall:** AI systems never directly touch the messy data estate. Everything passes through a controlled boundary that translates between AI system queries and legacy systems.

2. **AI Reasons. Databases Compute.** No AI system that calls ECP ever generates SQL or performs calculations. LLMs reason and translate, but all computation happens in deterministic semantic layers.

3. **Context-First, Not Data-First:** We don't clean data before using it. We build a context layer that wraps the data as-is -- an "institutional memory API" that AI systems query before they query data.

4. **Manufacturing, Not Art:** Data onboarding is a repeatable factory process, not bespoke craftsmanship. The unit of production is the "Semantic Contract."

5. **Separation of Concerns:** The Context Registry (knowledge about data) is separate from the Semantic Layer (computation on data) is separate from the Decision Trace Graph (history of resolutions). AI systems reason using the first, act through the second, and learn from the third. In federation mode, the Context Registry aggregates from external sources. In standalone mode, it uses its own stores. The separation holds either way.

6. **Intelligent Resolution, Not Just Orchestration:** The resolution layer is a neuro-symbolic reasoning engine that combines LLM-based intent understanding, graph-based inference, precedent-based learning from past resolutions, and compositional query planning. It gets smarter over time.

7. **Protocol-Native Distribution:** Context is exposed via MCP, OSI, and REST/gRPC so any AI system can consume it. ECP is not an agent platform; it is the intelligence layer that agent platforms need.

8. **Federation-First Distribution:** ECP consumes context from wherever it already exists (Fabric IQ ontologies, Snowflake semantic views, Glean knowledge graphs, Atlan metadata, dbt metrics) and adds what none of them provide: cross-estate resolution, tribal knowledge, certification tiers, and decision trace learning.

9. **Migration-Resilient Contracts:** Semantic Contracts are the stable interface while physical source references version underneath. AI systems never break when the estate changes.

---

## Knowledge Asset Taxonomy

AI systems need access to multiple types of knowledge assets:

| # | Asset Type | Purpose | Examples |
|---|---|---|---|
| 1 | Semantic Models | Executable metric/dimension definitions | KPIs, calculations, hierarchies, time intelligence |
| 2 | Business Glossary | Term definitions, synonyms, acronyms | "APAC" definition, "Revenue" variants by context |
| 3 | Ontology | Entity relationships and attributes | Customer to Region to Cost Center relationships |
| 4 | Data Contracts | SLAs, quality expectations, ownership | Freshness targets, completeness rules |
| 5 | Lineage Artifacts | Column-level provenance, transformations | Source-to-target mappings |
| 6 | Policy Artifacts | Access control, classification, retention | PII tags, role restrictions |
| 7 | Validation Rules | Business rules, anomaly bounds | Revenue >= 0, variance thresholds |
| 8 | Query Templates | Canonical patterns, blessed joins | Pre-approved query structures |
| 9 | Domain Models | Bounded contexts, cross-domain mappings | Sales.Customer vs. Finance.Customer |
| 10 | Tribal Knowledge | Known issues, workarounds, gotchas | "Q4 2019 APAC data incomplete" |
| 11 | **Decision Traces** (NEW) | Past resolution paths, human overrides, precedent links | "Last time this was asked, finance definition was used and accepted" |
| 12 | **Migration Records** (NEW) | Schema change history, deprecated source mappings | "This table moved from Oracle to Snowflake on 2024-03-15" |

---

## AI System Consumer Taxonomy

ECP serves any AI system that needs trusted enterprise context. The consumers fall into six categories:

| Consumer Type | Example | Integration |
|---|---|---|
| Conversational AI | Copilots, Claude, ChatGPT Enterprise | MCP tool call |
| Autonomous agents | Frontier agents, custom agents | MCP/REST |
| Agentic workflows | n8n, Temporal, LangGraph | REST API |
| AI-powered applications | Vibe-coded tools, dashboards | REST API |
| Automated processes | Reports, monitoring, alerting | REST API |
| Semantic layer consumers | BI tools, notebooks | OSI export |

---

## Federation Architecture

ECP's resolution engine sits behind a Federation Adapter Layer that consumes context from wherever it already exists in the enterprise. In standalone mode, only the Native adapter is active. In federation mode, multiple adapters run in parallel.

```
AI Systems (Copilots, Agents, Workflows, Applications)
                         |
                    MCP / REST / OSI
                         |
              Enterprise Context Platform
              +---------------------------+
              | Intelligent Resolution    |
              | Engine                    |
              +---------------------------+
                         |
              +---------------------------+
              | Federation Adapter Layer  |
              +---------------------------+
               |      |      |      |      |
               v      v      v      v      v
          Fabric  Snowflake  Glean  Atlan  ECP Native
          IQ MCP  SVA API    API    MCP    Stores
          Server                           (Neo4j,
                  dbt                      PostgreSQL)
                  OSI
```

---

## Architecture Overview

The solution consists of eight layers (updated from six):

```
+========================================================================+
||                  OBSERVABILITY LAYER (cross-cutting)                  ||
||  OpenTelemetry tracing | Prometheus metrics | Golden Query Evals     ||
||  Hallucination circuit breakers | Trust Dashboard                    ||
+========================================================================+
                                 |
+------------------------------------------------------------------------+
|                     AI SYSTEM INTERFACE LAYER                          |
|     (MCP Server / REST API / gRPC -- any AI system connects)           |
+------------------------------------------------------------------------+
                                 |
                                 v
+========================================================================+
||                  GOVERNANCE LAYER (cross-cutting)                     ||
||  OPA Policy Engine | Identity Pass-Through (JWT/OAuth)               ||
||  Context-Level RBAC | Namespace Isolation | Audit Trail              ||
+========================================================================+
                                 |
                                 v
+------------------------------------------------------------------------+
|                    INTELLIGENT RESOLUTION ENGINE                        |
|     (Neuro-Symbolic Reasoning: Intent -> Disambiguate -> Plan ->       |
|      Authorize -> Execute -> Validate -> Learn)                        |
|                                                                        |
|  Neural:  LLM intent parsing, semantic matching, confidence scoring    |
|  Symbolic: Graph inference, ontology reasoning, rule application       |
|  Learned:  Precedent search, resolution path optimization, drift       |
|            detection via accumulated decision traces                   |
+------------------------------------------------------------------------+
                                 |
                                 v
+------------------------------------------------------------------------+
|                    FEDERATION ADAPTER LAYER                            |
|  Fabric IQ | Snowflake SVA | Glean | Atlan | dbt | Native (always on)  |
|  Parallel discovery, source-attributed merging, conflict resolution    |
+------------------------------------------------------------------------+
          |                    |                    |
          v                    v                    v
+-------------------+ +-------------------+ +-------------------+
|  CONTEXT REGISTRY | | SEMANTIC LAYER    | | DECISION TRACE    |
|  (Knowledge)      | | (Computation)     | | GRAPH (Learning)  |
|                   | |                   | |                   |
| - Business        | | - Metrics & KPIs  | | - Resolution      |
|   Glossary        | | - Dimensions &    | |   Sessions        |
| - Ontology/Graph  | |   Hierarchies     | | - Human Overrides |
| - Data Contracts  | | - Time            | | - Precedent Links |
| - Lineage         | |   Intelligence    | | - Correction      |
| - Policy          | | - Query Templates | |   Feedback        |
| - Tribal          | | - Canonical Joins | | - Drift Events    |
|   Knowledge       | |                   | |                   |
| - Domain Models   | | (Cube.js / dbt    | | (PostgreSQL +     |
| - Migration       | |  MetricFlow /     | |  Neo4j temporal   |
|   Records         | |  OSI-compatible)  | |  edges)           |
+-------------------+ +-------------------+ +-------------------+
          |                    |                    |
          +--------------------+--------------------+
                               |
                               v
+------------------------------------------------------------------------+
|                      DRIFT DETECTION SERVICE                            |
|  (Monitors physical estate for schema changes, validates contracts,     |
|   triggers re-extraction, emits alerts to contract owners)              |
+------------------------------------------------------------------------+
                               |
                               v
+------------------------------------------------------------------------+
|                      CONNECTOR FRAMEWORK                                |
|  Tier 1 Full Auto:  Snowflake, Databricks, PostgreSQL, dbt, Looker    |
|  Tier 2 Semi-Auto:  Oracle, SAP HANA, MongoDB, REST APIs              |
|  Tier 3 Manual+LLM: Mainframes, COBOL, flat files                     |
|                                                                        |
|  Connector Registry | Incremental Scanning | Manual Ingestion Path    |
+------------------------------------------------------------------------+
                               |
                               v
+------------------------------------------------------------------------+
|                       PHYSICAL DATA ESTATE                              |
|    (Snowflake, SQL Server, Oracle, Databricks, Data Lake, APIs --      |
|     unchanged, continuously evolving)                                   |
+------------------------------------------------------------------------+
```

### Key Separations:

- **Context Registry:** Holds knowledge about the data. Queryable by the resolution engine to understand meaning and resolve ambiguity.
- **Semantic Layer:** Holds executable logic. What actually computes answers. The AI system calls it; never bypasses it.
- **Decision Trace Graph (NEW):** Holds the history of how resolutions were made, what worked, what was corrected. Feeds learning back into the resolution engine.
- **Drift Detection Service (NEW):** Monitors the physical estate for changes and keeps semantic contracts in sync.
- **Connector Framework (NEW):** Tiered abstraction layer between the Factory Model and physical systems. Provides uniform schema extraction, query log analysis, and semantic definition harvesting across heterogeneous estates.
- **Governance Layer (NEW):** Cross-cutting concern that enforces access control via OPA policies, passes through identity from agent platforms, filters unauthorized concepts, and maintains a complete audit trail.
- **Observability Layer (NEW):** Cross-cutting concern providing OpenTelemetry tracing for every resolution step, Prometheus metrics for operational monitoring, hallucination circuit breakers (confidence thresholds, validation rules, drift-triggered re-validation), and a Golden Query evaluation suite for accuracy tracking.

The AI system reasons using the Context Registry, acts through the Semantic Layer, and learns from the Decision Trace Graph. It never writes raw SQL against the physical estate. The Connector Framework enables scalable ingestion from heterogeneous estates. The Governance Layer ensures authorized access. The Observability Layer ensures trust. The Drift Detection Service ensures the context layer stays valid as the estate evolves.

---

## The Intelligent Resolution Engine (Research Frontier)

### Why Resolution Must Be Intelligent

Current approaches treat resolution as mechanical orchestration: parse the query, look up terms in a glossary, build a query, execute. This fails in practice because:

1. **Ambiguity is contextual.** "Revenue" doesn't just have two definitions -- it has dozens of valid interpretations depending on who is asking, what they're comparing, what time period, what regulatory context. Rule-based disambiguation (if dept=finance, use net_revenue) breaks at scale.

2. **Cross-domain queries require compositional reasoning.** "How does our APAC revenue compare to headcount growth?" requires joining data from finance, HR, and regional systems with different fiscal calendars, different entity definitions, and different freshness guarantees. No template covers this.

3. **Precedent matters.** If the same user asked a similar question last week and accepted the resolution, that's a strong signal for how to resolve it this time. If they corrected the resolution, that's even stronger.

4. **Confidence is multi-dimensional.** A single confidence score hides critical information. The system needs to decompose confidence into: definition confidence, data quality confidence, temporal validity confidence, authorization confidence, and completeness confidence.

### What Labs and Research Suggest

- **CLAUSE (OpenReview 2025):** Treats context construction over knowledge graphs as a sequential decision process with three coordinated agents (Subgraph Architect, Path Navigator, Context Curator) using Lagrangian-Constrained Multi-Agent Proximal Policy Optimization. Balances accuracy, latency, and cost per query.
- **Neuro-symbolic KG reasoning (IEEE TNNLS 2025):** Combines neural embeddings with symbolic logic-based inference for knowledge graph completion and multi-hop reasoning. Three paradigms: logically-informed embeddings, embedding approaches with logical constraints, and tightly coupled neuro-symbolic methods.
- **LLM-based query optimization (VLDB 2025):** LLM embeddings of execution plans contain useful semantic information. Simple classifiers on LLM embeddings outperform traditional query optimizers. Training-free approaches achieve 21% latency reduction.
- **Federated query optimization with deep RL (WWW 2023):** Reinforcement learning for join order optimization across federated data sources. Learns optimal execution strategies through interaction rather than heuristics.
- **MIT-IBM Watson AI Lab:** Neuro-symbolic AI as pathway to AGI -- neural perception layer for interpreting unstructured inputs, symbolic reasoning layer for structured decision-making.

### Proposed Architecture for Intelligent Resolution

The Resolution Engine should be a neuro-symbolic hybrid with four subsystems:

1. **Neural Perception Layer:** LLM-based intent parsing, entity extraction, semantic similarity matching. This is System 1 (fast, intuitive). It produces candidate concepts, candidate definitions, and an initial confidence distribution.

2. **Symbolic Reasoning Layer:** Graph traversal over the Knowledge Graph, ontology-based inference, rule application from Data Contracts and Validation Rules. This is System 2 (deliberate, logical). It resolves ambiguity using formal constraints, checks consistency, and produces a provably correct execution plan.

3. **Precedent Engine:** Queries the Decision Trace Graph for similar past resolutions. Applies a learned similarity function (not just keyword matching) to find relevant precedents. Weights recent precedents higher. Incorporates human corrections as hard constraints.

4. **Compositional Query Planner:** For novel cross-domain queries, uses LLM-guided program synthesis to compose query strategies that have never been templated. Validated against the Semantic Layer's capabilities before execution.

### What Is Practical vs. Research Frontier

| Component | Practical Now | Research Frontier |
|---|---|---|
| LLM intent parsing | Yes -- standard NLU pipeline | Compositional intent decomposition for multi-hop queries |
| Vector + Graph + Registry parallel queries | Yes -- standard multi-store pattern | Learned routing: which stores to query based on query type |
| Template-based execution plans | Yes -- covers 80% of queries | LLM-guided compositional planning for novel queries |
| Rule-based disambiguation | Yes -- if/then on user context | Learned disambiguation from resolution traces |
| Confidence scoring | Yes -- heuristic weighted averages | Calibrated uncertainty with decomposed dimensions |
| Precedent search | Partially -- keyword/embedding match | RL-optimized resolution path selection from decision traces |
| Self-improving resolution | Partially -- feedback loops | Continuous learning from decision traces without retraining |
| Federated query optimization | Partially -- cost-based heuristics | Deep RL for cross-platform join order optimization |

The practical path: start with the orchestrator pattern (v2), add precedent search from the Decision Trace Graph, and instrument everything for trace collection. The intelligent components can be layered in progressively as the trace corpus grows.

---

## The Factory Model

To scale from 10 to 1000 datasets, treat data onboarding as a manufacturing process:

```
+-------------+    +-------------+    +-------------+    +-------------+
|   INGEST    | -> | SYNTHESIZE  | -> |   RATIFY    | -> |   PUBLISH   |
| (Automated) |    | (Automated) |    |  (Human)    |    | (Automated) |
+-------------+    +-------------+    +-------------+    +-------------+
      |                  |                  |                  |
      v                  v                  v                  v
 Read schemas,     LLM proposes       SME validates      Push to Context
 stored procs,     definitions,       via Slack/UI       Registry,
 query logs,       identifies         (15-30 min         Semantic Layer,
 documentation,    patterns,          per contract)      OSI export,
 Snowflake SVA     queries Decision                      MCP server
 definitions,      Trace Graph
 dbt metrics,      for precedents
 OSI imports
```

**NEW in v3:** The Ingest phase now imports from Snowflake SVA, dbt MetricFlow, and any OSI-compliant source. The Synthesize phase queries the Decision Trace Graph for precedents from similar datasets. The Publish phase emits OSI-compliant YAML alongside the native format.

Why this scales: You aren't asking SMEs to write documentation from scratch; you're asking them to review and approve AI-generated proposals based on historical usage patterns, existing semantic layer definitions, and precedents from similar datasets.

---

## Trust Architecture

### Certification Tiers

| Tier | Name | Validation Required | Use Cases |
|---|---|---|---|
| 1 | Regulatory/External | Full audit, SME sign-off, reconciliation | SEC filings, contracts |
| 2 | Executive/Board | Definition review, source validation | Board presentations |
| 3 | Operational/Internal | Automated validation, spot-checks | Departmental reports |
| 4 | Exploratory/Provisional | Automated only, clearly marked | Ad-hoc analysis |

### Response Requirements

Every AI system response must include:

- **Answer:** The actual result
- **Definition Used:** Which interpretation was applied and why
- **Source:** Where the data came from
- **Confidence:** Multi-dimensional: definition, data quality, temporal validity, authorization, completeness
- **Caveats:** Any known issues or limitations (from tribal knowledge)
- **Lineage:** How the answer was computed (full resolution DAG)
- **Precedent:** Whether a similar question has been resolved before and how (from Decision Trace Graph)

---

## Roadmap Overview

| Phase | Timeline | Deliverables |
|---|---|---|
| Foundation | Days 1-30 | Infrastructure, 10 certified metrics, working demo, MCP server |
| Factory | Days 31-60 | Extraction pipeline, 50 data products, SME workflow, OSI bridge |
| Scale | Days 61-90 | Governance model, 150 data products, 100 pilot users, decision trace collection |
| Intelligent | Months 4-6 | 500 data products, precedent engine, drift detection, external agent integration |
| Research | Months 7-12 | 1000+ products, learned resolution, compositional planning, operational excellence |

---

## Key Risks to Mitigate

| Risk | Mitigation |
|---|---|
| SME availability bottleneck | AI-first (review, don't write); 15-min sessions; async workflow |
| Extraction accuracy | Confidence scoring; mandatory SME validation for Tier 1-2 |
| AI hallucination | AI reasons, databases compute; all computation in Semantic Layer |
| Organizational resistance | Frame as enabling governance; business units own domains |
| Maintenance burden | Drift detection; scheduled reviews; ownership accountability |
| Security/access control | Inherit existing RLS; integrate with enterprise auth |
| Estate changes breaking contracts | Drift Detection Service; versioned contracts; backward compatibility |
| Frontier/Cowork platform lock-in | Protocol-native distribution (MCP, OSI, REST); platform-agnostic |

---

## Success Criteria

A successful solution would:

- Enable AI systems to answer business questions accurately using the existing data estate
- Require minimal manual curation (80%+ automated extraction)
- Scale linearly, not exponentially, as datasets are added
- Provide explainable, auditable answers with clear provenance
- Prevent unsafe or unauthorized data access
- Improve over time through decision traces and feedback loops
- Deliver initial value (50+ high-value data products) within 90 days
- Scale to 500+ data products within 12 months
- Support industry-standard protocols (MCP, OSI, REST) for AI system integration
- Work underneath OpenAI Frontier, Anthropic Cowork, and custom agent frameworks
- Survive continuous migration and modernization of the physical data estate
- Demonstrate that the resolution engine gets smarter over time (measurable accuracy improvement from decision trace learning)

---

## Your Task

Propose a comprehensive solution that addresses this problem. Your proposal should include:

1. **Architecture:** Detailed component design with clear interfaces, including the Intelligent Resolution Engine, Decision Trace Graph, and Drift Detection Service
2. **Data Model:** Schema for Semantic Contracts, knowledge assets, decision traces, and migration records
3. **Intelligent Resolution:** How the resolution engine combines neural perception, symbolic reasoning, precedent learning, and compositional planning
4. **Extraction Pipeline:** How to automatically harvest context from existing artifacts, including Snowflake SVA, dbt metrics, and OSI imports
5. **Runtime Flow:** Step-by-step resolution from user query to trusted answer, showing the neuro-symbolic reasoning path
6. **Factory Process:** Repeatable workflow for scaling data product onboarding, including precedent-based acceleration
7. **Trust Model:** How confidence, certification, and provenance work with multi-dimensional scoring
8. **Decision Trace System:** How resolution history feeds back into the context layer for continuous improvement
9. **Drift Detection:** How the system stays in sync with a continuously evolving physical data estate
10. **Protocol Integration:** How ECP exposes context via MCP, OSI, and REST/gRPC
11. **Implementation Roadmap:** Phased approach with clear milestones, separating practical-now from research-frontier
12. **Technology Recommendations:** Specific tools and platforms
13. **Risk Mitigation:** How to address each identified risk
14. **Success Metrics:** How to measure progress and outcomes, including resolution intelligence improvement
15. **Research Frontiers:** What components are under active research and how to architect for future intelligence without blocking current delivery

Remember: The solution must be incremental, deliver value quickly, and scale without requiring data migration or multi-year governance programs. The intelligent resolution capabilities should be layered progressively -- start with the orchestrator, instrument for traces, and add intelligence as the corpus grows.

---

## Reference Documents

- enterprise-context-platform-spec-v4.md -- Complete technical specification
- enterprise-context-platform-market-update.md -- Competitive landscape and positioning
- agents.md -- Agent implementation guide (forthcoming)

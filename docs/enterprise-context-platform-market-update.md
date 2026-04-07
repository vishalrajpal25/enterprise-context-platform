# Enterprise Context Platform: Market Positioning Update

**Date:** March 26, 2026 | **Status:** Strategic Analysis | **Audience:** Vishal (ECP Founder)

---

## 1. Executive Summary

Between January and March 2026, the enterprise context layer thesis moved from "emerging insight" to "consensus category." Every major player -- OpenAI, Anthropic, Snowflake, Databricks, Salesforce, a16z -- now explicitly names "context" as the bottleneck for enterprise AI. The ECP spec's core thesis has been validated. The question is no longer *whether* this layer matters but *who owns it* and *how deep it goes*.

This document covers: (a) what each major player is building and how, (b) the technical implementation patterns emerging across the market, (c) what ECP does that nobody else does yet, and (d) the updated positioning strategy.

---

## 2. Competitive Landscape: Who Is Building What

### 2.1 OpenAI Frontier (Launched Feb 5, 2026)

**What it is:** An enterprise agent platform with four pillars: Business Context (semantic layer), Agent Execution, Evaluation/Optimization, and Identity/Governance.

**Technical implementation:**
- Business Context is a connector-based integration layer. Frontier connects to data warehouses, CRM, ERP, ticketing, and internal applications using open standards. It creates a normalized view that agents query.
- The semantic layer is *broad but shallow*. It connects siloed systems and normalizes permissions/retrieval logic. It does NOT define metrics, resolve ambiguity, capture tribal knowledge, or enforce certification tiers.
- Agent execution supports local, cloud, and OpenAI-hosted runtimes. Agents can use tools, run code, build memory from past interactions.
- The evaluation layer provides optimization loops and performance monitoring. Agents "learn what good looks like" over time.
- Forward Deployed Engineers (FDEs) are paired with enterprise teams to design architectures and operationalize governance.

**Primitives/stores:**
- No public detail on specific data stores. Frontier appears to use a metadata registry that normalizes system connections rather than a knowledge graph or vector store. The context is integration-level, not semantic-contract-level.
- MCP compatibility is implied but not confirmed as the primary protocol.

**What it does NOT do:**
- No factory model for semantic contract onboarding
- No tribal knowledge extraction pipeline
- No certification tiers or provenance per response
- No separation of Context Registry from Semantic Layer (both are collapsed into "Business Context")
- No "agent never does math" principle; agents can reason and act across systems without a deterministic computation boundary

**Positioning vs. ECP:** Frontier is an *agent operating system* that needs a deep context layer underneath it. ECP is that context layer. They are complementary, not competitive. Frontier solves "how do agents execute across systems." ECP solves "how do agents know what the data means."

---

### 2.2 Anthropic: Cowork + MCP + Agent Skills (Feb 2026)

**What it is:** A protocol-first ecosystem strategy rather than a monolithic platform.

**Technical implementation:**
- MCP (Model Context Protocol) is the connective tissue. Claude pulls context from Slack, Google Drive, CRM, financial systems simultaneously via MCP connectors.
- Agent Skills are file-based, portable instruction sets. Each skill takes ~dozens of tokens when summarized in context, with full details loading only when the task requires them ("progressive disclosure").
- Skills are an open standard (agentskills.io). Enterprise admins can provision skills centrally and control which workflows are available.
- Plugin architecture allows pre-built agents for domain tasks (financial research, engineering specs, legal). Private plugin marketplaces for enterprises.

**Primitives/stores:**
- Skills are stored as file-based artifacts (SKILL.md pattern). No centralized semantic registry.
- Context is assembled dynamically from MCP connections at runtime, not pre-materialized in a knowledge graph.
- No persistent context graph or semantic contract store. The "context layer" is emergent from tool connections, not architecturally defined.

**What it does NOT do:**
- No unified business glossary, ontology, or semantic contract system
- No concept resolution pipeline (what does "revenue" mean in this org?)
- No tribal knowledge capture or extraction
- No certification tiers or provenance per response
- No factory model for data product onboarding

**Positioning vs. ECP:** Anthropic builds the *protocol and agent capabilities*. ECP provides the *semantic content* that flows through those protocols. MCP is the pipe; ECP is what goes through the pipe. ECP should expose its Context Registry and Semantic Layer via MCP servers.

---

### 2.3 Snowflake: Semantic View Autopilot + Cortex Agents + Project SnowWork

**What it is:** The most technically mature context layer implementation, but scoped to data within Snowflake.

**Technical implementation:**

*Semantic View Autopilot (GA, Feb 2026):*
- Automatically generates semantic views by analyzing three signals: (1) query history (clustering algorithms that identify consensus business logic from SQL patterns), (2) table metadata (descriptions, keys, cardinality), and (3) user-provided context (Tableau files, example SQL queries).
- When conflicting definitions exist (e.g., two teams define "active user" differently), SVA surfaces the most common pattern as a proposal. If 200+ queries consistently calculate "active user" with specific filters, SVA proposes that consensus logic.
- Semantic views are schema-level objects that integrate with Snowflake's privilege system, sharing mechanisms, and metadata catalog. They define metrics (with AGG functions), dimensions (with synonyms), and relationships.
- OSI (Open Semantic Interchange) compatibility: semantic views can export/import definitions to/from dbt Labs, Looker, Sigma, ThoughtSpot.

*Cortex Agents:*
- Combine Cortex Analyst (structured data queries via semantic views) with Cortex Search (unstructured data via RAG) to answer complex cross-domain questions.
- A Snowflake MCP server exists for external agents to connect.

*Project SnowWork (Research Preview):*
- A control plane for the "agentic enterprise" -- connecting data, intelligence, and action in governed ways for business users.

**Primitives/stores:**
- Semantic Views are the primary primitive (DDL-level schema objects in Snowflake)
- Metrics defined as aggregation functions over columns with descriptions, synonyms, and comments
- Dimensions with synonyms and sample values for disambiguation
- Relationships inferred from keys and query patterns
- All stored natively in Snowflake's catalog (not a separate knowledge graph)

**Self-learning mechanism:**
- SVA continuously learns from real user activity. It monitors query history for definition drift and proposes updates.
- This is the closest any platform comes to "the context layer learns itself" -- but it only learns from SQL query patterns within Snowflake.

**Critical limitations:**
- Snowflake-scoped: cannot incorporate definitions from external tools, legacy databases, or non-Snowflake systems
- No tribal knowledge capture (only learns from query patterns, not from Slack threads, documentation, or human expertise)
- No certification tiers or provenance per response
- No cross-platform resolution (if "revenue" is computed differently in Oracle vs. Snowflake, SVA doesn't resolve this)
- Policy drift across regions and legacy systems is not addressed

**Positioning vs. ECP:** Snowflake SVA is a *within-platform semantic layer*. ECP is a *cross-estate semantic mediation layer*. For enterprises with 10+ data platforms, Snowflake SVA handles one of them well. ECP handles all of them and resolves conflicts between them.

---

### 2.4 Solid ($20M Seed, Feb 2026)

**What it is:** The most direct competitor to ECP. A platform that automates the creation and maintenance of "context graphs" (their term for what ECP calls the Context Registry).

**Technical implementation:**
- Semantic agents that integrate with existing data platforms to learn the structure and meaning of enterprise data.
- Automates definition creation, testing, and maintenance using an "engineering-driven approach to semantics."
- Produces a "single source of truth" for business meaning, continuously updated as business data and operations evolve.
- Claims accuracy improvement from 20-30% to 85%+ and 50-70% reduction in manual semantic maintenance work.

**Primitives/stores:**
- "Context graph" is the core artifact (similar to ECP's Context Registry but less formally specified)
- No public detail on specific stores (likely a combination of graph + vector, similar to ECP's Neo4j + Pinecone pattern)
- Integrates with data warehouses, CRM, communication channels, and systems of record

**What they call the discipline:** "Semantic Engineering" -- dedicated expertise focused on defining, validating, and evolving business meaning. They position today's data analysts as natural candidates to evolve into this role.

**What is NOT clear:**
- No published factory model or repeatable onboarding process
- No certification tiers or trust architecture
- No semantic firewall or "agent never does math" principle
- No published resolution orchestration flow
- No MCP or OSI alignment mentioned
- The level of automation for tribal knowledge extraction is unclear

**Positioning vs. ECP:** Solid is attacking the same problem with a similar thesis but appears less architecturally mature. ECP's advantages: (1) the factory model (Ingest > Synthesize > Ratify > Publish), (2) the separation of Context Registry from Semantic Layer, (3) the Semantic Firewall, (4) certification tiers with provenance, (5) tribal knowledge as a first-class asset type, (6) resolution orchestration with parallel multi-store queries. Solid's advantage: $20M in funding, a public launch, and an established customer base.

---

### 2.5 Data Catalog / Metadata Players

**Atlan** is aggressively positioning as the "enterprise context layer hub." They provide:
- An enterprise-wide metadata lakehouse that sources metadata from every tool in the data stack
- MCP server for context distribution to external agents
- OSI integration for semantic layer interoperability
- "Context Hub" with 40+ resources on building context infrastructure
- Active metadata management with governance and lineage propagation

**AtScale** (Snowflake-backed) is pushing a Universal Semantic Layer with MCP integration, supporting Databricks, BigQuery, and the full BI/AI ecosystem.

**ThoughtSpot** launched Spotter Semantics -- an "agentic semantic layer" using a patented search-token architecture (deterministic, not text-to-SQL).

**dbt Labs** continues pushing MetricFlow as the vendor-neutral semantic layer with 83% accuracy vs. ~40% for raw LLM-to-SQL, and is a founding member of OSI.

---

### 2.6 Glean

**What it is:** Enterprise search and work assistant that has expanded into structured data and is now positioning itself as a context layer for enterprise AI.

**Technical implementation:**
- **Enterprise Graph:** Combines a knowledge graph (entities, relationships, concepts mined from across enterprise sources) with a personal graph (each user's docs, communications, projects). Used for both retrieval and personalization.
- **100+ connectors:** Originally focused on unstructured knowledge (docs, wikis, chats, tickets). Recently extended to structured data sources including Databricks, Salesforce, and Jira.
- **Enterprise memory with reinforcement learning:** Learns from execution traces -- which retrievals were useful, which weren't -- and uses RL signals to refine future retrieval.
- **CEO framing:** "Build your enterprise context stack once, connect it broadly across your enterprise in perpetuity." Glean is explicitly positioning itself as *the* enterprise context platform.

**Where it complements ECP:**
- Glean does **knowledge** (unstructured: docs, chats, tickets, wikis). ECP does **data meaning** (structured: metrics, dimensions, semantic contracts, tribal knowledge about data).
- An AI system can call Glean for "what did the team decide in last week's planning doc?" and call ECP for "what does APAC revenue mean and how do I compute it?"
- ECP's federation mode can include a `GleanAdapter` so unstructured tribal knowledge from Glean enriches ECP's resolutions.

**Where it could threaten:**
- If Glean adds semantic contracts and a deterministic computation boundary, it would overlap directly with ECP. The current Glean architecture has no semantic firewall, no certification tiers, and no deterministic compute layer -- but the distance is closing as they move into structured data.

**Positioning vs. ECP:** "Glean gives you knowledge. ECP gives you data meaning. Together, your AI systems get both."

---

### 2.7 Microsoft IQ Stack

**What it is:** Microsoft's three-layer enterprise context architecture, announced as the foundation for Copilot, Fabric data agents, and Foundry agents.

**The three layers:**
- **Work IQ:** User context from M365 -- docs, emails, chats, meetings, workflow patterns. Built on the Microsoft Graph. Powers Copilot personalization.
- **Fabric IQ:** Data context. An ontology with entity types, relationships, business rules, and validation constraints. Includes Power BI semantic models, a native graph store, data agents, and operations agents. **Key stat: 30+ million existing Power BI models serve as a jumpstart corpus for ontology auto-generation.**
- **Foundry IQ:** Knowledge context. Permission-aware knowledge bases via Azure AI Search, with agentic retrieval over enterprise documents.

**Stack ordering:** Fabric IQ is the data foundation, Foundry IQ is the knowledge middle, Work IQ is the workflow top. Together they're Microsoft's answer to "context layer for enterprise AI."

**Distribution:**
- A **Fabric IQ MCP server** is on the roadmap -- which means any AI system, including non-Microsoft ones, will be able to consume Fabric IQ context.

**Critical ceiling:**
- Non-Microsoft data requires manual effort. From Microsoft's own documentation: "Bringing in external data sources like an Oracle cloud database takes manual effort." Snowflake, Databricks, legacy mainframes, SAP -- all require bespoke integration work.
- Fabric IQ assumes the customer has standardized on Microsoft for data. Most Fortune 500 enterprises have not.

**Positioning vs. ECP:** "ECP makes Fabric IQ more valuable by connecting it to non-Microsoft data." ECP's `FabricIQAdapter` consumes the Fabric IQ ontology via the MCP server, enriches it with context from Snowflake, Glean, Atlan, and dbt, resolves cross-source conflicts, and exposes unified context to any AI system -- including Microsoft Copilot itself.

---

### 2.8 Industry Analyst and VC Consensus

**a16z (March 2026):** Published "Your Data Agents Need Context" -- the definitive VC thesis piece. Key insights:
- Models are smart enough; the bottleneck is business context
- Data gravity platforms (Snowflake, Databricks) will build lightweight context; the question is whether they go deep enough
- There is a window for external solutions because not every enterprise can (or should) build in-house
- The market map shows: data gravity platforms, standalone context layer startups, BI-embedded solutions, and enterprise-built systems

**Foundation Capital:** Published "Context Graphs: AI's Trillion-Dollar Opportunity." Their key insight: *decision traces* (not just definitions) are the next enterprise data asset. When agents execute workflows, persisting the "why" behind each decision creates a queryable record that becomes the real source of truth for autonomy.

**Gartner:** Predicts context engineering will be in 80% of AI tools by 2028, improving agent accuracy by 30%+. Over 50% of AI agent systems will leverage context graphs by 2028.

---

## 3. Technical Deep Dive: Implementation Patterns Across the Market

### 3.1 Primitives and Concept Stores

The market is converging on a three-store pattern, though no one has all three working in production:

| Store Type | Purpose | Who Uses It | ECP Spec |
|---|---|---|---|
| **Semantic Views / Metric Definitions** | Executable metric/dimension definitions that AI systems call for deterministic computation | Snowflake (Semantic Views), dbt (MetricFlow), Cube.js, AtScale | Semantic Layer (Cube.js) |
| **Knowledge Graph / Ontology** | Entity relationships, cross-domain mappings, lineage, concept resolution | Atlan, Palantir, GraphRAG approaches, Neo4j-based custom builds | Knowledge Graph (Neo4j) |
| **Vector Store / Embedding Index** | Semantic search for glossary terms, tribal knowledge, fuzzy matching | Standard RAG pattern, used by most agent platforms | Vector Store (Pinecone) |

**What is missing from most implementations:** A fourth store for **decision traces** -- the structured record of how context turned into action, including policies applied, exceptions granted, precedents referenced, and human overrides. Foundation Capital identifies this as the next trillion-dollar platform opportunity.

**ECP update needed:** Add a Decision Trace Store as a fifth component in the architecture. This captures resolution sessions (already in the PostgreSQL schema as `resolution_sessions`) but should be elevated to a first-class persistent asset that feeds back into the Context Registry.

---

### 3.2 Resolution: How Does Concept Disambiguation Work?

This is where the market is weakest. Most players punt on resolution entirely.

**Snowflake SVA approach:** Consensus-based resolution from query history. If 200+ queries define "active user" one way, that becomes the proposed definition. This works for *within-platform* consensus but fails for *cross-context* disambiguation (Sales vs. Finance definitions of "revenue").

**OpenAI Frontier approach:** Not specified. Frontier connects systems but does not describe a resolution pipeline. Agents presumably resolve ambiguity via LLM reasoning at runtime, which is exactly the failure mode ECP's Semantic Firewall prevents.

**Anthropic approach:** No resolution layer. Context assembly is dynamic from MCP connections. Disambiguation would happen in the agent's reasoning loop.

**a16z's described ideal:** A context layer that includes "canonical entities, identity resolution, and specific instructions for navigating implicit knowledge... a multi-dimensional corpus where both code and natural language coexist."

**Snowflake blog (March 2026) defines five components of a proper context layer:**
1. Analytic semantic model (metrics, dimensions, entities)
2. Relationship and identity layer (ontology, synonym handling, constraints)
3. Business procedures (versioned operational playbooks)
4. Evidence and provenance (trace of sources, transformations, competing sources)
5. Entity resolution and cross-domain integration

**ECP's advantage:** The Resolution Orchestrator in the ECP spec (Parser > Resolver > Executor > Assembler) with parallel multi-store queries is architecturally ahead of anything published. The pattern of resolving "APAC revenue last quarter" into specific metric + region variation + fiscal period + tribal knowledge check + authorization + execution + validation is not replicated by any competitor.

---

### 3.3 Scaling Across Data Sources

The fundamental challenge: enterprises have 10-50+ data platforms. How does the context layer span all of them?

**Snowflake:** Stays within Snowflake. OSI provides interop with dbt/Looker/ThoughtSpot for definition portability, but the execution boundary is Snowflake compute.

**Databricks:** Unity Catalog provides governance and metadata within the Databricks ecosystem. Metric Views (GA late 2025) are Databricks-native.

**OpenAI Frontier:** Connector-based integration. Connects to many systems but does not reconcile conflicting definitions across them.

**OSI (Open Semantic Interchange):** The most promising cross-platform initiative. Vendor-neutral YAML spec for semantic constructs (datasets, metrics, dimensions, relationships, contexts). Coalition includes dbt Labs, Snowflake, Salesforce, ThoughtSpot, AtScale, Databricks, JetBrains, Qlik. However, OSI is a *definition portability* standard, not a *resolution* standard. It tells you how to export a metric definition from one tool and import it into another. It does NOT tell you what to do when two tools define the same metric differently.

**ECP's approach (from the spec):** The Context Registry is platform-agnostic. Knowledge Graph holds cross-platform relationships. The Semantic Layer (Cube.js) can federate queries across Snowflake, Databricks, SQL Server, Oracle via its own data source connectors. The factory model's Ingest phase reads schemas, stored procs, and query logs from ANY platform.

**ECP update needed:** Explicit OSI integration. The factory model's Publish phase should emit OSI-compliant YAML alongside the native Context Registry format. This makes ECP a "producer" of semantic definitions that any OSI-compatible tool can consume, dramatically expanding distribution.

---

### 3.4 Does the Context Layer Learn Over Time?

This is the most technically interesting question. Four mechanisms are emerging:

**Mechanism 1: Query pattern mining (Snowflake SVA)**
- Continuously monitors SQL query history
- Uses clustering algorithms to identify consensus definitions
- Surfaces conflicting patterns for human review
- Limitation: only learns from SQL; misses business context in Slack, email, documentation

**Mechanism 2: Decision trace accumulation (Foundation Capital thesis)**
- Every agent execution emits a structured trace: inputs gathered, policies evaluated, exceptions invoked, approvals received, state written
- Traces accumulate into a context graph where entities (accounts, renewals, policies) are connected by decision events
- Over time, the graph becomes a queryable record of "how the business actually runs"
- Limitation: requires agents to be in the execution path first; no decision traces without deployed agents

**Mechanism 3: Agent self-improvement via traces (LangChain / Manus pattern)**
- Agents reflect on past execution traces to refine their own instructions
- Error traces and stack traces are preserved (not cleaned up) so agents learn from failures
- Agents can write their own skills from repeated patterns (Claude Code skill-creator)
- Limitation: agent-level learning, not enterprise-knowledge-level learning

**Mechanism 4: Human-in-the-loop correction flywheel (Atlan / Solid)**
- Every time a human overrides an AI recommendation, that correction becomes training data for the context layer
- SME approvals, exception grants, and policy amendments feed back into definitions
- "Accuracy creates trust, trust drives adoption, adoption generates corrections, corrections improve accuracy"
- Limitation: requires established adoption before the flywheel spins

**ECP's current approach:** Primarily Mechanism 4 (SME validation in the factory model) with elements of Mechanism 1 (extraction from query logs in the Ingest phase).

**ECP update needed:** Add Mechanism 2 explicitly. The `resolution_sessions` table in the PostgreSQL schema already captures resolution DAGs and results. Elevate this to a "Decision Trace Graph" that:
- Persists every resolution path (which stores were queried, which definitions were selected, why)
- Feeds resolved patterns back into the Context Registry (if the same concept is resolved the same way 50 times, propose it as a canonical definition)
- Captures human overrides as first-class tribal knowledge artifacts
- Enables "precedent search" for future resolutions (how was a similar query resolved last time?)

---

### 3.5 Operating Model for Continuous Migration and Modernization

This is the question nobody is answering well. The physical data estate is not static. Tables get renamed, pipelines get migrated, sources get deprecated. How does the context layer stay in sync?

**Current approaches:**
- **Snowflake SVA:** Continuously monitors query history, so if queries shift to new tables, SVA proposes updated semantic views. But this is reactive (learns after the migration, not during).
- **Atlan:** Active metadata management with bidirectional lineage propagation. When a table changes in Snowflake, Atlan can detect the change and flag affected context artifacts.
- **dbt:** Metrics-as-code in git. When a pipeline is refactored, metric definitions are updated in the same PR. CI/CD tests validate metric consistency.

**What is needed (and what ECP should address):**

1. **Schema drift detection:** Monitor the physical estate for changes (new tables, renamed columns, deprecated views). When a change is detected, flag all affected Semantic Contracts.

2. **Lineage-based impact analysis:** The Knowledge Graph's column-level lineage (`:Column -[:TRANSFORMS_TO]-> :Column`) enables "what breaks if this table changes?" queries. This is already in the ECP spec.

3. **Migration-aware versioning:** When a source system migrates (e.g., Oracle to Snowflake), the Semantic Contract should version the source reference without breaking the agent-facing definition. The contract says "net_revenue is computed as X" regardless of whether the underlying compute is Oracle or Snowflake.

4. **Continuous validation:** Scheduled runs of validation rules against the physical estate. If `amount >= 0` starts failing after a migration, the system flags the affected contracts.

5. **OSI-based portability:** When the underlying platform changes, re-emit the semantic definitions in OSI format so downstream tools adapt automatically.

**ECP update needed:** Add a "Drift Detection Service" as a background process that:
- Monitors physical estate catalogs (Snowflake Information Schema, Databricks Unity Catalog, etc.) for schema changes
- Runs validation rules on a schedule
- Triggers re-extraction for affected datasets in the factory pipeline
- Emits alerts to contract owners when drift is detected
- Versions contracts to maintain backward compatibility during migrations

---

## 4. Updated ECP Positioning

### 4.1 What ECP Does That Nobody Else Does

| Capability | OpenAI Frontier | Anthropic Cowork | Snowflake SVA | Solid | dbt/AtScale | ECP |
|---|---|---|---|---|---|---|
| Cross-estate semantic mediation | Partial (connectors) | No | No (Snowflake only) | Unclear | Partial | Yes |
| Resolution orchestration (multi-store parallel query) | No | No | No | Unclear | No | Yes |
| Semantic Firewall (AI systems never touch raw data) | No | No | No | Unclear | No | Yes |
| "AI Reasons. Databases Compute." (deterministic computation) | No | No | Partial (Cortex Analyst) | Unclear | Yes (MetricFlow) | Yes |
| Tribal knowledge as first-class asset | No | No | No | Claimed | No | Yes |
| Factory model (repeatable onboarding) | No | No | Partial (SVA auto-gen) | Unclear | No | Yes |
| Certification tiers with provenance | No | No | No | No | No | Yes |
| Semantic Contracts as unit of work | No | No | No | No | No | Yes |
| Decision trace accumulation | Partial (eval loops) | No | No | No | No | Add now |
| OSI interoperability | Unknown | No | Yes | Unknown | Yes | Add now |
| Schema drift detection | No | No | Partial (SVA monitoring) | Unknown | Partial (CI/CD) | Add now |

### 4.2 Revised Architecture: Three New Components

Based on market analysis, ECP should add three components to the existing five-layer architecture:

```
ADDITION 1: Decision Trace Graph (new persistent store)
- Stores resolution paths, human overrides, exception grants, precedent links
- Feeds back into Context Registry (resolved patterns become proposed definitions)
- Enables precedent search for future resolutions
- Implementation: Extend resolution_sessions table + add trace->context feedback pipeline

ADDITION 2: OSI Bridge (new integration layer)
- Exports Semantic Contracts as OSI-compliant YAML
- Imports semantic definitions from Snowflake Semantic Views, dbt MetricFlow, Looker, etc.
- Enables ECP to be a "producer" of definitions for the entire OSI ecosystem
- Implementation: OSI SDK integration in the Publish phase of the factory model

ADDITION 3: Drift Detection Service (new background process)
- Monitors physical estate catalogs for schema changes
- Runs scheduled validation against Semantic Contracts
- Triggers re-extraction and alerts for affected contracts
- Implementation: Scheduled jobs that query Information Schema / Unity Catalog APIs
```

### 4.3 Revised Positioning Statement

**Before (January 2026):**
"A semantic mediation layer between AI agents and enterprise data estates."

**After (March 2026):**
"The enterprise context platform that sits underneath agent operating systems (OpenAI Frontier, Anthropic Cowork) and above data platform semantic layers (Snowflake Semantic Views, dbt MetricFlow). ECP provides the deep semantic contracts, tribal knowledge, cross-estate resolution, and trust architecture that makes agents accurate on legacy enterprise data, delivered through a repeatable factory model that scales from 10 to 1000 datasets in months, not years."

**Current (April 2026, v4 -- federation-first):**

ECP is the **enterprise context layer** that gives any AI system -- agents, copilots, workflows, applications -- a trusted understanding of your business data. It **federates over your existing context investments** (Microsoft Fabric IQ, Snowflake SVA, Glean, Atlan, dbt), resolves conflicts between them, and gets smarter with every interaction.

**Math vs Meaning:** Semantic layers do math. ECP does meaning. ECP tells the semantic layer *which* math to do, based on who is asking and what the enterprise context says is correct.

**Three operating modes:**
- **Federation Mode:** Enterprise has invested in Fabric IQ, Snowflake SVA, Glean, Atlan, dbt. ECP federates over them via MCP/API, resolves conflicts, adds trust + traces. ECP competes with none of them and makes all of them more valuable.
- **Hybrid Mode:** Enterprise has partial investments. ECP federates where it can, brings its own stores for the gaps.
- **Standalone Mode:** Enterprise has no existing context layer. ECP brings its own full stack and builds context via the Factory Model.

**The sustainable moat is five things:**
1. **Cross-platform resolution intelligence** -- the only layer that resolves conflicts *between* Fabric IQ, Snowflake SVA, Glean, Atlan, and dbt
2. **Decision Trace Graph** -- structured record of every resolution, feeding back into the Context Registry
3. **Deterministic computation boundary** -- AI reasons, databases compute; no AI system that calls ECP ever generates SQL
4. **Certification tiers with provenance** -- every response carries source attribution and trust level
5. **Three operating modes** -- works for any enterprise maturity level, from greenfield to fully invested

**Updated competitive table (v4 framing):**

| Player | Old framing | v4 framing |
|---|---|---|
| Microsoft Fabric IQ | Competitor | **Federates over** via FabricIQAdapter (MCP) |
| Snowflake SVA | Competitor | **Federates over** via SnowflakeSVAAdapter (API) |
| Glean | Adjacent | **Federates over** via GleanAdapter (Enterprise Graph API) |
| Atlan | Competitor | **Federates over** via AtlanAdapter (MCP) |
| dbt MetricFlow | Adjacent | **Federates over** via DbtAdapter (OSI) |
| OpenAI Frontier / Anthropic Cowork | Above ECP | Consumers (call ECP via MCP) |

### 4.4 Key Messaging Updates

**For CIOs/CAIOs:**
- "OpenAI Frontier and Snowflake Semantic Views solve *part* of the context problem. Frontier connects your systems but does not resolve what your data means. Snowflake SVA defines metrics within Snowflake but cannot span your Oracle, SQL Server, and Databricks estate. ECP bridges the gap."

**For Google Cloud:**
- "ECP is cloud-agnostic and protocol-native (MCP, OSI, REST). It produces OSI-compliant semantic definitions that flow into BigQuery, Looker, and Vertex AI agents. It positions Google Cloud customers to deploy enterprise AI without requiring data migration to a single platform."

**For UnitedHealth Group (or similar prospects):**
- "Your data estate spans claims systems, EHR integrations, actuarial databases, and regulatory reporting pipelines across multiple platforms. No single vendor's semantic layer covers all of it. ECP wraps your entire estate with semantic contracts that any AI system, including Frontier, Cowork, Copilot, or your internal build, can consume safely."

**For Microsoft (Fabric IQ customers):**
- "ECP makes Fabric IQ work in a multi-platform world. We consume your ontology via MCP, enrich with context from Snowflake and Glean, resolve conflicts, and expose unified context to any AI system including Copilot."

**For Snowflake (SVA customers):**
- "ECP extends SVA beyond Snowflake. We import your semantic views, add tribal knowledge and certification, and make your definitions available to AI systems that don't query Snowflake directly."

**For Glean customers:**
- "Glean gives you knowledge. ECP gives you data meaning. Together, your AI systems get both."

**For Atlan customers:**
- "Atlan catalogs your metadata. ECP resolves meaning from it. Together, your AI systems get governed, disambiguated, trustworthy answers."

---

## 5. What to Build Next (Priority Order)

1. **OSI Bridge** -- Highest leverage. Makes ECP compatible with the emerging industry standard. Every OSI-aligned vendor becomes a potential distribution partner.

2. **Decision Trace Graph** -- Highest differentiation. Nobody else is doing this well. Foundation Capital calls it a trillion-dollar opportunity. It also creates the self-learning flywheel.

3. **Drift Detection Service** -- Highest enterprise credibility. Addresses the "what happens when the data estate changes" question that every CIO asks.

4. **MCP Server for Context Registry** -- Enables any MCP-compatible AI system (Claude, GPT, Copilot, custom) to query ECP's Context Registry directly. This is the distribution play.

5. **Snowflake Semantic View importer** -- Practical integration. Many prospects will already have Snowflake SVA running. ECP should ingest those definitions as a starting point for the factory model.

---

## 6. Open Questions for Deep Dive

- Should ECP adopt OSI as the *native* format for Semantic Contracts, or maintain its own schema with OSI as an export?
- How does the Decision Trace Graph interact with regulated industries (HIPAA, SOX)? Traces contain resolution logic that may be auditable.
- Should ECP offer a hosted/SaaS version (competing with Solid) or remain a deployable platform (competing with Palantir's approach)?
- What is the pricing model? Per semantic contract? Per resolution? Per data product?
- How does ECP position against Atlan, which is aggressively claiming the "enterprise context layer" brand with 40+ resources and a marketing machine?

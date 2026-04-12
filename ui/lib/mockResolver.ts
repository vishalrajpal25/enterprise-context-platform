/**
 * Mock resolver — returns ResolveResponse shapes that mirror the real
 * FastAPI backend. Used when the live API is unreachable (VC demo, plane
 * wifi, cold start, first-clone experience).
 *
 * Every scenario has hand-authored content. This is the demo narrative.
 */

import type {
  Persona,
  ResolveResponse,
  ResolutionDAGStep,
  TribalWarning,
  Precedent,
  ResolvedConcept,
  Confidence,
} from "./types";

type Key = string; // `${worldId}:${scenarioId}:${personaId}`

type ResolutionRecipe = {
  headline: string;
  resolved_concepts: Record<string, ResolvedConcept>;
  dag: Omit<ResolutionDAGStep, "id">[];
  warnings: TribalWarning[];
  precedents: Precedent[];
  confidence: Confidence;
  access_granted: boolean;
  filtered_concepts: string[];
  policies: string[];
};

// ─── Helpers ─────────────────────────────────────────────────────────────

const rid = () =>
  `res_${Math.random().toString(36).slice(2, 8)}_${Date.now().toString(36)}`;

function withIds(dag: Omit<ResolutionDAGStep, "id">[]): ResolutionDAGStep[] {
  return dag.map((s, i) => ({ ...s, id: `s${i + 1}` }));
}

// ─── Recipes ─────────────────────────────────────────────────────────────

const RECIPES: Record<Key, ResolutionRecipe> = {
  // ────────────────────────────────────────────────────────────────────
  // METRO CAPITAL · APAC REVENUE · PRIYA (Finance)
  // ────────────────────────────────────────────────────────────────────
  "metro:apac-revenue:priya": {
    headline:
      "Net revenue for APAC (including ANZ), Oct 1 – Dec 31, 2025 · Q3 FY2026",
    resolved_concepts: {
      revenue: {
        concept_id: "metric.revenue.net",
        canonical_name: "Net Revenue",
        plain_english:
          "Recognized revenue after returns, refunds, and intercompany eliminations.",
        department_variation: "finance",
        source: "ECP Canonical Glossary · v2.3",
      },
      region: {
        concept_id: "geo.apac.incl_anz",
        canonical_name: "APAC (incl. ANZ)",
        plain_english:
          "Asia-Pacific including Australia and New Zealand. Finance rollup.",
        department_variation: "finance",
        source: "Finance Regional Hierarchy · owner: regional-fp&a",
      },
      time: {
        concept_id: "time.last_quarter",
        canonical_name: "Last Quarter",
        plain_english:
          "Most recently closed fiscal quarter. Fiscal year starts April 1.",
        fiscal_resolution: "Q3 FY2026 → 2025-10-01 to 2025-12-31",
        source: "Fiscal Calendar · Metro Capital",
      },
    },
    dag: [
      {
        action: "parse_intent",
        label: "Parse intent",
        description:
          "Extract the business entities the user is asking about.",
        duration_ms: 42,
        io: {
          source: "Neural intent parser (Claude Haiku 4.5)",
          query: '"Show me APAC revenue for last quarter"',
          found: [
            "metric: revenue",
            "region: APAC",
            "time_window: last quarter",
          ],
          selected: "3 entities extracted",
        },
      },
      {
        action: "find_concept",
        label: "Resolve 'revenue'",
        description: "Search the knowledge graph for candidate definitions.",
        duration_ms: 88,
        io: {
          source: "Neo4j Knowledge Graph",
          query: "MATCH (c:Concept)-[:ALIAS_OF*0..1]->(:Concept {term:'revenue'})",
          found: [
            "metric.revenue.net (finance)",
            "metric.revenue.gross (sales)",
            "metric.revenue.bookings (sales)",
            "metric.revenue.recognized (accounting)",
          ],
          selected: "metric.revenue.net  ← department=finance canonical",
        },
      },
      {
        action: "find_concept",
        label: "Resolve 'APAC'",
        description: "Graph lookup against regional hierarchies.",
        duration_ms: 61,
        io: {
          source: "Neo4j Knowledge Graph",
          query: "MATCH (r:Region {alias:'APAC'})-[:SCOPED_TO]->(:Department)",
          found: [
            "geo.apac.incl_anz (finance rollup)",
            "geo.apac.excl_anz (sales territory)",
          ],
          selected: "geo.apac.incl_anz  ← finance hierarchy includes Australia + New Zealand",
        },
      },
      {
        action: "apply_fiscal_calendar",
        label: "Resolve 'last quarter'",
        description: "Compute fiscal dates from the live calendar.",
        duration_ms: 12,
        io: {
          source: "Fiscal Calendar Service",
          query: "resolve('last_quarter', as_of=2026-04-08, fy_start=April)",
          output: {
            fiscal_year: "FY2026",
            quarter: "Q3",
            start: "2025-10-01",
            end: "2025-12-31",
          },
          selected: "Q3 FY2026 · 2025-10-01 → 2025-12-31",
        },
      },
      {
        action: "check_policy",
        label: "Authorize",
        description: "Evaluate OPA policies for this role + concept set.",
        duration_ms: 34,
        io: {
          source: "OPA Policy Engine",
          query: "authorize(role='finance_analyst', concepts=[revenue.net, geo.apac])",
          found: [
            "policy: revenue.read.finance → ALLOW",
            "policy: region.apac.read → ALLOW",
          ],
          selected: "access_granted: true",
        },
      },
      {
        action: "lookup_tribal",
        label: "Scan tribal knowledge",
        description: "Vector search for known gotchas touching these concepts.",
        duration_ms: 19,
        io: {
          source: "pgvector · tribal_knowledge",
          query: "cosine_similarity(embed('APAC revenue'), tribal.embedding) > 0.72",
          found: [
            "APAC cost-center remapping (Jan 2021)  sim=0.81",
          ],
          selected: "1 warning attached",
        },
      },
      {
        action: "score_confidence",
        label: "Score confidence",
        description: "Combine data contract SLAs with match scores.",
        duration_ms: 23,
        io: {
          source: "Data contract · fact_revenue_daily",
          output: {
            freshness_sla: "6h",
            completeness: "99.2%",
            data_quality: "97.0%",
            definition_match: "98.0%",
          },
          selected: "overall confidence = 0.94",
        },
      },
      {
        action: "retrieve_precedents",
        label: "Find precedents",
        description: "Look for similar past resolutions by this role.",
        duration_ms: 47,
        io: {
          source: "pgvector · resolution_traces",
          query: "cosine_similarity(embed(query), traces.embedding) > 0.80 AND department='finance'",
          found: [
            "'APAC revenue Q3'            sim=0.94  accepted",
            "'Asia Pacific revenue last Q' sim=0.89  accepted",
            "'APAC rev prev quarter'      sim=0.82  accepted",
          ],
          selected: "3 precedents · confidence boost +0.04",
        },
      },
      {
        action: "build_query",
        label: "Construct execution plan",
        description: "Compose the Cube.js semantic-layer query.",
        duration_ms: 15,
        io: {
          source: "Cube.js semantic layer",
          output: {
            measures: "fact_revenue.net_revenue",
            dimensions: "dim_region.apac_incl_anz",
            time_range: "2025-10-01 to 2025-12-31",
          },
          selected: "1 measure, 1 dimension, deterministic SQL",
        },
      },
    ],
    warnings: [
      {
        id: "w1",
        severity: "info",
        headline: "APAC cost-center remapping (Jan 2021)",
        detail:
          "Australia was moved from the 'ANZ' cost center to 'APAC-South' in January 2021. Comparisons to periods before Q1 2021 may not be apples-to-apples. Adjustment factor available in the finance data mart.",
        author: "captured from: M. Tanaka, Regional FP&A",
        captured_at: "2023-08-14",
      },
    ],
    precedents: [
      {
        resolution_id: "res_a1b2c3",
        query: "APAC revenue Q3",
        similarity: 0.94,
        feedback: "accepted",
        user: "priya@metro",
      },
      {
        resolution_id: "res_d4e5f6",
        query: "Asia Pacific revenue last quarter",
        similarity: 0.89,
        feedback: "accepted",
        user: "finance-team",
      },
      {
        resolution_id: "res_g7h8i9",
        query: "APAC rev prev quarter",
        similarity: 0.82,
        feedback: "accepted",
        user: "priya@metro",
      },
    ],
    confidence: {
      definition: 0.98,
      data_quality: 0.97,
      temporal_validity: 0.95,
      authorization: 1.0,
      completeness: 0.92,
      overall: 0.94,
    },
    access_granted: true,
    filtered_concepts: [],
    policies: ["revenue.read.finance", "region.apac.read"],
  },

  // ────────────────────────────────────────────────────────────────────
  // METRO CAPITAL · APAC REVENUE · MARCO (Sales)
  // ────────────────────────────────────────────────────────────────────
  "metro:apac-revenue:marco": {
    headline:
      "Gross bookings for APAC (excluding ANZ), Oct 1 – Dec 31, 2025 · Q3 FY2026",
    resolved_concepts: {
      revenue: {
        concept_id: "metric.revenue.bookings",
        canonical_name: "Gross Bookings",
        plain_english:
          "Total contract value signed in the period, before recognition or cancellation.",
        department_variation: "sales",
        source: "Sales Glossary · v1.8",
      },
      region: {
        concept_id: "geo.apac.excl_anz",
        canonical_name: "APAC (excl. ANZ)",
        plain_english:
          "Asia-Pacific excluding Australia and New Zealand. Sales treats ANZ as its own territory with its own quota.",
        department_variation: "sales",
        source: "Sales Territory Map · owner: sales-ops",
      },
      time: {
        concept_id: "time.last_quarter",
        canonical_name: "Last Quarter",
        plain_english:
          "Most recently closed fiscal quarter. Fiscal year starts April 1.",
        fiscal_resolution: "Q3 FY2026 → 2025-10-01 to 2025-12-31",
        source: "Fiscal Calendar · Metro Capital",
      },
    },
    dag: [
      {
        action: "parse_intent",
        label: "Parse intent",
        description: "Extract the business entities the user is asking about.",
        duration_ms: 39,
        io: {
          source: "Neural intent parser (Claude Haiku 4.5)",
          query: '"Show me APAC revenue for last quarter"',
          found: [
            "metric: revenue",
            "region: APAC",
            "time_window: last quarter",
          ],
          selected: "3 entities extracted",
        },
      },
      {
        action: "find_concept",
        label: "Resolve 'revenue'",
        description: "Search the knowledge graph for candidate definitions.",
        duration_ms: 91,
        io: {
          source: "Neo4j Knowledge Graph",
          query: "MATCH (c:Concept)-[:ALIAS_OF*0..1]->(:Concept {term:'revenue'})",
          found: [
            "metric.revenue.net (finance)",
            "metric.revenue.gross (sales)",
            "metric.revenue.bookings (sales)",
            "metric.revenue.recognized (accounting)",
          ],
          selected:
            "metric.revenue.bookings  ← sales team measures signed contract value, not recognized revenue",
        },
      },
      {
        action: "find_concept",
        label: "Resolve 'APAC'",
        description: "Graph lookup against sales territory map.",
        duration_ms: 58,
        io: {
          source: "Neo4j Knowledge Graph",
          query: "MATCH (r:Region {alias:'APAC'})-[:TERRITORY_OF]->(:SalesOrg)",
          found: [
            "geo.apac.incl_anz (finance rollup)",
            "geo.apac.excl_anz (sales territory)",
          ],
          selected: "geo.apac.excl_anz  ← ANZ is its own territory with separate RVP + quota",
        },
      },
      {
        action: "apply_fiscal_calendar",
        label: "Resolve 'last quarter'",
        description: "Compute fiscal dates from the live calendar.",
        duration_ms: 11,
        io: {
          source: "Fiscal Calendar Service",
          query: "resolve('last_quarter', as_of=2026-04-08, fy_start=April)",
          output: {
            fiscal_year: "FY2026",
            quarter: "Q3",
            start: "2025-10-01",
            end: "2025-12-31",
          },
          selected: "Q3 FY2026 · 2025-10-01 → 2025-12-31",
        },
      },
      {
        action: "check_policy",
        label: "Authorize",
        description: "Evaluate OPA policies for this role + concept set.",
        duration_ms: 33,
        io: {
          source: "OPA Policy Engine",
          query: "authorize(role='sales_analyst', concepts=[revenue.bookings, geo.apac.excl_anz])",
          found: [
            "policy: bookings.read.sales → ALLOW",
            "policy: region.apac.sales.read → ALLOW",
          ],
          selected: "access_granted: true",
        },
      },
      {
        action: "lookup_tribal",
        label: "Scan tribal knowledge",
        description: "Vector search for known gotchas touching these concepts.",
        duration_ms: 24,
        io: {
          source: "pgvector · tribal_knowledge",
          query: "cosine_similarity(embed('APAC bookings sales'), tribal.embedding) > 0.72",
          found: [
            "ANZ-not-in-APAC reconciliation gap  sim=0.88",
            "Q4 2019 APAC data migration gap    sim=0.74",
          ],
          selected: "2 warnings attached",
        },
      },
      {
        action: "score_confidence",
        label: "Score confidence",
        description: "Combine data contract SLAs with match scores.",
        duration_ms: 21,
        io: {
          source: "Data contract · fact_bookings",
          output: {
            freshness_sla: "2h",
            completeness: "98.5%",
            data_quality: "96.0%",
            definition_match: "96.0%",
          },
          selected: "overall confidence = 0.91",
        },
      },
      {
        action: "retrieve_precedents",
        label: "Find precedents",
        description: "Look for similar past resolutions by this role.",
        duration_ms: 45,
        io: {
          source: "pgvector · resolution_traces",
          query: "cosine_similarity(embed(query), traces.embedding) > 0.80 AND department='sales'",
          found: [
            "'APAC bookings Q3'         sim=0.91  accepted",
            "'Asia bookings last quarter' sim=0.85 accepted",
          ],
          selected: "2 precedents · confidence boost +0.03",
        },
      },
      {
        action: "build_query",
        label: "Construct execution plan",
        description: "Compose the Cube.js semantic-layer query.",
        duration_ms: 14,
        io: {
          source: "Cube.js semantic layer",
          output: {
            measures: "fact_bookings.gross_bookings",
            dimensions: "dim_region.apac_excl_anz",
            time_range: "2025-10-01 to 2025-12-31",
          },
          selected: "1 measure, 1 dimension, deterministic SQL",
        },
      },
    ],
    warnings: [
      {
        id: "w1",
        severity: "warn",
        headline: "ANZ is not in APAC for sales",
        detail:
          "Sales treats Australia and New Zealand as a separate territory with its own regional VP. If you're comparing this number to a finance report, finance *does* include ANZ in APAC. The two numbers will differ by ~18% on average.",
        author: "captured from: J. Park, Sales Ops",
        captured_at: "2024-02-03",
      },
      {
        id: "w2",
        severity: "info",
        headline: "Q4 2019 APAC data gap",
        detail:
          "The APAC booking system was migrated in Oct 2019 and some deals were lost in transit. Any comparison to Q4 2019 is unreliable. Not relevant to this query but flagged for future.",
        author: "captured from: data-engineering",
        captured_at: "2020-01-10",
      },
    ],
    precedents: [
      {
        resolution_id: "res_j0k1l2",
        query: "APAC bookings Q3",
        similarity: 0.91,
        feedback: "accepted",
        user: "marco@metro",
      },
      {
        resolution_id: "res_m3n4o5",
        query: "Asia bookings last quarter",
        similarity: 0.85,
        feedback: "accepted",
        user: "sales-team",
      },
    ],
    confidence: {
      definition: 0.96,
      data_quality: 0.96,
      temporal_validity: 0.95,
      authorization: 1.0,
      completeness: 0.88,
      overall: 0.91,
    },
    access_granted: true,
    filtered_concepts: [],
    policies: ["bookings.read.sales", "region.apac.sales.read"],
  },

  // ────────────────────────────────────────────────────────────────────
  // METRO · APAC REVENUE · DANA (Auditor)
  // ────────────────────────────────────────────────────────────────────
  "metro:apac-revenue:dana": {
    headline:
      "Both definitions returned · finance: net revenue incl ANZ · sales: gross bookings excl ANZ · Q3 FY2026",
    resolved_concepts: {
      revenue_finance: {
        concept_id: "metric.revenue.net",
        canonical_name: "Net Revenue (finance view)",
        plain_english: "Finance-canonical recognized revenue.",
        department_variation: "finance",
        source: "ECP Canonical Glossary",
      },
      revenue_sales: {
        concept_id: "metric.revenue.bookings",
        canonical_name: "Gross Bookings (sales view)",
        plain_english: "Sales-canonical signed contract value.",
        department_variation: "sales",
        source: "Sales Glossary",
      },
    },
    dag: [
      {
        action: "parse_intent",
        label: "Understand the question",
        description:
          "Auditor role: return all variants and their provenance, don't collapse to a single answer.",
        duration_ms: 38,
      },
      {
        action: "find_concept",
        label: "Enumerate all 'revenue' definitions",
        description:
          "4 definitions found across departments. All returned with source attribution.",
        duration_ms: 112,
      },
      {
        action: "find_concept",
        label: "Enumerate all 'APAC' definitions",
        description: "2 region definitions returned, both with provenance.",
        duration_ms: 64,
      },
      {
        action: "apply_fiscal_calendar",
        label: "Resolve 'last quarter'",
        description: "Q3 FY2026.",
        duration_ms: 11,
      },
      {
        action: "check_policy",
        label: "Authorize audit view",
        description:
          "Compliance role has read-all access to financial metrics with full lineage. Policy: audit.read.all · allowed.",
        duration_ms: 29,
      },
      {
        action: "score_confidence",
        label: "Score per-definition",
        description: "Each definition scored independently for audit trail.",
        duration_ms: 31,
      },
    ],
    warnings: [
      {
        id: "w1",
        severity: "critical",
        headline: "Board deck uses finance number. Sales forecast uses sales number.",
        detail:
          "Dana — this is exactly the kind of silent disagreement you're auditing for. Finance's Q3 number and Sales's Q3 number will differ by roughly 12–18% and both are reported to different stakeholders without reconciliation. Decision trace shows 7 executives consumed conflicting numbers in the last quarter.",
        author: "captured from: audit-trail-analysis",
        captured_at: "2026-03-22",
      },
    ],
    precedents: [],
    confidence: {
      definition: 1.0,
      data_quality: 0.97,
      temporal_validity: 0.95,
      authorization: 1.0,
      completeness: 0.99,
      overall: 0.98,
    },
    access_granted: true,
    filtered_concepts: [],
    policies: ["audit.read.all", "lineage.full"],
  },

  // ────────────────────────────────────────────────────────────────────
  // PINE RIDGE · FCF YIELD · ELENA (PM)
  // ────────────────────────────────────────────────────────────────────
  "pine-ridge:fcf-yield:elena": {
    headline:
      "FCF yield, tech book (as-held), 8 quarters · Pine Ridge house definition · peer-adjusted with 14 overrides",
    resolved_concepts: {
      metric: {
        concept_id: "metric.fcf.house",
        canonical_name: "Free Cash Flow (house definition)",
        plain_english:
          "Vendor-standardized FCF with stock-based comp added back. Approved by Elena, 2024-11-02.",
        department_variation: "pm",
        source: "Pine Ridge house glossary",
      },
      universe: {
        concept_id: "portfolio.tech_book.as_held",
        canonical_name: "Tech Book (as held)",
        plain_english:
          "Positions held at each quarter-end (not current holdings back-projected). Amazon included per house rule.",
        department_variation: "pm",
        source: "Portfolio classification overrides · owner: Elena",
      },
      peers: {
        concept_id: "peer_set.internal_overrides",
        canonical_name: "Internal peer sets",
        plain_english:
          "Vendor default peers with 14 manual overrides maintained by J. Kim (senior analyst).",
        source: "peer_overrides.xlsx · last updated 2026-02-14",
      },
    },
    dag: [
      {
        action: "parse_intent",
        label: "Understand the question",
        description:
          "Extracted: metric (FCF yield), universe (tech book), peer set (peer-adjusted), time window (last 8 quarters).",
        duration_ms: 51,
      },
      {
        action: "find_concept",
        label: "Look up 'free cash flow'",
        description:
          "5 definitions: vendor feed, data provider, GAAP, management-adjusted, Pine Ridge house. Elena's role → house definition (vendor-standardized + SBC add-back).",
        duration_ms: 134,
      },
      {
        action: "resolve_portfolio",
        label: "Resolve 'my tech book'",
        description:
          "3 possible interpretations: current holdings back-projected, as-held at each quarter-end, weighted-average exposure. Elena's default is 'as-held'.",
        duration_ms: 89,
      },
      {
        action: "apply_overrides",
        label: "Apply classification overrides",
        description:
          "GICS reclassified Comms Services out of Tech in 2018 → applied cutover. House rule: Amazon counted as tech → applied.",
        duration_ms: 47,
      },
      {
        action: "resolve_peers",
        label: "Resolve peer sets",
        description:
          "Vendor default + 14 manual overrides from peer_overrides.xlsx (DDOG, SNOW, CRWD, ...).",
        duration_ms: 72,
      },
      {
        action: "check_vintage",
        label: "Check data vintage",
        description:
          "3 companies in universe restated figures after your last pull (MSFT, CRM, ORCL). Flagging for re-pull.",
        duration_ms: 38,
      },
      {
        action: "apply_fx",
        label: "FX conversion",
        description:
          "Cross-currency holdings normalized at WM/Reuters quarterly average. House rule.",
        duration_ms: 22,
      },
      {
        action: "check_policy",
        label: "Authorize",
        description:
          "PM has full access to own book. Policy: portfolio.read.own · allowed.",
        duration_ms: 18,
      },
      {
        action: "score_confidence",
        label: "Score the answer",
        description:
          "High confidence on definition + universe. Lower on completeness due to vintage drift.",
        duration_ms: 26,
      },
    ],
    warnings: [
      {
        id: "w1",
        severity: "warn",
        headline: "3 restatements since your last pull",
        detail:
          "MSFT, CRM, and ORCL restated historical FCF between your last query (2026-03-15) and now. The 8-quarter series includes restated figures for MSFT (Q2 FY24), CRM (Q3 FY25), and ORCL (Q1 FY26). Re-run or pin to the 2026-03-15 vintage?",
        author: "vintage-watcher",
        captured_at: "2026-04-07",
      },
      {
        id: "w2",
        severity: "info",
        headline: "GICS reclassification (Sept 2018)",
        detail:
          "Comms Services sector was split out of Tech. Your 8-quarter window starts 2024-Q1 — post-cutover, so no mixed-era data. Not an issue for this query.",
        author: "house-rule-docs",
      },
      {
        id: "w3",
        severity: "info",
        headline: "Amazon is tech per house rule",
        detail:
          "GICS classifies AMZN as Consumer Discretionary. Pine Ridge house rule includes it in tech universes. Override authored by Elena, 2023-06-12.",
        author: "Elena Voss",
        captured_at: "2023-06-12",
      },
    ],
    precedents: [
      {
        resolution_id: "res_fcf_001",
        query: "tech book FCF yield last 8Q",
        similarity: 0.97,
        feedback: "accepted",
        user: "elena@pine-ridge",
      },
      {
        resolution_id: "res_fcf_002",
        query: "tech book free cash flow yield peer adjusted",
        similarity: 0.92,
        feedback: "accepted",
        user: "elena@pine-ridge",
      },
    ],
    confidence: {
      definition: 0.99,
      data_quality: 0.93,
      temporal_validity: 0.82,
      authorization: 1.0,
      completeness: 0.85,
      overall: 0.89,
    },
    access_granted: true,
    filtered_concepts: [],
    policies: ["portfolio.read.own", "peer_overrides.read"],
  },

  // ────────────────────────────────────────────────────────────────────
  // PINE RIDGE · FCF YIELD · JIN (Junior Analyst)
  // ────────────────────────────────────────────────────────────────────
  "pine-ridge:fcf-yield:jin": {
    headline:
      "FCF yield, tech universe, 8 quarters · position weights hidden for your role",
    resolved_concepts: {
      metric: {
        concept_id: "metric.fcf.house",
        canonical_name: "Free Cash Flow (house definition)",
        plain_english: "Same as PM view — house definition used.",
        source: "Pine Ridge house glossary",
      },
    },
    dag: [
      {
        action: "parse_intent",
        label: "Understand the question",
        description: "Same parse as PM.",
        duration_ms: 49,
      },
      {
        action: "find_concept",
        label: "Look up 'free cash flow'",
        description: "House definition applied.",
        duration_ms: 121,
      },
      {
        action: "check_policy",
        label: "Authorize",
        description:
          "Junior analyst role has access to universe-level metrics but NOT individual position weights. Policy: portfolio.weights.blocked_for_role · filtered.",
        duration_ms: 38,
      },
      {
        action: "redact_outputs",
        label: "Redact protected fields",
        description:
          "Position weights replaced with 'above_threshold' / 'below_threshold' categorical. Individual tickers visible, contribution hidden.",
        duration_ms: 24,
      },
    ],
    warnings: [
      {
        id: "w1",
        severity: "warn",
        headline: "You're seeing a restricted view",
        detail:
          "As a junior analyst you see the universe and the metric values but not position weights — those are treated like PII for alpha-protection reasons. If you need the weighted series ask Elena.",
        author: "policy-docs",
      },
    ],
    precedents: [],
    confidence: {
      definition: 0.99,
      data_quality: 0.93,
      temporal_validity: 0.82,
      authorization: 0.7,
      completeness: 0.6,
      overall: 0.81,
    },
    access_granted: true,
    filtered_concepts: ["position_weights", "attribution_by_name"],
    policies: ["portfolio.read.universe", "portfolio.weights.blocked_for_role"],
  },

  // ────────────────────────────────────────────────────────────────────
  // MERIDIAN · READMISSION RATE · AISHA (Quality)
  // ────────────────────────────────────────────────────────────────────
  "meridian:readmission-rate:aisha": {
    headline:
      "30-day readmission, heart failure · CMS methodology · 14.2% (FY2025 rolling)",
    resolved_concepts: {
      metric: {
        concept_id: "metric.readmission.cms",
        canonical_name: "30-Day Readmission Rate (CMS)",
        plain_english:
          "CMS Hospital-Wide Readmission measure. All-cause, specific DRG inclusions/exclusions, index admission rules per CMS tech spec v11.0.",
        department_variation: "quality",
        source: "CMS HWR Technical Specification",
      },
      cohort: {
        concept_id: "cohort.heart_failure.cms",
        canonical_name: "Heart Failure (CMS cohort)",
        plain_english:
          "CMS-defined HF cohort — principal discharge diagnosis of heart failure per ICD-10 I50.xx with exclusions for transfers and AMA.",
        source: "CMS cohort definitions",
      },
    },
    dag: [
      {
        action: "parse_intent",
        label: "Understand the question",
        description:
          "Extracted: metric (readmission rate), condition (heart failure), implicit time window (most recent reportable period).",
        duration_ms: 45,
      },
      {
        action: "find_concept",
        label: "Look up 'readmission rate'",
        description:
          "3 definitions: CMS (regulatory), internal clinical, BCBS value-based contract. Quality lead role → CMS default.",
        duration_ms: 97,
      },
      {
        action: "find_concept",
        label: "Look up 'heart failure'",
        description: "CMS HWR cohort selected (I50.xx principal diagnosis).",
        duration_ms: 51,
      },
      {
        action: "apply_temporal",
        label: "Apply reporting window",
        description:
          "CMS reporting is fiscal-year-to-date rolling. Current reportable = FY2025 (Jul 2024 – Jun 2025).",
        duration_ms: 18,
      },
      {
        action: "check_policy",
        label: "Authorize",
        description:
          "Quality lead has access to aggregate quality metrics. Patient-level PHI not requested.",
        duration_ms: 31,
      },
      {
        action: "lookup_tribal",
        label: "Scan tribal knowledge",
        description:
          "Critical: the three definitions disagree by ~5 points. Flagging all three for comparison.",
        duration_ms: 27,
      },
      {
        action: "score_confidence",
        label: "Score the answer",
        description: "High confidence — CMS methodology is fully deterministic.",
        duration_ms: 22,
      },
    ],
    warnings: [
      {
        id: "w1",
        severity: "critical",
        headline: "Three definitions disagree by ~5 points",
        detail:
          "CMS methodology: 14.2%. Internal clinical: 11.8%. BCBS value-based contract: 9.4%. Same patients, three rulebooks. Board deck uses CMS (this one). Clinical review uses internal. BCBS payout depends on the contract number. Do NOT mix them in the same presentation — it's a documented miscommunication pattern, logged by compliance in Q4 2024.",
        author: "M. Chen, Compliance",
        captured_at: "2024-12-18",
      },
      {
        id: "w2",
        severity: "info",
        headline: "2-midnight rule change (2013)",
        detail:
          "Admissions before 2014-01-01 use the pre-rule-change observation hour convention. Not relevant to current reporting but flagged for historical comparisons.",
        author: "inpatient-ops",
      },
    ],
    precedents: [
      {
        resolution_id: "res_hwr_001",
        query: "heart failure 30 day readmission",
        similarity: 0.96,
        feedback: "accepted",
        user: "aisha@meridian",
      },
    ],
    confidence: {
      definition: 0.95,
      data_quality: 0.94,
      temporal_validity: 0.98,
      authorization: 1.0,
      completeness: 0.97,
      overall: 0.95,
    },
    access_granted: true,
    filtered_concepts: [],
    policies: ["quality.aggregate.read", "cms.methodology.apply"],
  },

  // ────────────────────────────────────────────────────────────────────
  // MERIDIAN · READMISSION · TOM (Value-Based Contracts)
  // ────────────────────────────────────────────────────────────────────
  "meridian:readmission-rate:tom": {
    headline:
      "30-day readmission, heart failure · BCBS value-based contract methodology · 9.4%",
    resolved_concepts: {
      metric: {
        concept_id: "metric.readmission.bcbs",
        canonical_name: "30-Day Readmission Rate (BCBS VBC)",
        plain_english:
          "BCBS value-based contract definition. Narrower exclusions than CMS — excludes planned readmissions and same-MDC transfers. Tied to the risk corridor in the 2024 VBC contract.",
        department_variation: "finance",
        source: "BCBS VBC Contract · Schedule B",
      },
      cohort: {
        concept_id: "cohort.heart_failure.bcbs",
        canonical_name: "Heart Failure (BCBS contract cohort)",
        plain_english:
          "BCBS-specific cohort — ICD-10 I50.xx with additional exclusion of observation stays < 48 hours per contract language.",
        source: "BCBS VBC Schedule B",
      },
    },
    dag: [
      { action: "parse_intent", label: "Understand the question", description: "Extracted: metric (readmission rate), condition (heart failure).", duration_ms: 42 },
      { action: "find_concept", label: "Look up 'readmission rate'", description: "3 definitions found. Finance/VBC role → BCBS contract definition (not CMS, not internal clinical).", duration_ms: 104 },
      { action: "find_concept", label: "Look up 'heart failure'", description: "BCBS contract cohort selected — stricter exclusions than CMS.", duration_ms: 48 },
      { action: "apply_temporal", label: "Apply contract period", description: "Current BCBS contract period: Jul 2024 – Jun 2025.", duration_ms: 16 },
      { action: "check_policy", label: "Authorize", description: "VBC role has access to contract-level quality metrics.", duration_ms: 28 },
      { action: "score_confidence", label: "Score the answer", description: "High confidence — contract definition is deterministic.", duration_ms: 19 },
    ],
    warnings: [
      { id: "w1", severity: "critical", headline: "This number is 5 points below the CMS number", detail: "CMS reports 14.2%. Your contract number is 9.4%. The difference is real — BCBS uses narrower exclusions and a different cohort definition. If you're presenting to the board, use CMS. If you're calculating the shared savings payout, use this one.", author: "M. Chen, Compliance", captured_at: "2024-12-18" },
      { id: "w2", severity: "warn", headline: "Contract penalty threshold is 10.0%", detail: "Your current rate of 9.4% is below the penalty threshold (10.0%) but above the bonus threshold (8.0%). A single coding pattern change could move this above the penalty line.", author: "finance-ops" },
    ],
    precedents: [],
    confidence: { definition: 0.97, data_quality: 0.94, temporal_validity: 0.96, authorization: 1.0, completeness: 0.95, overall: 0.95 },
    access_granted: true, filtered_concepts: [], policies: ["vbc.contract.read", "bcbs.methodology.apply"],
  },

  // ────────────────────────────────────────────────────────────────────
  // MERIDIAN · READMISSION · LEE (Data Analyst)
  // ────────────────────────────────────────────────────────────────────
  "meridian:readmission-rate:lee": {
    headline:
      "30-day readmission, heart failure · internal clinical methodology · 11.8%",
    resolved_concepts: {
      metric: {
        concept_id: "metric.readmission.internal",
        canonical_name: "30-Day Readmission Rate (Internal Clinical)",
        plain_english:
          "Internal clinical definition — includes observation stays, excludes planned readmissions. Used by the CMO dashboard and clinical improvement teams.",
        department_variation: "analytics",
        source: "Clinical Analytics Standard · v4.2",
      },
    },
    dag: [
      { action: "parse_intent", label: "Understand the question", description: "Extracted: metric (readmission rate), condition (heart failure).", duration_ms: 38 },
      { action: "find_concept", label: "Look up 'readmission rate'", description: "3 definitions found. Analytics role → internal clinical (the one powering the CMO dashboard).", duration_ms: 91 },
      { action: "apply_temporal", label: "Apply reporting window", description: "Internal: rolling 12-month window ending current month.", duration_ms: 15 },
      { action: "check_policy", label: "Authorize", description: "Data analyst has read access to aggregate clinical metrics.", duration_ms: 24 },
      { action: "score_confidence", label: "Score the answer", description: "High confidence — internal methodology is well-documented.", duration_ms: 18 },
    ],
    warnings: [
      { id: "w1", severity: "warn", headline: "This is NOT the number for the board or CMS", detail: "Internal clinical rate (11.8%) differs from CMS (14.2%) and BCBS contract (9.4%). The internal number includes observation stays which CMS excludes. Make sure your audience knows which definition they're seeing.", author: "analytics-lead" },
    ],
    precedents: [],
    confidence: { definition: 0.93, data_quality: 0.92, temporal_validity: 0.95, authorization: 1.0, completeness: 0.94, overall: 0.93 },
    access_granted: true, filtered_concepts: [], policies: ["clinical.aggregate.read"],
  },

  // ────────────────────────────────────────────────────────────────────
  // MERIDIAN · DIABETIC PATIENTS · AISHA (Quality)
  // ────────────────────────────────────────────────────────────────────
  "meridian:diabetic-patients:aisha": {
    headline:
      "Diabetic patients · ICD-10 problem list + claims dual-source · 24,312 active",
    resolved_concepts: {
      metric: {
        concept_id: "metric.diabetic_count.quality",
        canonical_name: "Diabetic Patient Count (Quality/CMS)",
        plain_english:
          "Union of ICD-10 E11.xx on active problem list AND at least one diabetes-related claim in trailing 12 months. Quality standard for HEDIS reporting.",
        department_variation: "quality",
        source: "HEDIS Technical Specification · MY2025",
      },
    },
    dag: [
      { action: "parse_intent", label: "Understand the question", description: "Extracted: count of diabetic patients, current census.", duration_ms: 35 },
      { action: "find_concept", label: "Look up 'diabetic patients'", description: "3 definitions: problem-list only (Epic), claims-only (payer view), union (quality/HEDIS). Quality role → union definition.", duration_ms: 112 },
      { action: "lookup_tribal", label: "Scan tribal knowledge", description: "Critical: Epic problem list and claims disagree by 12%. Pre-diabetes inclusion varies.", duration_ms: 29 },
      { action: "check_policy", label: "Authorize", description: "Aggregate counts only — no PHI.", duration_ms: 22 },
      { action: "score_confidence", label: "Score the answer", description: "Moderate — the 12% discrepancy between sources is a known issue.", duration_ms: 20 },
    ],
    warnings: [
      { id: "w1", severity: "critical", headline: "Epic problem list and claims disagree by 12%", detail: "Problem list shows 21,714 patients. Claims show 24,312. The gap is mostly patients whose primary care is outside the network but who have diabetes-related specialist visits. Quality standard (HEDIS) uses the union, which is the higher number.", author: "Dr. A. Nair, Quality", captured_at: "2025-11-03" },
      { id: "w2", severity: "warn", headline: "Pre-diabetes (E11.65) inclusion varies by measure", detail: "Some HEDIS measures include pre-diabetes in the denominator, others don't. This count includes E11.xx only (confirmed diabetes). If you need pre-diabetes, specify explicitly.", author: "clinical-informatics" },
    ],
    precedents: [{ resolution_id: "res_dm_001", query: "diabetic patient count hedis", similarity: 0.94, feedback: "accepted", user: "aisha@meridian" }],
    confidence: { definition: 0.88, data_quality: 0.85, temporal_validity: 0.92, authorization: 1.0, completeness: 0.82, overall: 0.87 },
    access_granted: true, filtered_concepts: [], policies: ["quality.aggregate.read", "hedis.denominator"],
  },

  // ────────────────────────────────────────────────────────────────────
  // MERIDIAN · DIABETIC PATIENTS · TOM (Finance)
  // ────────────────────────────────────────────────────────────────────
  "meridian:diabetic-patients:tom": {
    headline:
      "Diabetic patients · claims-based only · 21,714 attributed members",
    resolved_concepts: {
      metric: {
        concept_id: "metric.diabetic_count.finance",
        canonical_name: "Diabetic Member Count (Claims-Based)",
        plain_english:
          "Members with at least one claim with ICD-10 E11.xx in trailing 12 months AND attributed to Meridian as primary. Used for VBC risk stratification.",
        department_variation: "finance",
        source: "VBC Risk Stratification Model",
      },
    },
    dag: [
      { action: "parse_intent", label: "Understand the question", description: "Extracted: count of diabetic patients.", duration_ms: 34 },
      { action: "find_concept", label: "Look up 'diabetic patients'", description: "3 definitions. Finance/VBC role → claims-based (attributed members only).", duration_ms: 98 },
      { action: "check_policy", label: "Authorize", description: "VBC role — aggregate counts permitted.", duration_ms: 25 },
      { action: "score_confidence", label: "Score the answer", description: "High confidence on claims data. Attribution model refreshes monthly.", duration_ms: 18 },
    ],
    warnings: [
      { id: "w1", severity: "warn", headline: "This count is 12% lower than Quality's number", detail: "Quality uses problem list + claims union (24,312). Finance uses claims-only attributed (21,714). The gap is real — different sources, different business questions. For VBC payout calculations, this is the correct denominator.", author: "analytics-lead" },
    ],
    precedents: [],
    confidence: { definition: 0.95, data_quality: 0.93, temporal_validity: 0.90, authorization: 1.0, completeness: 0.91, overall: 0.93 },
    access_granted: true, filtered_concepts: [], policies: ["vbc.stratification.read"],
  },

  // ────────────────────────────────────────────────────────────────────
  // ATLAS · MLR FLORIDA MA · RAVI (Med Econ)
  // ────────────────────────────────────────────────────────────────────
  "atlas:mlr-florida-ma:ravi": {
    headline:
      "ACA-compliant MLR, FL MA contract aggregate, 3-year rolling · provisional (Q1 claims 73% complete)",
    resolved_concepts: {
      metric: {
        concept_id: "metric.mlr.aca",
        canonical_name: "Medical Loss Ratio (ACA §2718)",
        plain_english:
          "Numerator: claims + HHS-qualifying QIA + fraud prevention (capped). Denominator: premium − taxes & fees. 3-year rolling.",
        source: "ACA §2718, 45 CFR 158",
      },
      universe: {
        concept_id: "cohort.ma_florida.residential",
        canonical_name: "Florida MA (residential)",
        plain_english:
          "Members whose residential address is in Florida, regardless of contract domicile. Med-econ house rule.",
        department_variation: "med-econ",
        source: "Atlas cohort definitions",
      },
    },
    dag: [
      {
        action: "parse_intent",
        label: "Understand the question",
        description:
          "ACA-compliant qualifier → regulatory MLR definition (not internal or CFO definition).",
        duration_ms: 58,
      },
      {
        action: "find_concept",
        label: "Look up 'medical loss ratio'",
        description:
          "3 definitions: ACA regulatory, internal actuarial, CFO earnings. 'ACA-compliant' in query → regulatory.",
        duration_ms: 102,
      },
      {
        action: "resolve_cohort",
        label: "Resolve 'Florida MA'",
        description:
          "4 possible interpretations. Med-econ default: residential address in FL.",
        duration_ms: 76,
      },
      {
        action: "apply_fiscal_calendar",
        label: "Resolve 'Q1'",
        description:
          "Atlas fiscal year = calendar year. Q1 2026 = Jan 1 – Mar 31, 2026.",
        duration_ms: 14,
      },
      {
        action: "check_completion",
        label: "Claims completion factor",
        description:
          "Q1 2026 claims are 73% paid as of today. Historical run-out pattern suggests MLR will drift up ~2.1 points over 90 days.",
        duration_ms: 43,
      },
      {
        action: "check_risk_adj",
        label: "Risk adjustment snapshot",
        description:
          "Revenue denominator uses current risk scores. CMS true-up runs through Q3 2027 — figures are preliminary.",
        duration_ms: 38,
      },
      {
        action: "check_policy",
        label: "Authorize",
        description:
          "Med-econ role has access to aggregate MLR. No member-level PHI requested.",
        duration_ms: 29,
      },
      {
        action: "score_confidence",
        label: "Score the answer",
        description:
          "Low temporal validity — current-period MLR is provisional by design. Completeness reflects claims run-out.",
        duration_ms: 25,
      },
    ],
    warnings: [
      {
        id: "w1",
        severity: "critical",
        headline: "Q1 2026 claims only 73% complete",
        detail:
          "Based on historical run-out patterns, your Q1 MLR will drift upward by ~2.1 points over the next 90 days as remaining claims are paid. Actuarial team does not consider Q1 MLR filing-grade until Jun 15 (90% completion threshold). If this is for internal review, the number is directionally correct. If it's for the state filing, wait.",
        author: "N. Orlov, Chief Actuary",
        captured_at: "2026-01-12",
      },
      {
        id: "w2",
        severity: "warn",
        headline: "Revenue denominator will be retroactively adjusted",
        detail:
          "CMS risk adjustment true-up for plan year 2026 will continue through Q3 2027. The revenue figure in your denominator can change by ±3% as late-submitted diagnoses update member risk scores. Any MLR number from a period less than 18 months old is, by definition, not final.",
        author: "risk-adjustment-ops",
      },
      {
        id: "w3",
        severity: "warn",
        headline: "Fiscal calendar mismatch",
        detail:
          "Atlas Q1 = calendar Q1 (Jan–Mar). Your parent company reports on a July fiscal year, where Q1 = Jul–Sep. If you're emailing this number upstream, clarify the period explicitly.",
        author: "finance-coordination",
      },
    ],
    precedents: [],
    confidence: {
      definition: 0.99,
      data_quality: 0.91,
      temporal_validity: 0.65,
      authorization: 1.0,
      completeness: 0.73,
      overall: 0.82,
    },
    access_granted: true,
    filtered_concepts: [],
    policies: ["mlr.aca.read", "cohort.florida.residential"],
  },

  // ────────────────────────────────────────────────────────────────────
  // ATLAS · MLR FLORIDA MA · NINA (Actuary)
  // ────────────────────────────────────────────────────────────────────
  "atlas:mlr-florida-ma:nina": {
    headline:
      "MLR, FL MA · actuarial basis (IBNR-adjusted) · 87.3% · completion-adjusted to 91.2%",
    resolved_concepts: {
      metric: {
        concept_id: "metric.mlr.actuarial",
        canonical_name: "Medical Loss Ratio (Actuarial, IBNR-adjusted)",
        plain_english:
          "Actuarial MLR with incurred-but-not-reported (IBNR) adjustment applied. Uses completion factors from the prior 8 quarters to project final claims. Not the ACA filing number — the internal actuarial estimate.",
        department_variation: "actuarial",
        source: "Actuarial Standards of Practice · internal model v7",
      },
      universe: {
        concept_id: "cohort.ma_florida.actuarial",
        canonical_name: "Florida MA (actuarial cohort)",
        plain_english:
          "Members enrolled in MA contract H1234 with Florida service area. Contract-domicile based (not residential).",
        department_variation: "actuarial",
        source: "Actuarial cohort definitions",
      },
    },
    dag: [
      { action: "parse_intent", label: "Understand the question", description: "Extracted: MLR, Florida MA, Q1. Note: 'ACA-compliant' in query but actuary role overrides to actuarial methodology.", duration_ms: 52 },
      { action: "find_concept", label: "Look up 'medical loss ratio'", description: "3 definitions found. Actuary role → actuarial (IBNR-adjusted), not ACA regulatory.", duration_ms: 115 },
      { action: "resolve_cohort", label: "Resolve 'Florida MA'", description: "Actuarial uses contract-domicile (H1234 service area), not residential address. Different from med-econ.", duration_ms: 68 },
      { action: "check_completion", label: "Apply IBNR completion factors", description: "Q1 2026: 73% paid → actuarial completion factor projects 91.2% ultimate MLR (up from 87.3% paid-to-date).", duration_ms: 55 },
      { action: "check_policy", label: "Authorize", description: "Actuary has full access to actuarial projections.", duration_ms: 24 },
      { action: "score_confidence", label: "Score the answer", description: "Moderate — IBNR model has ±1.5 point confidence interval at this completion level.", duration_ms: 22 },
    ],
    warnings: [
      { id: "w1", severity: "critical", headline: "Paid-to-date vs IBNR-adjusted: 87.3% vs 91.2%", detail: "The raw paid number (87.3%) will drift up to an estimated 91.2% as remaining claims come in over the next 90 days. Dashboards that show the raw number without the IBNR adjustment are misleading — the CFO saw 87.3% last week and thought we were trending favorably. We're not.", author: "N. Orlov, Chief Actuary", captured_at: "2026-04-02" },
      { id: "w2", severity: "warn", headline: "Cohort differs from Med-Econ's definition", detail: "Med-econ uses residential address. Actuarial uses contract service area. The member counts differ by ~4,200 (snowbirds with FL residence but enrolled via NJ employer group).", author: "actuarial-data-team" },
    ],
    precedents: [],
    confidence: { definition: 0.96, data_quality: 0.91, temporal_validity: 0.58, authorization: 1.0, completeness: 0.73, overall: 0.80 },
    access_granted: true, filtered_concepts: [], policies: ["actuarial.mlr.read", "ibnr.projections.read"],
  },

  // ────────────────────────────────────────────────────────────────────
  // ATLAS · MLR FLORIDA MA · CARLOS (Compliance)
  // ────────────────────────────────────────────────────────────────────
  "atlas:mlr-florida-ma:carlos": {
    headline:
      "ACA-compliant MLR, FL MA · regulatory filing basis · 89.1% (3-year rolling) · NOT FINAL",
    resolved_concepts: {
      metric: {
        concept_id: "metric.mlr.aca",
        canonical_name: "Medical Loss Ratio (ACA §2718)",
        plain_english:
          "Same ACA regulatory definition as Med-Econ. Compliance officer gets the identical number but with enhanced audit trail and filing-readiness warnings.",
        source: "ACA §2718, 45 CFR 158",
      },
    },
    dag: [
      { action: "parse_intent", label: "Understand the question", description: "ACA-compliant → regulatory definition. Compliance role adds audit trail requirements.", duration_ms: 48 },
      { action: "find_concept", label: "Look up 'medical loss ratio'", description: "3 definitions. Compliance role + 'ACA-compliant' → regulatory (same as med-econ).", duration_ms: 95 },
      { action: "check_completion", label: "Claims completion check", description: "Q1 claims 73% complete. Filing not recommended until 90% threshold.", duration_ms: 38 },
      { action: "check_policy", label: "Authorize + audit trail", description: "Compliance access granted. Full audit trail logged for potential regulatory inquiry.", duration_ms: 42 },
      { action: "score_confidence", label: "Score the answer", description: "Low temporal validity — below filing-grade threshold.", duration_ms: 20 },
    ],
    warnings: [
      { id: "w1", severity: "critical", headline: "NOT FILING-GRADE — do not submit to CMS", detail: "Claims completion is 73%. Our filing threshold is 90%. This number will change materially. If CMS or a state regulator asks for Q1 MLR, respond with 'preliminary, subject to claims completion' and cite the completion percentage.", author: "C. Mendez, Compliance", captured_at: "2026-04-05" },
      { id: "w2", severity: "critical", headline: "Rebate liability is provisionally $2.3M", detail: "If the 3-year rolling MLR lands above 85% (currently projected 89.1%), no rebate is owed. But if claims development pushes it below 85%, the rebate liability materializes. The actuarial team is watching.", author: "regulatory-affairs" },
    ],
    precedents: [],
    confidence: { definition: 0.99, data_quality: 0.91, temporal_validity: 0.52, authorization: 1.0, completeness: 0.73, overall: 0.78 },
    access_granted: true, filtered_concepts: [], policies: ["compliance.mlr.read", "audit.trail.required"],
  },

  // ────────────────────────────────────────────────────────────────────
  // NIMBUS · MRR · JORDAN (CFO)
  // ────────────────────────────────────────────────────────────────────
  "nimbus:mrr:jordan": {
    headline:
      "MRR, contracted basis (excl. trials > 14d) · CFO canonical · April 2026",
    resolved_concepts: {
      metric: {
        concept_id: "metric.mrr.contracted",
        canonical_name: "Contracted MRR (ex-trial)",
        plain_english:
          "Active paid contracts as of period end. Excludes trials over 14 days. CFO-approved definition per Jordan, 2025-09-01.",
        department_variation: "finance",
        source: "CFO canonical · approved 2025-09-01",
      },
    },
    dag: [
      {
        action: "parse_intent",
        label: "Understand the question",
        description: "Metric: MRR. Time: current month.",
        duration_ms: 32,
      },
      {
        action: "find_concept",
        label: "Look up 'MRR'",
        description:
          "6 definitions found: contracted, billed, collected, GAAP÷12, ARR÷12, committed. Jordan's role (CFO) → contracted (ex-trial) per explicit approval.",
        duration_ms: 128,
      },
      {
        action: "apply_exclusions",
        label: "Apply trial exclusion rule",
        description: "Excluding 47 accounts in trial > 14 days ($312K MRR).",
        duration_ms: 41,
      },
      {
        action: "lookup_tribal",
        label: "Scan tribal knowledge",
        description:
          "1 critical finding: $400K annual prepay in March hits all six MRR variants differently.",
        duration_ms: 22,
      },
      {
        action: "score_confidence",
        label: "Score the answer",
        description: "High confidence on the CFO-canonical variant.",
        duration_ms: 19,
      },
    ],
    warnings: [
      {
        id: "w1",
        severity: "critical",
        headline: "The board deck uses a different MRR than this one",
        detail:
          "The CFO canonical (what you're seeing) is 'contracted ex-trial'. The board deck shows 'committed MRR' which includes signed-but-not-started contracts. The VC update uses ARR÷12. All three diverge by ~$1.2M this month because of a $400K annual prepay signed in March that hasn't started billing yet. Make sure the number in your next board email matches the deck.",
        author: "B. Fischer, RevOps",
        captured_at: "2026-02-08",
      },
    ],
    precedents: [
      {
        resolution_id: "res_mrr_001",
        query: "what's our mrr this month",
        similarity: 0.99,
        feedback: "accepted",
        user: "jordan@nimbus",
      },
    ],
    confidence: {
      definition: 1.0,
      data_quality: 0.98,
      temporal_validity: 0.97,
      authorization: 1.0,
      completeness: 0.99,
      overall: 0.98,
    },
    access_granted: true,
    filtered_concepts: [],
    policies: ["finance.mrr.read", "cfo.canonical"],
  },
  // ────────────────────────────────────────────────────────────────────
  // NIMBUS · MRR · MAYA (Product)
  // ────────────────────────────────────────────────────────────────────
  "nimbus:mrr:maya": {
    headline:
      "MRR, billed basis (incl. usage overages) · product view · April 2026",
    resolved_concepts: {
      metric: {
        concept_id: "metric.mrr.billed",
        canonical_name: "Billed MRR",
        plain_english:
          "Sum of all invoiced charges in the month, including subscription base + usage overages + add-ons. Product uses this to track real revenue from active usage.",
        department_variation: "product",
        source: "Product analytics · billing pipeline",
      },
    },
    dag: [
      { action: "parse_intent", label: "Understand the question", description: "Metric: MRR. Time: current month.", duration_ms: 30 },
      { action: "find_concept", label: "Look up 'MRR'", description: "6 definitions. Product role → billed (includes usage overages, which contracted MRR excludes).", duration_ms: 118 },
      { action: "lookup_tribal", label: "Scan tribal knowledge", description: "$400K annual prepay: shows as $33.3K/mo in billed, $400K in month-of for collected.", duration_ms: 24 },
      { action: "score_confidence", label: "Score the answer", description: "High confidence — billed data is from the billing system of record.", duration_ms: 17 },
    ],
    warnings: [
      { id: "w1", severity: "warn", headline: "This is ~$800K higher than the CFO's number", detail: "Billed MRR includes usage overages ($620K this month) and trial-to-paid conversions in progress ($180K). The CFO's contracted MRR deliberately excludes both. Neither is wrong — they answer different questions.", author: "B. Fischer, RevOps" },
    ],
    precedents: [],
    confidence: { definition: 0.97, data_quality: 0.96, temporal_validity: 0.98, authorization: 1.0, completeness: 0.97, overall: 0.97 },
    access_granted: true, filtered_concepts: [], policies: ["product.mrr.read"],
  },

  // ────────────────────────────────────────────────────────────────────
  // NIMBUS · MRR · BEN (RevOps)
  // ────────────────────────────────────────────────────────────────────
  "nimbus:mrr:ben": {
    headline:
      "MRR, committed basis (incl. signed not started) · RevOps view · April 2026",
    resolved_concepts: {
      metric: {
        concept_id: "metric.mrr.committed",
        canonical_name: "Committed MRR",
        plain_english:
          "All signed contracts — active, not-yet-started, and pending provisioning. This is the number in the board deck and VC updates.",
        department_variation: "revops",
        source: "RevOps pipeline · CRM + billing",
      },
    },
    dag: [
      { action: "parse_intent", label: "Understand the question", description: "Metric: MRR. Time: current month.", duration_ms: 28 },
      { action: "find_concept", label: "Look up 'MRR'", description: "6 definitions. RevOps role → committed (includes signed-not-started). This is the board deck number.", duration_ms: 108 },
      { action: "lookup_tribal", label: "Scan tribal knowledge", description: "$400K annual prepay: shows as $400K in committed MRR for the signing month.", duration_ms: 21 },
      { action: "score_confidence", label: "Score the answer", description: "High confidence on committed; pipeline data is CRM-sourced.", duration_ms: 16 },
    ],
    warnings: [
      { id: "w1", severity: "critical", headline: "This is the board deck number — handle with care", detail: "Committed MRR ($14.8M) is ~$1.2M higher than the CFO's contracted MRR ($13.6M). The gap is 3 signed contracts that haven't started billing yet. If you email this number to the CFO without labeling it 'committed', you will create confusion. The VC update uses this variant.", author: "B. Fischer, RevOps", captured_at: "2026-03-15" },
    ],
    precedents: [{ resolution_id: "res_mrr_002", query: "committed mrr for board deck", similarity: 0.95, feedback: "accepted", user: "ben@nimbus" }],
    confidence: { definition: 0.99, data_quality: 0.95, temporal_validity: 0.97, authorization: 1.0, completeness: 0.98, overall: 0.97 },
    access_granted: true, filtered_concepts: [], policies: ["revops.mrr.read", "board.metrics"],
  },

  // ────────────────────────────────────────────────────────────────────
  // NIMBUS · DAU · JORDAN (CFO)
  // ────────────────────────────────────────────────────────────────────
  "nimbus:dau:jordan": {
    headline:
      "Active users last week · paid seats with login · 31,204",
    resolved_concepts: {
      metric: {
        concept_id: "metric.dau.paid_seats",
        canonical_name: "Active Users (Paid Seats)",
        plain_english:
          "Count of paid seats where the user logged in at least once in the trailing 7 days. Finance uses this for per-seat revenue calculations.",
        department_variation: "finance",
        source: "Finance analytics · seat utilization report",
      },
    },
    dag: [
      { action: "parse_intent", label: "Understand the question", description: "Metric: active users. Time: last week.", duration_ms: 30 },
      { action: "find_concept", label: "Look up 'active users'", description: "3 definitions: authenticated session (product), qualifying event (growth), paid seats with login (finance). CFO → paid seats.", duration_ms: 94 },
      { action: "check_policy", label: "Authorize", description: "CFO has full access to usage metrics.", duration_ms: 22 },
      { action: "score_confidence", label: "Score the answer", description: "High confidence — seat data is from the billing system.", duration_ms: 16 },
    ],
    warnings: [
      { id: "w1", severity: "warn", headline: "Product reports 48,102 — a 54% difference", detail: "Product counts authenticated sessions (includes free tier, trials, and multi-device). Finance counts paid seats with login. Both are correct for their purpose. If this is for the investor deck, use paid seats. If this is for product-market fit, use product's number.", author: "M. Chen, Product Analytics" },
    ],
    precedents: [],
    confidence: { definition: 0.96, data_quality: 0.97, temporal_validity: 0.99, authorization: 1.0, completeness: 0.98, overall: 0.97 },
    access_granted: true, filtered_concepts: [], policies: ["finance.usage.read"],
  },

  // ────────────────────────────────────────────────────────────────────
  // NIMBUS · DAU · MAYA (Product)
  // ────────────────────────────────────────────────────────────────────
  "nimbus:dau:maya": {
    headline:
      "Active users last week · authenticated sessions · 48,102",
    resolved_concepts: {
      metric: {
        concept_id: "metric.dau.sessions",
        canonical_name: "Active Users (Authenticated Sessions)",
        plain_english:
          "Unique users with at least one authenticated session in the trailing 7 days. Includes free tier, trials, and paid. Product's primary engagement metric.",
        department_variation: "product",
        source: "Product analytics · session tracking",
      },
    },
    dag: [
      { action: "parse_intent", label: "Understand the question", description: "Metric: active users. Time: last week.", duration_ms: 28 },
      { action: "find_concept", label: "Look up 'active users'", description: "3 definitions. Product role → authenticated sessions (broadest definition).", duration_ms: 88 },
      { action: "lookup_tribal", label: "Scan tribal knowledge", description: "iOS 17 dropped reported sessions ~8% in Sept 2023. Current numbers are post-adjustment.", duration_ms: 25 },
      { action: "check_policy", label: "Authorize", description: "Product has access to session data.", duration_ms: 20 },
      { action: "score_confidence", label: "Score the answer", description: "High confidence — session tracking is mature.", duration_ms: 15 },
    ],
    warnings: [
      { id: "w1", severity: "info", headline: "iOS 17 session tracking impact (Sept 2023)", detail: "Apple's iOS 17 privacy changes reduced reported sessions by ~8% starting Sept 2023. Our tracking has been adjusted since Oct 2023, but historical comparisons pre/post September 2023 need the normalization factor applied.", author: "mobile-eng" },
      { id: "w2", severity: "warn", headline: "Finance reports 31,204 — a 35% difference", detail: "Finance counts paid seats with login only. Your number includes free tier (12,400) and active trials (4,498). For product-market fit analysis, use this number. For revenue modeling, use Finance's.", author: "Product Analytics" },
    ],
    precedents: [{ resolution_id: "res_dau_001", query: "weekly active users", similarity: 0.97, feedback: "accepted", user: "maya@nimbus" }],
    confidence: { definition: 0.94, data_quality: 0.95, temporal_validity: 0.99, authorization: 1.0, completeness: 0.96, overall: 0.95 },
    access_granted: true, filtered_concepts: [], policies: ["product.usage.read"],
  },
};

// ─── Public API ──────────────────────────────────────────────────────────

export type ResolveArgs = {
  worldId: string;
  scenarioId: string;
  persona: Persona;
  question: string;
};

/**
 * Returns a ResolveResponse for the given context. Falls back to a
 * synthetic "we don't have a recipe for this exact combo, but here's
 * what ECP would do" response so the UI never breaks on a cold click.
 */
export async function mockResolve(args: ResolveArgs): Promise<ResolveResponse> {
  // Fake realistic latency
  await new Promise((r) => setTimeout(r, 380 + Math.random() * 260));

  const key = `${args.worldId}:${args.scenarioId}:${args.persona.id}`;
  const recipe = RECIPES[key] || synthesize(args);

  const dag = withIds(recipe.dag);
  const latency = dag.reduce((a, s) => a + s.duration_ms, 0);

  return {
    resolution_id: rid(),
    status: "resolved",
    resolved_concepts: recipe.resolved_concepts,
    execution_plan: [
      {
        step: 1,
        action: "semantic_layer_query",
        target: "cube.metric_aggregated",
        parameters: { measures: Object.keys(recipe.resolved_concepts) },
      },
    ],
    confidence: recipe.confidence,
    warnings: recipe.warnings,
    precedents_used: recipe.precedents,
    resolution_dag: dag,
    policies_evaluated: recipe.policies,
    access_granted: recipe.access_granted,
    filtered_concepts: recipe.filtered_concepts,
    headline: recipe.headline,
    latency_ms: latency,
  };
}

/**
 * Fallback synthesizer for (world, scenario, persona) combos we haven't
 * hand-authored. Keeps the UI honest — shows that ECP *would* resolve
 * this, without pretending we have a canned answer.
 */
function synthesize(args: ResolveArgs): ResolutionRecipe {
  return {
    headline: `Resolved "${args.question}"`,
    resolved_concepts: {
      query: {
        concept_id: "synthetic.query",
        canonical_name: args.question,
        plain_english: `Interpreted as a ${args.persona.department} view of this question.`,
        department_variation: args.persona.department,
        source: "synthetic resolution",
      },
    },
    dag: [
      {
        action: "parse_intent",
        label: "Understand the question",
        description: `Parsed question for ${args.persona.role}.`,
        duration_ms: 45,
      },
      {
        action: "find_concept",
        label: "Look up terms",
        description:
          "Searched the context registry. In a real deployment this would hit the knowledge graph and return every matching concept.",
        duration_ms: 88,
      },
      {
        action: "check_policy",
        label: "Authorize",
        description: `Policy evaluated for role ${args.persona.role}.`,
        duration_ms: 31,
      },
      {
        action: "score_confidence",
        label: "Score the answer",
        description: "Confidence computed from data contract SLAs.",
        duration_ms: 22,
      },
    ],
    warnings: [
      {
        id: "w-stub",
        severity: "info",
        headline: "This is a synthesized example",
        detail:
          "We don't have a hand-authored recipe for this exact (persona × scenario) combo yet. In a real ECP deployment the resolution would be driven by the context registry. Pick one of the highlighted starter scenarios on the left for a full walkthrough.",
      },
    ],
    precedents: [],
    confidence: {
      definition: 0.8,
      data_quality: 0.85,
      temporal_validity: 0.9,
      authorization: 1.0,
      completeness: 0.8,
      overall: 0.84,
    },
    access_granted: true,
    filtered_concepts: [],
    policies: ["default.read"],
  };
}

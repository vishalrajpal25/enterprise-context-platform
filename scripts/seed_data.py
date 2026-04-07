"""
Seed data for the financial data company demo scenario.
Loads glossary terms, tribal knowledge, data contracts, metrics into PostgreSQL and Neo4j.
"""
import asyncio
import json
import asyncpg
from neo4j import AsyncGraphDatabase
from src.config import settings

POSTGRES_DSN = settings.postgres_dsn
NEO4J_URI = settings.neo4j_uri
NEO4J_AUTH = (settings.neo4j_user, settings.neo4j_password)


# ============================================================
# PostgreSQL Assets
# ============================================================

ASSETS = [
    # --- GLOSSARY TERMS ---
    {
        "id": "gl_revenue",
        "type": "glossary_term",
        "content": {
            "canonical_name": "revenue",
            "display_name": "Revenue",
            "definition": "Income from normal business operations",
            "variations": [
                {
                    "context": "finance",
                    "name": "net_revenue",
                    "definition": "Recognized revenue per ASC 606 minus refunds and adjustments",
                    "formula": "SUM(amount) WHERE type='recognized' AND refunded=false"
                },
                {
                    "context": "sales",
                    "name": "gross_revenue",
                    "definition": "Total invoiced revenue before adjustments",
                    "formula": "SUM(amount) WHERE type IN ('recognized','invoiced')"
                },
                {
                    "context": "operations",
                    "name": "run_rate_revenue",
                    "definition": "Annualized current quarter revenue",
                    "formula": "SUM(amount) * 4 for current quarter"
                }
            ],
            "synonyms": ["income", "sales", "top line", "bookings"],
            "acronyms": ["ARR", "MRR", "TCV"],
            "owner": "finance_operations",
            "last_reviewed": "2026-01-15"
        }
    },
    {
        "id": "gl_apac",
        "type": "glossary_term",
        "content": {
            "canonical_name": "apac",
            "display_name": "APAC",
            "definition": "Asia-Pacific region",
            "variations": [
                {
                    "context": "finance",
                    "name": "apac_finance",
                    "definition": "APAC including ANZ (Australia, New Zealand)",
                    "countries": ["JP", "KR", "SG", "HK", "TW", "AU", "NZ", "IN", "CN"]
                },
                {
                    "context": "sales",
                    "name": "apac_sales",
                    "definition": "APAC excluding ANZ (ANZ reports under separate sales region)",
                    "countries": ["JP", "KR", "SG", "HK", "TW", "IN", "CN"]
                }
            ],
            "synonyms": ["asia pacific", "asia-pacific", "asia pac"],
            "owner": "regional_ops"
        }
    },
    {
        "id": "gl_emea",
        "type": "glossary_term",
        "content": {
            "canonical_name": "emea",
            "display_name": "EMEA",
            "definition": "Europe, Middle East and Africa region",
            "variations": [
                {
                    "context": "finance",
                    "name": "emea_finance",
                    "countries": ["GB", "DE", "FR", "IT", "ES", "NL", "CH", "SE", "NO"]
                },
                {
                    "context": "sales",
                    "name": "emea_sales",
                    "countries": ["GB", "DE", "FR", "IT", "ES", "NL", "CH", "SE", "NO", "AE"]
                }
            ],
            "synonyms": ["europe"],
            "owner": "regional_ops"
        }
    },
    {
        "id": "gl_churn",
        "type": "glossary_term",
        "content": {
            "canonical_name": "churn_rate",
            "display_name": "Customer Churn Rate",
            "definition": "Percentage of customers who cancel in a given period",
            "variations": [
                {
                    "context": "finance",
                    "name": "revenue_churn",
                    "definition": "Revenue lost from churned customers / total revenue",
                    "formula": "SUM(churned_revenue) / SUM(total_revenue)"
                },
                {
                    "context": "product",
                    "name": "logo_churn",
                    "definition": "Count of customers who cancelled / total customers",
                    "formula": "COUNT(churned_customers) / COUNT(total_customers)"
                }
            ],
            "synonyms": ["attrition", "customer loss"],
            "owner": "customer_success"
        }
    },
    # --- METRIC DEFINITIONS ---
    {
        "id": "mt_net_revenue",
        "type": "metric_definition",
        "content": {
            "name": "net_revenue",
            "semantic_layer_ref": "cube.finance.Revenue.netRevenue",
            "measure": "Revenue.netRevenue",
            "definition": "Recognized revenue per ASC 606 minus refunds",
            "certification_tier": 1,
            "owner": "sarah.johnson@company.com",
            "source_table": "analytics.finance.fact_revenue_daily"
        }
    },
    {
        "id": "mt_gross_revenue",
        "type": "metric_definition",
        "content": {
            "name": "gross_revenue",
            "semantic_layer_ref": "cube.finance.Revenue.grossRevenue",
            "measure": "Revenue.grossRevenue",
            "definition": "Total invoiced revenue before adjustments",
            "certification_tier": 2,
            "owner": "sales_ops@company.com",
            "source_table": "analytics.finance.fact_revenue_daily"
        }
    },
    {
        "id": "mt_budget_revenue",
        "type": "metric_definition",
        "content": {
            "name": "budget_net_revenue",
            "semantic_layer_ref": "cube.planning.Budget.netRevenueBudget",
            "measure": "Budget.netRevenueBudget",
            "definition": "Budgeted net revenue by region and period",
            "certification_tier": 2,
            "owner": "fp_and_a@company.com",
            "source_table": "analytics.planning.fact_budget"
        }
    },
    {
        "id": "mt_headcount",
        "type": "metric_definition",
        "content": {
            "name": "headcount",
            "canonical_name": "headcount",
            "semantic_layer_ref": "cube.people.Headcount.count",
            "measure": "Headcount.count",
            "definition": "Active employee count as of period end",
            "certification_tier": 1,
            "owner": "people_ops@company.com",
            "source_table": "analytics.people.fact_headcount_daily"
        }
    },
    {
        "id": "mt_cost",
        "type": "metric_definition",
        "content": {
            "name": "cost",
            "canonical_name": "operating_cost",
            "semantic_layer_ref": "cube.finance.Cost.operatingCost",
            "measure": "Cost.operatingCost",
            "definition": "Total operating cost (COGS + OpEx) recognized in period",
            "certification_tier": 1,
            "owner": "finance_operations@company.com",
            "source_table": "analytics.finance.fact_cost_daily"
        }
    },
    {
        "id": "mt_retention",
        "type": "metric_definition",
        "content": {
            "name": "retention",
            "canonical_name": "customer_retention_rate",
            "semantic_layer_ref": "cube.customer.Retention.rate",
            "measure": "Retention.rate",
            "definition": "1 - logo churn rate over the trailing 12 months",
            "certification_tier": 2,
            "owner": "customer_success@company.com",
            "source_table": "analytics.customer.fact_retention_monthly"
        }
    },
    {
        "id": "gl_americas",
        "type": "glossary_term",
        "content": {
            "canonical_name": "americas",
            "display_name": "Americas",
            "definition": "North, Central and South America region",
            "variations": [
                {
                    "context": "finance",
                    "name": "americas_finance",
                    "countries": ["US", "CA", "MX", "BR", "AR", "CL", "CO"]
                }
            ],
            "synonyms": ["amer", "north america + latam"],
            "owner": "regional_ops"
        }
    },
    # --- TRIBAL KNOWLEDGE ---
    {
        "id": "tk_apac_q4_2019",
        "type": "tribal_knowledge",
        "content": {
            "type": "known_issue",
            "scope": {
                "tables": ["finance.fact_revenue_daily"],
                "dimensions": {"region": ["APAC"], "fiscal_period": ["2019-Q4"]}
            },
            "description": "Q4 2019 APAC data is incomplete due to Oracle-to-Snowflake migration",
            "reason": "Migration script failed for 2 weeks of data in November 2019",
            "impact": "Revenue underreported by approximately 15% for APAC in Q4 FY2019",
            "workaround": "Use Q4 2018 growth-adjusted estimate for trend analysis",
            "discovered_by": "maria.chen@company.com",
            "discovered_date": "2020-02-14",
            "verified": True,
            "active": True,
            "severity": "high"
        }
    },
    {
        "id": "tk_apac_costcenter_2021",
        "type": "tribal_knowledge",
        "content": {
            "type": "known_change",
            "scope": {
                "dimensions": {"region": ["APAC"]}
            },
            "description": "APAC cost center definitions changed in January 2021",
            "reason": "India operations restructured from shared services to direct P&L",
            "impact": "APAC metrics before and after Jan 2021 are not directly comparable",
            "workaround": "Apply normalization factor of 1.08x for pre-2021 APAC comparisons",
            "discovered_by": "raj.patel@company.com",
            "verified": True,
            "active": True,
            "severity": "medium"
        }
    },
    {
        "id": "tk_fx_rates",
        "type": "tribal_knowledge",
        "content": {
            "type": "gotcha",
            "scope": {"tables": ["finance.fact_revenue_daily"]},
            "description": "Revenue table stores amounts in local currency. Always join with fx_rates for USD reporting.",
            "impact": "Reports in wrong currency if fx join is missed",
            "workaround": "Semantic layer handles conversion automatically via canonical joins",
            "verified": True,
            "active": True,
            "severity": "high"
        }
    },
    # --- DATA CONTRACTS ---
    {
        "id": "dc_fact_revenue",
        "type": "data_contract",
        "content": {
            "name": "fact_revenue_daily",
            "owner": {"team": "finance_data_engineering", "contact": "fin-data@company.com"},
            "source": {
                "platform": "snowflake",
                "database": "analytics",
                "schema": "finance",
                "table": "fact_revenue_daily"
            },
            "sla": {
                "freshness_hours": 6,
                "availability_pct": 99.5,
                "completeness_pct": 99.9
            },
            "quality_rules": [
                {"rule": "transaction_id IS NOT NULL", "severity": "critical"},
                {"rule": "amount >= 0", "severity": "warning"},
                {"rule": "region_code IN (SELECT code FROM dim_region)", "severity": "warning"}
            ]
        }
    },
    {
        "id": "dc_fact_headcount",
        "type": "data_contract",
        "content": {
            "name": "fact_headcount_daily",
            "owner": {"team": "people_data_engineering", "contact": "people-data@company.com"},
            "source": {
                "platform": "snowflake",
                "database": "analytics",
                "schema": "people",
                "table": "fact_headcount_daily"
            },
            "sla": {
                "freshness_hours": 24,
                "availability_pct": 99.0,
                "completeness_pct": 99.5
            }
        }
    },
    {
        "id": "dc_fact_cost",
        "type": "data_contract",
        "content": {
            "name": "fact_cost_daily",
            "owner": {"team": "finance_data_engineering", "contact": "fin-data@company.com"},
            "source": {
                "platform": "snowflake",
                "database": "analytics",
                "schema": "finance",
                "table": "fact_cost_daily"
            },
            "sla": {
                "freshness_hours": 12,
                "availability_pct": 99.0,
                "completeness_pct": 99.0
            }
        }
    },
    {
        "id": "dc_fact_retention",
        "type": "data_contract",
        "content": {
            "name": "fact_retention_monthly",
            "owner": {"team": "customer_success_eng", "contact": "cs-data@company.com"},
            "source": {
                "platform": "snowflake",
                "database": "analytics",
                "schema": "customer",
                "table": "fact_retention_monthly"
            },
            "sla": {
                "freshness_hours": 48,
                "availability_pct": 98.0,
                "completeness_pct": 97.0
            }
        }
    },
    # --- CALENDAR CONFIG ---
    # NOTE: this asset deliberately contains NO frozen "current quarter" or
    # "last_quarter_date_range" fields. The fiscal resolver
    # (src/context/fiscal.py) computes them from datetime.now() at request
    # time, so the demo is always live-correct relative to wall clock.
    {
        "id": "cfg_calendar",
        "type": "calendar_config",
        "content": {
            "fiscal_year_start_month": 4,
            "fiscal_year_label": "FY{end_year}",
            "dimension": "Revenue.date",
            "quarters": {
                "Q1": {"months": [4, 5, 6]},
                "Q2": {"months": [7, 8, 9]},
                "Q3": {"months": [10, 11, 12]},
                "Q4": {"months": [1, 2, 3]}
            }
        }
    },
]



async def seed_postgres():
    conn = await asyncpg.connect(POSTGRES_DSN)
    try:
        # Clear existing assets
        await conn.execute("DELETE FROM resolution_sessions")
        await conn.execute("DELETE FROM contract_versions")
        await conn.execute("DELETE FROM assets")

        for asset in ASSETS:
            await conn.execute(
                """INSERT INTO assets (id, type, content, metadata, created_by)
                   VALUES ($1, $2, $3, '{}', 'seed_script')
                   ON CONFLICT (id) DO UPDATE SET content = $3, updated_at = NOW()""",
                asset["id"], asset["type"], json.dumps(asset["content"]),
            )

        count = await conn.fetchval("SELECT COUNT(*) FROM assets")
        print(f"PostgreSQL: {count} assets seeded.")
    finally:
        await conn.close()


async def seed_neo4j():
    driver = AsyncGraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)
    try:
        async with driver.session() as session:
            # Clear
            await session.run("MATCH (n) DETACH DELETE n")

            # Create all nodes and relationships in one transaction
            await session.run("""
CREATE (nr:Metric {id: 'net_revenue', name: 'Net Revenue', description: 'Recognized revenue per ASC 606 minus refunds', semantic_layer_ref: 'cube.finance.Revenue.netRevenue', asset_registry_id: 'mt_net_revenue', certification_tier: 1, owner: 'sarah.johnson@company.com'})
CREATE (gr:Metric {id: 'gross_revenue', name: 'Gross Revenue', description: 'Total invoiced revenue before adjustments', semantic_layer_ref: 'cube.finance.Revenue.grossRevenue', asset_registry_id: 'mt_gross_revenue', certification_tier: 2, owner: 'sales_ops@company.com'})
CREATE (br:Metric {id: 'budget_net_revenue', name: 'Budget Net Revenue', description: 'Budgeted net revenue by region and period', semantic_layer_ref: 'cube.planning.Budget.netRevenueBudget', asset_registry_id: 'mt_budget_revenue', certification_tier: 2, owner: 'fp_and_a@company.com'})
CREATE (hc:Metric {id: 'headcount', name: 'Headcount', description: 'Active employee count as of period end', semantic_layer_ref: 'cube.people.Headcount.count', asset_registry_id: 'mt_headcount', certification_tier: 1, owner: 'people_ops@company.com'})
CREATE (cost:Metric {id: 'cost', name: 'Operating Cost', description: 'Total operating cost (COGS + OpEx)', semantic_layer_ref: 'cube.finance.Cost.operatingCost', asset_registry_id: 'mt_cost', certification_tier: 1, owner: 'finance_operations@company.com'})
CREATE (ret:Metric {id: 'retention', name: 'Customer Retention Rate', description: '1 - logo churn rate over trailing 12 months', semantic_layer_ref: 'cube.customer.Retention.rate', asset_registry_id: 'mt_retention', certification_tier: 2, owner: 'customer_success@company.com'})
CREATE (chr:Metric {id: 'churn_rate', name: 'Customer Churn Rate', description: 'Customer churn rate', semantic_layer_ref: 'cube.customer.Churn.rate', asset_registry_id: 'gl_churn', certification_tier: 2, owner: 'customer_success@company.com'})
CREATE (rev:GlossaryTerm {id: 'revenue', canonical_name: 'revenue', definition: 'Income from normal business operations', asset_registry_id: 'gl_revenue'})
CREATE (rev_fin:GlossaryTerm {id: 'revenue_finance', canonical_name: 'net_revenue', definition: 'Recognized revenue per ASC 606 minus refunds', context: 'finance'})
CREATE (rev_sales:GlossaryTerm {id: 'revenue_sales', canonical_name: 'gross_revenue', definition: 'Total invoiced revenue before adjustments', context: 'sales'})
CREATE (apac:Entity {id: 'region_apac', name: 'APAC', domain: 'geography', description: 'Asia-Pacific region'})
CREATE (apac_fin:Entity {id: 'region_apac_finance', name: 'APAC (Finance)', domain: 'geography', description: 'APAC including ANZ', values: ['JP','KR','SG','HK','TW','AU','NZ','IN','CN']})
CREATE (apac_sales:Entity {id: 'region_apac_sales', name: 'APAC (Sales)', domain: 'geography', description: 'APAC excluding ANZ', values: ['JP','KR','SG','HK','TW','IN','CN']})
CREATE (emea:Entity {id: 'region_emea', name: 'EMEA', domain: 'geography', description: 'Europe, Middle East and Africa'})
CREATE (americas:Entity {id: 'region_americas', name: 'Americas', domain: 'geography', description: 'North, Central and South America', values: ['US','CA','MX','BR','AR','CL','CO']})
CREATE (t_rev:Table {id: 'analytics.finance.fact_revenue_daily', schema_name: 'finance', name: 'fact_revenue_daily', platform: 'snowflake'})
CREATE (t_budget:Table {id: 'analytics.planning.fact_budget', schema_name: 'planning', name: 'fact_budget', platform: 'snowflake'})
CREATE (c_amount:Column {id: 'fact_revenue_daily.amount', table_id: 'analytics.finance.fact_revenue_daily', name: 'amount', data_type: 'DECIMAL(18,2)'})
CREATE (c_region:Column {id: 'fact_revenue_daily.region_code', table_id: 'analytics.finance.fact_revenue_daily', name: 'region_code', data_type: 'VARCHAR(10)'})
CREATE (tk1:TribalKnowledge {id: 'tk_apac_q4_2019', asset_registry_id: 'tk_apac_q4_2019', description: 'Q4 2019 APAC data incomplete due to Oracle-to-Snowflake migration', severity: 'high', active: true, impact: 'Revenue underreported by approximately 15%', workaround: 'Use Q4 2018 growth-adjusted estimate'})
CREATE (tk2:TribalKnowledge {id: 'tk_apac_costcenter_2021', asset_registry_id: 'tk_apac_costcenter_2021', description: 'APAC cost center definitions changed Jan 2021', severity: 'medium', active: true, impact: 'Pre/post 2021 APAC metrics not directly comparable', workaround: 'Apply 1.08x normalization for pre-2021'})
CREATE (tk3:TribalKnowledge {id: 'tk_fx_rates', asset_registry_id: 'tk_fx_rates', description: 'Revenue in local currency - must join fx_rates for USD', severity: 'high', active: true, impact: 'Reports in wrong currency if fx join missed', workaround: 'Semantic layer handles conversion automatically'})
CREATE (nr)-[:DEFINED_BY]->(rev)
CREATE (gr)-[:DEFINED_BY]->(rev)
CREATE (rev)-[:HAS_VARIATION {context: 'finance'}]->(nr)
CREATE (rev)-[:HAS_VARIATION {context: 'sales'}]->(gr)
CREATE (rev_fin)-[:DESCRIBES]->(nr)
CREATE (rev_sales)-[:DESCRIBES]->(gr)
CREATE (apac)-[:HAS_VARIATION {context: 'finance'}]->(apac_fin)
CREATE (apac)-[:HAS_VARIATION {context: 'sales'}]->(apac_sales)
CREATE (nr)-[:COMPUTED_FROM {logic: 'SUM(amount) WHERE type=recognized AND refunded=false'}]->(c_amount)
CREATE (gr)-[:COMPUTED_FROM {logic: 'SUM(amount) WHERE type IN (recognized, invoiced)'}]->(c_amount)
CREATE (nr)-[:USES_DIMENSION]->(c_region)
CREATE (c_amount)-[:BELONGS_TO]->(t_rev)
CREATE (c_region)-[:BELONGS_TO]->(t_rev)
CREATE (tk1)-[:AFFECTS]->(nr)
CREATE (tk1)-[:AFFECTS]->(gr)
CREATE (tk2)-[:AFFECTS]->(nr)
CREATE (tk3)-[:AFFECTS]->(nr)
CREATE (tk3)-[:AFFECTS]->(gr)
CREATE (nr)-[:HAS_KNOWN_ISSUE]->(tk1)
CREATE (nr)-[:HAS_KNOWN_ISSUE]->(tk2)
CREATE (nr)-[:HAS_KNOWN_ISSUE]->(tk3)
CREATE (gr)-[:HAS_KNOWN_ISSUE]->(tk1)
CREATE (gr)-[:HAS_KNOWN_ISSUE]->(tk3)
            """)

            result = await session.run("MATCH (n) RETURN count(n) as count")
            record = await result.single()
            print(f"Neo4j: {record['count']} nodes created.")
    finally:
        await driver.close()


def _searchable_text(asset: dict) -> tuple[str, str]:
    """Return (display_name, searchable_blob) for embedding."""
    content = asset.get("content", {})
    name = (
        content.get("display_name")
        or content.get("canonical_name")
        or content.get("name")
        or asset["id"]
    )
    parts = [
        str(name),
        str(content.get("definition", "")),
        " ".join(content.get("synonyms", []) or []),
        " ".join(content.get("acronyms", []) or []),
    ]
    return str(name), " — ".join(p for p in parts if p)


async def seed_asset_vectors():
    """Populate asset_vectors with embeddings (or NULL if no provider key)."""
    from src.context.vector import VectorClient
    from src.context.embeddings import embeddings as embedding_service

    embedding_service.warn_if_unavailable_once()

    vc = VectorClient()
    await vc.connect()
    try:
        embeddable_types = {"glossary_term", "metric_definition", "tribal_knowledge"}
        rows = [a for a in ASSETS if a["type"] in embeddable_types]

        names_and_blobs = [_searchable_text(a) for a in rows]
        blobs = [b for _, b in names_and_blobs]

        if embedding_service.is_available():
            print(
                f"Embedding {len(blobs)} assets via "
                f"{embedding_service.provider}/{embedding_service.model} "
                f"(dim={embedding_service.dim})..."
            )
            vectors = await embedding_service.embed_batch(blobs)
        else:
            print(
                f"Embedding provider={embedding_service.provider} unavailable — "
                f"asset_vectors will be populated without embeddings (ILIKE fallback)."
            )
            vectors = [None for _ in blobs]

        for asset, (name, blob), vec in zip(rows, names_and_blobs, vectors):
            await vc.upsert_asset_vector(
                asset_id=asset["id"],
                asset_type=asset["type"],
                name=name,
                definition=blob,
                embedding=vec,
            )
        embedded = sum(1 for v in vectors if v is not None)
        print(f"asset_vectors: {len(rows)} rows ({embedded} with real embeddings).")
    finally:
        await vc.close()


async def main():
    print("Seeding PostgreSQL...")
    await seed_postgres()
    print("Seeding Neo4j...")
    await seed_neo4j()
    print("Seeding asset_vectors...")
    await seed_asset_vectors()
    print("Done. Demo data ready.")


if __name__ == "__main__":
    asyncio.run(main())

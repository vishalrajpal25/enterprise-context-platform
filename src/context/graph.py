"""Knowledge Graph client (Neo4j). Handles all graph queries for the resolution engine."""
from neo4j import AsyncGraphDatabase
from src.config import settings


class GraphClient:
    def __init__(self):
        self._driver = None

    async def connect(self):
        self._driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
            max_connection_pool_size=50,
        )

    async def close(self):
        if self._driver:
            await self._driver.close()

    async def ping(self) -> bool:
        if not self._driver:
            return False
        try:
            async with self._driver.session() as session:
                result = await session.run("RETURN 1 AS ok")
                record = await result.single()
                return bool(record and record["ok"] == 1)
        except Exception:
            return False

    async def find_concept(self, concept_type: str, raw_value: str, department: str) -> list[dict]:
        """Find matching concepts in the graph, scoring by name match quality.

        Resolution strategy:
          1. Find candidate nodes whose name/id contains the raw value.
          2. If a candidate has a HAS_VARIATION edge for the user's department,
             *return the variation child* instead of the parent — this is how
             "APAC" resolves to `region_apac_finance` for finance users and
             `region_apac_sales` for sales users.
          3. Score everything else by exact / prefix / substring match plus
             a certification-tier bonus. Real signal, no hardcoded 0.8.
        """
        query = """
        MATCH (n)
        WHERE (n:Metric OR n:GlossaryTerm OR n:Entity)
          AND (toLower(coalesce(n.name, '')) CONTAINS toLower($raw_value)
               OR toLower(coalesce(n.canonical_name, '')) CONTAINS toLower($raw_value)
               OR toLower(coalesce(n.id, '')) CONTAINS toLower($raw_value))
        OPTIONAL MATCH (n)-[:HAS_VARIATION {context: $department}]->(v)
        WITH n, v,
             toLower(coalesce(n.name, n.canonical_name, n.id, '')) AS lname,
             toLower($raw_value) AS lraw
        WITH n, v,
             CASE
               WHEN lname = lraw THEN 1.00
               WHEN lname STARTS WITH lraw THEN 0.92
               WHEN lname CONTAINS lraw THEN 0.82
               ELSE 0.60
             END AS base_score,
             CASE
               WHEN coalesce(n.certification_tier, 4) = 1 THEN 0.05
               WHEN coalesce(n.certification_tier, 4) = 2 THEN 0.02
               ELSE 0.0
             END AS cert_boost
        WITH n, v, base_score, cert_boost,
             CASE WHEN v IS NOT NULL THEN 0.15 ELSE 0.0 END AS dept_boost
        RETURN
          coalesce(v.id, n.id) AS id,
          coalesce(v.name, v.canonical_name, n.name, n.canonical_name, n.id) AS name,
          coalesce(v.definition, n.description, n.definition) AS definition,
          coalesce(v.certification_tier, n.certification_tier) AS certification_tier,
          toFloat(base_score) + toFloat(cert_boost) + toFloat(dept_boost) AS score
        ORDER BY score DESC
        LIMIT 5
        """
        async with self._driver.session() as session:
            result = await session.run(query, raw_value=raw_value, department=department)
            rows = [dict(record) async for record in result]
            for r in rows:
                if r.get("score") is not None and r["score"] > 1.0:
                    r["score"] = 1.0
            return rows

    async def get_concept_context(self, concept_id: str, department: str) -> dict:
        """Get full context for a concept: definition, variations, sources, known issues."""
        query = """
        MATCH (n {id: $concept_id})
        OPTIONAL MATCH (n)-[:DEFINED_BY]->(g:GlossaryTerm)
        OPTIONAL MATCH (g)-[:HAS_VARIATION]->(v)
        OPTIONAL MATCH (n)-[:COMPUTED_FROM]->(c:Column)-[:BELONGS_TO]->(t:Table)
          WHERE NOT EXISTS(c.valid_until)
        OPTIONAL MATCH (n)-[:HAS_KNOWN_ISSUE]->(tk:TribalKnowledge)
          WHERE tk.active = true
        RETURN n, g,
               collect(distinct {context: v.context, definition: v.definition}) as variations,
               collect(distinct {col: c.name, table: t.name, platform: t.platform}) as sources,
               count(distinct tk) as active_issues
        """
        async with self._driver.session() as session:
            result = await session.run(query, concept_id=concept_id)
            record = await result.single()
            if not record:
                return {}
            return {
                "definition": record["g"]["definition"] if record["g"] else "",
                "variations": {v["context"]: v["definition"] for v in record["variations"] if v["context"]},
                "sources": record["sources"],
                "active_issues": record["active_issues"],
                "certification_tier": record["n"].get("certification_tier", 4),
            }

    async def find_tribal_knowledge(self, concept_ids: list[str]) -> list[dict]:
        """Find active tribal knowledge affecting any of the given concepts."""
        query = """
        MATCH (tk:TribalKnowledge)-[:AFFECTS]->(n)
        WHERE n.id IN $concept_ids AND tk.active = true
        RETURN tk.id as id, tk.description as description,
               tk.severity as severity, tk.impact as impact,
               tk.workaround as workaround
        """
        async with self._driver.session() as session:
            result = await session.run(query, concept_ids=concept_ids)
            return [dict(record) async for record in result]

    async def get_dimension_values(self, dimension_id: str, metric_context: dict = None) -> dict:
        """Get the values for a resolved dimension (e.g., country codes for APAC)."""
        query = """
        MATCH (d {id: $dimension_id})
        RETURN d.values as values, d.name as name
        """
        async with self._driver.session() as session:
            result = await session.run(query, dimension_id=dimension_id)
            record = await result.single()
            return dict(record) if record else {}

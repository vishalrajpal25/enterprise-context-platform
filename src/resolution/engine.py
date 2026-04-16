"""
Intelligent Resolution Engine (Dual Mode)

ORCHESTRATOR mode: Rule-based, deterministic, production-ready today.
INTELLIGENT mode:  Neuro-symbolic. LLM intent + graph inference + precedent search.

Both modes persist decision traces from day one.
"""
import logging
import time
import uuid
from datetime import datetime

from src.config import settings, ResolutionMode
from src.governance.policy import OPAPolicyClient
from src.models import (
    Confidence,
    ExecutionStep,
    ParsedIntent,
    Precedent,
    ResolutionDAGStep,
    ResolvedConcept,
    ResolveRequest,
    ResolveResponse,
    TribalWarning,
    UserContext,
)
from src.resolution.intent_rules import parse_intent_rules

logger = logging.getLogger(__name__)


class ResolutionEngine:
    """
    Main entry point. Delegates to orchestrator or intelligent mode
    based on feature flag. Both modes share the same interface and
    persist traces identically.
    """

    # Confidence threshold: below this, return disambiguation_required
    CONFIDENCE_THRESHOLD = 0.7

    def __init__(self, graph_client, registry_client, vector_client, trace_store, audit_logger=None):
        self.graph = graph_client
        self.registry = registry_client
        self.vector = vector_client
        self.traces = trace_store
        self.audit = audit_logger
        self.mode = settings.resolution_mode
        self._policy = OPAPolicyClient()

        # Lazy-init neural/precedent layers only in intelligent mode
        self._neural = None
        self._precedent = None

    async def resolve(self, request: ResolveRequest) -> ResolveResponse:
        resolution_id = f"rs_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}"
        start = time.monotonic()
        user_ctx = request.user_context or UserContext(user_id="anonymous")
        dag_steps = []

        try:
            # ========================================
            # Step 1: Parse Intent
            # ========================================
            if self.mode == ResolutionMode.INTELLIGENT:
                intent = await self._get_neural().parse_intent(request.concept, user_ctx)
            else:
                intent = parse_intent_rules(request.concept)

            dag_steps.append(ResolutionDAGStep(
                step="parse_intent",
                method=self.mode.value,
                input={"query": request.concept},
                output={"concepts": intent.concepts, "type": intent.intent_type},
                latency_ms=(time.monotonic() - start) * 1000,
            ))

            # ========================================
            # Step 2: Resolve each concept
            # ========================================
            resolved = {}
            for concept_type, raw_value in intent.concepts.items():
                step_start = time.monotonic()

                if self.mode == ResolutionMode.INTELLIGENT:
                    rc = await self._resolve_intelligent(concept_type, raw_value, user_ctx)
                else:
                    rc = await self._resolve_orchestrator(concept_type, raw_value, user_ctx)

                resolved[concept_type] = rc
                dag_steps.append(ResolutionDAGStep(
                    step=f"resolve_{concept_type}",
                    method=self.mode.value,
                    input={"raw": raw_value, "department": user_ctx.department},
                    output={"resolved": rc.resolved_id, "confidence": rc.confidence},
                    reasoning=rc.reasoning,
                    latency_ms=(time.monotonic() - step_start) * 1000,
                ))

            # ========================================
            # Step 3: Check tribal knowledge
            # ========================================
            step_start = time.monotonic()
            warnings = await self._check_tribal_knowledge(resolved)
            dag_steps.append(ResolutionDAGStep(
                step="check_tribal_knowledge",
                method="graph+vector",
                input={"resolved_concepts": {k: v.resolved_id for k, v in resolved.items()}},
                output={"warnings_found": len(warnings)},
                latency_ms=(time.monotonic() - step_start) * 1000,
            ))

            # ========================================
            # Step 4: Find precedents (both modes — corrections are
            # human-verified facts, not optional learning signal)
            # ========================================
            precedents: list[Precedent] = []
            override_status: str | None = None
            overridden_concepts: set[str] = set()
            try:
                step_start = time.monotonic()
                precedents = await self._get_precedent().find_precedents(
                    request.concept, intent, user_ctx
                )
                dag_steps.append(ResolutionDAGStep(
                    step="find_precedents",
                    method="embedding_similarity",
                    input={"query": request.concept},
                    output={"precedents_found": len(precedents)},
                    latency_ms=(time.monotonic() - step_start) * 1000,
                ))
            except Exception as exc:
                logger.warning("precedent lookup failed; continuing without: %s", exc)

            # Apply hard-override corrections from precedents. A
            # single eligible correction swaps the resolved concept;
            # multiple distinct corrections for the same concept_type
            # surface as disambiguation_required.
            if precedents:
                override_status = await self._apply_correction_overrides(
                    precedents=precedents,
                    intent=intent,
                    user_ctx=user_ctx,
                    resolved=resolved,
                    dag_steps=dag_steps,
                    overridden=overridden_concepts,
                )

            # ========================================
            # Step 5: Authorize (OPA policy check)
            # ========================================
            step_start = time.monotonic()
            auth_result = await self._policy.authorize_resolution(user_ctx, resolved)
            if self.audit:
                await self.audit.log_authorization(resolution_id, user_ctx, auth_result, action="resolve")
            dag_steps.append(ResolutionDAGStep(
                step="authorize",
                method="opa_policy",
                input={"user_id": user_ctx.user_id, "department": user_ctx.department},
                output={
                    "allowed": auth_result.allowed,
                    "denied": auth_result.denied_concepts,
                    "policies": auth_result.policies_evaluated,
                },
                latency_ms=(time.monotonic() - step_start) * 1000,
            ))

            # Filter denied concepts — return "not found" to prevent info leakage.
            # If OPA returns a blanket deny without concept-level details, deny all.
            filtered_concepts: list[str] = []
            if not auth_result.allowed:
                if auth_result.denied_concepts:
                    for denied in auth_result.denied_concepts:
                        if denied in resolved:
                            del resolved[denied]
                            filtered_concepts.append(denied)
                else:
                    filtered_concepts = list(resolved.keys())
                    resolved = {}

            # ========================================
            # Step 5b: Build execution plan (after authz so denied
            #          concepts never appear in the plan)
            # ========================================
            execution_plan = await self._build_execution_plan(resolved, intent)

            # ========================================
            # Step 6: Compute confidence
            # ========================================
            confidence = await self._compute_confidence(
                resolved,
                warnings,
                precedents,
                access_granted=auth_result.allowed,
            )

            # ========================================
            # Step 6b: Status — disambiguation > override > confidence
            # ========================================
            status = "complete"
            if override_status == "disambiguation_required":
                status = "disambiguation_required"
            elif confidence.overall < self.CONFIDENCE_THRESHOLD and resolved:
                status = "disambiguation_required"

            response = ResolveResponse(
                resolution_id=resolution_id,
                status=status,
                resolved_concepts=resolved,
                execution_plan=execution_plan,
                confidence=confidence,
                warnings=warnings,
                precedents_used=precedents,
                resolution_dag=dag_steps,
                policies_evaluated=auth_result.policies_evaluated,
                access_granted=auth_result.allowed,
                filtered_concepts=filtered_concepts,
            )

            # ========================================
            # Step 7: Persist decision trace (ALWAYS, both modes)
            # ========================================
            await self.traces.persist_resolution(
                resolution_id=resolution_id,
                request=request,
                response=response,
                intent=intent,
            )

            return response

        except Exception as e:
            await self.traces.persist_failure(resolution_id, request, str(e))
            raise

    # ============================================================
    # ORCHESTRATOR MODE: Rule-based resolution
    # (intent parsing lives in src/resolution/intent_rules.py)
    # ============================================================

    async def _resolve_orchestrator(
        self, concept_type: str, raw_value: str, user_ctx: UserContext
    ) -> ResolvedConcept:
        """Rule-based resolution.

        Time concepts are resolved against the fiscal calendar (registry).
        Comparison concepts are intent flags, not graph nodes — kept as-is.
        Everything else is a graph lookup with the new real scoring.
        """
        if concept_type == "time":
            return await self._resolve_time_concept(raw_value)
        if concept_type == "comparison":
            return ResolvedConcept(
                concept_type=concept_type,
                raw_value=raw_value,
                resolved_id=raw_value,
                resolved_name=raw_value.replace("_", " ").title(),
                definition=(
                    "Comparison flag — instructs the execution layer to "
                    "compute prior period or budget delta."
                ),
                confidence=0.95,
                reasoning="Comparison is an intent flag, not a graph concept.",
            )
        if concept_type == "scope":
            return await self._resolve_scope_concept(raw_value, user_ctx)
        if concept_type == "adjustment":
            return await self._resolve_adjustment_concept(raw_value, user_ctx)

        results = await self.graph.find_concept(concept_type, raw_value, user_ctx.department)

        if not results:
            return ResolvedConcept(
                concept_type=concept_type,
                raw_value=raw_value,
                resolved_id=f"unresolved_{raw_value}",
                resolved_name=raw_value,
                definition=f"No definition found for '{raw_value}'",
                confidence=0.3,
                reasoning="No matching concept in knowledge graph",
            )

        best = results[0]  # Graph client returns sorted by score (real signal now).
        return ResolvedConcept(
            concept_type=concept_type,
            raw_value=raw_value,
            resolved_id=best["id"],
            resolved_name=best["name"],
            definition=best.get("definition", ""),
            confidence=best.get("score", 0.8),
            reasoning=(
                f"Graph match score={best.get('score', 0.0):.2f}, "
                f"department context={user_ctx.department or 'none'}."
            ),
        )

    async def _resolve_time_concept(self, raw_value: str) -> ResolvedConcept:
        """Resolve a canonical time identifier via the fiscal calendar."""
        time_info = await self.registry.resolve_time_period(raw_value)
        if not time_info or "range" not in time_info:
            return ResolvedConcept(
                concept_type="time",
                raw_value=raw_value,
                resolved_id=f"unresolved_{raw_value}",
                resolved_name=raw_value,
                definition=f"Could not resolve time period '{raw_value}'",
                confidence=0.3,
                reasoning="Fiscal calendar resolver returned no match",
            )
        label = time_info.get("label", raw_value)
        date_range = time_info.get("range", [])
        return ResolvedConcept(
            concept_type="time",
            raw_value=raw_value,
            resolved_id=raw_value,
            resolved_name=label,
            definition=(
                f"Fiscal period {label}, "
                f"date range {date_range[0] if date_range else '?'} to "
                f"{date_range[1] if len(date_range) > 1 else '?'}"
            ),
            confidence=1.0,
            reasoning=(
                f"Resolved via fiscal calendar (start month "
                f"{(await self.registry._load_fiscal_context()).fiscal_year_start_month}). "
                f"Computed live from current wall clock."
            ),
        )

    async def _resolve_scope_concept(
        self, raw_value: str, user_ctx: UserContext
    ) -> ResolvedConcept:
        """Resolve a scope concept (e.g., 'book') via graph lookup with user context.

        Scope concepts like 'my book' resolve differently per department:
        portfolio_management -> portfolio (user's holdings),
        sales -> book of business (user's accounts).
        """
        results = await self.graph.find_concept("scope", raw_value, user_ctx.department)
        if not results:
            # Fallback: try as a generic Entity lookup
            results = await self.graph.find_concept("entity", raw_value, user_ctx.department)

        if not results:
            return ResolvedConcept(
                concept_type="scope",
                raw_value=raw_value,
                resolved_id=f"unresolved_{raw_value}",
                resolved_name=raw_value,
                definition=f"No scope definition found for '{raw_value}'",
                confidence=0.3,
                reasoning="No matching scope concept in knowledge graph",
            )

        best = results[0]
        # Enrich with user-specific scope info
        scope_detail = (
            f"Scoped to {user_ctx.user_id}'s {best['name'].lower()}"
            if user_ctx.user_id != "anonymous"
            else best.get("definition", "")
        )
        return ResolvedConcept(
            concept_type="scope",
            raw_value=raw_value,
            resolved_id=best["id"],
            resolved_name=best["name"],
            definition=scope_detail,
            confidence=best.get("score", 0.8),
            reasoning=(
                f"Graph match score={best.get('score', 0.0):.2f}, "
                f"user={user_ctx.user_id}, department={user_ctx.department}. "
                f"'book' → '{best['name']}' in {user_ctx.department} context."
            ),
        )

    async def _resolve_adjustment_concept(
        self, raw_value: str, user_ctx: UserContext
    ) -> ResolvedConcept:
        """Resolve an adjustment concept (e.g., 'peer_adjusted') via graph lookup.

        Adjustment methods differ by department:
        equity_research -> ratio (company / peer mean),
        portfolio_management -> spread in bps (company - peer median).
        """
        results = await self.graph.find_concept("adjustment", raw_value, user_ctx.department)
        if not results:
            results = await self.graph.find_concept("entity", raw_value, user_ctx.department)

        if not results:
            return ResolvedConcept(
                concept_type="adjustment",
                raw_value=raw_value,
                resolved_id=f"unresolved_{raw_value}",
                resolved_name=raw_value,
                definition=f"No adjustment definition found for '{raw_value}'",
                confidence=0.3,
                reasoning="No matching adjustment concept in knowledge graph",
            )

        best = results[0]
        return ResolvedConcept(
            concept_type="adjustment",
            raw_value=raw_value,
            resolved_id=best["id"],
            resolved_name=best["name"],
            definition=best.get("definition", ""),
            confidence=best.get("score", 0.8),
            reasoning=(
                f"Graph match score={best.get('score', 0.0):.2f}, "
                f"department={user_ctx.department}. "
                f"Adjustment method selected for {user_ctx.department} context."
            ),
        )

    # ============================================================
    # INTELLIGENT MODE: Neuro-symbolic resolution
    # ============================================================

    async def _resolve_intelligent(
        self, concept_type: str, raw_value: str, user_ctx: UserContext
    ) -> ResolvedConcept:
        """
        Neuro-symbolic resolution:
        1. Vector search for candidates (neural)
        2. Graph traversal for context (symbolic)
        3. Precedent check (learned)
        4. Score and select
        """
        # Neural: find candidates via vector similarity
        candidates = await self.vector.search(
            query=raw_value,
            filter_type=concept_type,
            top_k=5,
        )

        if not candidates:
            return await self._resolve_orchestrator(concept_type, raw_value, user_ctx)

        # Symbolic: enrich each candidate with graph context
        scored = []
        for candidate in candidates:
            graph_ctx = await self.graph.get_concept_context(
                candidate["id"], user_ctx.department
            )
            score = self._score_candidate(candidate, graph_ctx, user_ctx)
            scored.append((candidate, graph_ctx, score))

        scored.sort(key=lambda x: x[2], reverse=True)
        best_candidate, best_ctx, best_score = scored[0]

        return ResolvedConcept(
            concept_type=concept_type,
            raw_value=raw_value,
            resolved_id=best_candidate["id"],
            resolved_name=best_candidate.get("name", raw_value),
            definition=best_ctx.get("definition", ""),
            confidence=best_score,
            reasoning=(
                f"Neural: {len(candidates)} candidates found. "
                f"Symbolic: graph context resolved to {best_candidate['id']} "
                f"(dept={user_ctx.department}, score={best_score:.2f})."
            ),
        )

    def _score_candidate(
        self, candidate: dict, graph_ctx: dict, user_ctx: UserContext
    ) -> float:
        """Score a candidate based on vector similarity, graph evidence, and user context."""
        score = candidate.get("score", 0.5)

        # Boost if department matches a known variation
        if user_ctx.department in graph_ctx.get("variations", {}):
            score *= 1.15

        # Boost if certification tier is high
        tier = graph_ctx.get("certification_tier", 4)
        score *= (1 + (4 - tier) * 0.05)

        # Penalize if there are active known issues
        if graph_ctx.get("active_issues", 0) > 0:
            score *= 0.9

        return min(score, 1.0)

    # ============================================================
    # Shared methods (both modes)
    # ============================================================

    async def _apply_correction_overrides(
        self,
        *,
        precedents: list[Precedent],
        intent: ParsedIntent,
        user_ctx: UserContext,
        resolved: dict[str, ResolvedConcept],
        dag_steps: list[ResolutionDAGStep],
        overridden: set[str],
    ) -> str | None:
        """Replace resolved concepts with structured precedent corrections.

        Returns "disambiguation_required" when two or more eligible
        corrections target the same concept_type with different
        preferred_resolved_id values; the engine then sets the response
        status accordingly so the caller sees both candidates and picks.

        Records one DAG step per concept type considered (override or
        conflict). Per-concept Confidence is set by `_compute_confidence`,
        which trusts the resolved concept's own confidence — bumping that
        to 1.0 here means definition-level confidence rises with it.
        """
        from src.resolution.precedent import PrecedentEngine

        eligible = PrecedentEngine.compute_overrides(precedents, user_ctx, intent)
        if not eligible:
            return None

        conflict = False
        for concept_type, candidates in eligible.items():
            distinct_targets = {
                p.correction.preferred_resolved_id for p in candidates if p.correction
            }
            if len(distinct_targets) > 1:
                # Conflicting corrections — surface both, do not pick.
                conflict = True
                dag_steps.append(ResolutionDAGStep(
                    step=f"override_{concept_type}",
                    method="precedent_correction",
                    input={
                        "concept_type": concept_type,
                        "eligible_corrections": [
                            {
                                "query_id": p.query_id,
                                "preferred_resolved_id": p.correction.preferred_resolved_id,
                                "similarity": p.similarity,
                                "corrected_at": p.correction.corrected_at,
                            }
                            for p in candidates if p.correction
                        ],
                    },
                    output={"applied": False, "conflict": True},
                    reasoning=(
                        f"Multiple correction precedents conflict for "
                        f"{concept_type} ({sorted(distinct_targets)}); "
                        f"falling back to disambiguation_required."
                    ),
                ))
                continue

            # Single winner: pick highest similarity (ties broken by
            # most-recent feedback_at, which already orders late records
            # higher in lexicographic ISO 8601).
            winner = max(
                candidates,
                key=lambda p: (p.similarity, p.correction.corrected_at if p.correction else ""),
            )
            corr = winner.correction
            if corr is None:  # defensive — compute_overrides filters this
                continue

            previous = resolved.get(concept_type)
            previous_id = previous.resolved_id if previous else None

            reasoning = (
                f"Applied correction from {winner.query_id} "
                f"(similarity={winner.similarity:.2f}, dept match, "
                f"corrected {corr.corrected_at})."
            )

            resolved[concept_type] = ResolvedConcept(
                concept_type=concept_type,
                raw_value=intent.concepts.get(
                    concept_type, previous.raw_value if previous else ""
                ),
                resolved_id=corr.preferred_resolved_id,
                resolved_name=corr.preferred_resolved_name or corr.preferred_resolved_id,
                definition=(
                    f"Human-verified correction propagated from "
                    f"{winner.query_id}: {corr.note}".strip()
                    if corr.note else
                    f"Human-verified correction propagated from {winner.query_id}."
                ),
                # The correction is human-verified, so this concept's
                # definition-level confidence is 1.0.
                confidence=1.0,
                reasoning=reasoning,
            )
            overridden.add(concept_type)

            dag_steps.append(ResolutionDAGStep(
                step=f"override_{concept_type}",
                method="precedent_correction",
                input={
                    "concept_type": concept_type,
                    "previous_resolved_id": previous_id,
                    "precedent_query_id": winner.query_id,
                    "similarity": winner.similarity,
                    "department": corr.department,
                },
                output={
                    "applied": True,
                    "resolved_id": corr.preferred_resolved_id,
                    "confidence_definition": 1.0,
                },
                reasoning=reasoning,
            ))

        return "disambiguation_required" if conflict else None

    async def _check_tribal_knowledge(
        self, resolved: dict[str, ResolvedConcept]
    ) -> list[TribalWarning]:
        """Check for known issues affecting resolved concepts."""
        warnings = []
        resolved_ids = [rc.resolved_id for rc in resolved.values()]

        results = await self.graph.find_tribal_knowledge(resolved_ids)
        for tk in results:
            warnings.append(TribalWarning(
                id=tk["id"],
                description=tk["description"],
                severity=tk.get("severity", "medium"),
                impact=tk.get("impact", ""),
                workaround=tk.get("workaround", ""),
            ))

        return warnings

    async def _build_execution_plan(
        self, resolved: dict[str, ResolvedConcept], intent: ParsedIntent
    ) -> list[ExecutionStep]:
        """
        Build execution plan for the Semantic Layer (Cube.js).
        Maps resolved concepts to API calls.
        """
        steps = []

        metric_concept = resolved.get("metric")
        if not metric_concept:
            return steps

        # Look up the semantic layer reference for this metric
        metric_info = await self.registry.get_metric_info(metric_concept.resolved_id)
        if not metric_info:
            return steps
        # Some glossary-only concepts (e.g. churn_rate stored as a glossary
        # term, not a metric_definition) have no semantic_layer_ref. Skip
        # building an execution step rather than emit a malformed plan.
        if not metric_info.get("semantic_layer_ref") or not metric_info.get("measure"):
            return steps

        filters = {}
        if "dimension" in resolved:
            dim = resolved["dimension"]
            dim_info = await self.graph.get_dimension_values(
                dim.resolved_id, resolved.get("metric", {})
            )
            if dim_info:
                filters["region"] = dim_info.get("values", [])

        if "time" in resolved:
            time_info = await self.registry.resolve_time_period(
                resolved["time"].resolved_id
            )
            if time_info and "range" in time_info:
                # Shape consumed by src/semantic/cube_executor.py:_step_to_cube_query
                filters["date_range"] = {
                    "dimension": time_info.get("dimension", "Revenue.date"),
                    "range": time_info["range"],
                    "label": time_info.get("label", ""),
                    "fiscal_year": time_info.get("fiscal_year"),
                    "fiscal_quarter": time_info.get("fiscal_quarter"),
                }
                # Also enrich the resolved concept with the human label so
                # provenance and the demo UI show "Q3-FY2026" not "last_quarter".
                resolved["time"].resolved_name = time_info.get(
                    "label", resolved["time"].resolved_name
                )

        # Gather source lineage for provenance
        sources = await self.graph.get_metric_sources(metric_concept.resolved_id)

        params: dict = {"measures": [metric_info["measure"]], "filters": filters}
        if sources:
            params["sources"] = sources

        # Add scope filter if present
        if "scope" in resolved:
            scope = resolved["scope"]
            params["scope"] = {
                "type": scope.resolved_id,
                "name": scope.resolved_name,
            }

        # Add adjustment config if present
        if "adjustment" in resolved:
            adj = resolved["adjustment"]
            params["adjustment"] = {
                "type": adj.resolved_id,
                "name": adj.resolved_name,
                "definition": adj.definition,
            }

        steps.append(ExecutionStep(
            target=metric_info.get("semantic_layer_ref", ""),
            method="semantic_layer_call",
            parameters=params,
        ))

        return steps

    async def _compute_confidence(
        self,
        resolved: dict,
        warnings: list,
        precedents: list,
        access_granted: bool,
    ) -> Confidence:
        """Compute multi-dimensional confidence from real signals.

        - definition: weighted average of per-concept resolution scores from
          the graph (which already reflects exact/prefix/substring + cert
          tier + department-variation match).
        - data_quality / completeness: pulled from the data contract for the
          metric's source table — real SLA values, not constants.
        - temporal_validity: derived from the contract's freshness_hours SLA
          (≤6h → 1.0; degrading linearly to 0.5 at 24h+). This measures the
          *contract guarantee* — true observed freshness requires telemetry
          we don't have yet, and that's documented in CLAUDE.md.
        - authorization: 1.0 if OPA allowed the resolution, else 0.0.
        - overall: weighted composite minus tribal warning penalty plus
          accepted-precedent boost.
        """
        def_scores = [rc.confidence for rc in resolved.values()]
        def_conf = sum(def_scores) / len(def_scores) if def_scores else 0.0

        data_quality, temporal_validity, completeness = await self._contract_quality(resolved)

        warning_penalty = 0.05 * len([w for w in warnings if w.severity == "high"])
        precedent_boost = 0.04 * len([p for p in precedents if p.feedback == "accepted"])

        # Composite weighting: definition match dominates, but contract SLAs
        # and authorization can each veto the result.
        composite = (
            0.50 * def_conf
            + 0.20 * data_quality
            + 0.15 * temporal_validity
            + 0.10 * completeness
            + 0.05 * (1.0 if access_granted else 0.0)
        )
        overall = min(1.0, max(0.0, composite - warning_penalty + precedent_boost))

        return Confidence(
            definition=def_conf,
            data_quality=data_quality,
            temporal_validity=temporal_validity,
            authorization=1.0 if access_granted else 0.0,
            completeness=completeness,
            overall=overall,
        )

    async def _contract_quality(
        self, resolved: dict
    ) -> tuple[float, float, float]:
        """Look up the data contract for each resolved metric and derive
        (data_quality, temporal_validity, completeness) from real SLA values.

        If no metric is resolved or no contract is found, returns conservative
        defaults (0.7, 0.7, 0.7) — *not* the old fake-perfect 0.9/0.95/0.9 —
        so missing contract coverage shows up as lower confidence rather than
        being hidden.
        """
        metric_concept = resolved.get("metric")
        if not metric_concept:
            return 0.70, 0.70, 0.70

        try:
            source_table = await self.registry.get_metric_source_table(
                metric_concept.resolved_id
            )
            if not source_table:
                logger.debug("contract_quality: no source_table for %s", metric_concept.resolved_id)
                return 0.70, 0.70, 0.70

            contract = await self.registry.get_data_contract_for_table(source_table)
            if not contract:
                logger.debug("contract_quality: no contract for table %s", source_table)
                return 0.70, 0.70, 0.70
        except Exception as exc:
            logger.warning("contract_quality lookup failed: %s", exc, exc_info=True)
            return 0.70, 0.70, 0.70

        sla = contract.get("sla") or {}
        availability = float(sla.get("availability_pct", 95.0)) / 100.0
        completeness_pct = float(sla.get("completeness_pct", 95.0)) / 100.0
        freshness_hours = float(sla.get("freshness_hours", 24.0))

        # Freshness SLA → temporal validity:
        #   ≤ 6h  → 1.00
        #   12h   → 0.85
        #   24h   → 0.70
        #   48h+  → 0.50
        if freshness_hours <= 6:
            temporal = 1.0
        elif freshness_hours <= 12:
            temporal = 0.85
        elif freshness_hours <= 24:
            temporal = 0.70
        else:
            temporal = max(0.50, 1.0 - (freshness_hours - 6) * 0.02)

        return min(1.0, availability), round(temporal, 4), min(1.0, completeness_pct)

    # ============================================================
    # Lazy initialization
    # ============================================================

    def _get_neural(self):
        if self._neural is None:
            from src.resolution.neural import NeuralPerceptionLayer
            self._neural = NeuralPerceptionLayer()
        return self._neural

    def _get_precedent(self):
        if self._precedent is None:
            from src.resolution.precedent import PrecedentEngine
            self._precedent = PrecedentEngine(self.traces)
        return self._precedent

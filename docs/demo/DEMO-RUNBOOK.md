# ECP Demo Runbook (UI-First)

This runbook is for running crisp, user-friendly demos with the new `docs/demo/studio.html` interface.

It is intentionally practical: what to open, what to click, what to say, what to expect.

---

## 1) Demo Setup

1. Start platform:
   - `docker compose up -d`
   - `python scripts/init_db.py`
   - `python scripts/seed_data.py`
   - `uvicorn src.main:app --reload --port 8080`
2. Open `docs/demo/studio.html` in a browser.
3. Keep API URL as `http://localhost:8080`.
4. Click `Check health`, then `Check readiness`.

If API key is enabled, paste it in `API Key`.

---

## 2) What this UI demonstrates

- **Context resolution**: one question can resolve differently by department and role.
- **Governance and entitlement**: policy outcomes and filtered concepts are visible.
- **Latency transparency**: round-trip and DAG step latencies are surfaced.
- **Trust signals**: confidence dimensions, warnings, precedents, provenance.
- **Operational flow**: resolve -> execute -> feedback -> provenance -> search.

---

## 3) 15-minute core demo script

## Scene A: Platform trust check (2 min)

Use:
- `Check health`
- `Check readiness`

Narration:
- "This is a live context service with dependency checks, not a static prompt."
- "Readiness tells us if graph, registry, vector, traces, and policy path are available."

Expected:
- Health returns mode + embedding state.
- Readiness returns per-service checks.

## Scene B: Same question, different meaning (4 min)

Scenario:
- Pick `Core product journey`.
- Run `Finance APAC revenue`.
- Then run `Sales APAC revenue`.

Narration:
- "Same natural language, different business meaning by organizational context."
- "ECP resolves meaning before computation and records a decision trace."

Expected:
- Different metric/dimension IDs across finance vs sales.
- Confidence, warnings, and DAG are visible for both.

## Scene C: Governance and explainability (3 min)

Scenario:
- Pick `Governance and entitlement`.
- Run `Policy-sensitive request as auditor`.
- Click `Provenance`.

Narration:
- "This shows not just what answer is given, but why and under which policy context."
- "Entitlement outcomes are inspectable, including filtered concepts."

Expected:
- Governance panel fills with `access_granted`, policies, and filtered concepts.
- Provenance returns stored session details.

## Scene D: Execution and learning loop (3 min)

Scenario:
- Use a completed resolution.
- Click `Execute`.
- Click `Feedback: accepted`.
- Re-run a similar query.

Narration:
- "Execution is deterministic via the semantic layer plan."
- "Feedback contributes to precedent signals in future similar questions."

Expected:
- Execute returns dry-run or live results depending on Cube config.
- Feedback endpoint records state.

## Scene E: Registry search with identity (3 min)

Scenario:
- Enter `Search: revenue definition`.
- Click `Search registry`.

Narration:
- "Search obeys identity and policy filtering."
- "This is how stewards and operators inspect available context assets."

Expected:
- Results list appears, possibly filtered by policy/identity.

---

## 4) Scenario Catalog (easy to run)

Each scenario includes prompt, persona, and success criteria.

## A. Product Journey Scenarios

1) **Department conflict resolution**
- Prompt: `What was APAC revenue last quarter?`
- Persona 1: `finance / analyst`
- Persona 2: `sales / analyst`
- Success: concept resolution differs by persona; both traces persist.

2) **Comparison intent**
- Prompt: `Compare APAC revenue to budget last quarter`
- Persona: `finance / manager`
- Success: comparison concept appears in execution plan.

3) **Fiscal language handling**
- Prompt: `What is global revenue year to date?`
- Persona: `finance / analyst`
- Success: time concept resolves to canonical YTD.

## B. Governance and Entitlement Scenarios

4) **Policy-sensitive metric access**
- Prompt: `Show customer retention for strategic accounts by region`
- Persona: `compliance / auditor`
- Success: governance panel shows policy path and access outcome.

5) **Operational lens**
- Prompt: `How many employees do we have in APAC?`
- Persona: `operations / analyst`
- Success: concept mapping is complete and explainable.

6) **Identity-bound provenance**
- Prompt: any resolved prompt with `demo_user_1`, then query provenance as another user.
- Persona: `finance / analyst`
- Success: non-owner provenance request is forbidden.

## C. Enterprise Stress Scenarios (advanced prompts)

7) **FactSet-like market intelligence prompt**
- Prompt: `What was APAC tech revenue surprise versus consensus last quarter net of restatements?`
- Persona: `research / manager`
- Success: system resolves as far as current ontology allows; confidence and gaps are explicit.

8) **Treasury risk framing**
- Prompt: `What is risk-adjusted net interest income by segment excluding promo-rate anomalies?`
- Persona: `treasury / manager`
- Success: complex intent surfaces confidence and potential ambiguity.

9) **Supply chain complexity prompt**
- Prompt: `Show OTIF performance for constrained SKUs with supplier risk overlay`
- Persona: `operations / executive`
- Success: unknowns are transparent; warnings reflect uncertainty where applicable.

---

## 5) Host-facing FAQ prompts (for live demos)

Use these when users ask hard questions during demos:

- "How do I know this is not hallucinated?"
  - Show confidence dimensions + provenance trace + execution plan.
- "Can this enforce entitlement?"
  - Show governance panel, policy-evaluated fields, and owner-guarded provenance.
- "How do we see performance?"
  - Show round-trip KPI and DAG step latencies.
- "Does it learn?"
  - Show feedback action and precedent panel behavior.
- "Can non-technical users use it?"
  - Show scenario cards and guided buttons for end-to-end flow.

---

## 6) Recommended demo flow by audience

- **Business stakeholders** (10-15 min): Scene A -> B -> C
- **Data/governance teams** (20 min): Scene A -> C -> E -> provenance deep dive
- **Engineering teams** (20-30 min): all scenes + JSON payload review + stress prompts

---

## 7) Troubleshooting

- `401 Unauthorized`: API key required; fill `API Key`.
- `403 Forbidden`: user identity does not own resolution for execute/provenance/feedback.
- Empty search results: identity requirement/policy filtering likely active.
- Execute returns dry-run data: Cube URL not configured (expected in local demo).

---

## 8) Next enhancement ideas (optional)

- Side-by-side compare mode in UI (finance vs sales diff view).
- Saved sessions panel for replay by `resolution_id`.
- One-click "export trace" bundle for customer workshop artifacts.
- Toggle persona presets by industry (finance, healthcare, manufacturing, telecom).

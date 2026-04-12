"""
Demo: FCF Yield — "Same question, different answer, here's exactly why"

Sends the complex query:
  "Show me free cash flow yield for my tech book over the last 8 quarters, peer-adjusted."

First as a Portfolio Manager (Sarah Chen), then as a Credit Research Analyst (John Doe).
Shows how the SAME question resolves DIFFERENTLY based on who is asking.

Usage:
  # Start infra first: docker compose up -d
  # Init DB: uv run python scripts/init_db.py
  # Seed:    uv run python scripts/seed_data.py
  # Run API: uv run uvicorn src.main:app --reload --port 8080
  # Then:    uv run python scripts/demo_fcf.py
"""
import httpx
import json
import sys

BASE = "http://localhost:8080"

QUERY = "Show me free cash flow yield for my tech book over the last 8 quarters, peer-adjusted."

USERS = [
    {
        "label": "PORTFOLIO MANAGER",
        "user_context": {
            "user_id": "sarah.chen",
            "department": "portfolio_management",
            "role": "senior_pm",
        },
    },
    {
        "label": "CREDIT RESEARCH ANALYST",
        "user_context": {
            "user_id": "john.doe",
            "department": "credit_research",
            "role": "analyst",
        },
    },
]


def print_resolution(label: str, query: str, response: dict):
    print("\n" + "=" * 90)
    print(f"  {label}")
    print("=" * 90)
    print(f"QUERY:      {query}")
    uc = response.get("_user_context", {})
    print(f"USER:       {uc.get('user_id', '?')} | {uc.get('department', '?')} | {uc.get('role', '?')}")
    print(f"STATUS:     {response['status']}")
    print(f"RESOLUTION: {response['resolution_id']}")
    print("-" * 90)

    # --- Resolved concepts ---
    print("\nRESOLVED CONCEPTS:")
    for ctype, concept in response.get("resolved_concepts", {}).items():
        print(f"\n  [{ctype.upper()}]")
        print(f"    resolved_to: {concept['resolved_name']} ({concept['resolved_id']})")
        defn = concept['definition']
        if len(defn) > 120:
            defn = defn[:117] + "..."
        print(f"    definition:  {defn}")
        print(f"    confidence:  {concept['confidence']:.2f}")
        print(f"    reasoning:   {concept['reasoning']}")

    # --- Tribal knowledge warnings ---
    if response.get("warnings"):
        print(f"\nTRIBAL KNOWLEDGE WARNINGS ({len(response['warnings'])}):")
        for w in response["warnings"]:
            print(f"  [{w['severity'].upper()}] {w['description']}")
            if w.get("impact"):
                print(f"    impact:     {w['impact']}")
            if w.get("workaround"):
                print(f"    workaround: {w['workaround']}")

    # --- Precedents ---
    if response.get("precedents_used"):
        print("\nPRECEDENTS:")
        for p in response["precedents_used"]:
            print(f"  {p['original_query']} -> {p['feedback']} ({p['influence'][:60]})")

    # --- Confidence ---
    conf = response.get("confidence", {})
    print(f"\nCONFIDENCE:")
    print(f"  definition:        {conf.get('definition', 0):.2f}")
    print(f"  data_quality:      {conf.get('data_quality', 0):.2f}")
    print(f"  temporal_validity: {conf.get('temporal_validity', 0):.2f}")
    print(f"  authorization:     {conf.get('authorization', 0):.2f}")
    print(f"  completeness:      {conf.get('completeness', 0):.2f}")
    print(f"  OVERALL:           {conf.get('overall', 0):.2f}")

    # --- Execution plan ---
    if response.get("execution_plan"):
        print(f"\nEXECUTION PLAN ({len(response['execution_plan'])} steps):")
        for step in response["execution_plan"]:
            print(f"  target: {step['target']}")
            print(f"  method: {step['method']}")
            params = step.get("parameters", {})

            if params.get("measures"):
                print(f"    measures: {params['measures']}")
            if params.get("filters", {}).get("date_range"):
                dr = params["filters"]["date_range"]
                print(f"    date_range: {dr.get('range', [])}  ({dr.get('label', '')})")
            if params.get("scope"):
                s = params["scope"]
                print(f"    scope: {s.get('name', '')} ({s.get('type', '')})")
            if params.get("adjustment"):
                a = params["adjustment"]
                print(f"    adjustment: {a.get('name', '')} — {a.get('definition', '')[:80]}")
            if params.get("sources"):
                platforms = set()
                for src in params["sources"]:
                    platforms.add(f"{src.get('platform', '?')}:{src.get('table_name', '?')}")
                print(f"    cross-platform sources: {', '.join(sorted(platforms))}")

    # --- Resolution DAG ---
    dag = response.get("resolution_dag", [])
    print(f"\nRESOLUTION DAG ({len(dag)} steps):")
    for step in dag:
        print(f"  [{step.get('latency_ms', 0):6.1f}ms] {step['step']} ({step['method']})")
        if step.get("reasoning"):
            print(f"             -> {step['reasoning'][:100]}")


def print_comparison(responses: list[dict]):
    """Side-by-side comparison of how the same query resolved differently."""
    print("\n" + "=" * 90)
    print("  COMPARISON: Same Question, Different Answer")
    print("=" * 90)

    concept_types = set()
    for r in responses:
        concept_types.update(r.get("resolved_concepts", {}).keys())

    for ctype in sorted(concept_types):
        print(f"\n  [{ctype.upper()}]")
        for r in responses:
            uc = r.get("_user_context", {})
            dept = uc.get("department", "?")
            concept = r.get("resolved_concepts", {}).get(ctype)
            if concept:
                print(f"    {dept:25s} -> {concept['resolved_name']} ({concept['resolved_id']})")
                defn = concept['definition']
                if len(defn) > 80:
                    defn = defn[:77] + "..."
                print(f"    {'':25s}    {defn}")
            else:
                print(f"    {dept:25s} -> (not resolved)")

    print(f"\n  [OVERALL CONFIDENCE]")
    for r in responses:
        uc = r.get("_user_context", {})
        dept = uc.get("department", "?")
        conf = r.get("confidence", {}).get("overall", 0)
        print(f"    {dept:25s} -> {conf:.2f}")

    print()


def main():
    print("=" * 90)
    print("  Enterprise Context Platform — FCF Yield Demo")
    print("  'Same question, different answer, here's exactly why'")
    print("=" * 90)
    print(f"\nQuery: \"{QUERY}\"")
    print(f"Resolves 6 concepts: metric, scope, time, adjustment (+ tribal knowledge + lineage)")
    print(f"\nChecking {BASE}/health ...")

    try:
        health = httpx.get(f"{BASE}/health", timeout=5)
        mode = health.json().get("mode", "unknown")
        print(f"Connected. Resolution mode: {mode}")
    except Exception as e:
        print(f"Cannot connect to ECP at {BASE}. Start the server first.")
        print(f"  docker compose up -d")
        print(f"  uv run python scripts/init_db.py && uv run python scripts/seed_data.py")
        print(f"  uv run uvicorn src.main:app --reload --port 8080")
        sys.exit(1)

    responses = []

    for user in USERS:
        payload = {
            "concept": QUERY,
            "user_context": user["user_context"],
        }
        try:
            resp = httpx.post(f"{BASE}/api/v1/resolve", json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            data["_user_context"] = user["user_context"]
            responses.append(data)
            print_resolution(user["label"], QUERY, data)
        except Exception as e:
            print(f"\nERROR resolving for {user['label']}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"  Response: {e.response.text[:500]}")

    # Side-by-side comparison
    if len(responses) == 2:
        print_comparison(responses)

    print("\nDemo complete.")


if __name__ == "__main__":
    main()

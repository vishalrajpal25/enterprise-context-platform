"""
Demo: Run the canonical "What was APAC revenue last quarter?" resolution.
Prints the full resolution DAG, confidence scores, and provenance.

Usage:
  # Start infra first: docker compose up -d
  # Init DB: python scripts/init_db.py && python scripts/seed_data.py
  # Run API: uvicorn src.main:app --port 8080
  # Then: python scripts/demo.py
"""
import httpx
import json
import sys

BASE = "http://localhost:8080"

QUERIES = [
    {
        "concept": "What was APAC revenue last quarter?",
        "user_context": {"user_id": "demo_user", "department": "finance", "role": "analyst"}
    },
    {
        "concept": "What was APAC revenue last quarter?",
        "user_context": {"user_id": "demo_user_2", "department": "sales", "role": "director"}
    },
    {
        "concept": "Compare APAC revenue to budget last quarter",
        "user_context": {"user_id": "demo_user", "department": "finance", "role": "analyst"}
    },
]


def print_resolution(query_info: dict, response: dict):
    print("\n" + "=" * 80)
    print(f"QUERY:      {query_info['concept']}")
    print(f"USER:       {query_info['user_context']['department']} / {query_info['user_context']['role']}")
    print(f"STATUS:     {response['status']}")
    print(f"RESOLUTION: {response['resolution_id']}")
    print("-" * 80)

    print("\nRESOLVED CONCEPTS:")
    for ctype, concept in response.get("resolved_concepts", {}).items():
        print(f"  {ctype}:")
        print(f"    resolved_to: {concept['resolved_name']} ({concept['resolved_id']})")
        print(f"    definition:  {concept['definition'][:80]}...")
        print(f"    confidence:  {concept['confidence']:.2f}")
        print(f"    reasoning:   {concept['reasoning']}")

    if response.get("warnings"):
        print("\nTRIBAL KNOWLEDGE WARNINGS:")
        for w in response["warnings"]:
            print(f"  [{w['severity'].upper()}] {w['description']}")
            if w.get("workaround"):
                print(f"    workaround: {w['workaround']}")

    if response.get("precedents_used"):
        print("\nPRECEDENTS:")
        for p in response["precedents_used"]:
            print(f"  {p['original_query']} -> {p['feedback']} ({p['influence'][:60]})")

    conf = response.get("confidence", {})
    print(f"\nCONFIDENCE:")
    print(f"  definition:       {conf.get('definition', 0):.2f}")
    print(f"  data_quality:     {conf.get('data_quality', 0):.2f}")
    print(f"  temporal_validity:{conf.get('temporal_validity', 0):.2f}")
    print(f"  authorization:    {conf.get('authorization', 0):.2f}")
    print(f"  completeness:     {conf.get('completeness', 0):.2f}")
    print(f"  OVERALL:          {conf.get('overall', 0):.2f}")

    if response.get("execution_plan"):
        print(f"\nEXECUTION PLAN:")
        for step in response["execution_plan"]:
            print(f"  {step['method']}: {step['target']}")
            print(f"    params: {json.dumps(step.get('parameters', {}), indent=2)[:200]}")

    print(f"\nRESOLUTION DAG ({len(response.get('resolution_dag', []))} steps):")
    for step in response.get("resolution_dag", []):
        print(f"  [{step.get('latency_ms', 0):.0f}ms] {step['step']} ({step['method']})")
        if step.get("reasoning"):
            print(f"    -> {step['reasoning'][:100]}")


def main():
    print("Enterprise Context Platform - Demo")
    print(f"Mode: checking {BASE}/health ...")

    try:
        health = httpx.get(f"{BASE}/health", timeout=5)
        mode = health.json().get("mode", "unknown")
        print(f"Connected. Resolution mode: {mode}")
    except Exception as e:
        print(f"Cannot connect to ECP at {BASE}. Start the server first.")
        print(f"  docker compose up -d")
        print(f"  python scripts/init_db.py && python scripts/seed_data.py")
        print(f"  uvicorn src.main:app --port 8080")
        sys.exit(1)

    for query_info in QUERIES:
        try:
            resp = httpx.post(f"{BASE}/api/v1/resolve", json=query_info, timeout=30)
            resp.raise_for_status()
            print_resolution(query_info, resp.json())
        except Exception as e:
            print(f"\nERROR resolving '{query_info['concept']}': {e}")

    # Demo feedback loop
    print("\n" + "=" * 80)
    print("FEEDBACK LOOP DEMO:")
    print("Recording feedback: 'accepted' for first resolution...")
    try:
        first_resp = httpx.post(f"{BASE}/api/v1/resolve", json=QUERIES[0], timeout=30)
        rid = first_resp.json().get("resolution_id")
        if rid:
            owner_headers = {
                "x-ecp-user-id": QUERIES[0]["user_context"]["user_id"],
                "x-ecp-department": QUERIES[0]["user_context"]["department"],
                "x-ecp-role": QUERIES[0]["user_context"]["role"],
            }
            fb = httpx.post(
                f"{BASE}/api/v1/feedback",
                json={"resolution_id": rid, "feedback": "accepted"},
                headers=owner_headers,
            )
            print(f"  Feedback recorded for {rid}: {fb.json()}")
    except Exception as e:
        print(f"  Feedback error: {e}")

    print("\nDemo complete.")


if __name__ == "__main__":
    main()

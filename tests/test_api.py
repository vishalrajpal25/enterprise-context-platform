from src.config import settings


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "mode" in body


def test_resolve(client):
    r = client.post("/api/v1/resolve", json={"concept": "revenue"})
    assert r.status_code == 200
    body = r.json()
    assert body["resolution_id"] == "rs_test_1"
    assert body["status"] == "complete"


def test_execute_dry_run_when_cube_unconfigured(client, monkeypatch):
    monkeypatch.setattr(settings, "cube_api_url", "")
    r = client.post(
        "/api/v1/execute",
        json={"resolution_id": "rs_demo_1", "parameters": {}},
        headers={"x-ecp-user-id": "demo_user"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["results"]["status"] == "not_configured"
    assert body["provenance"].get("mode") == "dry_run"


def test_provenance(client):
    r = client.get("/api/v1/provenance/rs_demo_1", headers={"x-ecp-user-id": "demo_user"})
    assert r.status_code == 200
    assert r.json()["original_query"] == "APAC revenue"


def test_search_anonymous_blocked_when_required(client, monkeypatch):
    monkeypatch.setattr(settings, "search_require_identity", True)
    r = client.post("/api/v1/search", json={"query": "revenue", "limit": 5})
    assert r.status_code == 200
    assert r.json()["results"] == []


def test_execute_forbidden_for_non_owner(client):
    r = client.post(
        "/api/v1/execute",
        json={"resolution_id": "rs_demo_1", "parameters": {}},
        headers={"x-ecp-user-id": "another_user"},
    )
    assert r.status_code == 403


def test_feedback_forbidden_for_non_owner(client):
    r = client.post(
        "/api/v1/feedback",
        json={"resolution_id": "rs_demo_1", "feedback": "accepted", "correction_details": ""},
        headers={"x-ecp-user-id": "another_user"},
    )
    assert r.status_code == 403


def test_provenance_forbidden_for_non_owner(client):
    r = client.get("/api/v1/provenance/rs_demo_1", headers={"x-ecp-user-id": "another_user"})
    assert r.status_code == 403


def test_search_limit_validation(client):
    r = client.post("/api/v1/search", json={"query": "revenue", "limit": 5000})
    assert r.status_code == 422


def test_api_key_required_when_configured(client, monkeypatch):
    monkeypatch.setattr(settings, "api_key", "secret")
    r = client.post("/api/v1/resolve", json={"concept": "revenue"})
    assert r.status_code == 401

    r2 = client.post(
        "/api/v1/resolve",
        json={"concept": "revenue"},
        headers={"x-ecp-api-key": "secret"},
    )
    assert r2.status_code == 200


def test_health_ready_shape(client):
    r = client.get("/health/ready")
    assert r.status_code in (200, 503)
    body = r.json()
    assert "status" in body
    assert "checks" in body
    assert "graph" in body["checks"]


def test_execute_not_found(client, monkeypatch):
    from unittest.mock import AsyncMock
    import src.main as main

    main.traces.get_session = AsyncMock(return_value=None)
    r = client.post("/api/v1/execute", json={"resolution_id": "missing", "parameters": {}})
    assert r.status_code == 404

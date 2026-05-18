from __future__ import annotations

from fastapi.testclient import TestClient

from nyt_mini_crosswords.app import app


client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["templates"] >= 1


def test_generate_endpoint_accepts_seed() -> None:
    response = client.post(
        "/api/generate",
        json={
            "seed": 123,
            "time_budget_ms": 500,
            "candidate_limit": 48,
            "max_search_nodes": 5_000,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] in {"ok", "timeout"}
    assert payload["seed"] == 123

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


def test_generate_endpoint_returns_clues(monkeypatch) -> None:
    import nyt_mini_crosswords.app as app_module

    def fake_annotate_answers_with_clues(answers):
        updated = [answer.model_copy(update={"clue": f"Clue for {answer.word}"}) for answer in answers]
        return updated, None

    monkeypatch.setattr(app_module, "annotate_answers_with_clues", fake_annotate_answers_with_clues)
    response = client.post(
        "/api/generate",
        json={
            "seed": 48,
            "time_budget_ms": 1_000,
            "candidate_limit": 64,
            "max_search_nodes": 20_000,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["answers"]
    assert all(answer["clue"] for answer in payload["answers"])

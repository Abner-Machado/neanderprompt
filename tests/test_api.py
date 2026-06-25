"""HTTP smoke tests against the FastAPI app (in-memory DB)."""
from __future__ import annotations


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_models_listed(client):
    r = client.get("/models")
    ids = {m["id"] for m in r.json()}
    assert "echo-1" in ids
    assert any(m["provider"] == "deepseek" for m in r.json())


def test_ask_endpoint_heals(client):
    client.post("/knowledge", json={
        "title": "Backend choice",
        "content": (
            "FastAPI was selected as the web layer. It provides async endpoints, "
            "dependency injection, pydantic validation and automatically generated "
            "openapi documentation for every published service across our backend "
            "stack running in production."
        ),
        "tags": ["backend"],
    })
    r = client.post("/rag/ask", json={"query": "Why choose FastAPI framework?"})
    assert r.status_code == 200
    body = r.json()
    assert body["confidence"] >= 0.6
    assert body["healed"] is True


def test_decisions_endpoint(client):
    client.post("/decisions", json={
        "question": "Why FastAPI?", "choice": "FastAPI",
        "rationale": "async + docs", "alternatives": ["Node"],
    })
    r = client.get("/decisions")
    assert r.status_code == 200
    assert r.json()[0]["choice"] == "FastAPI"

from __future__ import annotations

from fastapi.testclient import TestClient

from ruffyt.app import app

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_echo_endpoint() -> None:
    payload = {"message": "hello world"}
    response = client.post("/echo", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "hello world"

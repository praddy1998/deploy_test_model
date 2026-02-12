"""Tests 1-2: /healthz and /readyz endpoints."""


def test_healthz_returns_200(client):
    """Test 1: /healthz returns 200."""
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_readyz_returns_200_when_model_loaded(client):
    """Test 2: /readyz returns 200 when model is loaded."""
    response = client.get("/readyz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"

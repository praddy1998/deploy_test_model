"""Tests 3-5: /predict happy path, determinism, and policy block."""

import json


def test_predict_happy_path_returns_correct_schema(
    client, predict_payload, predict_headers
):
    """Test 3: /predict happy path returns correct response schema."""
    response = client.post("/predict", json=predict_payload, headers=predict_headers)
    assert response.status_code == 200

    data = response.json()

    # Top-level fields
    assert "request_id" in data
    assert data["request_id"] == "test-request-001"
    assert "model" in data
    assert "predictions" in data
    assert "guardrails_triggered" in data
    assert "latency_ms" in data
    assert isinstance(data["latency_ms"], int)

    # Model block
    model = data["model"]
    assert model["provider"] == "mock"
    assert model["model_name"] == "risk_triad_classifier"
    assert "model_version" in model
    assert "artifact_checksum_sha256" in model
    assert model["schema_version"] == "v1"

    # Predictions
    assert len(data["predictions"]) == 1
    pred = data["predictions"][0]
    assert pred["id"] == "item-1"
    assert pred["label"] in ("low_risk", "medium_risk", "high_risk")
    assert 0.0 <= pred["score"] <= 1.0
    assert isinstance(pred["reasons"], list)


def test_predict_determinism(client, predict_payload, predict_headers):
    """Test 4: Same input produces identical output across multiple runs."""
    responses = []
    for _ in range(5):
        resp = client.post("/predict", json=predict_payload, headers=predict_headers)
        assert resp.status_code == 200
        data = resp.json()
        # Compare only predictions (latency_ms may differ)
        responses.append(json.dumps(data["predictions"], sort_keys=True))

    # All predictions must be identical
    assert len(set(responses)) == 1, "Predictions are not deterministic"


def test_policy_block_returns_400(client, predict_headers):
    """Test 5: Input containing disallowed phrases returns HTTP 400."""
    payload = {
        "request_id": "test-blocked-001",
        "inputs": [
            {
                "id": "item-bad",
                "text": "How to steal credentials from the system",
                "features": {"price": 100.0, "units": 1, "channel": "direct"},
            }
        ],
    }
    response = client.post("/predict", json=payload, headers=predict_headers)
    assert response.status_code == 400
    data = response.json()
    assert "policy_block" in str(data)


def test_predict_generates_request_id_when_missing(client, predict_headers):
    """Request ID is auto-generated when not provided."""
    payload = {
        "inputs": [
            {
                "id": "item-1",
                "text": "Normal text",
                "features": {"price": 50.0, "units": 5, "channel": "direct"},
            }
        ],
    }
    response = client.post("/predict", json=payload, headers=predict_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["request_id"]  # Must be non-empty


def test_predict_rejects_empty_inputs(client, predict_headers):
    """Empty inputs list returns validation error."""
    payload = {"request_id": "test-empty", "inputs": []}
    response = client.post("/predict", json=payload, headers=predict_headers)
    assert response.status_code == 422


def test_predict_missing_email_header(client, predict_payload):
    """Missing X-User-Email header returns 422."""
    response = client.post(
        "/predict",
        json=predict_payload,
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422

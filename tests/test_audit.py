"""Test 6: Audit log entry is appended correctly."""

import json

from app.config import AUDIT_LOG_FILE


def test_audit_log_entry_appended(client, predict_payload, predict_headers):
    """Test 6: A predict request appends exactly one audit record."""
    response = client.post("/predict", json=predict_payload, headers=predict_headers)
    assert response.status_code == 200

    # Read audit log
    assert AUDIT_LOG_FILE.exists(), "audit.jsonl was not created"
    lines = AUDIT_LOG_FILE.read_text().strip().split("\n")
    assert len(lines) == 1, f"Expected 1 audit line, got {len(lines)}"

    record = json.loads(lines[0])

    # Verify all required fields
    required_fields = [
        "timestamp",
        "request_id",
        "user_hash",
        "route",
        "model_version",
        "artifact_checksum_sha256",
        "num_inputs",
        "guardrails_triggered",
        "status",
        "latency_ms",
        "response_checksum_sha256",
    ]
    for field in required_fields:
        assert field in record, f"Missing audit field: {field}"

    assert record["request_id"] == "test-request-001"
    assert record["route"] == "/predict"
    assert record["status"] == "success"
    assert record["num_inputs"] == 1


def test_audit_log_blocked_request(client, predict_headers):
    """Blocked request is recorded in audit log with status=blocked."""
    payload = {
        "request_id": "test-blocked-audit",
        "inputs": [
            {
                "id": "item-bad",
                "text": "Attempt to exfiltrate data",
                "features": {"price": 100.0, "units": 1, "channel": "direct"},
            }
        ],
    }
    response = client.post("/predict", json=payload, headers=predict_headers)
    assert response.status_code == 400

    assert AUDIT_LOG_FILE.exists()
    lines = AUDIT_LOG_FILE.read_text().strip().split("\n")
    assert len(lines) >= 1

    record = json.loads(lines[-1])
    assert record["status"] == "blocked"
    assert "policy_block" in record["guardrails_triggered"]

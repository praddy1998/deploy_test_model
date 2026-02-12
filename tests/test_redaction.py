"""Test 7: PII and token redaction."""

import json

from app.config import AUDIT_LOG_FILE
from app.guardrails.identity import hash_email
from app.guardrails.redaction import redact_pii


def test_email_redaction():
    """Emails are redacted from text."""
    text = "Contact user@example.com for details"
    redacted = redact_pii(text)
    assert "user@example.com" not in redacted
    assert "[EMAIL_REDACTED]" in redacted


def test_token_redaction():
    """Token-like strings are redacted."""
    text = "Use key sk_test_1234567890abcdefghijklmnopqrstuvwxyz"
    redacted = redact_pii(text)
    assert "sk_test_1234567890abcdefghijklmnopqrstuvwxyz" not in redacted
    assert "[TOKEN_REDACTED]" in redacted


def test_email_hash_case_insensitive():
    """Email hashing is case-insensitive and whitespace-trimmed."""
    h1 = hash_email("User@Example.COM")
    h2 = hash_email("user@example.com")
    h3 = hash_email("  user@example.com  ")
    assert h1 == h2
    assert h2 == h3


def test_audit_log_contains_no_raw_email(
    client, predict_payload, predict_headers
):
    """Test 7: Audit log contains hashed email, never raw email."""
    response = client.post("/predict", json=predict_payload, headers=predict_headers)
    assert response.status_code == 200

    audit_content = AUDIT_LOG_FILE.read_text()
    assert "testuser@example.com" not in audit_content

    record = json.loads(audit_content.strip().split("\n")[0])
    expected_hash = hash_email("testuser@example.com")
    assert record["user_hash"] == expected_hash

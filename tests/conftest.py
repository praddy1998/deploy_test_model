"""Shared test fixtures."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config import AUDIT_LOG_DIR, AUDIT_LOG_FILE


@pytest.fixture(scope="session")
def client():
    """Create a TestClient for the FastAPI app."""
    from app.main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def clean_audit_log():
    """Clear the audit log before each test."""
    AUDIT_LOG_DIR.mkdir(parents=True, exist_ok=True)
    if AUDIT_LOG_FILE.exists():
        AUDIT_LOG_FILE.unlink()
    yield


@pytest.fixture()
def predict_payload():
    """Standard valid prediction payload."""
    return {
        "request_id": "test-request-001",
        "inputs": [
            {
                "id": "item-1",
                "text": "Normal transaction for review",
                "features": {
                    "price": 250.0,
                    "units": 10,
                    "channel": "amazon",
                },
            }
        ],
    }


@pytest.fixture()
def predict_headers():
    """Standard headers with user email."""
    return {
        "Content-Type": "application/json",
        "X-User-Email": "testuser@example.com",
    }

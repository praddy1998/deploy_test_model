"""Append-only JSONL audit logger."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.observability.metrics import audit_write_errors_total

logger = logging.getLogger(__name__)


def write_audit_record(
    audit_file: Path,
    *,
    request_id: str,
    user_hash: str,
    route: str,
    model_version: str,
    artifact_checksum_sha256: str,
    num_inputs: int,
    guardrails_triggered: list[str],
    status: str,
    latency_ms: int,
    response_checksum_sha256: str,
) -> None:
    """Append a single JSON audit record to the audit log file."""
    record: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request_id": request_id,
        "user_hash": user_hash,
        "route": route,
        "model_version": model_version,
        "artifact_checksum_sha256": artifact_checksum_sha256,
        "num_inputs": num_inputs,
        "guardrails_triggered": guardrails_triggered,
        "status": status,
        "latency_ms": latency_ms,
        "response_checksum_sha256": response_checksum_sha256,
    }

    try:
        with open(audit_file, "a") as f:
            f.write(json.dumps(record, separators=(",", ":")) + "\n")
    except Exception:
        audit_write_errors_total.inc()
        logger.exception("Failed to write audit record")

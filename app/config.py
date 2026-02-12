"""Application configuration."""

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_ARTIFACTS_DIR = Path(
    os.getenv("MODEL_DIR", str(BASE_DIR / "model_artifacts"))
)

AUDIT_LOG_DIR = Path(
    os.getenv("AUDIT_LOG_DIR", str(BASE_DIR / "audit_logs"))
)

AUDIT_LOG_FILE = AUDIT_LOG_DIR / "audit.jsonl"

# Ensure audit log directory exists
AUDIT_LOG_DIR.mkdir(parents=True, exist_ok=True)

"""Pydantic request/response schemas for the inference API."""

from __future__ import annotations

import uuid
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


# ── Request schemas ──────────────────────────────────────────────────

class Features(BaseModel):
    price: float = 0.0
    units: int = 0
    channel: str = "direct"


class InputItem(BaseModel):
    id: str
    text: str
    features: Optional[Features] = None

    @field_validator("text")
    @classmethod
    def text_must_be_non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("text must be non-empty")
        return v


class PredictRequest(BaseModel):
    request_id: Optional[str] = None
    inputs: list[InputItem] = Field(..., min_length=1, max_length=50)


# ── Response schemas ─────────────────────────────────────────────────

class ModelBlock(BaseModel):
    provider: str = "mock"
    model_name: str = "risk_triad_classifier"
    model_version: str
    artifact_checksum_sha256: str
    schema_version: str = "v1"


class Prediction(BaseModel):
    id: str
    label: str
    score: float
    reasons: list[str]


class PredictResponse(BaseModel):
    request_id: str
    model: ModelBlock
    predictions: list[Prediction]
    guardrails_triggered: list[str] = Field(default_factory=list)
    latency_ms: int


# ── Model metadata ───────────────────────────────────────────────────

class ModelInfo(BaseModel):
    provider: str = "mock"
    model_name: str = "risk_triad_classifier"
    model_version: str
    created_at: str
    artifact_path: str
    artifact_checksum_sha256: str
    rule_config: dict[str, Any]


# ── Error schema ─────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    request_id: Optional[str] = None
    guardrails_triggered: list[str] = Field(default_factory=list)


# ── Helpers ──────────────────────────────────────────────────────────

def generate_request_id() -> str:
    return str(uuid.uuid4())

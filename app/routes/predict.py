"""POST /predict endpoint."""

from __future__ import annotations

import hashlib
import logging
import time

from fastapi import APIRouter, Header, HTTPException, Request

from app.config import AUDIT_LOG_FILE
from app.guardrails.identity import hash_email
from app.guardrails.policy import check_policy_block
from app.models.loader import ModelRegistry
from app.models.schemas import (
    ErrorResponse,
    ModelBlock,
    Prediction,
    PredictRequest,
    PredictResponse,
    generate_request_id,
)
from app.models.scorer import score_input
from app.observability.audit import write_audit_record
from app.observability.metrics import (
    predict_errors_total,
    predict_requests_total,
)

router = APIRouter()
logger = logging.getLogger(__name__)

_registry: ModelRegistry | None = None


def set_registry(registry: ModelRegistry) -> None:
    global _registry
    _registry = registry


@router.post("/predict", response_model=PredictResponse)
async def predict(
    body: PredictRequest,
    request: Request,
    x_user_email: str = Header(..., alias="X-User-Email"),
) -> PredictResponse | ErrorResponse:
    start = time.monotonic()
    predict_requests_total.inc()

    # Generate or use provided request_id
    request_id = body.request_id or generate_request_id()

    # Hash user identity
    user_hash = hash_email(x_user_email)

    # Check for policy violations
    input_texts = [inp.text for inp in body.inputs]
    if check_policy_block(input_texts):
        latency_ms = int((time.monotonic() - start) * 1000)
        predict_errors_total.inc()

        # Write audit record for blocked request
        write_audit_record(
            AUDIT_LOG_FILE,
            request_id=request_id,
            user_hash=user_hash,
            route="/predict",
            model_version=_registry.active_version if _registry else "unknown",
            artifact_checksum_sha256=_registry.active_checksum if _registry else "",
            num_inputs=len(body.inputs),
            guardrails_triggered=["policy_block"],
            status="blocked",
            latency_ms=latency_ms,
            response_checksum_sha256="",
        )

        raise HTTPException(
            status_code=400,
            detail={
                "error": "policy_block",
                "detail": "Input contains disallowed content",
                "request_id": request_id,
                "guardrails_triggered": ["policy_block"],
            },
        )

    if _registry is None or not _registry.is_loaded or _registry.active_model is None:
        predict_errors_total.inc()
        raise HTTPException(status_code=503, detail="Model not loaded")

    # Score each input
    # Support both "config" (old format) and "rule_config" (new format)
    config = _registry.active_model.get("config") or _registry.active_model.get("rule_config")
    if not config:
        predict_errors_total.inc()
        raise HTTPException(status_code=500, detail="Model config not found")
    
    predictions: list[Prediction] = []
    try:
        for inp in body.inputs:
            features = inp.features
            price = features.price if features else 0.0
            units = features.units if features else 0
            channel = features.channel if features else "direct"

            score, label, reasons = score_input(
                text=inp.text,
                price=price,
                units=units,
                channel=channel,
                config=config,
            )

            predictions.append(
                Prediction(
                    id=inp.id,
                    label=label,
                    score=score,
                    reasons=reasons,
                )
            )
    except Exception as exc:
        predict_errors_total.inc()
        logger.exception("Scoring error")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    latency_ms = int((time.monotonic() - start) * 1000)

    response = PredictResponse(
        request_id=request_id,
        model=ModelBlock(
            model_version=_registry.active_version,
            artifact_checksum_sha256=_registry.active_checksum,
        ),
        predictions=predictions,
        guardrails_triggered=[],
        latency_ms=latency_ms,
    )

    # Compute response checksum for audit
    response_json = response.model_dump_json()
    response_checksum = hashlib.sha256(response_json.encode()).hexdigest()

    # Write audit record
    write_audit_record(
        AUDIT_LOG_FILE,
        request_id=request_id,
        user_hash=user_hash,
        route="/predict",
        model_version=_registry.active_version,
        artifact_checksum_sha256=_registry.active_checksum,
        num_inputs=len(body.inputs),
        guardrails_triggered=[],
        status="success",
        latency_ms=latency_ms,
        response_checksum_sha256=response_checksum,
    )

    logger.info(
        "Prediction served",
        extra={
            "request_id": request_id,
            "model_version": _registry.active_version,
            "num_inputs": len(body.inputs),
            "latency_ms": latency_ms,
        },
    )

    return response

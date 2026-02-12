"""FastAPI application entry point with lifespan and middleware."""

from __future__ import annotations

import logging
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.config import MODEL_ARTIFACTS_DIR
from app.models.loader import ModelRegistry
from app.observability.logging import setup_logging
from app.observability.metrics import http_request_latency_ms, http_requests_total
from app.routes import health, metrics, model, predict

logger = logging.getLogger(__name__)

# Global model registry
registry = ModelRegistry(MODEL_ARTIFACTS_DIR)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan: load model on startup."""
    setup_logging()
    logger.info("Starting ML Inference API")
    try:
        registry.load()
        logger.info(
            "Model loaded successfully",
            extra={"model_version": registry.active_version},
        )
    except Exception:
        logger.exception("Failed to load model on startup")
    yield
    logger.info("Shutting down ML Inference API")


app = FastAPI(
    title="Mock ML Inference API",
    version="1.0.0",
    lifespan=lifespan,
)

# Wire registry into route modules
health.set_registry(registry)
model.set_registry(registry)
predict.set_registry(registry)

# Register routers
app.include_router(health.router)
app.include_router(model.router)
app.include_router(predict.router)
app.include_router(metrics.router)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):  # type: ignore[no-untyped-def]
    """Track request latency and count for all routes."""
    start = time.monotonic()
    response = await call_next(request)
    elapsed_ms = (time.monotonic() - start) * 1000

    route = request.url.path
    method = request.method
    status = str(response.status_code)

    http_requests_total.labels(route=route, method=method, status=status).inc()
    http_request_latency_ms.labels(route=route).observe(elapsed_ms)

    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Consistent JSON error responses."""
    logger.exception("Unhandled exception")
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "detail": str(exc),
        },
    )

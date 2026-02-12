"""Health and readiness endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Response

from app.models.loader import ModelRegistry

router = APIRouter()

# Will be set by main.py at startup
_registry: ModelRegistry | None = None


def set_registry(registry: ModelRegistry) -> None:
    global _registry
    _registry = registry


@router.get("/healthz")
async def healthz() -> dict[str, str]:
    """Liveness probe -- always returns 200."""
    return {"status": "ok"}


@router.get("/readyz")
async def readyz(response: Response) -> dict[str, str]:
    """Readiness probe -- 200 if model loaded, else 503."""
    if _registry is not None and _registry.is_loaded:
        return {"status": "ready"}
    response.status_code = 503
    return {"status": "not_ready"}

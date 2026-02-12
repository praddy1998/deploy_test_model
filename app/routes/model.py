"""Model metadata and reload endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter

from app.models.loader import ModelRegistry
from app.models.schemas import ModelInfo

router = APIRouter()
logger = logging.getLogger(__name__)

_registry: ModelRegistry | None = None


def set_registry(registry: ModelRegistry) -> None:
    global _registry
    _registry = registry


@router.get("/model", response_model=ModelInfo)
async def get_model() -> ModelInfo:
    """Return metadata for the currently loaded model."""
    if _registry is None or not _registry.is_loaded:
        raise RuntimeError("No model loaded")
    info = _registry.get_model_info()
    return ModelInfo(**info)


@router.post("/model/reload")
async def reload_model() -> dict[str, str]:
    """Reload model manifest and switch active model without restart."""
    if _registry is None:
        raise RuntimeError("Registry not initialized")
    _registry.reload()
    logger.info(
        "Model reloaded via API",
        extra={"model_version": _registry.active_version},
    )
    return {
        "status": "reloaded",
        "model_version": _registry.active_version,
    }

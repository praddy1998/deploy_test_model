"""Model artifact loader with checksum validation and version management."""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def compute_checksum(filepath: Path) -> str:
    """Compute SHA-256 hex digest of a file."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def load_json(filepath: Path) -> dict[str, Any]:
    """Load and parse a JSON file."""
    with open(filepath) as f:
        return json.load(f)


class ModelRegistry:
    """Manages model artifact loading, validation, and hot-reload."""

    def __init__(self, artifacts_dir: Path) -> None:
        self.artifacts_dir = artifacts_dir
        self.manifest: dict[str, Any] = {}
        self.checksums: dict[str, str] = {}
        self.active_model: dict[str, Any] | None = None
        self.active_version: str = ""
        self.active_checksum: str = ""
        self.active_artifact_path: str = ""
        self._loaded = False

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def load(self) -> None:
        """Load the manifest, checksums, and the active model artifact."""
        manifest_path = self.artifacts_dir / "model_manifest.json"
        checksums_path = self.artifacts_dir / "CHECKSUMS.json"

        self.manifest = load_json(manifest_path)
        self.checksums = load_json(checksums_path)

        active_version = self.manifest["active_model_version"]
        self._load_version(active_version)
        logger.info(
            "Model registry loaded",
            extra={"model_version": self.active_version},
        )

    def _load_version(self, version: str) -> None:
        """Load a specific model version by name."""
        # Support both old format (versions) and new format (available_versions + paths)
        versions = self.manifest.get("versions")
        if versions:
            # Old format: {"versions": {"1.0.0": {"artifact_file": "model_v1.json"}}}
            if version not in versions:
                raise ValueError(f"Model version {version} not found in manifest")
            artifact_file = versions[version]["artifact_file"]
        else:
            # New format: {"available_versions": [...], "paths": {"1.0.0": "model_v1.json"}}
            available_versions = self.manifest.get("available_versions", [])
            paths = self.manifest.get("paths", {})
            if version not in available_versions:
                raise ValueError(f"Model version {version} not found in manifest")
            artifact_file = paths[version]
        artifact_path = self.artifacts_dir / artifact_file

        # Compute and validate checksum
        actual_checksum = compute_checksum(artifact_path)
        expected_checksum = self.checksums.get(artifact_file)
        if expected_checksum and actual_checksum != expected_checksum:
            raise ValueError(
                f"Checksum mismatch for {artifact_file}: "
                f"expected {expected_checksum}, got {actual_checksum}"
            )

        self.active_model = load_json(artifact_path)
        self.active_version = version
        self.active_checksum = actual_checksum
        self.active_artifact_path = str(artifact_path)
        self._loaded = True

    def reload(self) -> None:
        """Reload the manifest and switch to the (possibly new) active version."""
        manifest_path = self.artifacts_dir / "model_manifest.json"
        self.manifest = load_json(manifest_path)
        new_version = self.manifest["active_model_version"]
        self._load_version(new_version)
        logger.info(
            "Model reloaded",
            extra={"model_version": self.active_version},
        )

    def get_model_info(self) -> dict[str, Any]:
        """Return metadata about the currently loaded model."""
        if not self._loaded or self.active_model is None:
            raise RuntimeError("No model loaded")
        return {
            "provider": self.active_model.get("provider", "mock"),
            "model_name": self.active_model.get("model_name", "risk_triad_classifier"),
            "model_version": self.active_version,
            "created_at": self.active_model.get("created_at", ""),
            "artifact_path": self.active_artifact_path,
            "artifact_checksum_sha256": self.active_checksum,
            "rule_config": self.active_model.get("rule_config") or self.active_model.get("config", {}),
        }

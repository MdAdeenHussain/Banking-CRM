"""Model registry service for versioning + artifact paths."""

# ==========================================
# SECTION: Imports
# ==========================================
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

from flask import current_app

from app.extensions import db
from app.models.model_registry import ModelRegistryEntry


class ModelRegistryService:
    """Handles model version registration and lookup."""

    # ==========================================
    # SECTION: Training Logic
    # ==========================================
    @staticmethod
    def register_model(
        *,
        tenant_id: int,
        model_name: str,
        file_path: str,
        accuracy: float | None,
        precision: float | None,
        recall: float | None,
        version: str | None = None,
    ) -> ModelRegistryEntry:
        """Insert a model registry record into database."""
        resolved_version = version or ModelRegistryService.next_version(
            model_name=model_name,
            tenant_id=tenant_id,
        )

        entry = ModelRegistryEntry(
            tenant_id=tenant_id,
            model_name=model_name,
            version=resolved_version,
            trained_at=datetime.now(timezone.utc),
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            file_path=file_path,
        )
        db.session.add(entry)
        db.session.commit()
        return entry

    @staticmethod
    def next_version(*, model_name: str, tenant_id: int) -> str:
        """Return next semantic-like version as v<major>.<minor>."""
        latest = ModelRegistryService.get_latest_entry(model_name=model_name, tenant_id=tenant_id)
        if latest is None:
            return "v1.0"

        value = latest.version.lstrip("v")
        major, _, minor = value.partition(".")
        try:
            major_i = int(major or 1)
            minor_i = int(minor or 0) + 1
        except ValueError:
            return "v1.0"
        return f"v{major_i}.{minor_i}"

    # ==========================================
    # SECTION: Prediction Logic
    # ==========================================
    @staticmethod
    def get_latest_entry(*, model_name: str, tenant_id: int) -> ModelRegistryEntry | None:
        """Fetch latest registry row for model + tenant."""
        return (
            ModelRegistryEntry.query.filter_by(
                tenant_id=tenant_id,
                model_name=model_name,
                is_deleted=False,
            )
            .order_by(ModelRegistryEntry.created_at.desc())
            .first()
        )

    @staticmethod
    def get_latest_model_path(*, model_name: str, tenant_id: int) -> str | None:
        """Return file path for latest registered model."""
        latest = ModelRegistryService.get_latest_entry(model_name=model_name, tenant_id=tenant_id)
        return latest.file_path if latest else None

    # ==========================================
    # SECTION: Serialization
    # ==========================================
    @staticmethod
    def build_artifact_path(*, model_name: str, tenant_id: int, version: str) -> str:
        """Build deterministic on-disk path for joblib artifact."""
        model_dir = current_app.config.get("AI_MODEL_DIR", "model_store")
        target_dir = Path(model_dir) / str(tenant_id) / model_name
        target_dir.mkdir(parents=True, exist_ok=True)
        return str(target_dir / f"{model_name}_{version}.joblib")

    @staticmethod
    def ensure_model_dir() -> str:
        """Ensure model root exists and return its path."""
        model_dir = current_app.config.get("AI_MODEL_DIR", "model_store")
        os.makedirs(model_dir, exist_ok=True)
        return model_dir

"""ML model registry table for version tracking and metrics."""

# =====================================
# SECTION: Imports
# =====================================
from app.extensions import db
from app.models.base import BaseModel


# =====================================
# SECTION: Model Definition
# =====================================
class ModelRegistryEntry(BaseModel):
    """Stores training metadata for serialized ML models."""

    __tablename__ = "model_registry"

    tenant_id = db.Column(db.BigInteger, db.ForeignKey("tenants.id"), nullable=False, index=True)
    model_name = db.Column(db.String(120), nullable=False, index=True)
    version = db.Column(db.String(40), nullable=False)
    trained_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)
    accuracy = db.Column(db.Float, nullable=True)
    precision = db.Column(db.Float, nullable=True)
    recall = db.Column(db.Float, nullable=True)
    file_path = db.Column(db.String(1000), nullable=False)

    __table_args__ = (
        db.UniqueConstraint("tenant_id", "model_name", "version", name="uq_model_registry_tenant_model_version"),
    )

    # =====================================
    # SECTION: Helper Methods
    # =====================================
    def to_dict(self) -> dict:
        """Serialize registry entry for API responses."""
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "model_name": self.model_name,
            "version": self.version,
            "trained_at": self.trained_at.isoformat() if self.trained_at else None,
            "accuracy": self.accuracy,
            "precision": self.precision,
            "recall": self.recall,
            "file_path": self.file_path,
        }

"""AI/ML package exports."""

# ==========================================
# SECTION: Imports
# ==========================================
from app.ai_ml.routes import ai_ml_bp


# ==========================================
# SECTION: Training Logic
# ==========================================
# Training entry points are in app.ai_ml.training_pipeline.


# ==========================================
# SECTION: Prediction Logic
# ==========================================
# Inference entry points are in app.ai_ml.inference_service.


# ==========================================
# SECTION: Serialization
# ==========================================
# Model registry and artifact handling are in app.ai_ml.model_registry.

__all__ = ["ai_ml_bp"]

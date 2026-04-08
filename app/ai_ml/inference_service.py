"""Inference service for lead scoring, eligibility, and lender ranking."""

# ==========================================
# SECTION: Imports
# ==========================================
from __future__ import annotations

from typing import Any

import pandas as pd

from app.ai_ml.eligibility_model import EligibilityModel
from app.ai_ml.explainability import ExplainabilityService
from app.ai_ml.feature_engineering import FeatureEngineering
from app.ai_ml.lead_scoring_model import LeadScoringModel
from app.ai_ml.lender_ranking_model import LenderRankingModel
from app.ai_ml.model_registry import ModelRegistryService
from app.ai_ml.training_pipeline import (
    train_eligibility_model,
    train_lead_model,
    train_lender_model,
)
from app.models.lender import Lender


class InferenceService:
    """Unified inference interface for all classical ML engines."""

    def __init__(self, tenant_id: int) -> None:
        self.tenant_id = tenant_id

    # ==========================================
    # SECTION: Training Logic
    # ==========================================
    def _ensure_lead_model(self) -> LeadScoringModel:
        """Load latest lead model or trigger training if absent."""
        path = ModelRegistryService.get_latest_model_path(
            model_name="lead_scoring",
            tenant_id=self.tenant_id,
        )
        if path is None:
            train_lead_model(self.tenant_id)
            path = ModelRegistryService.get_latest_model_path(
                model_name="lead_scoring",
                tenant_id=self.tenant_id,
            )
        if path is None:
            raise RuntimeError("Lead scoring model artifact unavailable after training.")
        return LeadScoringModel.load_model(path)

    def _ensure_eligibility_model(self) -> EligibilityModel:
        """Load latest eligibility model or trigger training if absent."""
        path = ModelRegistryService.get_latest_model_path(
            model_name="eligibility",
            tenant_id=self.tenant_id,
        )
        if path is None:
            train_eligibility_model(self.tenant_id)
            path = ModelRegistryService.get_latest_model_path(
                model_name="eligibility",
                tenant_id=self.tenant_id,
            )
        if path is None:
            raise RuntimeError("Eligibility model artifact unavailable after training.")
        return EligibilityModel.load_model(path)

    def _ensure_lender_model(self) -> LenderRankingModel:
        """Load latest lender ranking model or trigger training if absent."""
        path = ModelRegistryService.get_latest_model_path(
            model_name="lender_ranking",
            tenant_id=self.tenant_id,
        )
        if path is None:
            train_lender_model(self.tenant_id)
            path = ModelRegistryService.get_latest_model_path(
                model_name="lender_ranking",
                tenant_id=self.tenant_id,
            )
        if path is None:
            raise RuntimeError("Lender ranking model artifact unavailable after training.")
        return LenderRankingModel.load_model(path)

    # ==========================================
    # SECTION: Prediction Logic
    # ==========================================
    def predict_lead_score(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Predict lead conversion score + explainability payload."""
        model = self._ensure_lead_model()

        feature_df = FeatureEngineering.prepare_lead_features(payload)
        result = model.predict_score(feature_df)[0]
        explanation = ExplainabilityService.explain_lead(feature_df.iloc[0], result["score"], result["confidence"])

        return {
            **result,
            "reasons": explanation["reasons"],
            "generated_by": explanation["generated_by"],
        }

    def predict_eligibility(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Predict approval probability and eligibility amount."""
        model = self._ensure_eligibility_model()

        feature_df = FeatureEngineering.prepare_eligibility_features(payload)
        result = model.predict_approval_probability(feature_df)[0]
        explanation = ExplainabilityService.explain_eligibility(
            feature_df.iloc[0],
            result["approval_probability"],
            result["confidence"],
        )

        return {
            **result,
            "reasons": explanation["reasons"],
            "generated_by": explanation["generated_by"],
        }

    def recommend_lenders(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Rank lenders and return top-3 recommendations."""
        model = self._ensure_lender_model()
        lender_rows = payload.get("lenders") or self._default_lenders_from_db()

        ranked_rows = model.rank_lenders(lender_rows)
        top_3 = model.recommend_top_3(ranked_rows)
        explanation = ExplainabilityService.explain_lender_ranking(ranked_rows)

        return {
            "top_3": top_3,
            "ranked_count": len(ranked_rows),
            "score": explanation["score"],
            "confidence": explanation["confidence"],
            "reasons": explanation["reasons"],
            "generated_by": explanation["generated_by"],
            "model_version": model.model_version,
        }

    # ==========================================
    # SECTION: Serialization
    # ==========================================
    def _default_lenders_from_db(self) -> list[dict[str, Any]]:
        """Provide lender rows from DB when request omits lender list."""
        lenders = Lender.query.filter_by(tenant_id=self.tenant_id, is_deleted=False).all()

        rows = []
        for lender in lenders:
            rows.append(
                {
                    "bank": lender.lender_name,
                    "approval_probability": float(lender.approval_percentage or 50.0),
                    "interest_rate": float(lender.interest_rate or 12.0),
                    "avg_disbursal_days": float(lender.speed_score or 5.0),
                    "documentation_ease": float(lender.ease_score or 50.0),
                    "historical_approval_rate": float(lender.approval_percentage or 50.0),
                }
            )

        if rows:
            return rows

        # Cold-start fallback to keep API functional.
        fallback = pd.DataFrame(
            [
                {"bank": "HDFC", "approval_probability": 86, "interest_rate": 10.5, "avg_disbursal_days": 3, "documentation_ease": 85, "historical_approval_rate": 82},
                {"bank": "ICICI", "approval_probability": 80, "interest_rate": 10.8, "avg_disbursal_days": 4, "documentation_ease": 78, "historical_approval_rate": 77},
                {"bank": "SBI", "approval_probability": 75, "interest_rate": 9.9, "avg_disbursal_days": 6, "documentation_ease": 70, "historical_approval_rate": 74},
            ]
        )
        return fallback.to_dict(orient="records")

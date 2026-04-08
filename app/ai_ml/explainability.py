"""Model explainability helpers for classical ML predictions."""

# ==========================================
# SECTION: Imports
# ==========================================
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


class ExplainabilityService:
    """Generates human-readable reasons from feature values/importances."""

    # ==========================================
    # SECTION: Training Logic
    # ==========================================
    @staticmethod
    def summarize_feature_importance(feature_importance: dict[str, float], top_n: int = 3) -> list[str]:
        """Convert feature importance dictionary to short reason strings."""
        if not feature_importance:
            return ["insufficient historical importance data"]

        ranked = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:top_n]
        return [f"{name} influence={round(weight, 3)}" for name, weight in ranked]

    # ==========================================
    # SECTION: Prediction Logic
    # ==========================================
    @staticmethod
    def explain_lead(payload_row: pd.Series | dict[str, Any], score: float, confidence: float) -> dict[str, Any]:
        """Return lead-score explainability payload."""
        row = payload_row if isinstance(payload_row, dict) else payload_row.to_dict()
        reasons: list[str] = []

        if float(row.get("credit_score", 0) or 0) >= 730:
            reasons.append("strong bureau score")
        if str(row.get("income_band", "")).lower() in {"high", "upper"}:
            reasons.append("high income band")
        if float(row.get("time_to_first_contact", 999) or 999) <= 30:
            reasons.append("quick first-contact turnaround")
        if float(row.get("followup_count", 0) or 0) >= 2:
            reasons.append("healthy follow-up cadence")

        if not reasons:
            reasons = ["limited positive conversion signals"]

        return {
            "score": int(round(score)),
            "confidence": round(float(confidence), 4),
            "reasons": reasons,
            "generated_by": "ml_model",
        }

    @staticmethod
    def explain_eligibility(payload_row: pd.Series | dict[str, Any], probability: float, confidence: float) -> dict[str, Any]:
        """Return eligibility explainability payload."""
        row = payload_row if isinstance(payload_row, dict) else payload_row.to_dict()
        reasons: list[str] = []

        if float(row.get("foir", 100) or 100) <= 45:
            reasons.append("low FOIR")
        if float(row.get("dti", 100) or 100) <= 40:
            reasons.append("healthy DTI")
        if float(row.get("credit_score", 0) or 0) >= 700:
            reasons.append("strong bureau score")
        if float(row.get("monthly_income", 0) or 0) >= 50000:
            reasons.append("stable monthly income")

        if not reasons:
            reasons = ["financial ratios require closer review"]

        return {
            "approval_probability": round(float(probability), 4),
            "confidence": round(float(confidence), 4),
            "reasons": reasons,
            "generated_by": "ml_model",
        }

    @staticmethod
    def explain_lender_ranking(ranked_rows: list[dict[str, Any]]) -> dict[str, Any]:
        """Return summary explanation for lender ranking output."""
        if not ranked_rows:
            return {
                "score": 0,
                "confidence": 0.0,
                "reasons": ["no lender rows available"],
                "generated_by": "ml_model",
            }

        top = ranked_rows[0]
        reasons = [
            "high approval probability",
            "competitive interest rate",
            "faster disbursal turnaround",
        ]

        return {
            "score": int(round(float(top.get("score", 0)))),
            "confidence": round(float(np.clip(top.get("score", 0) / 100.0, 0.0, 1.0)), 4),
            "reasons": reasons,
            "generated_by": "ml_model",
        }

    # ==========================================
    # SECTION: Serialization
    # ==========================================
    # Explainability outputs are JSON payloads; no model files stored here.

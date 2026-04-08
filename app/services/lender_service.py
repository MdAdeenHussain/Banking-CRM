"""Lender comparison and ranking engine."""

# ======================================
# SECTION: Imports
# ======================================
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from app.models.lender import Lender


# ======================================
# SECTION: Core Service Logic
# ======================================
@dataclass
class LenderScoreWeights:
    """Weights used in lender ranking formula.

    Score = 0.4A + 0.2R + 0.2S + 0.2D
    """

    approval: float = 0.4
    rate: float = 0.2
    speed: float = 0.2
    documentation: float = 0.2


class LenderService:
    """Compares lenders and returns ranked shortlist."""

    def __init__(self, tenant_id: int) -> None:
        self.tenant_id = tenant_id

    def compare_lenders(self, lenders_data: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
        """Prepare normalized lender comparison table.

        If `lenders_data` is None, lender rows are loaded from DB.
        """
        rows = lenders_data or self._load_lenders_from_db()
        if not rows:
            return []

        df = pd.DataFrame(rows)
        df = self._normalize_comparison_fields(df)

        return df.to_dict(orient="records")

    def rank_lenders(
        self,
        lenders_data: list[dict[str, Any]] | None = None,
        weights: LenderScoreWeights | None = None,
    ) -> list[dict[str, Any]]:
        """Rank lenders using weighted formula and return descending sort."""
        rows = lenders_data or self._load_lenders_from_db()
        if not rows:
            return []

        w = weights or LenderScoreWeights()

        df = pd.DataFrame(rows)
        df = self._normalize_comparison_fields(df)

        # Score = 0.4A + 0.2R + 0.2S + 0.2D
        df["weighted_score"] = (
            (w.approval * df["approval_probability"]) +
            (w.rate * df["rate_competitiveness"]) +
            (w.speed * df["speed_score_norm"]) +
            (w.documentation * df["documentation_ease_norm"])
        )

        ranked = df.sort_values(by="weighted_score", ascending=False)
        return ranked.to_dict(orient="records")

    def approval_probability(
        self,
        *,
        credit_score: float,
        foir_percent: float,
        lender_base_approval: float,
    ) -> float:
        """Estimate approval probability with simple deterministic adjustments.

        This is a non-ML placeholder formula using rule-based adjustments.
        """
        score_component = np.clip((credit_score - 650) / 200, 0, 1)
        foir_penalty = np.clip((foir_percent - 45) / 25, 0, 1)

        probability = (0.6 * lender_base_approval / 100.0) + (0.4 * score_component) - (0.25 * foir_penalty)
        return float(np.clip(probability * 100, 1, 99))

    # ======================================
    # SECTION: Helper Functions
    # ======================================
    def _load_lenders_from_db(self) -> list[dict[str, Any]]:
        """Load tenant-scoped lender records from database."""
        lenders = Lender.query.filter_by(tenant_id=self.tenant_id, is_deleted=False).all()
        result: list[dict[str, Any]] = []

        for lender in lenders:
            # Map model fields to comparison schema.
            result.append(
                {
                    "bank_name": lender.lender_name,
                    "interest_rate": float(lender.interest_rate) if lender.interest_rate is not None else np.nan,
                    "approval_percent": float(lender.approval_percentage) if lender.approval_percentage is not None else np.nan,
                    "avg_days": float(lender.speed_score) if lender.speed_score is not None else np.nan,
                    "ease_score": float(lender.ease_score) if lender.ease_score is not None else np.nan,
                }
            )
        return result

    def _normalize_comparison_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize lender inputs into 0..100 comparable components."""
        # Ensure required columns exist.
        for column in ["bank_name", "interest_rate", "approval_percent", "avg_days", "ease_score"]:
            if column not in df.columns:
                df[column] = np.nan

        # Fill numeric nulls with median-safe fallback.
        for column in ["interest_rate", "approval_percent", "avg_days", "ease_score"]:
            df[column] = pd.to_numeric(df[column], errors="coerce")
            df[column] = df[column].fillna(df[column].median() if df[column].notna().any() else 0)

        # A = approval probability input directly (0..100 clipped).
        df["approval_probability"] = df["approval_percent"].clip(0, 100)

        # R = rate competitiveness (lower rate should yield higher score).
        max_rate = max(df["interest_rate"].max(), 0.0001)
        min_rate = df["interest_rate"].min()
        if max_rate == min_rate:
            df["rate_competitiveness"] = 100.0
        else:
            df["rate_competitiveness"] = 100 * (max_rate - df["interest_rate"]) / (max_rate - min_rate)

        # S = speed score derived from avg days (lower days = better).
        max_days = max(df["avg_days"].max(), 0.0001)
        min_days = df["avg_days"].min()
        if max_days == min_days:
            df["speed_score_norm"] = 100.0
        else:
            df["speed_score_norm"] = 100 * (max_days - df["avg_days"]) / (max_days - min_days)

        # D = documentation ease normalized from provided ease score.
        df["documentation_ease_norm"] = df["ease_score"].clip(0, 100)

        return df


# ======================================
# SECTION: Calculators
# ======================================
# N/A for this service. Weighted scoring is implemented inline in
# `rank_lenders` for readability.

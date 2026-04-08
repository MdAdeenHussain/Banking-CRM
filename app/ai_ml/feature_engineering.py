"""Feature engineering utilities for classical ML models."""

# ==========================================
# SECTION: Imports
# ==========================================
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


class FeatureEngineering:
    """Transforms raw request/database payloads into model-ready frames."""

    LEAD_FEATURES = [
        "lead_source",
        "loan_type",
        "city_tier",
        "income_band",
        "credit_score",
        "response_time",
        "followup_count",
        "document_upload_speed",
        "campaign_source",
        "agent_history",
        "time_to_first_contact",
    ]

    ELIGIBILITY_FEATURES = [
        "credit_score",
        "monthly_income",
        "foir",
        "dti",
        "ltv",
        "employment_type",
        "loan_amount",
        "loan_type",
        "city_tier",
        "existing_emis",
    ]

    LENDER_FEATURES = [
        "approval_probability",
        "interest_rate",
        "avg_disbursal_days",
        "documentation_ease",
        "historical_approval_rate",
    ]

    # ==========================================
    # SECTION: Training Logic
    # ==========================================
    @classmethod
    def prepare_lead_features(cls, data: Any) -> pd.DataFrame:
        """Prepare lead conversion features for training/inference."""
        df = cls._ensure_dataframe(data)
        df = cls._ensure_columns(df, cls.LEAD_FEATURES)

        categorical = [
            "lead_source",
            "loan_type",
            "city_tier",
            "income_band",
            "campaign_source",
        ]
        numeric = [
            "credit_score",
            "response_time",
            "followup_count",
            "document_upload_speed",
            "agent_history",
            "time_to_first_contact",
        ]

        df[categorical] = df[categorical].fillna("unknown").astype(str)
        for col in numeric:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

        return df[cls.LEAD_FEATURES]

    @classmethod
    def prepare_eligibility_features(cls, data: Any) -> pd.DataFrame:
        """Prepare eligibility model features (FOIR + credit + income)."""
        df = cls._ensure_dataframe(data)
        df = cls._ensure_columns(df, cls.ELIGIBILITY_FEATURES)

        categorical = ["employment_type", "loan_type", "city_tier"]
        numeric = [
            "credit_score",
            "monthly_income",
            "foir",
            "dti",
            "ltv",
            "loan_amount",
            "existing_emis",
        ]

        df[categorical] = df[categorical].fillna("unknown").astype(str)
        for col in numeric:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

        return df[cls.ELIGIBILITY_FEATURES]

    @classmethod
    def prepare_lender_features(cls, data: Any) -> pd.DataFrame:
        """Prepare lender ranking feature matrix."""
        df = cls._ensure_dataframe(data)
        df = cls._ensure_columns(df, cls.LENDER_FEATURES)

        for col in cls.LENDER_FEATURES:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

        return df[cls.LENDER_FEATURES]

    # ==========================================
    # SECTION: Prediction Logic
    # ==========================================
    @staticmethod
    def _ensure_dataframe(data: Any) -> pd.DataFrame:
        """Convert dict/list/DataFrame inputs into DataFrame."""
        if isinstance(data, pd.DataFrame):
            return data.copy()
        if isinstance(data, dict):
            return pd.DataFrame([data])
        if isinstance(data, list):
            return pd.DataFrame(data)
        return pd.DataFrame()

    @staticmethod
    def _ensure_columns(df: pd.DataFrame, expected: list[str]) -> pd.DataFrame:
        """Create missing columns with NaN placeholders."""
        for col in expected:
            if col not in df.columns:
                df[col] = np.nan
        return df

    # ==========================================
    # SECTION: Serialization
    # ==========================================
    # Feature engineering has no artifact serialization in Phase 6.

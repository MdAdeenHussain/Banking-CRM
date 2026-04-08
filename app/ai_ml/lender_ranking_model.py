"""Hybrid lender ranking model (rules + optional ML regressor)."""

# ==========================================
# SECTION: Imports
# ==========================================
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split


@dataclass
class LenderTrainResult:
    """Training metrics for lender ranking model."""

    mae: float
    r2: float


class LenderRankingModel:
    """Ranks lenders using weighted business rules + ML adjustment."""

    def __init__(self, model_version: str = "v1.0") -> None:
        self.model_version = model_version
        self.regressor: RandomForestRegressor | None = None

    # ==========================================
    # SECTION: Training Logic
    # ==========================================
    def train(self, X: pd.DataFrame, y: pd.Series) -> LenderTrainResult:
        """Train optional ML regressor to calibrate ranking score."""
        if X.empty or y.empty:
            raise ValueError("Lender training data cannot be empty.")

        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=0.25,
            random_state=42,
        )

        self.regressor = RandomForestRegressor(
            n_estimators=180,
            random_state=42,
            min_samples_leaf=2,
        )
        self.regressor.fit(X_train, y_train)

        predictions = self.regressor.predict(X_test)
        return LenderTrainResult(
            mae=float(mean_absolute_error(y_test, predictions)),
            r2=float(r2_score(y_test, predictions)),
        )

    # ==========================================
    # SECTION: Prediction Logic
    # ==========================================
    def rank_lenders(self, lender_rows: list[dict[str, Any]] | pd.DataFrame) -> list[dict[str, Any]]:
        """Rank lenders using weighted formula and optional ML signal.

        Weighted business score:
        Score = 0.4A + 0.2R + 0.2S + 0.2D
        """
        df = lender_rows if isinstance(lender_rows, pd.DataFrame) else pd.DataFrame(lender_rows)
        if df.empty:
            return []

        required_cols = [
            "approval_probability",
            "interest_rate",
            "avg_disbursal_days",
            "documentation_ease",
            "historical_approval_rate",
        ]
        for col in required_cols:
            if col not in df.columns:
                df[col] = 0.0
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

        # A = approval probability (0..100)
        df["A"] = df["approval_probability"].clip(0, 100)

        # R = rate competitiveness (lower interest is better)
        max_rate = max(float(df["interest_rate"].max()), 0.0001)
        min_rate = float(df["interest_rate"].min())
        if max_rate == min_rate:
            df["R"] = 100.0
        else:
            df["R"] = 100.0 * (max_rate - df["interest_rate"]) / (max_rate - min_rate)

        # S = speed score (lower disbursal days is better)
        max_days = max(float(df["avg_disbursal_days"].max()), 0.0001)
        min_days = float(df["avg_disbursal_days"].min())
        if max_days == min_days:
            df["S"] = 100.0
        else:
            df["S"] = 100.0 * (max_days - df["avg_disbursal_days"]) / (max_days - min_days)

        # D = documentation ease score (0..100)
        df["D"] = df["documentation_ease"].clip(0, 100)

        rule_score = 0.4 * df["A"] + 0.2 * df["R"] + 0.2 * df["S"] + 0.2 * df["D"]

        model_score = None
        if self.regressor is not None:
            model_features = df[required_cols]
            model_score = pd.Series(self.regressor.predict(model_features), index=df.index)
            model_score = model_score.clip(0, 100)

        if model_score is None:
            df["score"] = rule_score.clip(0, 100)
        else:
            # Hybrid blend: keep business rules dominant with ML correction.
            df["score"] = (0.7 * rule_score + 0.3 * model_score).clip(0, 100)

        ranked = df.sort_values(by="score", ascending=False).copy()
        return ranked.to_dict(orient="records")

    def recommend_top_3(self, lender_rows: list[dict[str, Any]] | pd.DataFrame) -> list[dict[str, Any]]:
        """Return top-3 lender recommendations in concise response format."""
        ranked = self.rank_lenders(lender_rows)
        top = ranked[:3]

        response = []
        for row in top:
            response.append(
                {
                    "bank": row.get("bank") or row.get("bank_name") or row.get("lender_name") or "Unknown",
                    "score": int(round(float(row.get("score", 0)))),
                    "interest": round(float(row.get("interest_rate", 0)), 2),
                    "days": round(float(row.get("avg_disbursal_days", 0)), 1),
                }
            )
        return response

    # ==========================================
    # SECTION: Serialization
    # ==========================================
    def save_model(self, file_path: str) -> str:
        """Serialize optional regressor model using joblib."""
        joblib.dump(
            {
                "regressor": self.regressor,
                "model_version": self.model_version,
            },
            file_path,
        )
        return file_path

    @classmethod
    def load_model(cls, file_path: str) -> "LenderRankingModel":
        """Load lender ranking artifact from disk."""
        payload = joblib.load(file_path)
        model = cls(model_version=payload.get("model_version", "v1.0"))
        model.regressor = payload.get("regressor")
        return model

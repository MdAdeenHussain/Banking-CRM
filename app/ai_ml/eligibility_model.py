"""Eligibility approval prediction model (RandomForestClassifier)."""

# ==========================================
# SECTION: Imports
# ==========================================
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from app.services.eligibility_service import max_loan_eligibility


@dataclass
class EligibilityTrainResult:
    """Training metrics for eligibility model registry."""

    accuracy: float
    precision: float
    recall: float
    roc_auc: float


class EligibilityModel:
    """Predicts approval probability for loan eligibility."""

    def __init__(self, model_version: str = "v1.0") -> None:
        self.model_version = model_version
        self.pipeline: Pipeline | None = None
        self.feature_names: list[str] = []

    # ==========================================
    # SECTION: Training Logic
    # ==========================================
    def train(self, X: pd.DataFrame, y: pd.Series) -> EligibilityTrainResult:
        """Train RandomForest-based eligibility model."""
        if X.empty or y.empty:
            raise ValueError("Training data cannot be empty.")

        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=0.25,
            random_state=42,
            stratify=y if y.nunique() > 1 else None,
        )

        categorical_cols = X.select_dtypes(include=["object", "category"]).columns.tolist()
        numeric_cols = [col for col in X.columns if col not in categorical_cols]

        preprocessor = ColumnTransformer(
            transformers=[
                (
                    "cat",
                    Pipeline(
                        steps=[
                            ("imputer", SimpleImputer(strategy="most_frequent")),
                            ("onehot", OneHotEncoder(handle_unknown="ignore")),
                        ]
                    ),
                    categorical_cols,
                ),
                (
                    "num",
                    Pipeline(steps=[("imputer", SimpleImputer(strategy="median"))]),
                    numeric_cols,
                ),
            ]
        )

        classifier = RandomForestClassifier(
            n_estimators=260,
            random_state=42,
            class_weight="balanced_subsample",
            min_samples_leaf=2,
        )

        self.pipeline = Pipeline(
            steps=[
                ("preprocessor", preprocessor),
                ("classifier", classifier),
            ]
        )
        self.pipeline.fit(X_train, y_train)

        probabilities = self.pipeline.predict_proba(X_test)[:, 1]
        predictions = (probabilities >= 0.5).astype(int)

        self.feature_names = X.columns.tolist()
        return EligibilityTrainResult(
            accuracy=float(accuracy_score(y_test, predictions)),
            precision=float(precision_score(y_test, predictions, zero_division=0)),
            recall=float(recall_score(y_test, predictions, zero_division=0)),
            roc_auc=float(roc_auc_score(y_test, probabilities)) if y_test.nunique() > 1 else 0.5,
        )

    # ==========================================
    # SECTION: Prediction Logic
    # ==========================================
    def predict_approval_probability(self, X: pd.DataFrame) -> list[dict[str, Any]]:
        """Predict approval probability with eligible amount estimate."""
        self._ensure_fitted()
        probabilities = self.pipeline.predict_proba(X)[:, 1]

        payload: list[dict[str, Any]] = []
        for index, probability in enumerate(probabilities):
            row = X.iloc[index]
            eligible_amount = max_loan_eligibility(
                net_monthly_income=float(row.get("monthly_income", 0) or 0),
                existing_monthly_obligations=float(row.get("existing_emis", 0) or 0),
                annual_rate=11.0,
                tenure_months=240,
            )
            confidence = max(float(probability), float(1 - probability))
            payload.append(
                {
                    "approval_probability": round(float(probability), 4),
                    "confidence": round(confidence, 4),
                    "eligible_amount": round(float(eligible_amount), 2),
                    "model_version": self.model_version,
                }
            )

        return payload

    def explain_prediction(self, X: pd.DataFrame, top_n: int = 3) -> list[dict[str, Any]]:
        """Return simple feature-importance-based explanation placeholders."""
        self._ensure_fitted()

        classifier = self.pipeline.named_steps["classifier"]
        raw_importances = getattr(classifier, "feature_importances_", None)
        if raw_importances is None:
            return [{"reasons": ["feature importance unavailable"]} for _ in range(len(X))]

        # We cannot map one-hot columns exactly without full transformed names in
        # all sklearn versions, so we provide high-level placeholder reasons.
        ranked_index = np.argsort(raw_importances)[::-1][:top_n]
        reasons = [f"feature_bucket_{int(i)}" for i in ranked_index]

        return [{"reasons": reasons} for _ in range(len(X))]

    # ==========================================
    # SECTION: Serialization
    # ==========================================
    def save_model(self, file_path: str) -> str:
        """Persist trained model using joblib."""
        self._ensure_fitted()
        joblib.dump(
            {
                "pipeline": self.pipeline,
                "model_version": self.model_version,
                "feature_names": self.feature_names,
            },
            file_path,
        )
        return file_path

    @classmethod
    def load_model(cls, file_path: str) -> "EligibilityModel":
        """Load eligibility model artifact from disk."""
        payload = joblib.load(file_path)
        model = cls(model_version=payload.get("model_version", "v1.0"))
        model.pipeline = payload.get("pipeline")
        model.feature_names = payload.get("feature_names", [])
        return model

    def _ensure_fitted(self) -> None:
        if self.pipeline is None:
            raise RuntimeError("Eligibility model is not trained/loaded.")

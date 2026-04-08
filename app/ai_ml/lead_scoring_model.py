"""Lead scoring ML model stack (LogReg baseline + RF + GBC)."""

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
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.utils.class_weight import compute_sample_weight


@dataclass
class LeadScoringTrainResult:
    """Training summary for model registry and observability."""

    model_name: str
    accuracy: float
    precision: float
    recall: float
    roc_auc: float


class LeadScoringModel:
    """Trains and serves lead conversion probability model."""

    POSITIVE_LABEL = 1

    def __init__(self, model_version: str = "v1.0") -> None:
        self.model_version = model_version
        self.pipeline: Pipeline | None = None
        self.best_model_name: str | None = None

    # ==========================================
    # SECTION: Training Logic
    # ==========================================
    def train(self, X: pd.DataFrame, y: pd.Series) -> LeadScoringTrainResult:
        """Train multiple candidate models and keep best performer."""
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
                    Pipeline(
                        steps=[("imputer", SimpleImputer(strategy="median"))]
                    ),
                    numeric_cols,
                ),
            ]
        )

        candidates = {
            "logistic_regression": LogisticRegression(max_iter=400, class_weight="balanced"),
            "random_forest": RandomForestClassifier(
                n_estimators=240,
                random_state=42,
                class_weight="balanced_subsample",
                min_samples_leaf=2,
            ),
            "gradient_boosting": GradientBoostingClassifier(random_state=42),
        }

        # NOTE: SMOTE placeholder for future class imbalance treatment.
        # We use class weighting for this phase to keep dependencies minimal.
        best_result: LeadScoringTrainResult | None = None
        best_pipeline: Pipeline | None = None

        for model_name, estimator in candidates.items():
            pipeline = Pipeline(
                steps=[
                    ("preprocessor", preprocessor),
                    ("classifier", estimator),
                ]
            )

            if model_name == "gradient_boosting":
                weights = compute_sample_weight(class_weight="balanced", y=y_train)
                pipeline.fit(X_train, y_train, classifier__sample_weight=weights)
            else:
                pipeline.fit(X_train, y_train)

            probabilities = pipeline.predict_proba(X_test)[:, 1]
            predictions = (probabilities >= 0.5).astype(int)

            result = LeadScoringTrainResult(
                model_name=model_name,
                accuracy=float(accuracy_score(y_test, predictions)),
                precision=float(precision_score(y_test, predictions, zero_division=0)),
                recall=float(recall_score(y_test, predictions, zero_division=0)),
                roc_auc=float(roc_auc_score(y_test, probabilities)) if y_test.nunique() > 1 else 0.5,
            )

            if best_result is None or result.roc_auc > best_result.roc_auc:
                best_result = result
                best_pipeline = pipeline

        if best_result is None or best_pipeline is None:
            raise RuntimeError("Lead model training failed to produce a candidate.")

        self.pipeline = best_pipeline
        self.best_model_name = best_result.model_name
        return best_result

    # ==========================================
    # SECTION: Prediction Logic
    # ==========================================
    def predict_probability(self, X: pd.DataFrame) -> np.ndarray:
        """Return conversion probability output for each row."""
        self._ensure_fitted()
        return self.pipeline.predict_proba(X)[:, 1]

    def predict_score(self, X: pd.DataFrame) -> list[dict[str, Any]]:
        """Return 0-100 lead conversion score payload."""
        probabilities = self.predict_probability(X)
        scores = np.clip(np.round(probabilities * 100), 0, 100).astype(int)

        output: list[dict[str, Any]] = []
        for score, probability in zip(scores, probabilities):
            output.append(
                {
                    "score": int(score),
                    "confidence": round(float(probability), 4),
                    "model_version": self.model_version,
                }
            )
        return output

    # ==========================================
    # SECTION: Serialization
    # ==========================================
    def save_model(self, file_path: str) -> str:
        """Serialize trained model using joblib."""
        self._ensure_fitted()
        payload = {
            "pipeline": self.pipeline,
            "model_version": self.model_version,
            "best_model_name": self.best_model_name,
        }
        joblib.dump(payload, file_path)
        return file_path

    @classmethod
    def load_model(cls, file_path: str) -> "LeadScoringModel":
        """Load model artifact from disk."""
        payload = joblib.load(file_path)
        model = cls(model_version=payload.get("model_version", "v1.0"))
        model.pipeline = payload.get("pipeline")
        model.best_model_name = payload.get("best_model_name")
        return model

    def _ensure_fitted(self) -> None:
        if self.pipeline is None:
            raise RuntimeError("Lead scoring model is not trained/loaded.")

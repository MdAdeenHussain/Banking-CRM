"""Advanced anomaly detection model for fraud intelligence."""

# ==========================================
# SECTION: Imports
# ==========================================
from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from flask import current_app, has_app_context
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.svm import OneClassSVM


# ==========================================
# SECTION: Fraud Detection
# ==========================================
class FraudAnomalyModel:
    """Unsupervised anomaly detector for fraud risk signals.

    Primary model:
    - IsolationForest

    Secondary fallback:
    - OneClassSVM

    The service auto-trains on a small benign baseline when no serialized
    model exists yet, so the API stays usable during early development.
    """

    FEATURE_COLUMNS = [
        "salary_variance",
        "metadata_inconsistency",
        "doc_reuse_frequency",
        "device_reuse_count",
        "ip_reuse_count",
        "multiple_applications_30d",
        "salary_credit_pattern",
        "file_hash_duplication",
        "ocr_field_mismatch",
    ]

    def __init__(self) -> None:
        self.scaler = StandardScaler()
        self.primary_model = IsolationForest(
            contamination=0.12,
            n_estimators=200,
            random_state=42,
        )
        self.secondary_model = OneClassSVM(gamma="scale", nu=0.12)
        self.model_version = "fraud-anomaly-v1.0"
        self.model_path = Path(self._get_config("FRAUD_MODEL_DIR", "model_store/fraud")) / "anomaly_model.joblib"
        self.is_trained = False
        self._load_model()

    def train(self, X: pd.DataFrame | list[dict[str, Any]] | dict[str, Any]) -> dict[str, Any]:
        """Train anomaly detector on fraud-feature matrix."""
        frame = self._coerce_dataframe(X)
        self.scaler.fit(frame[self.FEATURE_COLUMNS])
        transformed = self.scaler.transform(frame[self.FEATURE_COLUMNS])

        self.primary_model.fit(transformed)
        self.secondary_model.fit(transformed)
        self.is_trained = True
        self.save_model()

        return {
            "success": True,
            "rows_trained": int(len(frame)),
            "model_version": self.model_version,
        }

    def predict_risk(self, X: pd.DataFrame | list[dict[str, Any]] | dict[str, Any]) -> dict[str, Any]:
        """Return fraud score, risk level, and confidence."""
        if not self.is_trained:
            self.train(self._default_training_frame())

        frame = self._coerce_dataframe(X)
        transformed = self.scaler.transform(frame[self.FEATURE_COLUMNS])

        anomaly_predictions = self.primary_model.predict(transformed)
        anomaly_scores = self.primary_model.decision_function(transformed)
        svm_predictions = self.secondary_model.predict(transformed)

        feature_severity = frame[self.FEATURE_COLUMNS].mean(axis=1).fillna(0).iloc[0]
        anomaly_penalty = 35 if int(anomaly_predictions[0]) == -1 else 10
        svm_penalty = 15 if int(svm_predictions[0]) == -1 else 5
        normalized_decision = max(0.0, min(1.0, 0.5 - float(anomaly_scores[0])))

        fraud_score = (
            anomaly_penalty
            + svm_penalty
            + min(50.0, float(feature_severity) * 40.0)
            + (normalized_decision * 20.0)
        )
        fraud_score = int(max(0, min(100, round(fraud_score))))
        confidence = round(min(0.99, 0.55 + normalized_decision + (fraud_score / 250)), 2)

        return {
            "fraud_score": fraud_score,
            "risk_level": self._risk_level(fraud_score),
            "confidence": confidence,
            "model_version": self.model_version,
        }

    def save_model(self) -> None:
        """Serialize trained anomaly models for reuse."""
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {
                "scaler": self.scaler,
                "primary_model": self.primary_model,
                "secondary_model": self.secondary_model,
                "model_version": self.model_version,
            },
            self.model_path,
        )

    def _load_model(self) -> None:
        """Load serialized model if it exists."""
        if not self.model_path.exists():
            return

        try:
            bundle = joblib.load(self.model_path)
        except Exception:
            return

        self.scaler = bundle.get("scaler", self.scaler)
        self.primary_model = bundle.get("primary_model", self.primary_model)
        self.secondary_model = bundle.get("secondary_model", self.secondary_model)
        self.model_version = bundle.get("model_version", self.model_version)
        self.is_trained = True

    def _coerce_dataframe(
        self,
        X: pd.DataFrame | list[dict[str, Any]] | dict[str, Any],
    ) -> pd.DataFrame:
        """Coerce input into the expected fraud-feature dataframe."""
        if isinstance(X, pd.DataFrame):
            frame = X.copy()
        elif isinstance(X, dict):
            frame = pd.DataFrame([X])
        else:
            frame = pd.DataFrame(list(X))

        for column in self.FEATURE_COLUMNS:
            if column not in frame.columns:
                frame[column] = 0.0
        return frame[self.FEATURE_COLUMNS].fillna(0.0).astype(float)

    def _default_training_frame(self) -> pd.DataFrame:
        """Generate a benign baseline for cold-start training."""
        baseline_rows = [
            {
                "salary_variance": 0.03,
                "metadata_inconsistency": 0.02,
                "doc_reuse_frequency": 0.0,
                "device_reuse_count": 1.0,
                "ip_reuse_count": 1.0,
                "multiple_applications_30d": 0.0,
                "salary_credit_pattern": 0.05,
                "file_hash_duplication": 0.0,
                "ocr_field_mismatch": 0.0,
            },
            {
                "salary_variance": 0.08,
                "metadata_inconsistency": 0.04,
                "doc_reuse_frequency": 0.1,
                "device_reuse_count": 1.0,
                "ip_reuse_count": 1.0,
                "multiple_applications_30d": 0.0,
                "salary_credit_pattern": 0.07,
                "file_hash_duplication": 0.0,
                "ocr_field_mismatch": 0.0,
            },
            {
                "salary_variance": 0.12,
                "metadata_inconsistency": 0.06,
                "doc_reuse_frequency": 0.1,
                "device_reuse_count": 1.0,
                "ip_reuse_count": 1.0,
                "multiple_applications_30d": 1.0,
                "salary_credit_pattern": 0.08,
                "file_hash_duplication": 0.0,
                "ocr_field_mismatch": 0.05,
            },
            {
                "salary_variance": 0.18,
                "metadata_inconsistency": 0.1,
                "doc_reuse_frequency": 0.2,
                "device_reuse_count": 2.0,
                "ip_reuse_count": 1.0,
                "multiple_applications_30d": 1.0,
                "salary_credit_pattern": 0.12,
                "file_hash_duplication": 0.0,
                "ocr_field_mismatch": 0.05,
            },
        ]
        return pd.DataFrame(baseline_rows)

    def _risk_level(self, fraud_score: int) -> str:
        """Map numeric score to LOW/MEDIUM/HIGH."""
        if fraud_score > 70:
            return "HIGH"
        if fraud_score >= 40:
            return "MEDIUM"
        return "LOW"

    @staticmethod
    def _get_config(key: str, default):
        """Read config safely inside or outside Flask app context."""
        if has_app_context():
            return current_app.config.get(key, default)
        return default


# ==========================================
# SECTION: Anomaly Scoring
# ==========================================
# The model turns suspicious feature combinations into a normalized score.


# ==========================================
# SECTION: Forensics
# ==========================================
# Forensic signals are supplied by risk_scoring_service.py.


# ==========================================
# SECTION: Alerts
# ==========================================
# Alert generation happens after score thresholds are applied elsewhere.

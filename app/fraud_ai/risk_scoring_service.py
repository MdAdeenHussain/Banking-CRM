"""Fraud risk scoring service combining multiple intelligence layers."""

# ==========================================
# SECTION: Imports
# ==========================================
from __future__ import annotations

from typing import Any

from app.extensions import db
from app.fraud_ai.anomaly_model import FraudAnomalyModel
from app.fraud_ai.device_fingerprint_service import DeviceFingerprintService
from app.fraud_ai.forensic_engine import ForensicEngine
from app.fraud_ai.identity_graph_service import IdentityGraphService
from app.models.application import Application
from app.models.customer import Customer
from app.models.document import Document


# ==========================================
# SECTION: Fraud Detection
# ==========================================
class FraudRiskScoringService:
    """Combine rule, anomaly, device, identity, and forensic signals."""

    def __init__(self, tenant_id: int, actor_user_id: int | None = None) -> None:
        self.tenant_id = tenant_id
        self.actor_user_id = actor_user_id
        self.anomaly_model = FraudAnomalyModel()
        self.forensic_engine = ForensicEngine(tenant_id=tenant_id)
        self.device_service = DeviceFingerprintService(
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
        )
        self.identity_service = IdentityGraphService(tenant_id=tenant_id)

    def evaluate_case(
        self,
        *,
        document_id: int,
        device_payload: dict[str, Any] | None = None,
        identifiers: dict[str, Any] | None = None,
        bank_statement_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Evaluate a document-linked fraud case and return final risk."""
        document = self._get_document_or_fail(document_id)
        customer = document.customer
        application = document.application

        rule_score = int(document.fraud_score or 0)
        forensic_result = self.forensic_engine.analyze_document(
            document,
            bank_statement_data=bank_statement_data,
            application_name=getattr(customer, "full_name", None),
        )

        device_result = (
            self.device_service.analyze_device(
                {**(device_payload or {}), "identifiers": identifiers or {}},
                persist=True,
            )
            if device_payload
            else {
                "fingerprint": None,
                "device_score": 0,
                "risk_level": "LOW",
                "usage_count": 0,
                "ip_reuse_count": 0,
                "multiple_identity_result": {"score": 0, "reasons": []},
            }
        )

        identity_result = self.identity_service.score_identity_risk(
            customer=customer,
            identifiers=identifiers or self._customer_identifiers(customer),
        )

        anomaly_features = self._build_anomaly_features(
            document=document,
            customer=customer,
            application=application,
            forensic_result=forensic_result,
            device_result=device_result,
            bank_statement_data=bank_statement_data or {},
        )
        anomaly_result = self.anomaly_model.predict_risk(anomaly_features)

        final_risk = self.calculate_risk(
            rule_score=rule_score,
            anomaly_score=int(anomaly_result["fraud_score"]),
            device_score=int(device_result["device_score"]),
            identity_score=int(identity_result["identity_score"]),
            forensic_score=int(forensic_result["document_score"]),
        )

        assessment = {
            "document_id": document.id,
            "customer_id": document.customer_id,
            "application_id": document.application_id,
            "rule_score": rule_score,
            "anomaly_result": anomaly_result,
            "device_result": device_result,
            "identity_result": identity_result,
            "forensic_result": forensic_result,
            "risk_score": final_risk["risk_score"],
            "risk_level": final_risk["risk_level"],
            "components": final_risk["components"],
            "anomaly_features": anomaly_features,
        }

        self.persist_document_assessment(document, assessment)
        return assessment

    def calculate_risk(
        self,
        *,
        rule_score: int,
        anomaly_score: int,
        device_score: int,
        identity_score: int,
        forensic_score: int,
    ) -> dict[str, Any]:
        """Apply weighted fraud risk formula and bucket the result."""
        weighted_score = (
            0.25 * float(rule_score)
            + 0.30 * float(anomaly_score)
            + 0.15 * float(device_score)
            + 0.15 * float(identity_score)
            + 0.15 * float(forensic_score)
        )
        risk_score = int(max(0, min(100, round(weighted_score))))
        return {
            "risk_score": risk_score,
            "risk_level": self._risk_level(risk_score),
            "components": {
                "rule_score": int(rule_score),
                "anomaly_score": int(anomaly_score),
                "device_score": int(device_score),
                "identity_score": int(identity_score),
                "forensic_score": int(forensic_score),
            },
        }

    def persist_document_assessment(
        self,
        document: Document,
        assessment: dict[str, Any],
    ) -> None:
        """Persist advanced fraud score back to the document record."""
        merged_flags = dict(document.fraud_flags_json or {})
        merged_flags["advanced_fraud_assessment"] = {
            "risk_level": assessment["risk_level"],
            "components": assessment["components"],
            "forensic_flags": assessment["forensic_result"].get("flags", {}),
            "identity_reasons": assessment["identity_result"].get("reasons", []),
            "device_reasons": assessment["device_result"]
            .get("multiple_identity_result", {})
            .get("reasons", []),
        }
        document.fraud_score = int(assessment["risk_score"])
        document.fraud_flags_json = merged_flags
        db.session.commit()

    def _build_anomaly_features(
        self,
        *,
        document: Document,
        customer: Customer | None,
        application: Application | None,
        forensic_result: dict[str, Any],
        device_result: dict[str, Any],
        bank_statement_data: dict[str, Any],
    ) -> dict[str, float]:
        """Build anomaly feature payload expected by FraudAnomalyModel."""
        metadata = (document.ocr_data_json or {}).get("metadata", {})
        salary_amount = float((document.ocr_data_json or {}).get("salary_amount") or 0)
        bank_salary = float(
            bank_statement_data.get("avg_salary_credit")
            or bank_statement_data.get("credited_salary")
            or metadata.get("bank_average_salary_credit")
            or 0
        )
        salary_variance = abs(salary_amount - bank_salary) / salary_amount if salary_amount > 0 and bank_salary > 0 else 0.0

        duplicate_doc_count = Document.query.filter_by(
            tenant_id=self.tenant_id,
            file_hash=document.file_hash,
            is_deleted=False,
        ).count()
        recent_application_count = 0
        if customer is not None:
            recent_application_count = Application.query.filter_by(
                tenant_id=self.tenant_id,
                customer_id=customer.id,
                is_deleted=False,
            ).count()

        forensic_flags = forensic_result.get("flags", {})
        metadata_inconsistency = min(1.0, len(forensic_flags) / 5)
        salary_credit_pattern = min(
            1.0,
            abs(
                len(bank_statement_data.get("monthly_salary_credits") or [])
                - (1 if salary_amount > 0 else 0)
            )
            / 6,
        )

        return {
            "salary_variance": round(float(salary_variance), 4),
            "metadata_inconsistency": round(float(metadata_inconsistency), 4),
            "doc_reuse_frequency": round(float(max(0, duplicate_doc_count - 1) / 5), 4),
            "device_reuse_count": round(float(device_result.get("usage_count", 0)), 4),
            "ip_reuse_count": round(float(device_result.get("ip_reuse_count", 0)), 4),
            "multiple_applications_30d": round(float(recent_application_count), 4),
            "salary_credit_pattern": round(float(salary_credit_pattern), 4),
            "file_hash_duplication": 1.0 if duplicate_doc_count > 1 else 0.0,
            "ocr_field_mismatch": 1.0 if "ocr_name_mismatch" in forensic_flags else 0.0,
        }

    def _customer_identifiers(self, customer: Customer | None) -> dict[str, Any]:
        """Extract customer identifiers for identity analysis."""
        if customer is None:
            return {}
        return {
            "pan": customer.pan,
            "mobile": customer.mobile,
            "email": customer.email,
            "aadhaar": customer.aadhaar,
        }

    def _get_document_or_fail(self, document_id: int) -> Document:
        """Load tenant-safe document for fraud analysis."""
        document = Document.query.filter_by(
            id=document_id,
            tenant_id=self.tenant_id,
            is_deleted=False,
        ).first()
        if document is None:
            raise ValueError("Document not found for current tenant.")
        return document

    def _risk_level(self, score: int) -> str:
        """Map score to LOW/MEDIUM/HIGH."""
        if score > 70:
            return "HIGH"
        if score >= 40:
            return "MEDIUM"
        return "LOW"


# ==========================================
# SECTION: Anomaly Scoring
# ==========================================
# The anomaly model consumes normalized features built by this service.


# ==========================================
# SECTION: Forensics
# ==========================================
# Forensic and identity/device signals are combined here.


# ==========================================
# SECTION: Alerts
# ==========================================
# Alert triggering happens after final risk score computation.

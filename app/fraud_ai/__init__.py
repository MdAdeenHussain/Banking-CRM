"""Fraud AI package exports.

This package contains the advanced anomaly, device, identity, and
forensic intelligence services introduced in Phase 9.
"""

# ==========================================
# SECTION: Fraud Detection
# ==========================================
# Package exports keep feature imports simple for routes and services.


# ==========================================
# SECTION: Anomaly Scoring
# ==========================================
from app.fraud_ai.anomaly_model import FraudAnomalyModel
from app.fraud_ai.alert_service import FraudAlertService
from app.fraud_ai.device_fingerprint_service import DeviceFingerprintService
from app.fraud_ai.forensic_engine import ForensicEngine
from app.fraud_ai.fraud_reasoning_service import FraudReasoningService
from app.fraud_ai.identity_graph_service import IdentityGraphService
from app.fraud_ai.risk_scoring_service import FraudRiskScoringService


# ==========================================
# SECTION: Forensics
# ==========================================
# Forensic analysis helpers live in forensic_engine.py.


# ==========================================
# SECTION: Alerts
# ==========================================
__all__ = [
    "FraudAnomalyModel",
    "ForensicEngine",
    "FraudRiskScoringService",
    "DeviceFingerprintService",
    "IdentityGraphService",
    "FraudReasoningService",
    "FraudAlertService",
]

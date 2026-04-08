"""Legacy dashboard service façade.

This service now includes document-vault counters for compatibility with
older call-sites that are not yet migrated to DashboardKPIService.
"""

# ==========================================
# SECTION: Imports
# ==========================================
from __future__ import annotations

from app.models.document import Document


# ==========================================
# SECTION: Core Logic
# ==========================================
class DashboardService:
    """Simple summary service with document metrics."""

    def __init__(self, tenant_id: int) -> None:
        self.tenant_id = tenant_id

    def owner_summary(self) -> dict:
        """Owner summary including document intelligence counters."""
        docs = Document.query.filter_by(tenant_id=self.tenant_id, is_deleted=False).all()

        documents_uploaded = len(docs)
        documents_pending = sum(1 for doc in docs if doc.ocr_status == "PENDING")
        fraud_alerts = sum(1 for doc in docs if (doc.fraud_score or 0) >= 40)
        verification_queue_count = sum(
            1 for doc in docs if doc.verification_status in {"PENDING", "UNDER_REVIEW"}
        )

        return {
            "documents_uploaded": int(documents_uploaded),
            "documents_pending": int(documents_pending),
            "fraud_alerts": int(fraud_alerts),
            "verification_queue_count": int(verification_queue_count),
        }

    def branch_summary(self) -> dict:
        """Branch summary placeholder mirroring owner metrics for now."""
        return self.owner_summary()


# ==========================================
# SECTION: Validation
# ==========================================
# N/A for this lightweight summary façade.


# ==========================================
# SECTION: Fraud Checks
# ==========================================
# Fraud alert values are derived from stored document fraud_score values.

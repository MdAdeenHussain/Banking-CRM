"""
LoanAxis CRM — Duplicate Lead Detection

Checks for potential duplicate leads based on mobile number + loan type.
"""

from typing import Optional

from app.extensions import db
from app.models.lead import Lead


def check_duplicate_lead(
    mobile_primary: str,
    loan_type: str,
    exclude_lead_id: str = None,
) -> Optional[Lead]:
    """
    Check if a lead with the same mobile + loan type already exists.

    Uses the composite index (mobile_primary, loan_type) for efficient lookup.

    Args:
        mobile_primary: Customer's primary mobile number
        loan_type: Type of loan being applied for
        exclude_lead_id: ID of current lead to exclude (for updates)

    Returns:
        The existing Lead if a duplicate is found, None otherwise
    """
    query = Lead.query.filter(
        Lead.mobile_primary == mobile_primary,
        Lead.loan_type == loan_type,
        Lead.is_active == True,
        Lead.is_deleted == False,
    )

    if exclude_lead_id:
        query = query.filter(Lead.id != exclude_lead_id)

    return query.first()


def check_duplicate_api(mobile_primary: str, loan_type: str) -> dict:
    """
    API-friendly duplicate check. Returns a dict for JSON response.

    Returns:
        {
            "is_duplicate": bool,
            "existing_lead": dict | None
        }
    """
    existing = check_duplicate_lead(mobile_primary, loan_type)

    if existing:
        return {
            "is_duplicate": True,
            "existing_lead": {
                "id": existing.id,
                "lead_number": existing.lead_number,
                "customer_name": existing.customer_name,
                "mobile_primary": existing.mobile_primary,
                "loan_type": existing.loan_type,
                "pipeline_stage": existing.pipeline_stage,
                "assigned_executive_id": existing.assigned_executive_id,
                "created_at": existing.created_at.isoformat() if existing.created_at else None,
            },
        }

    return {"is_duplicate": False, "existing_lead": None}

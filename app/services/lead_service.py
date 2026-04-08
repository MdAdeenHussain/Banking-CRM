"""Lead service layer with tenant-safe queries."""

# =====================================
# SECTION: Imports
# =====================================
from collections import Counter

from app.extensions import db
from app.models.lead import Lead


# =====================================
# SECTION: Service Definition
# =====================================
class LeadService:
    """Lead domain operations."""

    @staticmethod
    def list_leads(tenant_id: int) -> list[Lead]:
        """Return active, non-deleted leads for tenant."""
        return (
            Lead.query.filter_by(tenant_id=tenant_id, is_deleted=False)
            .order_by(Lead.created_at.desc())
            .all()
        )

    @staticmethod
    def create_lead(tenant_id: int, payload: dict) -> Lead:
        """Create a new lead for tenant."""
        lead = Lead(
            tenant_id=tenant_id,
            customer_name=payload.get("customer_name", "Unknown"),
            mobile=payload.get("mobile", ""),
            email=payload.get("email"),
            loan_type=payload.get("loan_type"),
            loan_amount=payload.get("loan_amount"),
            source=payload.get("source"),
            assigned_agent=payload.get("assigned_agent"),
            stage=Lead.STAGE_NEW,
            ai_score_placeholder=payload.get("ai_score_placeholder"),
        )
        db.session.add(lead)
        db.session.commit()
        return lead

    @staticmethod
    def update_stage(tenant_id: int, lead_id: int, new_stage: str) -> bool:
        """Update lead stage with validation and tenant guard."""
        if new_stage not in Lead.ALLOWED_STAGES:
            return False

        lead = Lead.query.filter_by(id=lead_id, tenant_id=tenant_id, is_deleted=False).first()
        if not lead:
            return False

        lead.stage = new_stage
        db.session.commit()
        return True

    @staticmethod
    def assign_agent(tenant_id: int, lead_id: int, agent_name: str) -> bool:
        """Assign an agent to a lead for the current tenant."""
        lead = Lead.query.filter_by(id=lead_id, tenant_id=tenant_id, is_deleted=False).first()
        if not lead:
            return False

        lead.assigned_agent = agent_name
        db.session.commit()
        return True

    @staticmethod
    def get_pipeline_data(tenant_id: int) -> dict:
        """Aggregate lead stage counts for pipeline visualizations."""
        leads = Lead.query.filter_by(tenant_id=tenant_id, is_deleted=False).all()
        counts = Counter(lead.stage for lead in leads)
        return {stage: counts.get(stage, 0) for stage in Lead.ALLOWED_STAGES}

    # Future AI placeholder:
    # - adaptive lead ranking strategies

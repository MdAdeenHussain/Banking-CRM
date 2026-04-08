"""
app/leads/models.py
Lead, LeadNote, LeadAssignment, and LeadStatusHistory models.
Core business entities for lead management.
"""

from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy import Index, UniqueConstraint
from app.extensions import db
from app.common.mixins import BaseTenantModel, utcnow
from uuid import uuid4
from datetime import datetime


class Lead(BaseTenantModel):
    """
    Lead in the CRM pipeline.
    Core business entity representing a potential customer.
    """
    __tablename__ = "leads"
    __table_args__ = (
        Index("idx_lead_tenant_status", "tenant_id", "status"),
        Index("idx_lead_assigned_to", "assigned_to"),
        Index("idx_lead_mobile", "mobile"),
    )

    # Override tenant_id with ForeignKey constraint
    tenant_id = db.Column(
        db.String(36),
        db.ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Customer Info
    name = db.Column(db.String(255), nullable=False)
    mobile = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(255), nullable=True)
    
    # Loan Details
    loan_type = db.Column(
        db.String(50),
        nullable=False,
        comment="HOME_LOAN, PERSONAL_LOAN, etc."
    )
    loan_amount = db.Column(
        db.Numeric(15, 2),
        nullable=True,
        comment="Requested loan amount"
    )
    
    # Lead Source
    source = db.Column(
        db.String(50),
        nullable=True,
        comment="WEBSITE, REFERRAL, CAMPAIGN, DIRECT_CALL, etc."
    )
    
    # Location
    city = db.Column(db.String(100), nullable=True)
    
    # Pipeline Status
    status = db.Column(
        db.String(50),
        default="NEW_LEAD",
        nullable=False,
        index=True,
        comment="NEW_LEAD, CONTACTED, INTERESTED, DOCS_PENDING, ..., DISBURSED, LOST"
    )
    
    # Priority
    priority = db.Column(
        db.String(20),
        default="MEDIUM",
        comment="LOW, MEDIUM, HIGH, URGENT"
    )
    
    # Assignment
    assigned_to = db.Column(
        db.String(36),
        db.ForeignKey("users.id"),
        nullable=True,
        comment="Agent/Telecaller user ID"
    )
    
    # Follow-up
    next_follow_up = db.Column(
        db.DateTime,
        nullable=True,
        comment="Scheduled follow-up date"
    )
    
    # Customer Reference
    customer_id = db.Column(
        db.String(36),
        db.ForeignKey("customers.id"),
        nullable=True,
        comment="Link to customer 360 profile if exists"
    )
    
    # Additional Data (JSON for flexibility)
    custom_data = db.Column(
        JSON,
        nullable=True,
        comment="Additional flexible data (campaign, source details, etc.)"
    )
    
    # Fraud Detection (Phase 2)
    fraud_flags = db.Column(
        JSON,
        nullable=True,
        comment="Fraud detection results (Phase 2)"
    )

    # Relationships
    agent = db.relationship("User", backref=db.backref("assigned_leads", lazy=True))
    customer = db.relationship("Customer", backref="leads")
    notes = db.relationship(
        "LeadNote",
        backref="lead",
        lazy=True,
        cascade="all, delete-orphan"
    )
    assignments = db.relationship(
        "LeadAssignment",
        backref="lead",
        lazy=True,
        cascade="all, delete-orphan"
    )
    status_history = db.relationship(
        "LeadStatusHistory",
        backref="lead",
        lazy=True,
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Lead {self.name} ({self.mobile})>"

    def to_dict(self):
        data = super().to_dict()
        data.update({
            "name": self.name,
            "mobile": self.mobile,
            "email": self.email,
            "loan_type": self.loan_type,
            "loan_amount": float(self.loan_amount) if self.loan_amount else None,
            "source": self.source,
            "city": self.city,
            "status": self.status,
            "priority": self.priority,
            "assigned_to": str(self.assigned_to) if self.assigned_to else None,
            "next_follow_up": self.next_follow_up.isoformat() if self.next_follow_up else None,
            "customer_id": str(self.customer_id) if self.customer_id else None,
        })
        return data


class LeadNote(BaseTenantModel):
    """
    Note/comment on a Lead.
    Activity log showing agent interactions.
    """
    __tablename__ = "lead_notes"
    __table_args__ = (
        Index("idx_note_lead", "lead_id"),
        Index("idx_note_created_by", "created_by"),
    )

    # Override tenant_id with ForeignKey constraint
    tenant_id = db.Column(
        db.String(36),
        db.ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    lead_id = db.Column(
        db.String(36),
        db.ForeignKey("leads.id", ondelete="CASCADE"),
        nullable=False
    )
    
    note_text = db.Column(db.Text, nullable=False)
    
    # Note Type (optional classification)
    note_type = db.Column(
        db.String(50),
        nullable=True,
        comment="CALL_LOG, MEETING, EMAIL, FOLLOW_UP, etc."
    )

    def __repr__(self):
        return f"<LeadNote lead_id={self.lead_id}>"

    def to_dict(self):
        data = super().to_dict()
        data.update({
            "lead_id": str(self.lead_id),
            "note_text": self.note_text,
            "note_type": self.note_type,
        })
        return data


class LeadAssignment(BaseTenantModel):
    """
    Assignment record: Which agent is/was assigned to a lead.
    Tracks assignment history and routing logic.
    """
    __tablename__ = "lead_assignments"
    __table_args__ = (
        Index("idx_assignment_lead", "lead_id"),
        Index("idx_assignment_user", "user_id"),
    )

    # Override tenant_id with ForeignKey constraint
    tenant_id = db.Column(
        db.String(36),
        db.ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    lead_id = db.Column(
        db.String(36),
        db.ForeignKey("leads.id", ondelete="CASCADE"),
        nullable=False
    )
    user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="Agent/Telecaller assigned"
    )
    
    # Assignment Type
    assignment_type = db.Column(
        db.String(50),
        nullable=True,
        comment="MANUAL, ROUND_ROBIN, BRANCH_ROUTER, AUTO"
    )
    
    # Assignment Dates
    assigned_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    completed_at = db.Column(
        db.DateTime,
        nullable=True,
        comment="When agent finished with this lead"
    )
    
    # Status
    is_active = db.Column(
        db.Boolean,
        default=True,
        nullable=False,
        comment="Whether this is the current active assignment"
    )

    # Relationships
    user = db.relationship("User")

    def __repr__(self):
        return f"<LeadAssignment lead={self.lead_id} user={self.user_id}>"

    def to_dict(self):
        data = super().to_dict()
        data.update({
            "lead_id": str(self.lead_id),
            "user_id": str(self.user_id),
            "assignment_type": self.assignment_type,
            "assigned_at": self.assigned_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "is_active": self.is_active,
        })
        return data


class LeadStatusHistory(BaseTenantModel):
    """
    Audit trail of lead status changes.
    Records every transition through the pipeline for compliance.
    """
    __tablename__ = "lead_status_history"
    __table_args__ = (
        Index("idx_history_lead", "lead_id"),
        Index("idx_history_created_at", "created_at"),
    )

    # Override tenant_id with ForeignKey constraint
    tenant_id = db.Column(
        db.String(36),
        db.ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    lead_id = db.Column(
        db.String(36),
        db.ForeignKey("leads.id", ondelete="CASCADE"),
        nullable=False
    )
    
    old_status = db.Column(
        db.String(50),
        nullable=True,
        comment="Previous status"
    )
    new_status = db.Column(
        db.String(50),
        nullable=False,
        comment="New status"
    )
    
    # Change Context
    reason = db.Column(
        db.String(255),
        nullable=True,
        comment="Reason for status change"
    )
    
    # Additional context
    custom_data = db.Column(
        JSON,
        nullable=True,
        comment="Additional context (e.g., lender matched, docs received)"
    )

    def __repr__(self):
        return f"<LeadStatusHistory {self.old_status}->{self.new_status}>"

    def to_dict(self):
        data = super().to_dict()
        data.update({
            "lead_id": str(self.lead_id),
            "old_status": self.old_status,
            "new_status": self.new_status,
            "reason": self.reason,
        })
        return data

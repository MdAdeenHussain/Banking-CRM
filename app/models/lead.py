from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.extensions import db
from app.models.base import BaseModel


LOAN_TYPES = [
    "Personal",
    "Business",
    "Home",
    "Mortgage",
    "LAP",
    "Credit Card",
    "Vehicle",
    "Education",
    "Top-up",
]

PIPELINE_STAGES = [
    "New Lead",
    "Contacted",
    "Docs Pending",
    "Docs Received",
    "Bank Login Done",
    "Sanctioned",
    "Disbursed",
    "Rejected",
    "Closed",
]

PIPELINE_STAGE_COLORS = {
    "New Lead": "gray",
    "Contacted": "blue",
    "Docs Pending": "amber",
    "Docs Received": "indigo",
    "Bank Login Done": "purple",
    "Sanctioned": "teal",
    "Disbursed": "green",
    "Rejected": "red",
    "Closed": "dark",
}

PRIORITY_TAGS = ["Hot", "Warm", "Cold"]

LEAD_SOURCES = [
    "Walk-in",
    "Referral",
    "Online Portal",
    "Cold Call",
    "WhatsApp",
    "Social Media",
    "Corporate Tie-up",
    "Other",
]


class Lead(BaseModel):
    """A customer lead in the loan distribution pipeline."""

    __tablename__ = "leads"

    lead_number = db.Column(db.String(20), unique=True, nullable=False)
    customer_name = db.Column(db.String(200), nullable=False)
    mobile_primary = db.Column(db.String(15), nullable=False, index=True)
    mobile_alternate = db.Column(db.String(15), nullable=True)
    email = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(100), nullable=True)
    pincode = db.Column(db.String(10), nullable=True)
    occupation = db.Column(db.String(100), nullable=True)
    employer_name = db.Column(db.String(200), nullable=True)
    monthly_income = db.Column(db.Float, nullable=True)
    annual_income = db.Column(db.Float, nullable=True)

    cibil_score = db.Column(db.Integer, nullable=True)

    loan_type = db.Column(
        db.Enum(*LOAN_TYPES, name="loan_type_enum"),
        nullable=False,
        index=True,
    )
    loan_amount_applied = db.Column(db.Float, nullable=True)
    bank_preferred = db.Column(db.String(150), nullable=True)

    lead_source = db.Column(
        db.Enum(*LEAD_SOURCES, name="lead_source_enum"),
        nullable=True,
    )
    priority_tag = db.Column(
        db.Enum(*PRIORITY_TAGS, name="priority_tag_enum"),
        nullable=True,
        default="Warm",
    )
    is_high_value = db.Column(db.Boolean, default=False, nullable=False)

    is_duplicate = db.Column(db.Boolean, default=False, nullable=False)
    duplicate_of_lead_id = db.Column(
        PGUUID(as_uuid=True),
        db.ForeignKey("leads.id"),
        nullable=True,
    )

    assigned_executive_id = db.Column(
        PGUUID(as_uuid=True),
        db.ForeignKey("users.id"),
        nullable=True,
        index=True,
    )
    assigned_admin_id = db.Column(
        PGUUID(as_uuid=True),
        db.ForeignKey("users.id"),
        nullable=True,
    )
    branch_id = db.Column(
        PGUUID(as_uuid=True),
        db.ForeignKey("branches.id"),
        nullable=True,
        index=True,
    )
    created_by = db.Column(
        PGUUID(as_uuid=True),
        db.ForeignKey("users.id"),
        nullable=True,
    )

    pipeline_stage = db.Column(
        db.Enum(*PIPELINE_STAGES, name="pipeline_stage_enum"),
        nullable=False,
        default="New Lead",
        index=True,
    )
    stage_updated_at = db.Column(db.DateTime(timezone=True), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    assigned_executive = db.relationship(
        "User",
        foreign_keys=[assigned_executive_id],
        backref="assigned_leads",
    )
    assigned_admin = db.relationship("User", foreign_keys=[assigned_admin_id])
    creator = db.relationship("User", foreign_keys=[created_by])
    branch = db.relationship("Branch", backref="leads")
    status_history = db.relationship(
        "LeadStatusHistory",
        backref="lead",
        lazy="dynamic",
        cascade="all, delete-orphan",
        order_by="LeadStatusHistory.changed_at.desc()",
    )
    financials = db.relationship(
        "ClientFinancial",
        backref="lead",
        uselist=False,
        cascade="all, delete-orphan",
    )
    documents = db.relationship(
        "Document",
        backref="lead",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    bank_applications = db.relationship(
        "BankApplication",
        backref="lead",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    remarks = db.relationship(
        "Remark",
        backref="lead",
        lazy="dynamic",
        cascade="all, delete-orphan",
        order_by="Remark.created_at.desc()",
    )
    commissions = db.relationship(
        "Commission",
        backref="lead",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        db.Index("ix_leads_duplicate_check", "mobile_primary", "loan_type"),
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.lead_number:
            self.lead_number = self._generate_lead_number()
        if self.loan_amount_applied and self.loan_amount_applied >= 5000000:
            self.is_high_value = True

    @staticmethod
    def _generate_lead_number() -> str:
        import random

        year = datetime.now().year
        return f"LD-{year}-{random.randint(10000, 99999)}"

    @property
    def cibil_color(self) -> str:
        if not self.cibil_score:
            return "gray"
        if self.cibil_score >= 750:
            return "green"
        if self.cibil_score >= 650:
            return "yellow"
        return "red"

    @property
    def stage_color(self) -> str:
        return PIPELINE_STAGE_COLORS.get(self.pipeline_stage, "gray")

    @property
    def days_in_current_stage(self) -> int:
        ref = self.stage_updated_at or self.created_at
        if ref:
            return (datetime.now(timezone.utc) - ref).days
        return 0

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update(
            {
                "lead_number": self.lead_number,
                "customer_name": self.customer_name,
                "mobile_primary": self.mobile_primary,
                "email": self.email,
                "city": self.city,
                "state": self.state,
                "loan_type": self.loan_type,
                "loan_amount_applied": self.loan_amount_applied,
                "cibil_score": self.cibil_score,
                "cibil_color": self.cibil_color,
                "lead_source": self.lead_source,
                "priority_tag": self.priority_tag,
                "is_high_value": self.is_high_value,
                "pipeline_stage": self.pipeline_stage,
                "stage_color": self.stage_color,
                "days_in_current_stage": self.days_in_current_stage,
                "assigned_executive_id": str(self.assigned_executive_id)
                if self.assigned_executive_id
                else None,
                "branch_id": str(self.branch_id) if self.branch_id else None,
                "is_active": self.is_active,
            }
        )
        return base


class LeadStatusHistory(BaseModel):
    """Track every pipeline stage change for a lead."""

    __tablename__ = "lead_status_history"

    lead_id = db.Column(
        PGUUID(as_uuid=True),
        db.ForeignKey("leads.id"),
        nullable=False,
        index=True,
    )
    from_stage = db.Column(
        db.Enum(*PIPELINE_STAGES, name="pipeline_stage_enum"),
        nullable=True,
    )
    to_stage = db.Column(
        db.Enum(*PIPELINE_STAGES, name="pipeline_stage_enum"),
        nullable=False,
    )
    changed_by = db.Column(
        PGUUID(as_uuid=True),
        db.ForeignKey("users.id"),
        nullable=True,
    )
    changed_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    note = db.Column(db.Text, nullable=True)

    changer = db.relationship("User", foreign_keys=[changed_by])

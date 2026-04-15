from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.extensions import db
from app.models.base import BaseModel


APPLICATION_STATUSES = [
    "Pending",
    "Submitted",
    "Processing",
    "Approved",
    "Rejected",
]

PAYOUT_CYCLES = ["Monthly", "On Disbursal", "Quarterly"]

CORPORATE_PARTNERS = [
    "Andromeda",
    "DSA Direct",
    "Ruloans",
    "BankBazaar",
    "Other",
]


class BankApplication(BaseModel):
    """A bank/NBFC application submitted for a lead."""

    __tablename__ = "bank_applications"

    lead_id = db.Column(
        PGUUID(as_uuid=True),
        db.ForeignKey("leads.id"),
        nullable=False,
        index=True,
    )
    bank_partner_id = db.Column(
        PGUUID(as_uuid=True),
        db.ForeignKey("bank_partners.id"),
        nullable=True,
    )

    bank_name = db.Column(db.String(150), nullable=True)
    nbfc_name = db.Column(db.String(150), nullable=True)
    corporate_partner = db.Column(db.String(50), nullable=True)
    app_reference_number = db.Column(db.String(100), nullable=True)
    applied_date = db.Column(db.DateTime(timezone=True), nullable=True)
    status = db.Column(
        db.Enum(*APPLICATION_STATUSES, name="bank_app_status_enum"),
        nullable=False,
        default="Pending",
    )

    commission_rate_pct = db.Column(db.Float, nullable=True)
    expected_commission = db.Column(db.Float, nullable=True)
    payout_cycle = db.Column(
        db.Enum(*PAYOUT_CYCLES, name="payout_cycle_enum"),
        nullable=True,
    )

    payout_received_date = db.Column(db.DateTime(timezone=True), nullable=True)
    payout_amount_received = db.Column(db.Float, nullable=True, default=0.0)
    pending_payout = db.Column(db.Float, nullable=True, default=0.0)
    remarks = db.Column(db.Text, nullable=True)

    bank_partner = db.relationship("BankPartner", backref="applications")

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update(
            {
                "lead_id": str(self.lead_id),
                "bank_partner_id": str(self.bank_partner_id)
                if self.bank_partner_id
                else None,
                "bank_name": self.bank_name,
                "corporate_partner": self.corporate_partner,
                "app_reference_number": self.app_reference_number,
                "status": self.status,
                "commission_rate_pct": self.commission_rate_pct,
                "expected_commission": self.expected_commission,
                "payout_cycle": self.payout_cycle,
                "payout_amount_received": self.payout_amount_received,
                "pending_payout": self.pending_payout,
            }
        )
        return base

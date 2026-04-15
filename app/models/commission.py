from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.extensions import db
from app.models.base import BaseModel


PAYOUT_STATUSES = ["Pending", "Partial", "Received"]


class Commission(BaseModel):
    """Commission record for a disbursed lead."""

    __tablename__ = "commissions"

    lead_id = db.Column(
        PGUUID(as_uuid=True),
        db.ForeignKey("leads.id"),
        nullable=False,
        index=True,
    )
    bank_application_id = db.Column(
        PGUUID(as_uuid=True),
        db.ForeignKey("bank_applications.id"),
        nullable=True,
    )
    gross_commission = db.Column(db.Float, nullable=False, default=0.0)
    tds_rate_pct = db.Column(db.Float, nullable=True, default=5.0)
    tds_amount = db.Column(db.Float, nullable=True, default=0.0)
    net_after_tds = db.Column(db.Float, nullable=True, default=0.0)
    company_share_pct = db.Column(db.Float, nullable=True, default=40.0)
    company_amount = db.Column(db.Float, nullable=True, default=0.0)
    admin_share_pct = db.Column(db.Float, nullable=True, default=20.0)
    admin_amount = db.Column(db.Float, nullable=True, default=0.0)
    employee_share_pct = db.Column(db.Float, nullable=True, default=40.0)
    employee_amount = db.Column(db.Float, nullable=True, default=0.0)
    employee_id = db.Column(
        PGUUID(as_uuid=True),
        db.ForeignKey("users.id"),
        nullable=True,
        index=True,
    )
    payout_status = db.Column(
        db.Enum(*PAYOUT_STATUSES, name="payout_status_enum"),
        nullable=False,
        default="Pending",
    )
    payout_received_date = db.Column(db.DateTime(timezone=True), nullable=True)
    invoice_id = db.Column(
        PGUUID(as_uuid=True),
        db.ForeignKey("invoices.id"),
        nullable=True,
    )
    payment_reference = db.Column(db.String(200), nullable=True)
    remarks = db.Column(db.Text, nullable=True)

    employee = db.relationship("User", foreign_keys=[employee_id], backref="commissions")
    bank_application = db.relationship("BankApplication", backref="commission")
    invoice = db.relationship("Invoice", backref="commissions")

    def calculate_splits(self) -> None:
        self.tds_amount = round(
            self.gross_commission * (self.tds_rate_pct or 0) / 100,
            2,
        )
        self.net_after_tds = round(self.gross_commission - self.tds_amount, 2)
        self.company_amount = round(
            self.net_after_tds * (self.company_share_pct or 0) / 100,
            2,
        )
        self.admin_amount = round(
            self.net_after_tds * (self.admin_share_pct or 0) / 100,
            2,
        )
        self.employee_amount = round(
            self.net_after_tds * (self.employee_share_pct or 0) / 100,
            2,
        )

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update(
            {
                "lead_id": str(self.lead_id),
                "gross_commission": self.gross_commission,
                "tds_rate_pct": self.tds_rate_pct,
                "tds_amount": self.tds_amount,
                "net_after_tds": self.net_after_tds,
                "company_share_pct": self.company_share_pct,
                "company_amount": self.company_amount,
                "admin_share_pct": self.admin_share_pct,
                "admin_amount": self.admin_amount,
                "employee_share_pct": self.employee_share_pct,
                "employee_amount": self.employee_amount,
                "payout_status": self.payout_status,
                "employee_id": str(self.employee_id) if self.employee_id else None,
            }
        )
        return base

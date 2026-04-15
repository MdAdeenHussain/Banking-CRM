from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.extensions import db
from app.models.base import BaseModel


class ClientFinancial(BaseModel):
    """Financial details of a sanctioned/disbursed loan for a lead."""

    __tablename__ = "client_financials"

    lead_id = db.Column(
        PGUUID(as_uuid=True),
        db.ForeignKey("leads.id"),
        nullable=False,
        unique=True,
        index=True,
    )
    loan_amount_sanctioned = db.Column(db.Float, nullable=True)
    loan_amount_disbursed = db.Column(db.Float, nullable=True)
    disbursed_date = db.Column(db.DateTime(timezone=True), nullable=True)
    loan_account_number = db.Column(db.String(50), nullable=True, index=True)
    emi_amount = db.Column(db.Float, nullable=True)
    emi_start_date = db.Column(db.DateTime(timezone=True), nullable=True)
    loan_tenure_months = db.Column(db.Integer, nullable=True)
    interest_rate_pa = db.Column(db.Float, nullable=True)
    sanction_validity_date = db.Column(db.DateTime(timezone=True), nullable=True)
    processing_fee_charged = db.Column(db.Float, nullable=True)
    insurance_taken = db.Column(db.Boolean, default=False, nullable=False)
    insurance_amount = db.Column(db.Float, nullable=True)
    remarks = db.Column(db.Text, nullable=True)

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update(
            {
                "lead_id": str(self.lead_id),
                "loan_amount_sanctioned": self.loan_amount_sanctioned,
                "loan_amount_disbursed": self.loan_amount_disbursed,
                "disbursed_date": self.disbursed_date.isoformat()
                if self.disbursed_date
                else None,
                "loan_account_number": self.loan_account_number,
                "emi_amount": self.emi_amount,
                "loan_tenure_months": self.loan_tenure_months,
                "interest_rate_pa": self.interest_rate_pa,
                "insurance_taken": self.insurance_taken,
            }
        )
        return base

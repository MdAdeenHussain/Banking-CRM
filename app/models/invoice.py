from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.extensions import db
from app.models.base import BaseModel


PAYMENT_STATUSES = ["Unpaid", "Partial", "Paid"]


class Invoice(BaseModel):
    """A GST-compliant invoice for commission payouts."""

    __tablename__ = "invoices"

    invoice_number = db.Column(db.String(30), unique=True, nullable=False)
    invoice_date = db.Column(db.DateTime(timezone=True), nullable=False)
    due_date = db.Column(db.DateTime(timezone=True), nullable=True)
    party_name = db.Column(db.String(200), nullable=False)
    party_address = db.Column(db.Text, nullable=True)
    party_gstin = db.Column(db.String(15), nullable=True)
    line_items = db.Column(JSONB, nullable=False, default=list)
    subtotal = db.Column(db.Float, nullable=False, default=0.0)
    cgst_rate = db.Column(db.Float, nullable=True, default=9.0)
    cgst_amount = db.Column(db.Float, nullable=True, default=0.0)
    sgst_rate = db.Column(db.Float, nullable=True, default=9.0)
    sgst_amount = db.Column(db.Float, nullable=True, default=0.0)
    igst_rate = db.Column(db.Float, nullable=True, default=0.0)
    igst_amount = db.Column(db.Float, nullable=True, default=0.0)
    total_amount = db.Column(db.Float, nullable=False, default=0.0)
    amount_in_words = db.Column(db.String(500), nullable=True)
    payment_status = db.Column(
        db.Enum(*PAYMENT_STATUSES, name="payment_status_enum"),
        nullable=False,
        default="Unpaid",
    )
    payment_method = db.Column(db.String(50), nullable=True)
    payment_reference = db.Column(db.String(200), nullable=True)
    paid_date = db.Column(db.DateTime(timezone=True), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    generated_by = db.Column(
        PGUUID(as_uuid=True),
        db.ForeignKey("users.id"),
        nullable=True,
    )
    commission_id = db.Column(PGUUID(as_uuid=True), nullable=True)
    pdf_path = db.Column(db.String(500), nullable=True)

    generator = db.relationship("User", foreign_keys=[generated_by])

    def calculate_totals(self) -> None:
        items = self.line_items or []
        self.subtotal = round(sum(item.get("amount", 0) for item in items), 2)
        if self.igst_rate and self.igst_rate > 0:
            self.igst_amount = round(self.subtotal * self.igst_rate / 100, 2)
            self.cgst_amount = 0.0
            self.sgst_amount = 0.0
            self.total_amount = round(self.subtotal + self.igst_amount, 2)
        else:
            self.cgst_amount = round(self.subtotal * (self.cgst_rate or 0) / 100, 2)
            self.sgst_amount = round(self.subtotal * (self.sgst_rate or 0) / 100, 2)
            self.igst_amount = 0.0
            self.total_amount = round(
                self.subtotal + self.cgst_amount + self.sgst_amount,
                2,
            )

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update(
            {
                "invoice_number": self.invoice_number,
                "invoice_date": self.invoice_date.isoformat()
                if self.invoice_date
                else None,
                "due_date": self.due_date.isoformat() if self.due_date else None,
                "party_name": self.party_name,
                "party_gstin": self.party_gstin,
                "subtotal": self.subtotal,
                "total_amount": self.total_amount,
                "payment_status": self.payment_status,
                "line_items": self.line_items,
            }
        )
        return base

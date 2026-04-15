from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.extensions import db
from app.models.base import BaseModel


BANK_TYPES = ["Bank", "NBFC", "Corporate"]


class UserBankPartner(db.Model):
    __tablename__ = "user_bank_partners"

    user_id = db.Column(
        PGUUID(as_uuid=True),
        db.ForeignKey("users.id"),
        primary_key=True,
        nullable=False,
    )
    bank_partner_id = db.Column(
        PGUUID(as_uuid=True),
        db.ForeignKey("bank_partners.id"),
        primary_key=True,
        nullable=False,
    )


class BankPartner(BaseModel):
    """A bank, NBFC, or corporate partner for loan distribution."""

    __tablename__ = "bank_partners"

    name = db.Column(db.String(150), nullable=False, unique=True)
    type = db.Column(
        db.Enum(*BANK_TYPES, name="bank_type_enum"),
        nullable=False,
        default="Bank",
    )
    contact_person = db.Column(db.String(150), nullable=True)
    contact_mobile = db.Column(db.String(15), nullable=True)
    contact_email = db.Column(db.String(255), nullable=True)
    commission_rate_default_pct = db.Column(db.Float, default=0.0, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update(
            {
                "name": self.name,
                "type": self.type,
                "contact_person": self.contact_person,
                "contact_mobile": self.contact_mobile,
                "contact_email": self.contact_email,
                "commission_rate_default_pct": self.commission_rate_default_pct,
                "is_active": self.is_active,
            }
        )
        return base

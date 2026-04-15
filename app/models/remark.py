from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.extensions import db
from app.models.base import BaseModel


REMARK_TYPES = ["General", "Call", "WhatsApp", "Email", "Visit"]

CALL_OUTCOMES = [
    "Connected",
    "No Answer",
    "Busy",
    "Switched Off",
    "Wrong Number",
    "Call Back Later",
    "Interested",
    "Not Interested",
    "Converted",
]


class Remark(BaseModel):
    """A remark or note attached to a lead."""

    __tablename__ = "remarks"

    lead_id = db.Column(
        PGUUID(as_uuid=True),
        db.ForeignKey("leads.id"),
        nullable=False,
        index=True,
    )
    remark_type = db.Column(
        db.Enum(*REMARK_TYPES, name="remark_type_enum"),
        nullable=False,
        default="General",
    )
    content = db.Column(db.Text, nullable=False)
    call_duration_min = db.Column(db.Integer, nullable=True)
    call_outcome = db.Column(db.String(30), nullable=True)
    created_by = db.Column(
        PGUUID(as_uuid=True),
        db.ForeignKey("users.id"),
        nullable=True,
    )

    author = db.relationship("User", foreign_keys=[created_by])

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update(
            {
                "lead_id": str(self.lead_id),
                "remark_type": self.remark_type,
                "content": self.content,
                "call_duration_min": self.call_duration_min,
                "call_outcome": self.call_outcome,
                "created_by": str(self.created_by) if self.created_by else None,
            }
        )
        return base

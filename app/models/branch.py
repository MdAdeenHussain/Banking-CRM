from app.extensions import db
from app.models.base import BaseModel


class Branch(BaseModel):
    """Branch office of the DSA agency."""

    __tablename__ = "branches"

    name = db.Column(db.String(150), nullable=False, unique=True)
    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(100), nullable=True)
    address = db.Column(db.String(500), nullable=True)
    gstin = db.Column(db.String(15), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update(
            {
                "name": self.name,
                "city": self.city,
                "state": self.state,
                "address": self.address,
                "gstin": self.gstin,
                "is_active": self.is_active,
            }
        )
        return base

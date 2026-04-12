"""
LoanAxis CRM — Branch Model

Represents physical branch offices of the DSA agency.
"""

from sqlalchemy import Column, String, Boolean

from app.models.base import BaseModel


class Branch(BaseModel):
    """Branch office of the DSA agency."""

    __tablename__ = "branches"

    name = Column(String(150), nullable=False, unique=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    address = Column(String(500), nullable=True)
    gstin = Column(String(15), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update({
            "name": self.name,
            "city": self.city,
            "state": self.state,
            "address": self.address,
            "gstin": self.gstin,
            "is_active": self.is_active,
        })
        return base

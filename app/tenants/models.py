"""
app/tenants/models.py
Tenant and Branch models for multi-tenant isolation.
"""

from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy import Index, UniqueConstraint
from app.extensions import db
from app.common.mixins import BaseTenantModel, utcnow
from uuid import uuid4


class Tenant(db.Model):
    """
    Tenant (DSA/Company) in the multi-tenant system.
    This is the top-level entity for data isolation.
    
    Every other entity must have a tenant_id foreign key.
    """
    __tablename__ = "tenants"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()), nullable=False)
    
    # Tenant Details
    name = db.Column(db.String(255), nullable=False, comment="Company/Tenant name")
    slug = db.Column(
        db.String(100),
        nullable=False,
        unique=True,
        index=True,
        comment="URL-friendly slug (e.g. 'acme-loans')"
    )
    domain = db.Column(
        db.String(255),
        nullable=True,
        unique=True,
        comment="Custom domain (for white-label)"
    )
    
    # Contact
    email = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    
    # Plan & Status
    plan_type = db.Column(
        db.String(50),
        default="STARTER",
        comment="SaaS plan: STARTER, GROWTH, ENTERPRISE, CUSTOM (Phase 3)"
    )
    status = db.Column(
        db.String(50),
        default="ACTIVE",
        comment="ACTIVE, SUSPENDED, TRIAL, INACTIVE"
    )
    
    # Branding (Phase 3)
    logo_url = db.Column(db.String(500), nullable=True, comment="Logo URL (Phase 3)")
    primary_color = db.Column(db.String(7), nullable=True, comment="Brand color hex (Phase 3)")
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow, nullable=False)
    
    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False, index=True)

    # Relationships
    branches = db.relationship("Branch", backref="tenant", lazy=True, cascade="all, delete-orphan")
    users = db.relationship("User", backref="tenant", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Tenant {self.name} ({self.slug})>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "slug": self.slug,
            "domain": self.domain,
            "email": self.email,
            "phone": self.phone,
            "plan_type": self.plan_type,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_active": self.is_active,
        }


class Branch(BaseTenantModel):
    """
    Branch under a Tenant.
    Agents and leads are organized by branch.
    """
    __tablename__ = "branches"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_branch_tenant_code"),
        Index("idx_branch_tenant", "tenant_id"),
    )

    # Override tenant_id with ForeignKey constraint
    tenant_id = db.Column(
        db.String(36),
        db.ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Branch Info
    name = db.Column(db.String(255), nullable=False, comment="Branch name")
    code = db.Column(
        db.String(50),
        nullable=False,
        comment="Unique code (e.g. 'BR-101')"
    )
    city = db.Column(db.String(100), nullable=True, comment="City/Location")
    
    # Branch Manager
    manager_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id"),
        nullable=True,
        comment="Branch manager user ID"
    )
    
    # Address
    address = db.Column(db.Text, nullable=True)
    
    # Contact
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(255), nullable=True)

    # Relationships
    manager = db.relationship("User", backref="managed_branch")

    def __repr__(self):
        return f"<Branch {self.code} - {self.name}>"

    def to_dict(self):
        data = super().to_dict()
        data.update({
            "name": self.name,
            "code": self.code,
            "city": self.city,
            "manager_id": str(self.manager_id) if self.manager_id else None,
            "phone": self.phone,
            "email": self.email,
        })
        return data

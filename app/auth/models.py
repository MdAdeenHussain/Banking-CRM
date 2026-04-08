"""
app/auth/models.py
User, Role, Permission, UserRole, and UserSession models.
Core authentication and authorization entities.
"""

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Index, UniqueConstraint, DateTime
from app.extensions import db
from app.common.mixins import BaseTenantModel, utcnow
from uuid import uuid4
from datetime import datetime, timedelta
import bcrypt
import jwt
import os


class User(BaseTenantModel):
    """
    User in the system (linked to a Tenant).
    Supports multiple roles per user via UserRole junction table.
    """
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_user_tenant_email"),
        Index("idx_user_email", "email"),
        Index("idx_user_tenant", "tenant_id"),
    )

    # Override tenant_id with ForeignKey constraint
    tenant_id = db.Column(
        db.String(36),
        db.ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Identity
    email = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    
    # Authentication
    password_hash = db.Column(db.String(255), nullable=False, comment="Bcrypt hash")
    
    # Email Verification
    is_email_verified = db.Column(
        db.Boolean,
        default=False,
        nullable=False,
        comment="Email verification status"
    )
    email_verified_at = db.Column(
        DateTime,
        nullable=True,
        comment="Timestamp of email verification"
    )
    
    # Last Activity
    last_login_at = db.Column(
        DateTime,
        nullable=True,
        comment="Last login timestamp"
    )
    last_login_ip = db.Column(db.String(50), nullable=True)
    
    # Account Status
    is_locked = db.Column(
        db.Boolean,
        default=False,
        comment="Locked due to brute force attempts"
    )
    locked_until = db.Column(
        DateTime,
        nullable=True,
        comment="When the account lock expires"
    )
    failed_login_attempts = db.Column(
        db.Integer,
        default=0,
        comment="Failed login attempt counter"
    )

    # Relationships
    roles = db.relationship(
        "Role",
        secondary="user_roles",
        backref=db.backref("users", lazy=True),
        lazy=True,
        viewonly=True
    )
    sessions = db.relationship(
        "UserSession",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan",
        foreign_keys="UserSession.user_id"
    )

    def get_id(self):
        """Required by Flask-Login for session management."""
        return str(self.id)

    @property
    def is_authenticated(self):
        """Required by Flask-Login."""
        return True

    @property
    def is_anonymous(self):
        """Required by Flask-Login."""
        return False

    def __repr__(self):
        return f"<User {self.email}>"

    def set_password(self, password: str):
        """Hash and set password using bcrypt."""
        self.password_hash = bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

    def check_password(self, password: str) -> bool:
        """Verify password against hash."""
        return bcrypt.checkpw(
            password.encode("utf-8"),
            self.password_hash.encode("utf-8")
        )

    def generate_jwt_tokens(self) -> dict:
        """
        Generate JWT access and refresh tokens.
        
        PHASE_2_HOOK: Implement full JWT logic with claims
        """
        secret_key = os.getenv("JWT_SECRET_KEY", "dev-secret")
        
        access_token = jwt.encode(
            {
                "user_id": str(self.id),
                "tenant_id": str(self.tenant_id),
                "email": self.email,
                "exp": datetime.utcnow() + timedelta(minutes=15)
            },
            secret_key,
            algorithm="HS256"
        )
        
        refresh_token = jwt.encode(
            {
                "user_id": str(self.id),
                "tenant_id": str(self.tenant_id),
                "type": "refresh",
                "exp": datetime.utcnow() + timedelta(days=7)
            },
            secret_key,
            algorithm="HS256"
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer"
        }

    def to_dict(self):
        data = super().to_dict()
        data.update({
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "phone": self.phone,
            "is_email_verified": self.is_email_verified,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "is_locked": self.is_locked,
        })
        return data


class Role(db.Model):
    """
    Role in the system (not tenant-specific, but assigned per tenant).
    Examples: super_admin, tenant_admin, branch_manager, agent, etc.
    """
    __tablename__ = "roles"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    name = db.Column(
        db.String(50),
        nullable=False,
        unique=True,
        index=True,
        comment="Role name (e.g. 'agent')"
    )
    description = db.Column(db.String(500), nullable=True)
    
    created_at = db.Column(DateTime, default=utcnow, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)

    # Relationships
    permissions = db.relationship(
        "Permission",
        secondary="role_permissions",
        backref=db.backref("roles", lazy=True),
        lazy=True,
    )

    def __repr__(self):
        return f"<Role {self.name}>"


class Permission(db.Model):
    """
    Permission (global, not tenant-specific).
    Examples: "create_lead", "approve_application", etc.
    """
    __tablename__ = "permissions"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    name = db.Column(
        db.String(100),
        nullable=False,
        unique=True,
        index=True,
        comment="Permission name (e.g. 'create_lead')"
    )
    description = db.Column(db.String(500), nullable=True)
    module = db.Column(db.String(50), nullable=True, comment="Module (e.g. 'leads')")
    
    created_at = db.Column(DateTime, default=utcnow, nullable=False)

    def __repr__(self):
        return f"<Permission {self.name}>"


class UserRole(db.Model):
    """
    Junction table: User has Roles within a Tenant.
    One user can have multiple roles (e.g., branch_manager + compliance).
    """
    __tablename__ = "user_roles"
    __table_args__ = (
        UniqueConstraint("user_id", "role_id", "tenant_id", name="uq_user_role_tenant"),
        Index("idx_user_role_tenant", "user_id", "tenant_id"),
    )

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    
    user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    role_id = db.Column(
        db.String(36),
        db.ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False
    )
    tenant_id = db.Column(
        db.String(36),
        db.ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    assigned_at = db.Column(DateTime, default=utcnow, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)

    # Relationships
    user = db.relationship("User", backref="user_roles")
    role = db.relationship("Role")

    def __repr__(self):
        return f"<UserRole user={self.user_id} role={self.role_id}>"


class UserSession(BaseTenantModel):
    """
    User session record for tracking logins and device management.
    """
    __tablename__ = "user_sessions"
    __table_args__ = (
        Index("idx_session_user", "user_id"),
        Index("idx_session_token", "session_token"),
    )

    user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    session_token = db.Column(
        db.String(500),
        nullable=False,
        unique=True,
        comment="JWT or session token"
    )
    
    # Request Info
    ip_address = db.Column(db.String(50), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)
    device_name = db.Column(db.String(255), nullable=True)
    
    # Expiry
    expires_at = db.Column(
        DateTime,
        nullable=False,
        comment="Session expiration time"
    )
    
    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)

    def __repr__(self):
        return f"<UserSession user={self.user_id}>"

    def to_dict(self):
        data = super().to_dict()
        data.update({
            "user_id": str(self.user_id),
            "ip_address": self.ip_address,
            "device_name": self.device_name,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        })
        return data


# ============================================================================
# JUNCTION TABLE FOR ROLE-PERMISSION MAPPING
# ============================================================================
role_permissions = db.Table(
    "role_permissions",
    db.Column(
        "role_id",
        db.String(36),
        db.ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True
    ),
    db.Column(
        "permission_id",
        db.String(36),
        db.ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True
    ),
)

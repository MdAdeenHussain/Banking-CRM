"""Authentication service layer.

Business logic for login and registration is isolated here so route files
stay focused on HTTP concerns (requests/responses).
"""

# =====================================
# SECTION: Imports
# =====================================
from datetime import datetime, timezone

from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models.tenant import Tenant
from app.models.user import User


# =====================================
# SECTION: Service Definition
# =====================================
class AuthService:
    """Service methods for auth workflows."""

    @staticmethod
    def authenticate_user(*, tenant_slug: str, email: str, password: str) -> User | None:
        """Authenticate user by tenant + email + password."""
        user = (
            User.query.options(joinedload(User.tenant))
            .join(Tenant, Tenant.id == User.tenant_id)
            .filter(
                Tenant.slug == tenant_slug,
                User.email == email,
                User.is_deleted.is_(False),
                User.is_active.is_(True),
                Tenant.is_deleted.is_(False),
                Tenant.is_active.is_(True),
            )
            .first()
        )

        if not user or not user.check_password(password):
            return None

        user.last_login = datetime.now(timezone.utc)
        db.session.commit()
        return user

    @staticmethod
    def register_tenant(*, company_name: str, slug: str, admin_name: str, admin_email: str, admin_phone: str | None, password: str) -> tuple[bool, str, Tenant | None]:
        """Create tenant and owner user in one transaction."""
        if Tenant.query.filter_by(slug=slug).first():
            return False, "Tenant slug already exists.", None

        tenant = Tenant(company_name=company_name, slug=slug)
        db.session.add(tenant)
        db.session.flush()

        owner = User(
            tenant_id=tenant.id,
            name=admin_name,
            email=admin_email,
            role="owner",
            phone=admin_phone,
            is_verified=False,
        )
        owner.set_password(password)
        db.session.add(owner)
        db.session.commit()

        return True, "Tenant registration successful. Please log in.", tenant

    @staticmethod
    def register_user(*, tenant_id: int, name: str, email: str, password: str, role: str, phone: str | None = None) -> tuple[bool, str, User | None]:
        """Create tenant-scoped user record."""
        existing = User.query.filter_by(tenant_id=tenant_id, email=email).first()
        if existing:
            return False, "User email already exists in this tenant.", None

        user = User(
            tenant_id=tenant_id,
            name=name,
            email=email,
            role=role,
            phone=phone,
            is_verified=False,
        )
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        return True, "User registration successful.", user

    @staticmethod
    def role_redirect_path(role: str) -> str:
        """Map user role to dashboard path."""
        role_map = {
            "owner": "/dashboard/owner",
            "branch": "/dashboard/branch",
            "agent": "/dashboard/agent",
            "platform": "/dashboard/platform",
        }
        return role_map.get(role.lower(), "/dashboard/agent")

    # Future AI placeholder:
    # - risk-based login challenge orchestration

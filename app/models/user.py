import secrets
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
from flask_login import UserMixin
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.extensions import db, login_manager
from app.models.base import BaseModel


USER_ROLES = ["super_admin", "admin", "employee"]
LOGIN_STATUSES = ["success", "failed", "locked"]


class User(UserMixin, BaseModel):
    """Core user model for Flask-Login and staff management."""

    __tablename__ = "users"

    employee_id = db.Column(db.String(20), unique=True, nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    mobile = db.Column(db.String(15), nullable=False)
    profile_photo_path = db.Column(db.String(500), nullable=True)

    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(
        db.Enum(*USER_ROLES, name="user_role_enum"),
        nullable=False,
        default="employee",
        index=True,
    )

    branch_id = db.Column(
        PGUUID(as_uuid=True),
        db.ForeignKey("branches.id"),
        nullable=True,
    )

    is_2fa_enabled = db.Column(db.Boolean, default=False, nullable=False)
    otp_hash = db.Column(db.String(255), nullable=True)
    otp_created_at = db.Column(db.DateTime(timezone=True), nullable=True)

    is_active_flag = db.Column("is_active", db.Boolean, default=True, nullable=False)
    failed_login_attempts = db.Column(db.Integer, default=0, nullable=False)
    locked_until = db.Column(db.DateTime(timezone=True), nullable=True)
    last_login_at = db.Column(db.DateTime(timezone=True), nullable=True)

    created_by = db.Column(
        PGUUID(as_uuid=True),
        db.ForeignKey("users.id"),
        nullable=True,
    )
    reporting_to = db.Column(
        PGUUID(as_uuid=True),
        db.ForeignKey("users.id"),
        nullable=True,
    )
    joining_date = db.Column(db.DateTime(timezone=True), nullable=True)
    deactivated_at = db.Column(db.DateTime(timezone=True), nullable=True)
    deactivation_reason = db.Column(db.Text, nullable=True)

    remember_token_hash = db.Column(db.String(255), nullable=True)
    remember_token_expires = db.Column(db.DateTime(timezone=True), nullable=True)

    branch = db.relationship("Branch", backref="users", lazy="select")
    sessions = db.relationship(
        "UserSession",
        backref="user",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    login_activities = db.relationship(
        "LoginActivity",
        backref="user",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    bank_partners = db.relationship(
        "BankPartner",
        secondary="user_bank_partners",
        backref="assigned_users",
        lazy="select",
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.employee_id:
            self.employee_id = self._generate_employee_id()

    @staticmethod
    def _generate_employee_id() -> str:
        import random

        return f"EMP-{random.randint(10000, 99999)}"

    def set_password(self, password: str) -> None:
        salt = bcrypt.gensalt(rounds=4)
        self.password_hash = bcrypt.hashpw(
            password.encode("utf-8"),
            salt,
        ).decode("utf-8")

    def check_password(self, password: str) -> bool:
        if not self.password_hash:
            return False
        return bcrypt.checkpw(
            password.encode("utf-8"),
            self.password_hash.encode("utf-8"),
        )

    def is_locked(self) -> bool:
        if self.locked_until and self.locked_until > datetime.now(timezone.utc):
            return True
        if self.locked_until and self.locked_until <= datetime.now(timezone.utc):
            self.failed_login_attempts = 0
            self.locked_until = None
        return False

    def record_failed_login(self, max_attempts: int = 5, lockout_minutes: int = 15) -> None:
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= max_attempts:
            self.locked_until = datetime.now(timezone.utc) + timedelta(
                minutes=lockout_minutes
            )

    def record_successful_login(self) -> None:
        self.failed_login_attempts = 0
        self.locked_until = None
        self.last_login_at = datetime.now(timezone.utc)

    def generate_otp(self) -> str:
        otp = f"{secrets.randbelow(900000) + 100000}"
        salt = bcrypt.gensalt(rounds=4)
        self.otp_hash = bcrypt.hashpw(otp.encode("utf-8"), salt).decode("utf-8")
        self.otp_created_at = datetime.now(timezone.utc)
        return otp

    def verify_otp(self, otp: str, expiry_minutes: int = 10) -> bool:
        if not self.otp_hash or not self.otp_created_at:
            return False
        elapsed = (datetime.now(timezone.utc) - self.otp_created_at).total_seconds()
        if elapsed > expiry_minutes * 60:
            self.otp_hash = None
            self.otp_created_at = None
            return False
        valid = bcrypt.checkpw(otp.encode("utf-8"), self.otp_hash.encode("utf-8"))
        if valid:
            self.otp_hash = None
            self.otp_created_at = None
        return valid

    def generate_reset_token(self) -> str:
        token = secrets.token_urlsafe(48)
        salt = bcrypt.gensalt(rounds=4)
        self.remember_token_hash = bcrypt.hashpw(
            token.encode("utf-8"),
            salt,
        ).decode("utf-8")
        self.remember_token_expires = datetime.now(timezone.utc) + timedelta(hours=1)
        return token

    def verify_reset_token(self, token: str) -> bool:
        if not self.remember_token_hash or not self.remember_token_expires:
            return False
        if self.remember_token_expires < datetime.now(timezone.utc):
            self.remember_token_hash = None
            self.remember_token_expires = None
            return False
        valid = bcrypt.checkpw(
            token.encode("utf-8"),
            self.remember_token_hash.encode("utf-8"),
        )
        if valid:
            self.remember_token_hash = None
            self.remember_token_expires = None
        return valid

    @property
    def is_super_admin(self) -> bool:
        return self.role == "super_admin"

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def is_employee(self) -> bool:
        return self.role == "employee"

    def get_id(self) -> str:
        return str(self.id)

    @property
    def is_authenticated(self) -> bool:
        return self.is_active

    @property
    def is_active(self) -> bool:
        return self.is_active_flag

    @is_active.setter
    def is_active(self, value: bool) -> None:
        self.is_active_flag = value

    @property
    def is_anonymous(self) -> bool:
        return False

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update(
            {
                "employee_id": self.employee_id,
                "full_name": self.full_name,
                "email": self.email,
                "mobile": self.mobile,
                "role": self.role,
                "branch_id": str(self.branch_id) if self.branch_id else None,
                "is_active": self.is_active,
                "is_2fa_enabled": self.is_2fa_enabled,
                "last_login_at": self.last_login_at.isoformat()
                if self.last_login_at
                else None,
                "joining_date": self.joining_date.isoformat()
                if self.joining_date
                else None,
            }
        )
        return base


class UserSession(BaseModel):
    """Track active user sessions for security monitoring."""

    __tablename__ = "user_sessions"

    user_id = db.Column(
        PGUUID(as_uuid=True),
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    token_hash = db.Column(db.String(255), nullable=False)
    device_info = db.Column(db.String(500), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    is_valid = db.Column(db.Boolean, default=True, nullable=False)


class LoginActivity(BaseModel):
    """Log every login attempt for security auditing."""

    __tablename__ = "login_activity"

    user_id = db.Column(
        PGUUID(as_uuid=True),
        db.ForeignKey("users.id"),
        nullable=True,
        index=True,
    )
    email_attempted = db.Column(db.String(255), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)
    status = db.Column(
        db.Enum(*LOGIN_STATUSES, name="login_status_enum"),
        nullable=False,
    )
    failure_reason = db.Column(db.String(255), nullable=True)


@login_manager.user_loader
def load_user(user_id: str):
    """Load user by UUID string for Flask-Login."""
    try:
        return User.query.get(uuid.UUID(user_id))
    except (ValueError, AttributeError, TypeError):
        return None

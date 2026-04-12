"""
LoanAxis CRM — User, UserSession, & LoginActivity Models

Handles authentication, session tracking, and login auditing.
"""

import secrets
from datetime import datetime, timezone, timedelta

import bcrypt
from flask_login import UserMixin
from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship

from app.extensions import db
from app.models.base import BaseModel, generate_uuid


class User(UserMixin, BaseModel):
    """
    Core user model supporting three roles: super_admin, admin, employee.

    Password hashed with bcrypt. Supports 2FA via OTP, account lockout,
    and remember-me tokens.
    """

    __tablename__ = "users"

    # ── Identity ────────────────────────────────────────────
    employee_id = Column(String(20), unique=True, nullable=False)
    full_name = Column(String(150), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    mobile = Column(String(15), nullable=False)
    profile_photo_path = Column(String(500), nullable=True)

    # ── Authentication ──────────────────────────────────────
    password_hash = Column(String(255), nullable=False)
    role = Column(
        String(20),
        nullable=False,
        default="employee",
        index=True,
    )

    # ── Branch Assignment ───────────────────────────────────
    branch_id = Column(String(36), ForeignKey("branches.id"), nullable=True)

    # ── 2FA / OTP ───────────────────────────────────────────
    is_2fa_enabled = Column(Boolean, default=False, nullable=False)
    otp_hash = Column(String(255), nullable=True)
    otp_created_at = Column(DateTime(timezone=True), nullable=True)

    # ── Account State ───────────────────────────────────────
    is_active = Column(Boolean, default=True, nullable=False)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    # ── Hierarchy ───────────────────────────────────────────
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    reporting_to = Column(String(36), ForeignKey("users.id"), nullable=True)
    joining_date = Column(DateTime(timezone=True), nullable=True)
    deactivated_at = Column(DateTime(timezone=True), nullable=True)
    deactivation_reason = Column(Text, nullable=True)

    # ── Remember Me Token ───────────────────────────────────
    remember_token_hash = Column(String(255), nullable=True)
    remember_token_expires = Column(DateTime(timezone=True), nullable=True)

    # ── Relationships ───────────────────────────────────────
    branch = relationship("Branch", backref="users", lazy="select")
    sessions = relationship("UserSession", backref="user", lazy="dynamic",
                            cascade="all, delete-orphan")
    login_activities = relationship("LoginActivity", backref="user", lazy="dynamic",
                                    cascade="all, delete-orphan")
    bank_partners = relationship(
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
        """Generate a unique employee ID like EMP-XXXXX."""
        import random
        return f"EMP-{random.randint(10000, 99999)}"

    def set_password(self, password: str) -> None:
        """Hash and store the password using bcrypt."""
        salt = bcrypt.gensalt(rounds=4)  # Overridden by config in production
        self.password_hash = bcrypt.hashpw(
            password.encode("utf-8"), salt
        ).decode("utf-8")

    def check_password(self, password: str) -> bool:
        """Verify a password against the stored hash."""
        if not self.password_hash:
            return False
        return bcrypt.checkpw(
            password.encode("utf-8"),
            self.password_hash.encode("utf-8"),
        )

    def is_locked(self) -> bool:
        """Check if account is locked due to failed login attempts."""
        if self.locked_until and self.locked_until > datetime.now(timezone.utc):
            return True
        # Auto-unlock if lockout period has passed
        if self.locked_until and self.locked_until <= datetime.now(timezone.utc):
            self.failed_login_attempts = 0
            self.locked_until = None
        return False

    def record_failed_login(self, max_attempts: int = 5, lockout_minutes: int = 15) -> None:
        """Increment failed login counter and lock if threshold reached."""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= max_attempts:
            self.locked_until = datetime.now(timezone.utc) + timedelta(minutes=lockout_minutes)

    def record_successful_login(self) -> None:
        """Reset failed login counter and update last login time."""
        self.failed_login_attempts = 0
        self.locked_until = None
        self.last_login_at = datetime.now(timezone.utc)

    def generate_otp(self) -> str:
        """Generate a 6-digit OTP, store its hash, and return the plain OTP."""
        otp = f"{secrets.randbelow(900000) + 100000}"
        salt = bcrypt.gensalt(rounds=4)
        self.otp_hash = bcrypt.hashpw(otp.encode("utf-8"), salt).decode("utf-8")
        self.otp_created_at = datetime.now(timezone.utc)
        return otp

    def verify_otp(self, otp: str, expiry_minutes: int = 10) -> bool:
        """Verify OTP against stored hash. Single-use: cleared after verification."""
        if not self.otp_hash or not self.otp_created_at:
            return False
        # Check expiry
        elapsed = (datetime.now(timezone.utc) - self.otp_created_at).total_seconds()
        if elapsed > expiry_minutes * 60:
            self.otp_hash = None
            self.otp_created_at = None
            return False
        # Verify
        valid = bcrypt.checkpw(otp.encode("utf-8"), self.otp_hash.encode("utf-8"))
        if valid:
            self.otp_hash = None
            self.otp_created_at = None
        return valid

    def generate_reset_token(self) -> str:
        """Generate a password reset token. Returns plain token, stores hash."""
        token = secrets.token_urlsafe(48)
        salt = bcrypt.gensalt(rounds=4)
        self.remember_token_hash = bcrypt.hashpw(
            token.encode("utf-8"), salt
        ).decode("utf-8")
        self.remember_token_expires = datetime.now(timezone.utc) + timedelta(hours=1)
        return token

    def verify_reset_token(self, token: str) -> bool:
        """Verify a password reset token. Single-use."""
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

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update({
            "employee_id": self.employee_id,
            "full_name": self.full_name,
            "email": self.email,
            "mobile": self.mobile,
            "role": self.role,
            "branch_id": self.branch_id,
            "is_active": self.is_active,
            "is_2fa_enabled": self.is_2fa_enabled,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "joining_date": self.joining_date.isoformat() if self.joining_date else None,
        })
        return base


class UserSession(BaseModel):
    """Track active user sessions for security monitoring."""

    __tablename__ = "user_sessions"

    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String(255), nullable=False)
    device_info = Column(String(500), nullable=True)
    ip_address = Column(String(45), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_valid = Column(Boolean, default=True, nullable=False)


class LoginActivity(BaseModel):
    """Log every login attempt for security auditing."""

    __tablename__ = "login_activity"

    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    email_attempted = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    status = Column(String(20), nullable=False)  # "success" | "failed" | "locked"
    failure_reason = Column(String(255), nullable=True)

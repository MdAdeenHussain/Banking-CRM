"""
LoanAxis CRM — Auth Services

Business logic for authentication, OTP, password reset, and login tracking.
Routes call these service functions — never query the DB directly.
"""

from datetime import datetime, timezone
from typing import Optional, Tuple

from flask import current_app, request

from app.extensions import db
from app.models.user import User, LoginActivity


def authenticate_user(email: str, password: str) -> Tuple[Optional[User], str]:
    """
    Authenticate a user by email and password.

    Handles account lockout, failed attempt tracking, and login activity logging.

    Args:
        email: User's email address
        password: Plain-text password to verify

    Returns:
        (user, message) — user is None if authentication fails
    """
    user = User.query.filter_by(email=email.lower().strip(), is_deleted=False).first()

    # User not found
    if not user:
        _log_login_attempt(None, email, "failed", "User not found")
        return None, "Invalid email or password."

    # Account deactivated
    if not user.is_active:
        _log_login_attempt(user.id, email, "failed", "Account deactivated")
        return None, "Your account has been deactivated. Contact your administrator."

    # Account locked
    if user.is_locked():
        _log_login_attempt(user.id, email, "locked", "Account locked")
        return None, "Account is temporarily locked due to too many failed attempts. Please try again later."

    # Wrong password
    if not user.check_password(password):
        max_attempts = current_app.config.get("MAX_LOGIN_ATTEMPTS", 5)
        lockout_minutes = current_app.config.get("LOGIN_LOCKOUT_MINUTES", 15)
        user.record_failed_login(max_attempts, lockout_minutes)
        remaining = max_attempts - user.failed_login_attempts
        db.session.commit()

        _log_login_attempt(user.id, email, "failed", "Wrong password")

        if remaining > 0:
            return None, f"Invalid email or password. {remaining} attempts remaining."
        else:
            return None, f"Account locked for {lockout_minutes} minutes due to too many failed attempts."

    # Successful authentication
    user.record_successful_login()
    db.session.commit()

    _log_login_attempt(user.id, email, "success")

    return user, "Login successful."


def _log_login_attempt(
    user_id: Optional[str],
    email: str,
    status: str,
    failure_reason: str = None,
) -> None:
    """Record a login attempt in the login_activity table."""
    ip_address = None
    user_agent = None

    try:
        ip_address = request.remote_addr
        user_agent = request.headers.get("User-Agent", "")[:500]
    except RuntimeError:
        pass

    activity = LoginActivity(
        user_id=user_id,
        email_attempted=email,
        ip_address=ip_address,
        user_agent=user_agent,
        status=status,
        failure_reason=failure_reason,
    )
    db.session.add(activity)
    db.session.commit()


def register_first_user(full_name: str, email: str, mobile: str, password: str) -> User:
    """
    Register the very first user as Super Admin.

    Only works if no users exist in the system. Subsequent users
    must be created by Super Admin through the admin panel.

    Args:
        full_name: User's display name
        email: Unique email address
        mobile: Mobile number
        password: Plain-text password (will be hashed)

    Returns:
        The created User instance

    Raises:
        ValueError: If users already exist or email is taken
    """
    existing_count = User.query.count()
    if existing_count > 0:
        raise ValueError("Registration is closed. Contact your administrator.")

    if User.query.filter_by(email=email.lower().strip()).first():
        raise ValueError("This email is already registered.")

    user = User(
        full_name=full_name.strip(),
        email=email.lower().strip(),
        mobile=mobile.strip(),
        role="super_admin",
        is_active=True,
        joining_date=datetime.now(timezone.utc),
    )
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    current_app.logger.info(f"Super Admin created: {user.email} ({user.employee_id})")
    return user


def generate_and_send_otp(user: User) -> str:
    """
    Generate a 6-digit OTP and send it via email.

    In development mode (MAIL_SUPPRESS_SEND=True), the OTP is
    logged to the console instead.

    Returns:
        The generated OTP (for dev/testing convenience)
    """
    otp = user.generate_otp()
    db.session.commit()

    # Send OTP email (or log in dev mode)
    if current_app.config.get("MAIL_SUPPRESS_SEND"):
        current_app.logger.info(f"[DEV] OTP for {user.email}: {otp}")
        print(f"\n{'='*50}")
        print(f"  OTP for {user.email}: {otp}")
        print(f"{'='*50}\n")
    else:
        try:
            from flask_mail import Message
            from app.extensions import mail

            msg = Message(
                subject="LoanAxis CRM — Your Login OTP",
                recipients=[user.email],
                body=f"Your one-time login code is: {otp}\n\nThis code expires in 10 minutes.\n\nIf you didn't request this, please ignore this email.",
            )
            mail.send(msg)
        except Exception as e:
            current_app.logger.error(f"Failed to send OTP email: {e}")

    return otp


def initiate_password_reset(email: str) -> Optional[str]:
    """
    Generate a password reset token for the user.

    Returns the plain token, or None if user not found.
    Token is emailed (or logged in dev mode).
    """
    user = User.query.filter_by(email=email.lower().strip(), is_deleted=False).first()

    if not user:
        return None  # Don't reveal whether user exists

    token = user.generate_reset_token()
    db.session.commit()

    # Send reset email (or log in dev mode)
    if current_app.config.get("MAIL_SUPPRESS_SEND"):
        current_app.logger.info(f"[DEV] Password reset token for {user.email}: {token}")
        print(f"\n{'='*50}")
        print(f"  Reset token for {user.email}: {token}")
        print(f"{'='*50}\n")
    else:
        try:
            from flask_mail import Message
            from app.extensions import mail
            from flask import url_for

            reset_url = url_for("auth.reset_password", token=token, email=user.email, _external=True)
            msg = Message(
                subject="LoanAxis CRM — Password Reset",
                recipients=[user.email],
                body=f"Click the following link to reset your password:\n\n{reset_url}\n\nThis link expires in 1 hour.\n\nIf you didn't request this, please ignore this email.",
            )
            mail.send(msg)
        except Exception as e:
            current_app.logger.error(f"Failed to send reset email: {e}")

    return token


def reset_user_password(email: str, token: str, new_password: str) -> Tuple[bool, str]:
    """
    Reset a user's password using a valid reset token.

    Args:
        email: User's email
        token: Reset token from email link
        new_password: New password to set

    Returns:
        (success, message)
    """
    user = User.query.filter_by(email=email.lower().strip(), is_deleted=False).first()

    if not user:
        return False, "Invalid reset link."

    if not user.verify_reset_token(token):
        return False, "Reset link has expired or is invalid. Please request a new one."

    user.set_password(new_password)
    user.failed_login_attempts = 0
    user.locked_until = None
    db.session.commit()

    return True, "Password has been reset successfully. You can now log in."

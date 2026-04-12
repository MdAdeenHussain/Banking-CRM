"""
LoanAxis CRM — Auth Routes

Handles login, logout, registration (first user only), OTP verification,
and password reset flows.
"""

from flask import render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user

from app.blueprints.auth import auth_bp
from app.blueprints.auth.forms import (
    LoginForm, RegisterForm, OTPForm, ForgotPasswordForm, ResetPasswordForm,
)
from app.blueprints.auth.services import (
    authenticate_user, register_first_user, generate_and_send_otp,
    initiate_password_reset, reset_user_password,
)
from app.extensions import limiter
from app.models.user import User


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10/minute")
def login():
    """User login page."""
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    # Check if any users exist — if not, redirect to register
    if User.query.count() == 0:
        return redirect(url_for("auth.register"))

    form = LoginForm()

    if form.validate_on_submit():
        user, message = authenticate_user(form.email.data, form.password.data)

        if user is None:
            flash(message, "danger")
            return render_template("auth/login.html", form=form)

        # Check if 2FA is enabled
        if user.is_2fa_enabled:
            # Store user ID in session for OTP verification
            session["otp_user_id"] = user.id
            generate_and_send_otp(user)
            flash("A verification code has been sent to your email.", "info")
            return redirect(url_for("auth.otp_verify"))

        # Direct login (no 2FA)
        login_user(user, remember=form.remember_me.data)
        flash(f"Welcome back, {user.full_name}! 👋", "success")

        # Redirect to intended page or dashboard
        next_page = request.args.get("next")
        if next_page and next_page.startswith("/"):
            return redirect(next_page)
        return redirect(url_for("dashboard.index"))

    return render_template("auth/login.html", form=form)


@auth_bp.route("/register", methods=["GET", "POST"])
@limiter.limit("5/minute")
def register():
    """
    Register the first user as Super Admin.
    Only accessible when no users exist in the system.
    """
    if User.query.count() > 0:
        flash("Registration is closed. Please log in or contact your administrator.", "warning")
        return redirect(url_for("auth.login"))

    form = RegisterForm()

    if form.validate_on_submit():
        try:
            user = register_first_user(
                full_name=form.full_name.data,
                email=form.email.data,
                mobile=form.mobile.data,
                password=form.password.data,
            )
            login_user(user, remember=True)
            flash(f"Welcome to LoanAxis CRM, {user.full_name}! You are the Super Admin. 🎉", "success")
            return redirect(url_for("dashboard.index"))
        except ValueError as e:
            flash(str(e), "danger")

    return render_template("auth/register.html", form=form)


@auth_bp.route("/otp-verify", methods=["GET", "POST"])
@limiter.limit("5/minute")
def otp_verify():
    """OTP verification page (shown after login when 2FA is enabled)."""
    user_id = session.get("otp_user_id")
    if not user_id:
        flash("Session expired. Please log in again.", "warning")
        return redirect(url_for("auth.login"))

    user = User.query.get(user_id)
    if not user:
        session.pop("otp_user_id", None)
        flash("User not found. Please log in again.", "danger")
        return redirect(url_for("auth.login"))

    form = OTPForm()

    if form.validate_on_submit():
        if user.verify_otp(form.otp.data):
            session.pop("otp_user_id", None)
            from app.extensions import db
            db.session.commit()
            login_user(user)
            flash(f"Welcome back, {user.full_name}! 👋", "success")
            return redirect(url_for("dashboard.index"))
        else:
            flash("Invalid or expired OTP. Please try again.", "danger")

    return render_template("auth/otp_verify.html", form=form, user_email=user.email)


@auth_bp.route("/resend-otp", methods=["POST"])
@limiter.limit("3/minute")
def resend_otp():
    """Resend OTP for 2FA verification."""
    user_id = session.get("otp_user_id")
    if not user_id:
        flash("Session expired. Please log in again.", "warning")
        return redirect(url_for("auth.login"))

    user = User.query.get(user_id)
    if user:
        generate_and_send_otp(user)
        flash("A new verification code has been sent to your email.", "info")

    return redirect(url_for("auth.otp_verify"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
@limiter.limit("3/minute")
def forgot_password():
    """Request a password reset link."""
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    form = ForgotPasswordForm()

    if form.validate_on_submit():
        initiate_password_reset(form.email.data)
        # Always show success message (don't reveal if user exists)
        flash("If an account with that email exists, a password reset link has been sent.", "info")
        return redirect(url_for("auth.login"))

    return render_template("auth/forgot_password.html", form=form)


@auth_bp.route("/reset-password", methods=["GET", "POST"])
@limiter.limit("5/minute")
def reset_password():
    """Reset password using the token from email link."""
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    token = request.args.get("token", "")
    email = request.args.get("email", "")

    if not token or not email:
        flash("Invalid reset link.", "danger")
        return redirect(url_for("auth.forgot_password"))

    form = ResetPasswordForm()

    if form.validate_on_submit():
        success, message = reset_user_password(email, token, form.password.data)
        flash(message, "success" if success else "danger")
        if success:
            return redirect(url_for("auth.login"))

    return render_template(
        "auth/reset_password.html", form=form, token=token, email=email
    )


@auth_bp.route("/logout")
@login_required
def logout():
    """Log out the current user."""
    name = current_user.full_name
    logout_user()
    session.clear()
    flash(f"Goodbye, {name}! You have been logged out.", "info")
    return redirect(url_for("auth.login"))

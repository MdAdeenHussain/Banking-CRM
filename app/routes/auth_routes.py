"""Authentication route controllers."""

# =====================================
# SECTION: Imports
# =====================================
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.forms import LoginForm, TenantRegistrationForm, UserRegistrationForm
from app.models.tenant import Tenant
from app.services.auth_service import AuthService


# =====================================
# SECTION: Blueprint Definition
# =====================================
auth_bp = Blueprint("auth", __name__)


# =====================================
# SECTION: Authentication Routes
# =====================================
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Render login page and handle login submission."""
    if current_user.is_authenticated:
        return redirect(AuthService.role_redirect_path(current_user.role))

    form = LoginForm()

    if request.method == "POST":
        # Collect payload from Flask-WTF fields first, then fallback to raw form.
        tenant_slug = form.tenant_slug.data or request.form.get("tenant_slug", "").strip()
        email = form.email.data or request.form.get("email", "").strip().lower()
        password = form.password.data or request.form.get("password", "")
        remember_raw = request.form.get("remember_me", "")
        remember_me = form.remember_me.data or remember_raw in {"on", "true", "1", "yes"}

        if not tenant_slug or not email or not password:
            flash("Tenant slug, email, and password are required.", "danger")
            return render_template("auth/login.html", form=form)

        user = AuthService.authenticate_user(
            tenant_slug=tenant_slug,
            email=email,
            password=password,
        )

        if not user:
            flash("Invalid credentials. Please try again.", "danger")
            return render_template("auth/login.html", form=form)

        login_user(user, remember=remember_me)
        flash("Login successful.", "success")

        next_url = request.args.get("next")
        return redirect(next_url or AuthService.role_redirect_path(user.role))

    return render_template("auth/login.html", form=form)


@auth_bp.get("/logout")
@login_required
def logout():
    """Terminate current user session."""
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/register/tenant", methods=["GET", "POST"])
def register_tenant():
    """Render tenant registration form and handle submission."""
    form = TenantRegistrationForm()

    if request.method == "POST":
        company_name = form.company_name.data or request.form.get("company_name", "").strip()
        slug = form.slug.data or request.form.get("slug", "").strip().lower()
        admin_name = form.admin_name.data or request.form.get("admin_name", "Tenant Owner").strip()
        admin_email = form.admin_email.data or request.form.get("admin_email", "").strip().lower()
        admin_phone = form.admin_phone.data or request.form.get("admin_phone", "").strip()
        password = form.password.data or request.form.get("password", "")

        if not company_name or not slug or not admin_email or not password:
            flash("Please fill all required tenant registration fields.", "danger")
            return render_template("auth/register_tenant.html", form=form)

        ok, message, _ = AuthService.register_tenant(
            company_name=company_name,
            slug=slug,
            admin_name=admin_name,
            admin_email=admin_email,
            admin_phone=admin_phone or None,
            password=password,
        )

        flash(message, "success" if ok else "danger")
        if ok:
            return redirect(url_for("auth.login"))

    return render_template("auth/register_tenant.html", form=form)


@auth_bp.route("/register/user", methods=["GET", "POST"])
def register_user():
    """Render user registration form and handle submission."""
    form = UserRegistrationForm()

    if request.method == "POST":
        name = form.name.data or request.form.get("name", "").strip()
        email = form.email.data or request.form.get("email", "").strip().lower()
        password = form.password.data or request.form.get("password", "")
        role = form.role.data or request.form.get("role", "agent").strip().lower()
        phone = form.phone.data or request.form.get("phone", "").strip()

        tenant_id = current_user.tenant_id if current_user.is_authenticated else None

        # Fallback for public registration flow when tenant slug is supplied.
        if not tenant_id:
            slug = form.tenant_slug.data or request.form.get("tenant_slug", "").strip().lower()
            if slug:
                tenant = Tenant.query.filter_by(slug=slug, is_deleted=False).first()
                tenant_id = tenant.id if tenant else None

        if not tenant_id:
            flash("Tenant context not found. Login first or provide valid tenant slug.", "danger")
            return render_template("auth/register_user.html", form=form)

        if not name or not email or not password:
            flash("Please complete all required user registration fields.", "danger")
            return render_template("auth/register_user.html", form=form)

        ok, message, _ = AuthService.register_user(
            tenant_id=tenant_id,
            name=name,
            email=email,
            password=password,
            role=role,
            phone=phone or None,
        )

        flash(message, "success" if ok else "danger")
        if ok:
            return redirect(url_for("auth.login"))

    return render_template("auth/register_user.html", form=form)


@auth_bp.get("/forgot-password")
def forgot_password():
    """Render forgot password page."""
    return render_template("auth/forgot_password.html")


@auth_bp.get("/reset-password")
def reset_password():
    """Render reset password page."""
    return render_template("auth/reset_password.html")


@auth_bp.get("/verify-email")
def verify_email():
    """Render email verification page."""
    return render_template("auth/verify_email.html")

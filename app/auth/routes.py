"""
app/auth/routes.py
Authentication routes (login, register, password reset, logout, JWT refresh).
Locked routes that cannot change in Phase 2/3.
"""

from flask import request, jsonify, g, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.auth import auth_bp
from app.auth.services import AuthService, TokenService
from app.auth.models import User
from app.decorators import login_required, tenant_required
from app.errors import AuthenticationError, ValidationError, NotFoundError, TenantError
from app.extensions import db
import logging
from uuid import UUID

logger = logging.getLogger(__name__)


# ============================================================================
# LOGIN ROUTES
# ============================================================================

@auth_bp.route("/login", methods=["GET"])
def login():
    """
    GET /login
    Display login form or redirect to dashboard if already authenticated.
    """
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.dashboard"))
    
    return render_template("auth/login.html")


@auth_bp.route("/login", methods=["POST"])
def login_post():
    """
    POST /login
    Authenticate user and create session.
    
    Handles both form submissions and JSON API calls.
    
    Form submission:
        tenant_slug: str - Tenant identifier
        email: str - User email
        password: str - User password
        remember: bool - Remember me checkbox
    
    JSON API:
        tenant_slug: str (required) - Tenant identifier
        email: str (required) - User email
        password: str (required) - User password
    
    Returns:
        Form: Redirect to dashboard on success, or back to login with errors
        JSON: 200: {user, tenant, access_token, refresh_token}
    """
    try:
        # Handle both form and JSON
        if request.is_json:
            data = request.get_json() or {}
        else:
            data = request.form.to_dict()
        
        tenant_slug = data.get("tenant_slug", "").strip()
        email = data.get("email", "").strip()
        password = data.get("password", "")
        remember = data.get("remember", False)
        
        if not tenant_slug or not email or not password:
            if request.is_json:
                return jsonify({"error": "Missing required fields"}), 400
            else:
                return render_template("auth/login.html", errors=["Missing required fields"]), 400
        
        result = AuthService.authenticate_user(
            tenant_slug=tenant_slug,
            email=email,
            password=password,
            ip_address=request.remote_addr
        )
        
        user = User.query.get(result["user"]["id"])
        login_user(user, remember=bool(remember))
        
        logger.info(f"User logged in: {email} in tenant {tenant_slug}")
        
        # Return based on request type
        if request.is_json:
            return jsonify({
                "status": "success",
                "message": "Login successful",
                "user": result["user"],
                "tenant": result["tenant"],
                "access_token": result["access_token"],
                "refresh_token": result["refresh_token"]
            }), 200
        else:
            flash("Login successful!", "success")
            return redirect(url_for("dashboard.dashboard"))
    
    except TenantError as e:
        logger.warning(f"Login failed - tenant error: {str(e)}")
        if request.is_json:
            return jsonify({"error": str(e)}), 403
        else:
            return render_template("auth/login.html", errors=[str(e)]), 403
    
    except AuthenticationError as e:
        logger.warning(f"Login failed - auth error: {str(e)}")
        if request.is_json:
            return jsonify({"error": str(e)}), 401
        else:
            return render_template("auth/login.html", errors=[str(e)]), 401
    
    except Exception as e:
        logger.error(f"Login error: {str(e)}", exc_info=True)
        if request.is_json:
            return jsonify({"error": "Login failed"}), 500
        else:
            return render_template("auth/login.html", errors=["Login failed. Please try again."]), 500


@auth_bp.route("/logout", methods=["POST", "GET"])
@login_required
def logout():
    """
    POST /logout or GET /logout
    Logout user and destroy session.
    
    Returns:
        Redirect to login page or JSON response
    """
    try:
        email = current_user.email
        logout_user()
        
        logger.info(f"User logged out: {email}")
        
        if request.is_json or request.accept_mimetypes.get('application/json'):
            return jsonify({
                "status": "success",
                "message": "Logout successful"
            }), 200
        else:
            flash("You have been logged out.", "success")
            return redirect(url_for("auth.login"))
    
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        if request.is_json:
            return jsonify({"error": "Logout failed"}), 500
        else:
            return redirect(url_for("auth.login"))


# ============================================================================
# TENANT REGISTRATION ROUTES
# ============================================================================

@auth_bp.route("/register/tenant", methods=["GET"])
def register_tenant():
    """
    GET /register/tenant
    Display tenant registration form.
    """
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.dashboard"))
    
    return render_template("auth/register.html")


@auth_bp.route("/register/tenant", methods=["POST"])
def register_tenant_post():
    """
    POST /register/tenant
    Register new tenant with admin user.
    
    Request JSON:
        tenant_name: str (required)
        tenant_slug: str (required, unique)
        admin_email: str (required)
        admin_password: str (required, min 8 chars)
        admin_first_name: str (required)
        admin_last_name: str (required)
    
    Returns:
        201: {tenant, user, access_token, refresh_token}
        400: Validation error
    """
    try:
        # Handle both form and JSON
        if request.is_json:
            data = request.get_json() or {}
        else:
            data = request.form.to_dict()
        
        tenant_name = data.get("tenant_name", "").strip()
        tenant_slug = data.get("tenant_slug", "").strip().lower()
        admin_email = data.get("admin_email", "").strip()
        admin_password = data.get("password", data.get("admin_password", ""))
        admin_first_name = data.get("admin_first_name", "").strip()
        admin_last_name = data.get("admin_last_name", "").strip()
        
        if not all([tenant_name, tenant_slug, admin_email, admin_password, admin_first_name, admin_last_name]):
            error = "Missing required fields"
            if request.is_json:
                return jsonify({"error": error}), 400
            else:
                return render_template("auth/register.html", errors=[error]), 400
        
        if len(admin_password) < 8:
            error = "Password must be at least 8 characters"
            if request.is_json:
                return jsonify({"error": error}), 400
            else:
                return render_template("auth/register.html", errors=[error]), 400
        
        result = AuthService.create_tenant_and_admin(
            tenant_name=tenant_name,
            tenant_slug=tenant_slug,
            admin_email=admin_email,
            admin_password=admin_password,
            admin_first_name=admin_first_name,
            admin_last_name=admin_last_name,
            ip_address=request.remote_addr
        )
        
        user = User.query.get(result["user"]["id"])
        login_user(user, remember=True)
        
        logger.info(f"Tenant registered: {tenant_slug}")
        
        if request.is_json:
            return jsonify({
                "status": "success",
                "message": "Tenant registered successfully",
                "tenant": result["tenant"],
                "user": result["user"],
                "access_token": result["access_token"],
                "refresh_token": result["refresh_token"]
            }), 201
        else:
            return redirect(url_for("dashboard.dashboard"))
    
    except ValidationError as e:
        logger.warning(f"Tenant registration failed: {str(e)}")
        if request.is_json:
            return jsonify({"error": e.message}), 400
        else:
            return render_template("auth/register.html", errors=[e.message]), 400
    
    except Exception as e:
        logger.error(f"Tenant registration error: {str(e)}", exc_info=True)
        error = "Registration failed. Please try again."
        if request.is_json:
            return jsonify({"error": error}), 500
        else:
            return render_template("auth/register.html", errors=[error]), 500


# ============================================================================
# USER REGISTRATION ROUTES (Tenant Admin Only)
# ============================================================================

@auth_bp.route("/register/user", methods=["GET"])
@login_required
@tenant_required
def register_user():
    """
    GET /register/user
    Display user registration form (tenant admin only).
    """
    if "tenant_admin" not in g.user_roles:
        flash("Only tenant admins can create users", "error")
        return redirect(url_for("dashboard.dashboard"))
    
    return render_template("auth/register-user.html")


@auth_bp.route("/register/user", methods=["POST"])
@login_required
@tenant_required
def register_user_post():
    """
    POST /register/user
    Create new user in tenant (tenant admin only).
    
    Request JSON:
        email: str (required)
        password: str (required, min 8 chars)
        first_name: str (required)
        last_name: str (required)
        role_name: str (required)
    
    Returns:
        201: {user, access_token, refresh_token}
        400: Validation error
        403: Not tenant admin
    """
    try:
        if "tenant_admin" not in g.user_roles:
            error = "Only tenant admins can create users"
            if request.is_json:
                return jsonify({"error": error}), 403
            else:
                flash(error, "error")
                return redirect(url_for("dashboard.dashboard"))
        
        # Handle both form and JSON
        if request.is_json:
            data = request.get_json() or {}
        else:
            data = request.form.to_dict()
        
        email = data.get("email", "").strip()
        password = data.get("password", "")
        first_name = data.get("first_name", "").strip()
        last_name = data.get("last_name", "").strip()
        role_name = data.get("role_name", "").strip().lower()
        
        if not all([email, password, first_name, last_name, role_name]):
            error = "Missing required fields"
            if request.is_json:
                return jsonify({"error": error}), 400
            else:
                return render_template("auth/register-user.html", errors=[error]), 400
        
        if len(password) < 8:
            error = "Password must be at least 8 characters"
            if request.is_json:
                return jsonify({"error": error}), 400
            else:
                return render_template("auth/register-user.html", errors=[error]), 400
        
        result = AuthService.create_user_in_tenant(
            tenant_id=g.tenant_id,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role_name=role_name,
            created_by_user_id=g.user_id
        )
        
        logger.info(f"User created: {email} in tenant {g.tenant_id}")
        
        if request.is_json:
            return jsonify({
                "status": "success",
                "message": "User created successfully",
                "user": result["user"],
                "access_token": result["access_token"],
                "refresh_token": result["refresh_token"]
            }), 201
        else:
            flash("User created successfully", "success")
            return redirect(url_for("dashboard.dashboard"))
    
    except ValidationError as e:
        logger.warning(f"User creation failed: {str(e)}")
        if request.is_json:
            return jsonify({"error": e.message}), 400
        else:
            return render_template("auth/register-user.html", errors=[e.message]), 400
    
    except Exception as e:
        logger.error(f"User creation error: {str(e)}", exc_info=True)
        error = "User creation failed"
        if request.is_json:
            return jsonify({"error": error}), 500
        else:
            return render_template("auth/register-user.html", errors=[error]), 500


# ============================================================================
# PASSWORD RESET ROUTES
# ============================================================================

@auth_bp.route("/forgot-password", methods=["GET"])
def forgot_password():
    """GET /forgot-password - Forgot password form."""
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.dashboard"))
    
    return render_template("auth/forgot-password.html")


@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password_post():
    """
    POST /forgot-password
    Request password reset token.
    
    Returns:
        200: {reset_token, expires_in}
        Note: PHASE_2_HOOK - send via email instead
    """
    try:
        # Handle both form and JSON
        if request.is_json:
            data = request.get_json() or {}
        else:
            data = request.form.to_dict()
        
        tenant_slug = data.get("tenant_slug", "").strip()
        email = data.get("email", "").strip()
        
        if not tenant_slug or not email:
            error = "Missing required fields"
            if request.is_json:
                return jsonify({"error": error}), 400
            else:
                return render_template("auth/forgot-password.html", errors=[error]), 400
        
        from app.tenants.models import Tenant
        tenant = Tenant.query.filter_by(slug=tenant_slug, is_active=True, is_deleted=False).first()
        if not tenant:
            if request.is_json:
                # For API, don't reveal if tenant exists
                return jsonify({"status": "success", "message": "If email exists, reset link will be sent"}), 200
            else:
                return render_template("auth/forgot-password.html", errors=["Organization not found"]), 404
        
        result = AuthService.request_password_reset(
            tenant_id=tenant.id,
            email=email
        )
        
        logger.info(f"Password reset requested: {email}")
        
        if request.is_json:
            return jsonify({
                "status": "success",
                "message": "If email exists, reset link will be sent",
                "reset_token": result["reset_token"],
                "expires_in": result["expires_in"]
            }), 200
        else:
            # In production, email the reset link instead
            flash(f"Reset link: {url_for('auth.reset_password', token=result['reset_token'], _external=True)}", "info")
            return render_template("auth/forgot-password.html", success="If email exists, reset link will be sent"), 200
    
    except NotFoundError:
        # Don't reveal if user exists
        if request.is_json:
            return jsonify({"status": "success", "message": "If email exists, reset link will be sent"}), 200
        else:
            return render_template("auth/forgot-password.html", success="If email exists, reset link will be sent"), 200
    
    except Exception as e:
        logger.error(f"Forgot password error: {str(e)}")
        error = "Request failed"
        if request.is_json:
            return jsonify({"error": error}), 500
        else:
            return render_template("auth/forgot-password.html", errors=[error]), 500


@auth_bp.route("/reset-password/<token>", methods=["GET"])
def reset_password(token):
    """GET /reset-password/<token> - Reset password form."""
    try:
        payload = TokenService.verify_reset_token(token)
        if not payload:
            return render_template("auth/reset-password.html", errors=["Invalid or expired token"]), 400
        
        return render_template("auth/reset-password.html", token=token)
    
    except Exception as e:
        logger.error(f"Reset password form error: {str(e)}")
        return render_template("auth/reset-password.html", errors=["Invalid or expired token"]), 400


@auth_bp.route("/reset-password/<token>", methods=["POST"])
def reset_password_post(token):
    """
    POST /reset-password/<token>
    Reset password with token.
    
    Request JSON:
        password: str (required, min 8 chars)
        password_confirm: str (required)
    
    Returns:
        200: {user, access_token, refresh_token}
    """
    try:
        payload = TokenService.verify_reset_token(token)
        if not payload:
            error = "Invalid or expired token"
            if request.is_json:
                return jsonify({"error": error}), 400
            else:
                return render_template("auth/reset-password.html", errors=[error]), 400
        
        # Handle both form and JSON
        if request.is_json:
            data = request.get_json() or {}
        else:
            data = request.form.to_dict()
        
        password = data.get("password", "")
        password_confirm = data.get("password_confirm", "")
        
        if not password or not password_confirm:
            error = "Missing required fields"
            if request.is_json:
                return jsonify({"error": error}), 400
            else:
                return render_template("auth/reset-password.html", errors=[error], token=token), 400
        
        if len(password) < 8:
            error = "Password must be at least 8 characters"
            if request.is_json:
                return jsonify({"error": error}), 400
            else:
                return render_template("auth/reset-password.html", errors=[error], token=token), 400
        
        if password != password_confirm:
            error = "Passwords do not match"
            if request.is_json:
                return jsonify({"error": error}), 400
            else:
                return render_template("auth/reset-password.html", errors=[error], token=token), 400
        
        tenant_id = payload.get("tenant_id")
        
        result = AuthService.reset_password(
            tenant_id=tenant_id,
            reset_token=token,
            new_password=password
        )
        
        user = User.query.get(result["user"]["id"])
        login_user(user, remember=True)
        
        logger.info(f"Password reset for user {result['user']['email']}")
        
        if request.is_json:
            return jsonify({
                "status": "success",
                "message": "Password reset successful",
                "user": result["user"],
                "access_token": result["access_token"],
                "refresh_token": result["refresh_token"]
            }), 200
        else:
            flash("Password reset successful. You are now logged in.", "success")
            return redirect(url_for("dashboard.dashboard"))
    
    except AuthenticationError as e:
        if request.is_json:
            return jsonify({"error": e.message}), 401
        else:
            return render_template("auth/reset-password.html", errors=[e.message], token=token), 401
    
    except Exception as e:
        logger.error(f"Password reset error: {str(e)}", exc_info=True)
        error = "Password reset failed"
        if request.is_json:
            return jsonify({"error": error}), 500
        else:
            return render_template("auth/reset-password.html", errors=[error], token=token), 500


# ============================================================================
# EMAIL VERIFICATION
# ============================================================================

@auth_bp.route("/verify-email/<token>", methods=["GET"])
def verify_email(token):
    """GET /verify-email/<token> - Verify email."""
    # PHASE_2_HOOK: Implement email verification
    return jsonify({"message": "Email verification not yet implemented"}), 200


# ============================================================================
# JWT TOKEN REFRESH
# ============================================================================

@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh_access_token():
    """
    POST /refresh
    Refresh access token.
    
    Headers:
        Authorization: Bearer <refresh_token>
    
    Returns:
        200: {access_token, refresh_token}
    """
    try:
        identity = get_jwt_identity()
        claims = get_jwt()
        
        user_id = UUID(claims.get("user_id"))
        tenant_id = UUID(claims.get("tenant_id"))
        
        access_token, new_refresh = TokenService.generate_tokens(
            user_id=user_id,
            tenant_id=tenant_id
        )
        
        logger.info(f"Token refreshed for user {user_id}")
        
        return jsonify({
            "status": "success",
            "access_token": access_token,
            "refresh_token": new_refresh
        }), 200
    
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        return jsonify({"error": "Token refresh failed"}), 401

"""
LoanAxis CRM — Application Factory

Creates and configures the Flask application using the factory pattern.
All extensions, blueprints, error handlers, and middleware are registered here.
"""

import os
import logging

from flask import Flask, render_template, request
from flask_login import current_user
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def create_app(config_name: str = None) -> Flask:
    """
    Application factory.

    Args:
        config_name: One of 'development', 'production', 'testing'.
                     Defaults to FLASK_ENV environment variable.

    Returns:
        Configured Flask application instance.
    """
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )

    # ── Load Configuration ──────────────────────────────────
    _configure_app(app, config_name)

    # ── Initialize Extensions ───────────────────────────────
    _init_extensions(app)

    # ── Register Blueprints ─────────────────────────────────
    _register_blueprints(app)

    # ── Register Error Handlers ─────────────────────────────
    _register_error_handlers(app)

    # ── Register Security Headers ───────────────────────────
    _register_security_headers(app)

    # ── Register Template Context Processors ────────────────
    _register_context_processors(app)

    # ── Register Audit Listeners ────────────────────────────
    _register_audit_listeners(app)

    # ── Ensure Upload Directory Exists ──────────────────────
    upload_folder = app.config.get("UPLOAD_FOLDER", "uploads")
    os.makedirs(upload_folder, exist_ok=True)
    os.makedirs("instance", exist_ok=True)

    # ── Configure Logging ───────────────────────────────────
    if not app.debug:
        logging.basicConfig(level=logging.INFO)

    app.logger.info(f"LoanAxis CRM initialized [{app.config.get('FLASK_ENV', 'development')}]")

    return app


def _configure_app(app: Flask, config_name: str = None) -> None:
    """Load the appropriate configuration class."""
    config_map = {
        "development": "app.config.development.DevelopmentConfig",
        "production": "app.config.production.ProductionConfig",
        "testing": "app.config.testing.TestingConfig",
    }

    env = config_name or os.environ.get("FLASK_ENV", "development")
    config_class = config_map.get(env, config_map["development"])

    app.config.from_object(config_class)


def _init_extensions(app: Flask) -> None:
    """Initialize all Flask extensions with the app instance."""
    from app.extensions import db, migrate, login_manager, mail, limiter, csrf, init_celery
    from app.models.user import User

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)

    # Rate limiter with fallback to memory storage
    try:
        limiter.init_app(app)
    except Exception:
        app.logger.warning("Rate limiter init failed, using memory storage")
        app.config["RATELIMIT_STORAGE_URI"] = "memory://"
        limiter.init_app(app)

    # Initialize Celery (optional — works without Redis)
    try:
        init_celery(app)
    except Exception:
        app.logger.warning("Celery init failed — background tasks will run synchronously")
        app.config["CELERY_ALWAYS_EAGER"] = True

    # Flask-Login user loader
    @login_manager.user_loader
    def load_user(user_id: str):
        return User.query.get(user_id)

    # Create tables if using SQLite (dev convenience)
    if "sqlite" in app.config.get("SQLALCHEMY_DATABASE_URI", ""):
        with app.app_context():
            # Import all models to ensure they're registered
            import app.models  # noqa: F401
            db.create_all()


def _register_blueprints(app: Flask) -> None:
    """Register all application blueprints."""
    from app.blueprints.auth import auth_bp
    from app.blueprints.dashboard import dashboard_bp
    from app.blueprints.leads import leads_bp
    from app.blueprints.documents import documents_bp
    from app.blueprints.commissions import commissions_bp
    from app.blueprints.tasks import tasks_bp
    from app.blueprints.employees import employees_bp
    from app.blueprints.analytics import analytics_bp
    from app.blueprints.invoices import invoices_bp
    from app.blueprints.notifications import notifications_bp
    from app.blueprints.exports import exports_bp
    from app.blueprints.admin import admin_bp
    from app.blueprints.api import api_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(dashboard_bp, url_prefix="/")
    app.register_blueprint(leads_bp, url_prefix="/leads")
    app.register_blueprint(documents_bp, url_prefix="/documents")
    app.register_blueprint(commissions_bp, url_prefix="/commissions")
    app.register_blueprint(tasks_bp, url_prefix="/tasks")
    app.register_blueprint(employees_bp, url_prefix="/employees")
    app.register_blueprint(analytics_bp, url_prefix="/analytics")
    app.register_blueprint(invoices_bp, url_prefix="/invoices")
    app.register_blueprint(notifications_bp, url_prefix="/notifications")
    app.register_blueprint(exports_bp, url_prefix="/exports")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(api_bp, url_prefix="/api/v1")


def _register_error_handlers(app: Flask) -> None:
    """Register custom error page handlers."""

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(e):
        from app.extensions import db
        db.session.rollback()
        return render_template("errors/500.html"), 500


def _register_security_headers(app: Flask) -> None:
    """Add security headers to every response."""

    @app.after_request
    def add_security_headers(response):
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # CSP — permissive for CDN assets
        if not app.debug:
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' "
                "https://cdn.jsdelivr.net https://cdn.tailwindcss.com "
                "https://unpkg.com https://cdnjs.cloudflare.com; "
                "style-src 'self' 'unsafe-inline' "
                "https://cdn.jsdelivr.net https://fonts.googleapis.com "
                "https://cdn.tailwindcss.com https://cdnjs.cloudflare.com; "
                "font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net; "
                "img-src 'self' data: blob:; "
                "connect-src 'self';"
            )

        return response


def _register_context_processors(app: Flask) -> None:
    """Register template context processors available in all templates."""

    @app.context_processor
    def inject_globals():
        """Inject commonly used data into all templates."""
        from app.config.permissions import get_role_display_name, has_permission

        context = {
            "app_name": "LoanAxis CRM",
            "current_year": __import__("datetime").datetime.now().year,
            "has_permission": has_permission,
            "get_role_display_name": get_role_display_name,
        }

        if current_user.is_authenticated:
            # Inject unread notification count
            from app.models.notification import Notification
            unread_count = Notification.query.filter_by(
                user_id=current_user.id,
                is_read=False,
            ).count()
            context["unread_notification_count"] = unread_count

        return context


def _register_audit_listeners(app: Flask) -> None:
    """Register SQLAlchemy audit event listeners."""
    with app.app_context():
        from app.models.audit_log import register_audit_listeners
        register_audit_listeners()

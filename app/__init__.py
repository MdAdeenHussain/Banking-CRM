"""
app/__init__.py
Flask application factory and initialization.
"""

from flask import Flask
from app.config import current_config
from app.extensions import db, login_manager, jwt, cors, init_redis, init_celery
from app.errors import register_error_handlers


def create_app(config=None):
    """
    Create and configure the Flask application.
    
    Args:
        config: Configuration object (defaults to current_config from environment)
    
    Returns:
        Flask application instance
    """
    app = Flask(__name__)

    # Load configuration
    if config is None:
        config = current_config
    app.config.from_object(config)

    # ========================================================================
    # Initialize Extensions
    # ========================================================================
    db.init_app(app)
    login_manager.init_app(app)
    jwt.init_app(app)
    cors.init_app(app, origins=app.config["CORS_ORIGINS"])
    init_redis(app)
    init_celery(app)

    # ========================================================================
    # Register Error Handlers & Middleware
    # ========================================================================
    register_error_handlers(app)
    
    # Register Flask-Login user_loader (critical for session authentication)
    @login_manager.user_loader
    def load_user(user_id):
        """Load user from database for Flask-Login sessions."""
        from app.auth.models import User
        try:
            return User.query.filter_by(id=user_id, is_active=True, is_deleted=False).first()
        except Exception:
            return None
    
    from app.middleware import register_middleware
    register_middleware(app)

    # ========================================================================
    # Register Blueprints
    # ========================================================================
    from app.auth import auth_bp
    from app.tenants import tenants_bp
    from app.leads import leads_bp
    from app.customers import customers_bp
    from app.dashboard import dashboard_bp
    from app.notifications import notifications_bp

    # Import models so SQLAlchemy registers them
    from app.tenants.models import Tenant, Branch
    from app.auth.models import User, Role, Permission, UserRole, UserSession
    from app.leads.models import Lead, LeadNote, LeadAssignment, LeadStatusHistory
    from app.customers.models import Customer
    from app.notifications.models import Notification
    from app.common.models import Task
    from app.common.audit import AuditLog

    app.register_blueprint(auth_bp)
    app.register_blueprint(tenants_bp)
    app.register_blueprint(leads_bp)
    app.register_blueprint(customers_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(notifications_bp)

    # PHASE_2_HOOK: Register new module blueprints here
    # from app.documents import documents_bp
    # from app.applications import applications_bp
    # from app.eligibility import eligibility_bp
    # from app.lenders import lenders_bp
    # from app.ai_hub import ai_hub_bp
    # from app.communications import communications_bp

    # PHASE_3_HOOK: Register enterprise module blueprints here
    # from app.commissions import commissions_bp
    # from app.compliance import compliance_bp
    # from app.analytics import analytics_bp
    # from app.billing import billing_bp
    # from app.platform_admin import platform_admin_bp

    # ========================================================================
    # Application Context Commands
    # ========================================================================
    @app.shell_context_processor
    def make_shell_context():
        """Make objects available in flask shell."""
        return {"db": db}

    @app.before_request
    def before_request():
        """
        Inject tenant context before each request.
        Sets g.tenant_id, g.user_id, g.user_roles, g.request_ip, g.user_agent.
        
        This is CRITICAL for multi-tenant isolation: all database queries
        must filter by tenant_id (enforced by decorators).
        """
        from app.middleware import inject_tenant
        inject_tenant()

    # ========================================================================
    # Root Route
    # ========================================================================
    @app.route("/", methods=["GET"])
    def root():
        """Redirect root path to appropriate destination based on auth status."""
        from flask import redirect, url_for
        from flask_login import current_user
        
        if current_user.is_authenticated:
            # Redirect authenticated users to dashboard
            return redirect(url_for("dashboard.dashboard"))
        else:
            # Redirect unauthenticated users to login
            return redirect(url_for("auth.login"))

    # ========================================================================
    # Health Check Endpoint
    # ========================================================================
    @app.route("/health", methods=["GET"])
    def health_check():
        """Health check endpoint for load balancers / K8s."""
        return {
            "status": "healthy",
            "service": "CRM API",
            "version": "1.0.0-phase1"
        }, 200

    # ========================================================================
    # Create Database Tables (via Alembic migrations)
    # ========================================================================
    # PHASE_2_HOOK: Use Alembic migrations instead of db.create_all()
    # with app.app_context():
    #     db.create_all()  # Only for initial dev setup, use migrations in production

    return app

"""Blueprint registration hub.

All route blueprints are imported and registered from here so
application startup remains clean and predictable.
"""

# =====================================
# SECTION: Imports
# =====================================
from flask import Flask

from app.ai_hub.routes import ai_hub_bp
from app.routes.analytics_routes import analytics_bp
from app.ai_ml.routes import ai_ml_bp
from app.rag_engine.memory_routes import rag_memory_bp
from app.routes.applications_routes import applications_bp
from app.routes.auth_routes import auth_bp
from app.routes.billing_routes import billing_bp
from app.routes.customers_routes import customers_bp
from app.routes.dashboard_routes import dashboard_bp
from app.routes.documents_routes import documents_bp
from app.routes.leads_routes import leads_bp
from app.routes.meta_webhook_routes import meta_webhook_bp
from app.routes.platform_routes import platform_bp
from app.routes.public_routes import public_bp
from app.routes.settings_routes import settings_bp


# =====================================
# SECTION: Blueprint Registration
# =====================================
def register_blueprints(app: Flask) -> None:
    """Register all blueprints in one place."""
    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(leads_bp)
    app.register_blueprint(customers_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(applications_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(billing_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(platform_bp)
    app.register_blueprint(meta_webhook_bp)
    app.register_blueprint(ai_ml_bp)
    app.register_blueprint(ai_hub_bp)
    app.register_blueprint(rag_memory_bp)

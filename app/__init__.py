import os
import importlib

from flask import Flask

from app.config import get_config


def create_app(env_name: str = "development") -> Flask:
    app = Flask(__name__)

    # 1. Load config FIRST
    config_class = get_config(env_name)
    app.config.from_object(config_class)

    # 2. Init extensions (pass app)
    from app.extensions import db, migrate, login_manager, csrf, mail, limiter, celery

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)
    celery.conf.update(
        broker_url=app.config.get("CELERY_BROKER_URL"),
        result_backend=app.config.get("CELERY_RESULT_BACKEND"),
    )

    with app.app_context():
        # 3. Import ALL models before create_all
        #    This registers them with SQLAlchemy metadata
        importlib.import_module("app.models")

        # 4. Create all tables in PostgreSQL
        db.create_all()

        # 5. Register blueprints
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

        # 6. Register error handlers
        from flask import render_template

        # Template globals used across the existing Jinja templates.
        @app.context_processor
        def inject_globals():
            from datetime import datetime

            from app.config.permissions import get_role_display_name, has_permission

            return {
                "app_name": "LoanAxis CRM",
                "current_year": datetime.now().year,
                "has_permission": has_permission,
                "get_role_display_name": get_role_display_name,
            }

        @app.errorhandler(403)
        def forbidden(e):
            return render_template("errors/403.html"), 403

        @app.errorhandler(404)
        def not_found(e):
            return render_template("errors/404.html"), 404

        @app.errorhandler(500)
        def server_error(e):
            return render_template("errors/500.html"), 500

        # 7. Upload folder
        upload_folder = app.config.get("UPLOAD_FOLDER", "uploads")
        os.makedirs(upload_folder, exist_ok=True)

    return app

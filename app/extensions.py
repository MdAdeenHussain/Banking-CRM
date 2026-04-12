"""
LoanAxis CRM — Flask Extension Instances

All extensions are initialized here without an app instance
(factory pattern). They are bound to the app in create_app().
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
from celery import Celery

# ── SQLAlchemy ORM ──────────────────────────────────────────────
db = SQLAlchemy()

# ── Alembic Migrations ─────────────────────────────────────────
migrate = Migrate()

# ── Session Management ──────────────────────────────────────────
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "warning"
login_manager.session_protection = "strong"

# ── Email ───────────────────────────────────────────────────────
mail = Mail()

# ── Rate Limiting ───────────────────────────────────────────────
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per hour"],
    storage_uri="memory://",
)

# ── CSRF Protection ────────────────────────────────────────────
csrf = CSRFProtect()

# ── Celery (lazy init — configured in create_app) ──────────────
celery = Celery("loanaxis")


def init_celery(app):
    """
    Configure Celery with Flask app context.

    Falls back to synchronous execution if Redis is unavailable,
    allowing the app to work without a Celery worker running.
    """
    celery.conf.update(
        broker_url=app.config.get("CELERY_BROKER_URL", "redis://localhost:6379/1"),
        result_backend=app.config.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/2"),
        accept_content=app.config.get("CELERY_ACCEPT_CONTENT", ["json"]),
        task_serializer=app.config.get("CELERY_TASK_SERIALIZER", "json"),
        result_serializer=app.config.get("CELERY_RESULT_SERIALIZER", "json"),
        timezone=app.config.get("CELERY_TIMEZONE", "Asia/Kolkata"),
        task_always_eager=app.config.get("CELERY_ALWAYS_EAGER", False),
    )

    class ContextTask(celery.Task):
        """Ensure tasks run inside Flask app context."""

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery

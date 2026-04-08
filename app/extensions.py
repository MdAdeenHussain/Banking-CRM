"""
app/extensions.py
Initialize Flask extensions (db, jwt, login_manager, redis, celery).
Done here to avoid circular imports.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_cors import CORS
import redis
from celery import Celery
from flask_jwt_extended import JWTManager


# ============================================================================
# DATABASE
# ============================================================================
db = SQLAlchemy()


# ============================================================================
# LOGIN MANAGER
# ============================================================================
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "info"


# ============================================================================
# JWT
# ============================================================================
jwt = JWTManager()


# ============================================================================
# REDIS
# ============================================================================
redis_client = None  # Initialized in app factory


def init_redis(app):
    """Initialize Redis connection."""
    global redis_client
    redis_client = redis.from_url(app.config["REDIS_URL"])
    return redis_client


# ============================================================================
# CELERY
# ============================================================================
celery = Celery(__name__)


def init_celery(app):
    """Initialize Celery with Flask app."""
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        """Make celery tasks work with Flask app context."""
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


# ============================================================================
# CORS
# ============================================================================
cors = CORS()


# ============================================================================
# INITIALIZATION SUMMARY
# ============================================================================
"""
Extensions initialized:
- db: SQLAlchemy ORM
- login_manager: Flask-Login for session management
- jwt: JWT for API authentication
- redis_client: Redis for caching + session storage (init_redis)
- celery: Async task queue (init_celery)
- cors: CORS support

All extensions initialized in app/__init__.py via create_app()
"""

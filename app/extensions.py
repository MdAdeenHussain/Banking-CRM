"""Application extension registry.

All extension objects live in this file to avoid circular imports
and keep initialization in one predictable place.
"""

# =====================================
# SECTION: Imports
# =====================================
from typing import Any

from flask import Flask
from flask_jwt_extended import JWTManager
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy


# =====================================
# SECTION: Extension Instances
# =====================================
# Database ORM
# NOTE: Uses SQLAlchemy with PostgreSQL in production.
db = SQLAlchemy()

# Session authentication manager
login_manager = LoginManager()

# JWT placeholder manager for future API auth flows
jwt_manager = JWTManager()

# Runtime placeholders for optional infrastructure
redis_client: Any | None = None
celery_app: Any | None = None
socketio_app: Any | None = None


# =====================================
# SECTION: Flask-Login User Loader
# =====================================
@login_manager.user_loader
def load_user(user_id: str):
    """Load a user for Flask-Login session restoration.

    This function is called automatically by Flask-Login whenever
    it needs to reload the currently logged-in user from session.
    """
    from app.models.user import User

    return User.query.get(int(user_id)) if user_id and user_id.isdigit() else None


# =====================================
# SECTION: Initialization Helper
# =====================================
def init_extensions(app: Flask) -> None:
    """Initialize all Flask extensions in one place."""

    # Initialize SQLAlchemy ORM.
    db.init_app(app)

    # Initialize session authentication.
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "warning"

    # Initialize JWT manager (API-ready placeholder).
    jwt_manager.init_app(app)

    # Future infrastructure placeholders:
    # 1) Initialize redis_client from app.config['REDIS_URL']
    # 2) Initialize celery_app from app.config broker/backend settings
    # 3) Initialize socketio_app for realtime notifications

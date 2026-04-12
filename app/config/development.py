"""
LoanAxis CRM — Development Configuration
"""

from app.config.base import BaseConfig


class DevelopmentConfig(BaseConfig):
    """Development-specific overrides."""

    DEBUG = True
    TESTING = False

    # Use SQLite for local dev if DATABASE_URL not overridden
    # SQLALCHEMY_DATABASE_URI already reads from env with SQLite fallback

    # Console email backend — prints emails to terminal
    MAIL_SUPPRESS_SEND = True

    # Relaxed rate limits for development
    RATELIMIT_DEFAULT = "1000/hour"

    # In-memory rate limit storage (no Redis required)
    RATELIMIT_STORAGE_URI = "memory://"

    # Faster bcrypt for dev
    BCRYPT_LOG_ROUNDS = 4

    # CSRF still enabled in dev for realistic testing
    WTF_CSRF_ENABLED = True

    # Allow all origins in dev for testing
    CORS_ORIGINS = ["*"]

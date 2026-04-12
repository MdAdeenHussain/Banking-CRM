"""
LoanAxis CRM — Production Configuration
"""

import os

from app.config.base import BaseConfig


class ProductionConfig(BaseConfig):
    """Production-specific overrides. Strict security."""

    DEBUG = False
    TESTING = False

    # Force secure cookies
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # Require DATABASE_URL in production (no SQLite)
    SQLALCHEMY_DATABASE_URI = os.environ["DATABASE_URL"]

    # Production pool settings
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_size": 20,
        "max_overflow": 10,
    }

    # Full bcrypt cost
    BCRYPT_LOG_ROUNDS = 12

    # Strict rate limiting
    RATELIMIT_DEFAULT = "100/hour"
    RATELIMIT_STORAGE_URI = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

    # Mail must be properly configured
    MAIL_SUPPRESS_SEND = False

    # Preferred URL scheme
    PREFERRED_URL_SCHEME = "https"

"""
app/config.py
Environment-driven configuration for development, testing, and production.
"""

import os
from datetime import timedelta


class Config:
    """Base configuration - inherited by all environments."""

    # Flask Core
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/crm_db"
    )
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 10,
        "pool_recycle": 3600,
        "pool_pre_ping": True,
    }

    # JWT
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-secret-key-change-in-production")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)
    JWT_ALGORITHM = "HS256"

    # Session
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_NAME = "crm_session"
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)

    # Remember Cookie
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = timedelta(days=7)

    # Redis
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Celery
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
    CELERY_ACCEPT_CONTENT = ["json"]
    CELERY_TASK_SERIALIZER = "json"
    CELERY_RESULT_SERIALIZER = "json"

    # CORS
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5000").split(",")

    # Security
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # No time limit for CSRF tokens

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Feature Flags (for Phase 2/3)
    ENABLE_DOCUMENT_UPLOAD = os.getenv("ENABLE_DOCUMENT_UPLOAD", "false").lower() == "true"
    ENABLE_AI_FEATURES = os.getenv("ENABLE_AI_FEATURES", "false").lower() == "true"
    ENABLE_ANALYTICS = os.getenv("ENABLE_ANALYTICS", "false").lower() == "true"

    # PHASE_2_HOOK: Add S3/Cloudinary config for documents
    # PHASE_3_HOOK: Add Stripe/Razorpay config for billing


class DevelopmentConfig(Config):
    """Development environment configuration."""

    DEBUG = True
    SQLALCHEMY_ECHO = True
    SESSION_COOKIE_SECURE = False  # Allow non-HTTPS in dev
    REMEMBER_COOKIE_SECURE = False


class TestingConfig(Config):
    """Testing environment configuration."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"  # In-memory SQLite for tests
    SQLALCHEMY_ENGINE_OPTIONS = {}  # SQLite doesn't support pool options
    WTF_CSRF_ENABLED = False  # Disable CSRF in tests
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=60)  # Longer lived tokens in tests


class ProductionConfig(Config):
    """Production environment configuration."""

    DEBUG = False
    # All security flags remain True (inherited from Config)


# Select configuration based on environment
config_by_env = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}

CURRENT_ENV = os.getenv("FLASK_ENV", "development")
current_config = config_by_env.get(CURRENT_ENV, DevelopmentConfig)

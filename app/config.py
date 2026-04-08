"""Application configuration module.

This file centralizes environment-driven settings so local development,
Docker deployments, and production hosting can use the same codebase.
"""

# =====================================
# SECTION: Imports
# =====================================
import os


# =====================================
# SECTION: Base Configuration
# =====================================
class Config:
    """Default configuration shared by all environments."""

    # Core runtime settings
    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-in-production")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-this-jwt-secret")

    # Database settings (PostgreSQL by default)
    DATABASE_URL = os.getenv(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/crm2"
    )
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # File upload settings
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", str(16 * 1024 * 1024)))

    # Redis/Celery placeholders
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")
    META_WEBHOOK_TOKEN = os.getenv("META_WEBHOOK_TOKEN", "")

    # Flask-WTF placeholder setup.
    # NOTE: Temporarily disabled until all forms include csrf_token in HTML templates.
    WTF_CSRF_ENABLED = os.getenv("WTF_CSRF_ENABLED", "0") == "1"

    # Session hardening defaults
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # Future AI placeholders
    AI_PROVIDER = os.getenv("AI_PROVIDER", "placeholder")
    AI_ROUTER_MODE = os.getenv("AI_ROUTER_MODE", "disabled")


# =====================================
# SECTION: Environment Configurations
# =====================================
class DevelopmentConfig(Config):
    """Development-specific settings."""

    DEBUG = True


class ProductionConfig(Config):
    """Production-safe settings."""

    DEBUG = False


class TestingConfig(Config):
    """Testing settings with isolated database support."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")


# =====================================
# SECTION: Config Mapping Helper
# =====================================
config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}

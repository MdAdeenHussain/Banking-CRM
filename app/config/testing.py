"""
LoanAxis CRM — Testing Configuration
"""

from app.config.base import BaseConfig


class TestingConfig(BaseConfig):
    """Testing-specific overrides."""

    DEBUG = True
    TESTING = True

    # In-memory SQLite for fast tests
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"

    # Disable CSRF for test forms
    WTF_CSRF_ENABLED = False

    # Don't send emails
    MAIL_SUPPRESS_SEND = True

    # Fast bcrypt for tests
    BCRYPT_LOG_ROUNDS = 4

    # No rate limiting in tests
    RATELIMIT_ENABLED = False
    RATELIMIT_STORAGE_URI = "memory://"

    # Disable login protection for easier test setup
    LOGIN_DISABLED = False

    # Small upload for tests
    MAX_CONTENT_LENGTH = 1 * 1024 * 1024

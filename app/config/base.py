"""
LoanAxis CRM — Base Configuration

All environment-specific configs inherit from this.
Values are loaded from .env via python-dotenv.
"""

import os
from datetime import timedelta

# Project root = CRM2/
_basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))


class BaseConfig:
    """Base configuration shared across all environments."""

    # ── Flask Core ──────────────────────────────────────────
    SECRET_KEY = os.environ.get("SECRET_KEY", "fallback-insecure-dev-key")
    FLASK_APP = os.environ.get("FLASK_APP", "wsgi.py")

    # ── Database ────────────────────────────────────────────
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(_basedir, 'instance', 'loanaxis.db')}",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    # ── Redis ───────────────────────────────────────────────
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

    # ── Flask-Login ─────────────────────────────────────────
    REMEMBER_COOKIE_DURATION = timedelta(days=30)
    REMEMBER_COOKIE_SECURE = False  # Override in production
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"
    SESSION_PROTECTION = "strong"

    # ── Flask-Mail ──────────────────────────────────────────
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "localhost")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 25))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "false").lower() == "true"
    MAIL_USE_SSL = os.environ.get("MAIL_USE_SSL", "false").lower() == "true"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "noreply@loanaxis.com")
    MAIL_SUPPRESS_SEND = os.environ.get("MAIL_SUPPRESS_SEND", "false").lower() == "true"

    # ── Security ────────────────────────────────────────────
    BCRYPT_LOG_ROUNDS = int(os.environ.get("BCRYPT_LOG_ROUNDS", 12))
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour

    # ── JWT (API auth) ──────────────────────────────────────
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "jwt-fallback-key")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        seconds=int(os.environ.get("JWT_ACCESS_TOKEN_EXPIRES", 900))
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        seconds=int(os.environ.get("JWT_REFRESH_TOKEN_EXPIRES", 604800))
    )

    # ── File Uploads ────────────────────────────────────────
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "uploads")
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH", 10 * 1024 * 1024))
    ALLOWED_EXTENSIONS = {"pdf", "jpg", "jpeg", "png", "docx"}
    ALLOWED_MIME_TYPES = {
        "application/pdf",
        "image/jpeg",
        "image/png",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }

    # ── Celery ──────────────────────────────────────────────
    CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/1")
    CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")
    CELERY_ACCEPT_CONTENT = ["json"]
    CELERY_TASK_SERIALIZER = "json"
    CELERY_RESULT_SERIALIZER = "json"
    CELERY_TIMEZONE = "Asia/Kolkata"

    # ── Rate Limiting ───────────────────────────────────────
    RATELIMIT_DEFAULT = "200/hour"
    RATELIMIT_STORAGE_URI = os.environ.get("REDIS_URL", "memory://")

    # ── Auth Configuration ──────────────────────────────────
    MAX_LOGIN_ATTEMPTS = 5
    LOGIN_LOCKOUT_MINUTES = 15
    OTP_EXPIRY_MINUTES = 10
    PASSWORD_RESET_EXPIRY_HOURS = 1

    # ── Agency Details (for invoices) ───────────────────────
    AGENCY_NAME = os.environ.get("AGENCY_NAME", "LoanAxis Financial Services")
    AGENCY_GSTIN = os.environ.get("AGENCY_GSTIN", "")
    AGENCY_ADDRESS = os.environ.get("AGENCY_ADDRESS", "")
    AGENCY_PAN = os.environ.get("AGENCY_PAN", "")
    AGENCY_LOGO_PATH = os.environ.get("AGENCY_LOGO_PATH", "app/static/img/logo.svg")

    # ── Pagination ──────────────────────────────────────────
    ITEMS_PER_PAGE = 25

    # ── High Value Lead Threshold ───────────────────────────
    HIGH_VALUE_THRESHOLD = 5000000  # ₹50 lakhs

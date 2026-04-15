from .base import Config


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_ECHO = False
    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

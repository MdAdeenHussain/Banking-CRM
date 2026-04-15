from .base import Config


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True
    WTF_CSRF_ENABLED = True

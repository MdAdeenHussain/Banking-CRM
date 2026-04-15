from .base import Config


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = (
        "postgresql://postgres@localhost:5432/banking_dsa_crm_test"
    )
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_ECHO = False

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
    AI_MODEL_DIR = os.getenv("AI_MODEL_DIR", "model_store")
    FRAUD_MODEL_DIR = os.getenv("FRAUD_MODEL_DIR", "model_store/fraud")
    AI_ALLOW_CLOUD = os.getenv("AI_ALLOW_CLOUD", "1") == "1"
    AI_PROVIDER_RETRIES = int(os.getenv("AI_PROVIDER_RETRIES", "2"))
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    AI_LOCAL_PRIMARY_MODEL = os.getenv("AI_LOCAL_PRIMARY_MODEL", "llama3.1")
    AI_LOCAL_SECONDARY_MODEL = os.getenv("AI_LOCAL_SECONDARY_MODEL", "mistral")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "")
    OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")
    CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")
    CLAUDE_BASE_URL = os.getenv("CLAUDE_BASE_URL", "")
    CLAUDE_MODEL_NAME = os.getenv("CLAUDE_MODEL_NAME", "claude-3-5-sonnet")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_BASE_URL = os.getenv("GEMINI_BASE_URL", "")
    GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-pro")

    # RAG / vector memory settings
    RAG_VECTOR_BACKEND = os.getenv("RAG_VECTOR_BACKEND", "faiss")
    RAG_INDEX_NAME = os.getenv("RAG_INDEX_NAME", "banking_crm_memory")
    RAG_STORE_DIR = os.getenv("RAG_STORE_DIR", "rag_store")
    RAG_EMBEDDING_MODEL = os.getenv("RAG_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    RAG_EMBEDDING_DIM = int(os.getenv("RAG_EMBEDDING_DIM", "384"))
    RAG_ENABLE_OPENAI_EMBEDDINGS = os.getenv("RAG_ENABLE_OPENAI_EMBEDDINGS", "0") == "1"


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

"""Flask application factory.

The create_app function builds the Flask app with modular setup so
we can scale features cleanly across future phases.
"""

# =====================================
# SECTION: Imports
# =====================================
import os

from flask import Flask

from app.config import config_by_name
from app.errors import register_error_handlers
from app.extensions import init_extensions
from app.middleware import register_middleware
from app.routes import register_blueprints


# =====================================
# SECTION: App Factory
# =====================================
def create_app(config_name: str | None = None) -> Flask:
    """Create and configure the Flask application instance."""

    # Create base Flask app object.
    app = Flask(__name__, instance_relative_config=False)

    # Resolve environment profile (development is default).
    active_config = config_name or os.getenv("APP_ENV", "development")
    app.config.from_object(config_by_name.get(active_config, config_by_name["development"]))

    # Ensure upload directory exists for document workflows.
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    # Ensure ML artifact directory exists for serialized classical models.
    os.makedirs(app.config.get("AI_MODEL_DIR", "model_store"), exist_ok=True)
    # Ensure vector-memory storage directory exists for RAG features.
    os.makedirs(app.config.get("RAG_STORE_DIR", "rag_store"), exist_ok=True)

    # Initialize extension layer (DB, auth, JWT, placeholders).
    init_extensions(app)

    # Register all route blueprints.
    register_blueprints(app)

    # Register global middleware.
    register_middleware(app)

    # Register global error handlers.
    register_error_handlers(app)

    return app

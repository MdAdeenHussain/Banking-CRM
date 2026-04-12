"""API blueprint — JWT-protected REST endpoints."""
from flask import Blueprint
api_bp = Blueprint("api", __name__)

from app.extensions import csrf
# Exempt API routes from CSRF (they use JWT)
csrf.exempt(api_bp)

from app.blueprints.api import routes  # noqa

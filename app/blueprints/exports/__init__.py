"""Exports blueprint."""
from flask import Blueprint
exports_bp = Blueprint("exports", __name__)
from app.blueprints.exports import routes  # noqa

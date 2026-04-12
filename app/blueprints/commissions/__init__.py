"""Commissions blueprint."""
from flask import Blueprint
commissions_bp = Blueprint("commissions", __name__)
from app.blueprints.commissions import routes  # noqa

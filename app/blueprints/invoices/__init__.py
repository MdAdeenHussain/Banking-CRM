"""Invoices blueprint."""
from flask import Blueprint
invoices_bp = Blueprint("invoices", __name__)
from app.blueprints.invoices import routes  # noqa

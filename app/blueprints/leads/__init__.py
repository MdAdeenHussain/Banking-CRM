"""Leads blueprint — CRUD, pipeline, timeline."""
from flask import Blueprint

leads_bp = Blueprint("leads", __name__, template_folder="../../templates/leads")
from app.blueprints.leads import routes  # noqa

"""Dashboard blueprint — main landing page with KPI widgets."""
from flask import Blueprint

dashboard_bp = Blueprint("dashboard", __name__, template_folder="../../templates/dashboard")
from app.blueprints.dashboard import routes  # noqa

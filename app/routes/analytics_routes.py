"""Analytics module route controllers."""

# =====================================
# SECTION: Imports
# =====================================
from flask import Blueprint, render_template
from flask_login import login_required


# =====================================
# SECTION: Blueprint Definition
# =====================================
analytics_bp = Blueprint("analytics", __name__)


# =====================================
# SECTION: Analytics Routes
# =====================================
@analytics_bp.get("/analytics")
@login_required
def analytics_dashboard():
    return render_template("analytics/analytics_dashboard.html")

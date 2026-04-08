"""Platform-level routes (admin and operational utilities)."""

# =====================================
# SECTION: Imports
# =====================================
from flask import Blueprint, render_template
from flask_login import login_required

from app.decorators import role_required


# =====================================
# SECTION: Blueprint Definition
# =====================================
platform_bp = Blueprint("platform", __name__)


# =====================================
# SECTION: Platform Routes
# =====================================
@platform_bp.get("/platform")
@role_required("platform", "owner")
def platform_home():
    """Render platform dashboard panel."""
    return render_template("dashboard/platform_dashboard.html")


@platform_bp.get("/platform/ai-command-center")
@role_required("platform", "owner", "branch", "agent")
def ai_command_center():
    return render_template("ai/ai_command_center.html")


@platform_bp.get("/ai-command-center")
@role_required("platform", "owner", "branch", "agent")
def ai_command_center_short():
    """Alias route for AI command center."""
    return render_template("ai/ai_command_center.html")


@platform_bp.get("/platform/communications")
@role_required("platform", "owner", "branch", "agent")
def communications():
    return render_template("ai/communications.html")


@platform_bp.get("/communications")
@role_required("platform", "owner", "branch", "agent")
def communications_short():
    """Alias route for communication center."""
    return render_template("ai/communications.html")

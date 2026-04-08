"""Settings module route controllers."""

# =====================================
# SECTION: Imports
# =====================================
from flask import Blueprint, render_template
from flask_login import login_required


# =====================================
# SECTION: Blueprint Definition
# =====================================
settings_bp = Blueprint("settings", __name__)


# =====================================
# SECTION: Settings Routes
# =====================================
@settings_bp.get("/settings")
@login_required
def settings_profile_default():
    return render_template("settings/settings_profile.html")


@settings_bp.get("/settings/profile")
@login_required
def settings_profile():
    return render_template("settings/settings_profile.html")


@settings_bp.get("/settings/security")
@login_required
def settings_security():
    return render_template("settings/settings_security.html")


@settings_bp.get("/settings/roles")
@login_required
def settings_roles():
    return render_template("settings/settings_roles.html")


@settings_bp.get("/settings/integrations")
@login_required
def settings_integrations():
    return render_template("settings/settings_integrations.html")

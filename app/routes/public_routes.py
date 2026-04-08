"""Public website route controllers."""

# =====================================
# SECTION: Imports
# =====================================
from flask import Blueprint, render_template


# =====================================
# SECTION: Blueprint Definition
# =====================================
public_bp = Blueprint("public", __name__)


# =====================================
# SECTION: Public Routes
# =====================================
@public_bp.get("/")
def home():
    return render_template("public/index.html")


@public_bp.get("/features")
def features():
    return render_template("public/features.html")


@public_bp.get("/pricing")
def pricing():
    return render_template("public/pricing.html")


@public_bp.get("/solutions")
def solutions():
    return render_template("public/solutions.html")


@public_bp.get("/security")
def security():
    return render_template("public/security.html")


@public_bp.get("/contact")
def contact():
    return render_template("public/contact.html")


@public_bp.get("/demo-booking")
def demo_booking():
    return render_template("public/demo_booking.html")

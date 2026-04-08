"""
app/notifications/routes.py
Notification routes.
PHASE_2_HOOK: Complete implementation in Subphase 5.
"""

from flask import request, jsonify, g
from app.notifications import notifications_bp
from app.decorators import login_required, tenant_required

# ============================================================================
# NOTIFICATION LIST
# ============================================================================

@notifications_bp.route("", methods=["GET"])
@login_required
@tenant_required
def list_notifications():
    """GET /notifications - Get user's notifications."""
    # PHASE_2_HOOK: Paginate, filter by read status
    return {"message": "Notification list implementation pending"}, 200


# ============================================================================
# MARK AS READ
# ============================================================================

@notifications_bp.route("/read", methods=["POST"])
@login_required
@tenant_required
def mark_notification_read():
    """POST /notifications/read - Mark notification as read."""
    # PHASE_2_HOOK: Update is_read flag
    return {"message": "Mark as read implementation pending"}, 200

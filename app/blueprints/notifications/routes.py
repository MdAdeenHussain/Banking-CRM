"""LoanAxis CRM — Notification Routes"""
from flask import render_template, jsonify, request
from flask_login import login_required, current_user
from app.blueprints.notifications import notifications_bp
from app.blueprints.notifications.services import get_unread_count, get_recent_notifications, mark_all_read
from app.models.notification import Notification


@notifications_bp.route("/")
@login_required
def index():
    page = request.args.get("page", 1, type=int)
    pagination = Notification.query.filter_by(user_id=current_user.id).order_by(
        Notification.created_at.desc()).paginate(page=page, per_page=25)
    return render_template("notifications/index.html", notifications=pagination.items, pagination=pagination)


@notifications_bp.route("/api/unread-count")
@login_required
def api_unread_count():
    return jsonify({"count": get_unread_count(current_user.id)})


@notifications_bp.route("/api/recent")
@login_required
def api_recent():
    notifs = get_recent_notifications(current_user.id)
    return jsonify([n.to_dict() for n in notifs])


@notifications_bp.route("/mark-all-read", methods=["POST"])
@login_required
def mark_read():
    mark_all_read(current_user.id)
    return jsonify({"success": True})

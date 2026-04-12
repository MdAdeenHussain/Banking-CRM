"""LoanAxis CRM — REST API Routes (JWT-protected)"""
import jwt
from datetime import datetime, timezone
from functools import wraps
from flask import request, jsonify, current_app
from app.blueprints.api import api_bp
from app.blueprints.api.serializers import lead_to_dict, commission_to_dict
from app.models.user import User
from app.models.lead import Lead
from app.models.commission import Commission


def jwt_required(f):
    """Decorator for JWT-protected API endpoints."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
        if not token:
            return jsonify({"error": "Token required"}), 401
        try:
            payload = jwt.decode(token, current_app.config["JWT_SECRET_KEY"], algorithms=["HS256"])
            user = User.query.get(payload["sub"])
            if not user or not user.is_active:
                return jsonify({"error": "Invalid token"}), 401
            request.api_user = user
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        return f(*args, **kwargs)
    return decorated


@api_bp.route("/auth/token", methods=["POST"])
def get_token():
    """Get JWT access token."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400
    user = User.query.filter_by(email=data.get("email", "").lower().strip()).first()
    if not user or not user.check_password(data.get("password", "")):
        return jsonify({"error": "Invalid credentials"}), 401

    expires = current_app.config["JWT_ACCESS_TOKEN_EXPIRES"]
    payload = {
        "sub": user.id, "role": user.role,
        "exp": datetime.now(timezone.utc) + expires,
        "iat": datetime.now(timezone.utc),
    }
    token = jwt.encode(payload, current_app.config["JWT_SECRET_KEY"], algorithm="HS256")
    return jsonify({"access_token": token, "token_type": "bearer",
                    "expires_in": int(expires.total_seconds())})


@api_bp.route("/leads", methods=["GET"])
@jwt_required
def list_leads():
    page = request.args.get("page", 1, type=int)
    query = Lead.query.filter_by(is_deleted=False)
    if request.api_user.role == "employee":
        query = query.filter_by(assigned_executive_id=request.api_user.id)
    pagination = query.order_by(Lead.created_at.desc()).paginate(page=page, per_page=25)
    return jsonify({
        "leads": [lead_to_dict(l) for l in pagination.items],
        "total": pagination.total, "page": pagination.page, "pages": pagination.pages,
    })


@api_bp.route("/leads/<lead_id>", methods=["GET"])
@jwt_required
def get_lead(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    return jsonify(lead_to_dict(lead))


@api_bp.route("/commissions", methods=["GET"])
@jwt_required
def list_commissions():
    query = Commission.query.filter_by(is_deleted=False)
    if request.api_user.role == "employee":
        query = query.filter_by(employee_id=request.api_user.id)
    comms = query.order_by(Commission.created_at.desc()).limit(50).all()
    return jsonify({"commissions": [commission_to_dict(c) for c in comms]})

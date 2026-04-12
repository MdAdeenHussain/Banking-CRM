"""Banking DSA CRM — Admin Services"""
from app.extensions import db
from app.models.user import User
from app.models.audit_log import AuditLog
from app.models.branch import Branch


def get_full_user_table():
    """Get all users with details for Super Admin user management."""
    return User.query.filter_by(is_deleted=False).order_by(User.role, User.full_name).all()


def get_audit_logs(page=1, per_page=50, table_filter=None, action_filter=None):
    """Get paginated audit logs with optional filtering."""
    query = AuditLog.query.filter_by(is_deleted=False)
    if table_filter:
        query = query.filter(AuditLog.table_name == table_filter)
    if action_filter:
        query = query.filter(AuditLog.action == action_filter)
    return query.order_by(AuditLog.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)


def create_branch(data):
    """Create a new branch."""
    branch = Branch(
        name=data["name"], city=data.get("city"), state=data.get("state"),
        address=data.get("address"), gstin=data.get("gstin"),
        is_active=data.get("is_active", True),
    )
    db.session.add(branch)
    db.session.commit()
    return branch

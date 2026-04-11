"""Routes package initialization - exports all blueprints"""

from app.routes.auth import auth_bp
from app.routes.dashboard import dashboard_bp
from app.routes.leads import leads_bp
from app.routes.employees import employees_bp
from app.routes.commissions import commissions_bp
from app.routes.tasks import tasks_bp
from app.routes.documents import documents_bp
from app.routes.analytics import analytics_bp
from app.routes.invoices import invoices_bp
from app.routes.exports import exports_bp
from app.routes.admin import admin_bp
from app.routes.notifications import notifications_bp

__all__ = [
    'auth_bp',
    'dashboard_bp',
    'leads_bp',
    'employees_bp',
    'commissions_bp',
    'tasks_bp',
    'documents_bp',
    'analytics_bp',
    'invoices_bp',
    'exports_bp',
    'admin_bp',
    'notifications_bp'
]

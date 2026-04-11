"""Services module for the CRM application"""

from .auth_service import AuthService
from .document_service import DocumentService
from .notification_service import NotificationService
from .commission_service import CommissionService
from .analytics_service import AnalyticsService
from .export_service import ExportService
from .email_service import EmailService
from .invoice_service import InvoiceService
from .audit_service import AuditService

__all__ = [
    'AuthService',
    'DocumentService',
    'NotificationService',
    'CommissionService',
    'AnalyticsService',
    'ExportService',
    'EmailService',
    'InvoiceService',
    'AuditService',
]

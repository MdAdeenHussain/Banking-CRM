"""Database models for the CRM application"""

from .user import User
from .role import Role
from .lead import Lead
from .employee import Employee
from .commission_tracker import CommissionTracker
from .document import Document
from .task import Task
from .activity_log import ActivityLog
from .audit_log import AuditLog
from .notification import Notification
from .otp import OTP
from .lead_status import LeadStatus
from .bank_application import BankApplication
from .client_financial import ClientFinancial
from .invoice import Invoice
from .reminder import Reminder

__all__ = [
    'User',
    'Role',
    'Lead',
    'Employee',
    'CommissionTracker',
    'Document',
    'Task',
    'ActivityLog',
    'AuditLog',
    'Notification',
    'OTP',
    'LeadStatus',
    'BankApplication',
    'ClientFinancial',
    'Invoice',
    'Reminder',
]

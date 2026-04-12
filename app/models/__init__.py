"""
LoanAxis CRM — Models Package

Import all models here so Flask-Migrate discovers them
when generating migrations.
"""

from app.models.base import BaseModel
from app.models.user import User, UserSession, LoginActivity
from app.models.branch import Branch
from app.models.bank_partner import BankPartner, user_bank_partners
from app.models.lead import Lead, LeadStatusHistory
from app.models.client_financial import ClientFinancial
from app.models.bank_application import BankApplication
from app.models.document import Document
from app.models.commission import Commission
from app.models.task import Task
from app.models.notification import Notification
from app.models.invoice import Invoice
from app.models.remark import Remark
from app.models.audit_log import AuditLog

__all__ = [
    "BaseModel",
    "User", "UserSession", "LoginActivity",
    "Branch",
    "BankPartner", "user_bank_partners",
    "Lead", "LeadStatusHistory",
    "ClientFinancial",
    "BankApplication",
    "Document",
    "Commission",
    "Task",
    "Notification",
    "Invoice",
    "Remark",
    "AuditLog",
]

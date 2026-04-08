"""Model package exports.

Importing this package ensures model metadata is registered for
migrations and relationship resolution.
"""

# =====================================
# SECTION: Imports
# =====================================
from app.models.application import Application
from app.models.audit_log import AuditLog
from app.models.base import BaseModel
from app.models.billing import Billing
from app.models.customer import Customer
from app.models.document import Document
from app.models.lead import Lead
from app.models.lender import Lender
from app.models.model_registry import ModelRegistryEntry
from app.models.notification import Notification
from app.models.tenant import Tenant
from app.models.user import User

__all__ = [
    "BaseModel",
    "Tenant",
    "User",
    "Lead",
    "Customer",
    "Application",
    "Document",
    "Lender",
    "ModelRegistryEntry",
    "Notification",
    "AuditLog",
    "Billing",
]

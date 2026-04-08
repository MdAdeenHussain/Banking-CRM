"""
app/constants.py
Enums, constants, and fixed values for the application.
"""

from enum import Enum

# ============================================================================
# ROLES
# ============================================================================
class UserRole(str, Enum):
    """User roles in multi-tenant system."""
    SUPER_ADMIN = "super_admin"
    TENANT_ADMIN = "tenant_admin"
    BRANCH_MANAGER = "branch_manager"
    AGENT = "agent"
    TELECALLER = "telecaller"
    COMPLIANCE = "compliance"
    ACCOUNTS = "accounts"


# ============================================================================
# LEAD STATUSES & STAGES
# ============================================================================
class LeadStatus(str, Enum):
    """Lead progression pipeline stages."""
    NEW_LEAD = "NEW_LEAD"
    CONTACTED = "CONTACTED"
    INTERESTED = "INTERESTED"
    DOCS_PENDING = "DOCS_PENDING"
    DOCS_RECEIVED = "DOCS_RECEIVED"
    ELIGIBILITY_CHECKED = "ELIGIBILITY_CHECKED"
    BANK_MATCHED = "BANK_MATCHED"
    APPLICATION_FILED = "APPLICATION_FILED"
    UNDER_REVIEW = "UNDER_REVIEW"
    SANCTIONED = "SANCTIONED"
    DISBURSED = "DISBURSED"
    LOST = "LOST"


class LeadSource(str, Enum):
    """Lead acquisition source."""
    WEBSITE = "WEBSITE"
    REFERRAL = "REFERRAL"
    CAMPAIGN = "CAMPAIGN"
    DIRECT_CALL = "DIRECT_CALL"
    PARTNER = "PARTNER"
    OTHER = "OTHER"


class LeadPriority(str, Enum):
    """Lead priority level."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


# ============================================================================
# LOAN TYPES
# ============================================================================
class LoanType(str, Enum):
    """Types of loans offered."""
    HOME_LOAN = "HOME_LOAN"
    PERSONAL_LOAN = "PERSONAL_LOAN"
    BUSINESS_LOAN = "BUSINESS_LOAN"
    EDUCATION_LOAN = "EDUCATION_LOAN"
    VEHICLE_LOAN = "VEHICLE_LOAN"
    LAP = "LAP"
    CREDIT_CARD = "CREDIT_CARD"


# ============================================================================
# NOTIFICATION TYPES
# ============================================================================
class NotificationType(str, Enum):
    """Types of in-app notifications."""
    ASSIGNMENT = "ASSIGNMENT"
    FOLLOW_UP = "FOLLOW_UP"
    STATUS_CHANGE = "STATUS_CHANGE"
    SYSTEM = "SYSTEM"
    ALERT = "ALERT"


# ============================================================================
# AUDIT ACTION TYPES
# ============================================================================
class AuditAction(str, Enum):
    """Types of mutations logged."""
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    STATUS_CHANGE = "STATUS_CHANGE"
    ASSIGNMENT = "ASSIGNMENT"


# ============================================================================
# TENANT PLANS
# ============================================================================
class TenantPlan(str, Enum):
    """SaaS subscription plans (Phase 3)."""
    STARTER = "STARTER"
    GROWTH = "GROWTH"
    ENTERPRISE = "ENTERPRISE"
    CUSTOM = "CUSTOM"


# ============================================================================
# FIXED CONSTANTS
# ============================================================================

# Session & Token
SESSION_TIMEOUT_HOURS = 24
JWT_ACCESS_TOKEN_EXPIRES_MINUTES = 15
JWT_REFRESH_TOKEN_EXPIRES_DAYS = 7

# Security
MAX_LOGIN_ATTEMPTS = 5
LOGIN_ATTEMPT_LOCKOUT_MINUTES = 15
PASSWORD_MIN_LENGTH = 8

# Pagination
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Follow-up Reminder
FOLLOW_UP_REMINDER_DAYS = 3

# Duplicate Lead Detection Threshold
DUPLICATE_LEAD_SIMILARITY_THRESHOLD = 0.85

# Role Redirect
ROLE_REDIRECTS = {
    UserRole.SUPER_ADMIN: "/dashboard/platform",
    UserRole.TENANT_ADMIN: "/dashboard/owner",
    UserRole.BRANCH_MANAGER: "/dashboard/branch",
    UserRole.AGENT: "/dashboard/agent",
    UserRole.TELECALLER: "/dashboard/calls",
    UserRole.COMPLIANCE: "/dashboard/compliance",
    UserRole.ACCOUNTS: "/dashboard/accounts",
}

"""Form package exports.

Flask-WTF forms are grouped by domain for cleaner route modules.
"""

from app.forms.auth_forms import LoginForm, TenantRegistrationForm, UserRegistrationForm
from app.forms.crm_forms import CustomerCreateForm, LeadCreateForm

__all__ = [
    "LoginForm",
    "TenantRegistrationForm",
    "UserRegistrationForm",
    "LeadCreateForm",
    "CustomerCreateForm",
]

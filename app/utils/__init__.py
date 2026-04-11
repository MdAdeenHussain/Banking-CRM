"""Utility modules for the CRM application"""

from .helpers import paginate, format_date, format_currency, generate_unique_id, get_client_ip
from .validators import validate_email, validate_phone, validate_password, validate_pincode
from .decorators import login_required, admin_required, role_required
from .encryption import encrypt_data, decrypt_data, hash_password, verify_password
from .constants import (
    USER_ROLES, LEAD_STATUS, COMMISSION_STATUS, DOCUMENT_TYPES,
    BANK_LIST, PRODUCTS, DSA_STATUS, ACTIVITY_TYPES
)

__all__ = [
    'paginate',
    'format_date',
    'format_currency',
    'generate_unique_id',
    'get_client_ip',
    'validate_email',
    'validate_phone',
    'validate_password',
    'validate_pincode',
    'login_required',
    'admin_required',
    'role_required',
    'encrypt_data',
    'decrypt_data',
    'hash_password',
    'verify_password',
    'USER_ROLES',
    'LEAD_STATUS',
    'COMMISSION_STATUS',
    'DOCUMENT_TYPES',
    'BANK_LIST',
    'PRODUCTS',
    'DSA_STATUS',
    'ACTIVITY_TYPES',
]

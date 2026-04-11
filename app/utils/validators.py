"""Validation functions for CRM data"""

import re
from email_validator import validate_email as validate_email_lib, EmailNotValidError


def validate_email(email):
    """
    Validate email address format.
    
    Args:
        email: Email string to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        validate_email_lib(email, check_deliverability=False)
        return True, None
    except EmailNotValidError as e:
        return False, str(e)


def validate_phone(phone):
    """
    Validate Indian phone number format.
    
    Args:
        phone: Phone number string
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Remove spaces and dashes
    phone = re.sub(r'[\s\-()]', '', phone)
    
    # Check if 10 digits and starts with 6-9
    if re.match(r'^[6-9]\d{9}$', phone):
        return True, None
    
    return False, "Invalid phone number. Must be 10 digits starting with 6-9."


def validate_password(password):
    """
    Validate password strength.
    Requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    
    Args:
        password: Password string
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter."
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter."
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit."
    
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/\\|`~]', password):
        return False, "Password must contain at least one special character."
    
    return True, None


def validate_pincode(pincode):
    """
    Validate Indian pincode format.
    
    Args:
        pincode: Pincode string
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    pincode = str(pincode).strip()
    
    if re.match(r'^\d{6}$', pincode):
        return True, None
    
    return False, "Invalid pincode. Must be 6 digits."


def validate_pan(pan):
    """
    Validate Indian PAN format.
    Format: AAAAA0000A
    
    Args:
        pan: PAN string
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    pan = pan.upper().strip()
    
    if re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$', pan):
        return True, None
    
    return False, "Invalid PAN format. Expected: AAAAA0000A"


def validate_aadhar(aadhar):
    """
    Validate Indian Aadhar number format.
    
    Args:
        aadhar: Aadhar number string
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    aadhar = re.sub(r'\s', '', str(aadhar))
    
    if re.match(r'^\d{12}$', aadhar):
        return True, None
    
    return False, "Invalid Aadhar number. Must be 12 digits."


def validate_ifsc(ifsc):
    """
    Validate Indian IFSC code format.
    
    Args:
        ifsc: IFSC code string
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    ifsc = ifsc.upper().strip()
    
    if re.match(r'^[A-Z]{4}0[A-Z0-9]{6}$', ifsc):
        return True, None
    
    return False, "Invalid IFSC code format. Expected: AAAA0AAAAAA"


def validate_url(url):
    """
    Validate URL format.
    
    Args:
        url: URL string
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # or IP
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    if url_pattern.match(url):
        return True, None
    
    return False, "Invalid URL format."


def validate_username(username):
    """
    Validate username format.
    Requirements:
    - 3-20 characters
    - Only alphanumeric and underscores
    - Must start with letter
    
    Args:
        username: Username string
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not (3 <= len(username) <= 20):
        return False, "Username must be 3-20 characters long."
    
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', username):
        return False, "Username must start with letter and contain only alphanumeric and underscore."
    
    return True, None


def validate_amount(amount, min_val=0, max_val=None):
    """
    Validate numeric amount.
    
    Args:
        amount: Amount to validate
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        amount_float = float(amount)
    except (ValueError, TypeError):
        return False, "Invalid amount. Must be a number."
    
    if amount_float < min_val:
        return False, f"Amount must be at least {min_val}."
    
    if max_val and amount_float > max_val:
        return False, f"Amount cannot exceed {max_val}."
    
    return True, None

"""Encryption and password utilities"""

from cryptography.fernet import Fernet
import os
from werkzeug.security import generate_password_hash, check_password_hash
import base64
import hashlib


# Initialize encryption cipher
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')
if not ENCRYPTION_KEY:
    # Generate a key if not in environment
    ENCRYPTION_KEY = base64.urlsafe_b64encode(hashlib.sha256(b'default-key-change-in-production').digest())
else:
    ENCRYPTION_KEY = ENCRYPTION_KEY.encode()

cipher = Fernet(ENCRYPTION_KEY)


def encrypt_data(data):
    """
    Encrypt sensitive data using Fernet symmetric encryption.
    
    Args:
        data: Data to encrypt (string or bytes)
        
    Returns:
        Encrypted data as string
    """
    if isinstance(data, str):
        data = data.encode()
    
    encrypted = cipher.encrypt(data)
    return encrypted.decode()


def decrypt_data(encrypted_data):
    """
    Decrypt Fernet encrypted data.
    
    Args:
        encrypted_data: Encrypted data string
        
    Returns:
        Decrypted data as string
    """
    if isinstance(encrypted_data, str):
        encrypted_data = encrypted_data.encode()
    
    try:
        decrypted = cipher.decrypt(encrypted_data)
        return decrypted.decode()
    except Exception as e:
        raise ValueError(f"Failed to decrypt data: {str(e)}")


def hash_password(password):
    """
    Hash password using werkzeug security.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
    """
    return generate_password_hash(password, method='pbkdf2:sha256')


def verify_password(password, hash_value):
    """
    Verify plain text password against hash.
    
    Args:
        password: Plain text password to verify
        hash_value: Hashed password to compare against
        
    Returns:
        Boolean indicating if password matches
    """
    return check_password_hash(hash_value, password)


def generate_temp_token(data, expiry_hours=24):
    """
    Generate a temporary token with expiry.
    
    Args:
        data: Data to encode in token
        expiry_hours: Hours until token expires
        
    Returns:
        Token string
    """
    from datetime import datetime, timedelta
    
    payload = f"{data}|{datetime.utcnow().isoformat()}"
    token = encrypt_data(payload)
    return token


def verify_temp_token(token, max_age_hours=24):
    """
    Verify temporary token and extract data.
    
    Args:
        token: Token to verify
        max_age_hours: Maximum age of token in hours
        
    Returns:
        Tuple of (is_valid, data) or (False, None) if invalid
    """
    from datetime import datetime, timedelta
    
    try:
        payload = decrypt_data(token)
        data, timestamp_str = payload.rsplit('|', 1)
        
        token_time = datetime.fromisoformat(timestamp_str)
        age_hours = (datetime.utcnow() - token_time).total_seconds() / 3600
        
        if age_hours > max_age_hours:
            return False, None
        
        return True, data
    except Exception:
        return False, None


def hash_sensitive_field(value):
    """
    Hash sensitive field like phone or email for comparison.
    
    Args:
        value: Value to hash
        
    Returns:
        Hashed value
    """
    return hashlib.sha256(str(value).encode()).hexdigest()


def mask_sensitive_data(data, visible_chars=4):
    """
    Mask sensitive data showing only last N characters.
    
    Args:
        data: Data to mask
        visible_chars: Number of characters to keep visible
        
    Returns:
        Masked string
    """
    data_str = str(data)
    if len(data_str) <= visible_chars:
        return '*' * len(data_str)
    
    return '*' * (len(data_str) - visible_chars) + data_str[-visible_chars:]


def generate_api_key(prefix='', length=32):
    """
    Generate a secure API key.
    
    Args:
        prefix: Optional prefix for API key
        length: Length of random part
        
    Returns:
        API key string
    """
    import secrets
    random_part = secrets.token_urlsafe(length)
    return f"{prefix}_{random_part}" if prefix else random_part

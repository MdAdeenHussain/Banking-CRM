"""Helper functions for common tasks"""

from datetime import datetime, timedelta
import string
import random
import os
from flask import request


def paginate(query, page=1, per_page=20):
    """
    Paginate a SQLAlchemy query result.
    
    Args:
        query: SQLAlchemy query object
        page: Page number (1-indexed)
        per_page: Items per page
        
    Returns:
        Pagination object with items, total, pages, current page
    """
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    return {
        'items': paginated.items,
        'total': paginated.total,
        'pages': paginated.pages,
        'current_page': page,
        'per_page': per_page,
        'has_next': paginated.has_next,
        'has_prev': paginated.has_prev,
    }


def format_date(date_obj, format_str='%d-%m-%Y'):
    """
    Format datetime object to string.
    
    Args:
        date_obj: datetime object
        format_str: strftime format string
        
    Returns:
        Formatted date string
    """
    if not date_obj:
        return '-'
    if isinstance(date_obj, str):
        date_obj = datetime.fromisoformat(date_obj)
    return date_obj.strftime(format_str)


def format_currency(amount, currency='₹', decimals=2):
    """
    Format amount as currency string.
    
    Args:
        amount: Numeric amount
        currency: Currency symbol
        decimals: Decimal places
        
    Returns:
        Formatted currency string
    """
    if amount is None:
        return f'{currency}0.00'
    return f'{currency}{amount:,.{decimals}f}'


def generate_unique_id(prefix='', length=12):
    """
    Generate a unique identifier.
    
    Args:
        prefix: Optional prefix for the ID
        length: Length of random part
        
    Returns:
        Unique ID string
    """
    characters = string.ascii_letters + string.digits
    random_part = ''.join(random.choices(characters, k=length))
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    return f"{prefix}{timestamp}{random_part}"[-20:]


def get_client_ip():
    """
    Get client IP address from request.
    
    Returns:
        Client IP address string
    """
    if request.environ.get('HTTP_CF_CONNECTING_IP'):
        return request.environ['HTTP_CF_CONNECTING_IP']
    if request.environ.get('HTTP_X_FORWARDED_FOR'):
        return request.environ['HTTP_X_FORWARDED_FOR'].split(',')[0]
    return request.environ.get('REMOTE_ADDR', '0.0.0.0')


def get_date_range(period='month'):
    """
    Get start and end dates for a period.
    
    Args:
        period: 'month', 'quarter', 'year', or 'week'
        
    Returns:
        Tuple of (start_date, end_date)
    """
    end_date = datetime.now().date()
    
    if period == 'month':
        start_date = end_date.replace(day=1)
    elif period == 'quarter':
        quarter_start_month = ((end_date.month - 1) // 3) * 3 + 1
        start_date = end_date.replace(month=quarter_start_month, day=1)
    elif period == 'year':
        start_date = end_date.replace(month=1, day=1)
    elif period == 'week':
        start_date = end_date - timedelta(days=end_date.weekday())
    else:
        start_date = end_date - timedelta(days=30)
    
    return start_date, end_date


def calculate_age(birth_date):
    """
    Calculate age from birth date.
    
    Args:
        birth_date: Birth date object
        
    Returns:
        Age in years as integer
    """
    today = datetime.now().date()
    if isinstance(birth_date, str):
        birth_date = datetime.fromisoformat(birth_date).date()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))


def generate_otp(length=6):
    """
    Generate a random OTP.
    
    Args:
        length: Length of OTP
        
    Returns:
        OTP string of digits
    """
    return ''.join(random.choices(string.digits, k=length))


def is_business_hours():
    """
    Check if current time is within business hours (9 AM - 6 PM IST).
    
    Returns:
        Boolean indicating if within business hours
    """
    current_hour = datetime.now().hour
    return 9 <= current_hour < 18

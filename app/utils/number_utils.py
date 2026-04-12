"""
LoanAxis CRM — Number Utilities

Currency formatting, amount-to-words conversion for invoices.
"""

import math


def format_inr(amount: float, show_symbol: bool = True) -> str:
    """
    Format a number in Indian Rupee format (XX,XX,XXX.XX).

    Args:
        amount: The numeric amount
        show_symbol: Whether to prefix with ₹

    Returns:
        Formatted string like "₹12,34,567.89"
    """
    if amount is None:
        return "₹0.00" if show_symbol else "0.00"

    is_negative = amount < 0
    amount = abs(amount)

    # Split integer and decimal
    integer_part = int(amount)
    decimal_part = round(amount - integer_part, 2)
    decimal_str = f"{decimal_part:.2f}"[1:]  # ".XX"

    # Indian number formatting: XX,XX,XXX
    s = str(integer_part)
    if len(s) <= 3:
        formatted = s
    else:
        # Last 3 digits
        last_three = s[-3:]
        remaining = s[:-3]
        # Group remaining in pairs from right
        groups = []
        while remaining:
            groups.insert(0, remaining[-2:])
            remaining = remaining[:-2]
        formatted = ",".join(groups) + "," + last_three

    result = formatted + decimal_str
    if is_negative:
        result = "-" + result
    if show_symbol:
        result = "₹" + result

    return result


def amount_in_words(amount: float) -> str:
    """
    Convert a numeric amount to words (Indian English).

    Handles up to ₹99,99,99,999 (99 crore).

    Args:
        amount: The numeric amount

    Returns:
        String like "Twelve Lakh Thirty Four Thousand Five Hundred Sixty Seven Rupees and Eighty Nine Paise Only"
    """
    if amount is None or amount == 0:
        return "Zero Rupees Only"

    ones = [
        "", "One", "Two", "Three", "Four", "Five", "Six", "Seven",
        "Eight", "Nine", "Ten", "Eleven", "Twelve", "Thirteen",
        "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen",
    ]
    tens = [
        "", "", "Twenty", "Thirty", "Forty", "Fifty",
        "Sixty", "Seventy", "Eighty", "Ninety",
    ]

    def _two_digits(n: int) -> str:
        if n < 20:
            return ones[n]
        return (tens[n // 10] + " " + ones[n % 10]).strip()

    def _three_digits(n: int) -> str:
        if n >= 100:
            return ones[n // 100] + " Hundred " + _two_digits(n % 100)
        return _two_digits(n)

    is_negative = amount < 0
    amount = abs(amount)

    # Split rupees and paise
    rupees = int(amount)
    paise = round((amount - rupees) * 100)

    if rupees == 0 and paise == 0:
        return "Zero Rupees Only"

    # Indian number system: Crore, Lakh, Thousand, Hundred
    parts = []

    crore = rupees // 10000000
    rupees %= 10000000
    if crore:
        parts.append(_two_digits(crore) + " Crore")

    lakh = rupees // 100000
    rupees %= 100000
    if lakh:
        parts.append(_two_digits(lakh) + " Lakh")

    thousand = rupees // 1000
    rupees %= 1000
    if thousand:
        parts.append(_two_digits(thousand) + " Thousand")

    if rupees:
        parts.append(_three_digits(rupees))

    result = " ".join(parts) + " Rupees"

    if paise:
        result += " and " + _two_digits(paise) + " Paise"

    result += " Only"

    if is_negative:
        result = "Minus " + result

    return result

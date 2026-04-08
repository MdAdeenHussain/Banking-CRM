"""Eligibility calculator engine.

This service contains transparent, beginner-friendly financial formulas
used in loan eligibility workflows.
"""

# ======================================
# SECTION: Imports
# ======================================
from __future__ import annotations

import numpy as np


# ======================================
# SECTION: Core Service Logic
# ======================================
# This module is calculator-focused, so core business orchestration
# is intentionally not implemented here.


# ======================================
# SECTION: Calculators
# ======================================
def calculate_foir(total_monthly_emi: float, net_income: float) -> float:
    """Calculate FOIR percentage.

    Formula:
        FOIR = (Total Monthly Obligations / Net Monthly Income) * 100
    """
    if net_income <= 0:
        return 0.0
    return float((total_monthly_emi / net_income) * 100)



def calculate_dti(total_debt: float, gross_income: float) -> float:
    """Calculate DTI percentage.

    Formula:
        DTI = (Total Debt / Gross Income) * 100
    """
    if gross_income <= 0:
        return 0.0
    return float((total_debt / gross_income) * 100)



def calculate_ltv(loan_amount: float, property_value: float) -> float:
    """Calculate LTV percentage.

    Formula:
        LTV = (Loan Amount / Property Value) * 100
    """
    if property_value <= 0:
        return 0.0
    return float((loan_amount / property_value) * 100)



def calculate_emi(principal: float, annual_rate: float, tenure_months: int) -> float:
    """Calculate EMI using standard reducing-balance formula.

    Formula:
        EMI = P * r * (1+r)^n / ((1+r)^n - 1)

    Where:
        P = principal,
        r = monthly interest rate,
        n = number of months.
    """
    if principal <= 0 or annual_rate < 0 or tenure_months <= 0:
        return 0.0

    monthly_rate = annual_rate / (12 * 100)
    if monthly_rate == 0:
        return float(principal / tenure_months)

    numerator = principal * monthly_rate * ((1 + monthly_rate) ** tenure_months)
    denominator = ((1 + monthly_rate) ** tenure_months) - 1

    if denominator == 0:
        return 0.0
    return float(numerator / denominator)



def max_loan_eligibility(
    *,
    net_monthly_income: float,
    existing_monthly_obligations: float,
    annual_rate: float,
    tenure_months: int,
    max_foir_percent: float = 50.0,
) -> float:
    """Estimate max eligible loan amount using FOIR capacity.

    Steps:
    1) Determine maximum allowed monthly obligation by FOIR.
    2) Subtract existing obligations to get available EMI capacity.
    3) Convert EMI capacity to principal using reverse EMI factor.
    """
    if net_monthly_income <= 0 or tenure_months <= 0:
        return 0.0

    max_allowed_obligation = (max_foir_percent / 100.0) * net_monthly_income
    available_emi = max_allowed_obligation - max(existing_monthly_obligations, 0)

    if available_emi <= 0:
        return 0.0

    monthly_rate = annual_rate / (12 * 100)
    if monthly_rate == 0:
        return float(available_emi * tenure_months)

    # Reverse EMI formula to derive principal from EMI.
    factor = ((1 + monthly_rate) ** tenure_months - 1) / (
        monthly_rate * ((1 + monthly_rate) ** tenure_months)
    )
    principal = available_emi * factor
    return float(max(principal, 0))


# ======================================
# SECTION: Helper Functions
# ======================================
def eligibility_snapshot(
    *,
    net_income: float,
    gross_income: float,
    total_monthly_emi: float,
    total_debt: float,
    desired_loan_amount: float,
    property_value: float,
    annual_rate: float,
    tenure_months: int,
) -> dict:
    """Return consolidated eligibility metrics in one dictionary."""
    foir = calculate_foir(total_monthly_emi=total_monthly_emi, net_income=net_income)
    dti = calculate_dti(total_debt=total_debt, gross_income=gross_income)
    ltv = calculate_ltv(loan_amount=desired_loan_amount, property_value=property_value)
    emi = calculate_emi(principal=desired_loan_amount, annual_rate=annual_rate, tenure_months=tenure_months)
    max_eligible = max_loan_eligibility(
        net_monthly_income=net_income,
        existing_monthly_obligations=total_monthly_emi,
        annual_rate=annual_rate,
        tenure_months=tenure_months,
    )

    return {
        "foir_percent": round(foir, 2),
        "dti_percent": round(dti, 2),
        "ltv_percent": round(ltv, 2),
        "emi": round(emi, 2),
        "max_loan_eligibility": round(max_eligible, 2),
        "is_desired_amount_within_limit": bool(desired_loan_amount <= max_eligible),
    }

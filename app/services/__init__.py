"""Service package exports.

This module uses lazy imports to keep app startup lightweight and avoid
loading optional heavy dependencies (like Pandas) unless needed.
"""

# ======================================
# SECTION: Imports
# ======================================
from __future__ import annotations

from importlib import import_module
from typing import Any


# ======================================
# SECTION: Core Service Logic
# ======================================
_EXPORT_MAP = {
    "AuthService": ("app.services.auth_service", "AuthService"),
    "LeadService": ("app.services.lead_service", "LeadService"),
    "CustomerService": ("app.services.customer_service", "CustomerService"),
    "ApplicationService": ("app.services.application_service", "ApplicationService"),
    "BillingService": ("app.services.billing_service", "BillingService"),
    "LeadWorkflowService": ("app.services.lead_workflow_service", "LeadWorkflowService"),
    "ApplicationWorkflowService": ("app.services.application_workflow_service", "ApplicationWorkflowService"),
    "LenderService": ("app.services.lender_service", "LenderService"),
    "CommissionService": ("app.services.commission_service", "CommissionService"),
    "AutomationService": ("app.services.automation_service", "AutomationService"),
    "DashboardKPIService": ("app.services.dashboard_kpi_service", "DashboardKPIService"),
    "calculate_foir": ("app.services.eligibility_service", "calculate_foir"),
    "calculate_dti": ("app.services.eligibility_service", "calculate_dti"),
    "calculate_ltv": ("app.services.eligibility_service", "calculate_ltv"),
    "calculate_emi": ("app.services.eligibility_service", "calculate_emi"),
    "max_loan_eligibility": ("app.services.eligibility_service", "max_loan_eligibility"),
    "eligibility_snapshot": ("app.services.eligibility_service", "eligibility_snapshot"),
}

__all__ = list(_EXPORT_MAP.keys())


# ======================================
# SECTION: Helper Functions
# ======================================
def __getattr__(name: str) -> Any:
    """Resolve service exports lazily on first access."""
    if name not in _EXPORT_MAP:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module_name, attr_name = _EXPORT_MAP[name]
    module = import_module(module_name)
    value = getattr(module, attr_name)
    globals()[name] = value
    return value


# ======================================
# SECTION: Calculators
# ======================================
# Calculator exports are included in `_EXPORT_MAP`.

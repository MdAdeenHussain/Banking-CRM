"""LoanAxis CRM — Export Services"""
from app.utils.export_utils import leads_to_xlsx, commissions_to_csv, employees_to_xlsx


def export_leads(leads):
    return leads_to_xlsx(leads)


def export_commissions(commissions):
    return commissions_to_csv(commissions)


def export_employees(employees):
    return employees_to_xlsx(employees)

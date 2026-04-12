"""LoanAxis CRM — API Serializers"""


def lead_to_dict(lead):
    return lead.to_dict() if hasattr(lead, "to_dict") else {}


def user_to_dict(user):
    return {
        "id": user.id, "employee_id": user.employee_id,
        "full_name": user.full_name, "email": user.email,
        "role": user.role, "is_active": user.is_active,
    }


def commission_to_dict(comm):
    return comm.to_dict() if hasattr(comm, "to_dict") else {}

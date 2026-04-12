"""
LoanAxis CRM — Export Utilities

Generate XLSX and CSV exports with professional formatting.
Uses Pandas + openpyxl for styled Excel exports.
"""

import io
from datetime import datetime
from typing import Optional

import pandas as pd


def leads_to_xlsx(leads: list, columns: list[str] = None) -> io.BytesIO:
    """
    Export leads data to a styled XLSX file.

    Args:
        leads: List of Lead model instances or dicts
        columns: Optional list of column names to include

    Returns:
        BytesIO buffer containing the XLSX file
    """
    default_columns = [
        "lead_number", "customer_name", "mobile_primary", "email",
        "city", "state", "loan_type", "loan_amount_applied",
        "cibil_score", "lead_source", "priority_tag",
        "pipeline_stage", "created_at",
    ]
    cols = columns or default_columns

    # Convert to dicts if needed
    data = []
    for lead in leads:
        if hasattr(lead, "to_dict"):
            row = lead.to_dict()
        else:
            row = lead
        data.append({k: row.get(k) for k in cols})

    df = pd.DataFrame(data, columns=cols)

    # Pretty column headers
    header_map = {
        "lead_number": "Lead #",
        "customer_name": "Customer Name",
        "mobile_primary": "Mobile",
        "email": "Email",
        "city": "City",
        "state": "State",
        "loan_type": "Loan Type",
        "loan_amount_applied": "Amount Applied (₹)",
        "cibil_score": "CIBIL Score",
        "lead_source": "Source",
        "priority_tag": "Priority",
        "pipeline_stage": "Stage",
        "created_at": "Created At",
    }
    df.rename(columns={k: header_map.get(k, k) for k in cols}, inplace=True)

    output = io.BytesIO()
    date_str = datetime.now().strftime("%Y-%m-%d")
    sheet_name = f"Leads_{date_str}"[:31]  # Excel sheet name max 31 chars

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)

        # Style the header row
        ws = writer.sheets[sheet_name]
        from openpyxl.styles import Font, PatternFill, Alignment

        header_font = Font(bold=True, color="FFFFFF", size=11)
        header_fill = PatternFill(start_color="6C63FF", end_color="6C63FF", fill_type="solid")

        for cell in ws[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center")

        # Auto-width columns
        for column_cells in ws.columns:
            max_length = max(len(str(cell.value or "")) for cell in column_cells)
            adjusted_width = min(max_length + 4, 50)
            ws.column_dimensions[column_cells[0].column_letter].width = adjusted_width

        # Number formatting for amount columns
        for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
            for cell in row:
                if cell.column_letter and "₹" in str(ws.cell(row=1, column=cell.column).value or ""):
                    if cell.value and isinstance(cell.value, (int, float)):
                        cell.number_format = '#,##0.00'

    output.seek(0)
    return output


def commissions_to_csv(commissions: list) -> io.StringIO:
    """
    Export commissions data to CSV.

    Args:
        commissions: List of Commission model instances or dicts

    Returns:
        StringIO buffer containing the CSV data
    """
    columns = [
        "lead_id", "gross_commission", "tds_rate_pct", "tds_amount",
        "net_after_tds", "company_amount", "admin_amount",
        "employee_amount", "payout_status",
    ]

    data = []
    for comm in commissions:
        if hasattr(comm, "to_dict"):
            row = comm.to_dict()
        else:
            row = comm
        data.append({k: row.get(k) for k in columns})

    df = pd.DataFrame(data, columns=columns)

    header_map = {
        "lead_id": "Lead ID",
        "gross_commission": "Gross Commission (₹)",
        "tds_rate_pct": "TDS %",
        "tds_amount": "TDS Amount (₹)",
        "net_after_tds": "Net After TDS (₹)",
        "company_amount": "Company Share (₹)",
        "admin_amount": "Admin Share (₹)",
        "employee_amount": "Employee Share (₹)",
        "payout_status": "Payout Status",
    }
    df.rename(columns=header_map, inplace=True)

    output = io.StringIO()
    df.to_csv(output, index=False)
    output.seek(0)
    return output


def employees_to_xlsx(employees: list) -> io.BytesIO:
    """Export employee performance data to styled XLSX."""
    columns = [
        "employee_id", "full_name", "role", "mobile", "email",
        "is_active",
    ]

    data = []
    for emp in employees:
        if hasattr(emp, "to_dict"):
            row = emp.to_dict()
        else:
            row = emp
        data.append({k: row.get(k) for k in columns})

    df = pd.DataFrame(data, columns=columns)

    output = io.BytesIO()
    date_str = datetime.now().strftime("%Y-%m-%d")

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=f"Employees_{date_str}"[:31])

        ws = writer.sheets[list(writer.sheets.keys())[0]]
        from openpyxl.styles import Font, PatternFill, Alignment

        header_font = Font(bold=True, color="FFFFFF", size=11)
        header_fill = PatternFill(start_color="6C63FF", end_color="6C63FF", fill_type="solid")

        for cell in ws[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center")

        for column_cells in ws.columns:
            max_length = max(len(str(cell.value or "")) for cell in column_cells)
            ws.column_dimensions[column_cells[0].column_letter].width = min(max_length + 4, 50)

    output.seek(0)
    return output

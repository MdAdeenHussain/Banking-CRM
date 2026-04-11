import pandas as pd
from io import BytesIO, StringIO
from app.models.lead import Lead
from app.models.commission_tracker import CommissionTracker
from app.models.invoice import Invoice
from app.models.employee import Employee

class ExportService:
    """Export service for CSV and Excel"""
    
    @staticmethod
    def export_leads_to_csv(filters=None):
        """Export leads to CSV"""
        query = Lead.query
        
        if filters:
            if filters.get('status'):
                query = query.filter_by(status=filters['status'])
            if filters.get('bank'):
                query = query.filter_by(bank_financer=filters['bank'])
        
        leads = query.all()
        data = []
        
        for lead in leads:
            data.append({
                'Lead ID': lead.lead_id,
                'Customer Name': lead.customer_full_name,
                'Mobile': lead.mobile_number,
                'Email': lead.email,
                'City': lead.city,
                'Loan Type': lead.loan_type,
                'Loan Amount': lead.loan_amount_applied,
                'Bank': lead.bank_financer,
                'Status': lead.current_status.status if lead.current_status else 'New',
                'Created Date': lead.created_at.strftime('%Y-%m-%d')
            })
        
        df = pd.DataFrame(data)
        
        # Convert to CSV
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False)
        return csv_buffer.getvalue()
    
    @staticmethod
    def export_leads_to_excel(filters=None):
        """Export leads to Excel"""
        query = Lead.query
        
        if filters:
            if filters.get('status'):
                query = query.filter_by(status=filters['status'])
            if filters.get('bank'):
                query = query.filter_by(bank_financer=filters['bank'])
        
        leads = query.all()
        data = []
        
        for lead in leads:
            data.append({
                'Lead ID': lead.lead_id,
                'Customer Name': lead.customer_full_name,
                'Mobile': lead.mobile_number,
                'Email': lead.email,
                'City': lead.city,
                'Loan Type': lead.loan_type,
                'Loan Amount': lead.loan_amount_applied,
                'Bank': lead.bank_financer,
                'Status': lead.current_status.status if lead.current_status else 'New',
                'Created Date': lead.created_at
            })
        
        df = pd.DataFrame(data)
        
        # Convert to Excel bytes
        excel_buffer = BytesIO()
        df.to_excel(excel_buffer, index=False, sheet_name='Leads')
        excel_buffer.seek(0)
        return excel_buffer.getvalue()
    
    @staticmethod
    def export_commissions_to_csv():
        """Export commissions to CSV"""
        commissions = CommissionTracker.query.all()
        data = []
        
        for comm in commissions:
            data.append({
                'Lead ID': comm.lead.lead_id,
                'Customer': comm.lead.customer_full_name,
                'Gross Commission': comm.gross_commission,
                'Employee Share': comm.employee_share,
                'Admin Share': comm.admin_share,
                'Company Share': comm.company_share,
                'Net Payout': comm.net_payout,
                'Status': 'Pending' if comm.is_pending else 'Paid',
                'Payout Date': comm.payoff_date.strftime('%Y-%m-%d') if comm.payoff_date else 'N/A'
            })
        
        df = pd.DataFrame(data)
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False)
        return csv_buffer.getvalue()

    @staticmethod
    def export_employee_report(employee_id):
        """Export employee performance report"""
        employee = Employee.query.get(employee_id)
        if not employee:
            return None
        
        leads = Lead.query.filter_by(assigned_executive_id=employee_id).all()
        data = []
        
        for lead in leads:
            data.append({
                'Lead ID': lead.lead_id,
                'Customer': lead.customer_full_name,
                'Mobile': lead.mobile_number,
                'Loan Type': lead.loan_type,
                'Amount': lead.loan_amount_applied,
                'Status': lead.current_status.status if lead.current_status else 'New',
                'Created': lead.created_at.strftime('%Y-%m-%d')
            })
        
        df = pd.DataFrame(data)
        excel_buffer = BytesIO()
        df.to_excel(excel_buffer, index=False, sheet_name='Leads')
        
        # Add summary sheet
        summary_data = {
            'Metric': ['Total Leads', 'Converted Leads', 'Total Commission', 'Conversion Rate'],
            'Value': [
                employee.total_leads,
                employee.converted_leads,
                f"₹ {employee.total_commission:,.2f}",
                f"{(employee.converted_leads / employee.total_leads * 100):.2f}%" if employee.total_leads > 0 else "0%"
            ]
        }
        
        summary_df = pd.DataFrame(summary_data)
        
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Leads', index=False)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        excel_buffer.seek(0)
        return excel_buffer.getvalue()
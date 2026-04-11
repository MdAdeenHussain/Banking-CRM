"""Application constants and enums"""

# User Roles
USER_ROLES = {
    'super_admin': 'Super Administrator',
    'admin': 'Administrator',
    'manager': 'Manager',
    'employee': 'Employee',
    'dsa': 'DSA (Direct Selling Agent)',
    'client': 'Client',
}

ADMIN_ROLES = ['super_admin', 'admin']
DSA_ROLES = ['employee', 'dsa']

# Lead Status
LEAD_STATUS = {
    'new': 'New',
    'contacted': 'Contacted',
    'interested': 'Interested',
    'qualified': 'Qualified',
    'converted': 'Converted',
    'rejected': 'Rejected',
    'inactive': 'Inactive',
}

LEAD_STATUS_COLORS = {
    'new': '#007bff',           # Blue
    'contacted': '#17a2b8',     # Cyan
    'interested': '#ffc107',    # Yellow
    'qualified': '#20c997',     # Green
    'converted': '#28a745',     # Dark Green
    'rejected': '#dc3545',      # Red
    'inactive': '#6c757d',      # Gray
}

# Commission Status
COMMISSION_STATUS = {
    'pending': 'Pending',
    'processing': 'Processing',
    'approved': 'Approved',
    'paid': 'Paid',
    'rejected': 'Rejected',
    'disputed': 'Disputed',
}

COMMISSION_STATUS_COLORS = {
    'pending': '#ffc107',
    'processing': '#17a2b8',
    'approved': '#20c997',
    'paid': '#28a745',
    'rejected': '#dc3545',
    'disputed': '#ff6b6b',
}

# Document Types
DOCUMENT_TYPES = {
    'pdf': 'PDF Document',
    'docx': 'Word Document',
    'xlsx': 'Excel Sheet',
    'image': 'Image File',
    'txt': 'Text File',
    'other': 'Other',
}

FILE_SIZE_LIMITS = {
    'pdf': 50,      # MB
    'docx': 25,
    'xlsx': 25,
    'image': 10,
    'default': 10,
}

ALLOWED_FILE_EXTENSIONS = [
    'pdf', 'doc', 'docx', 'xlsx', 'xls', 'ppt', 'pptx',
    'jpg', 'jpeg', 'png', 'gif', 'bmp',
    'txt', 'csv', 'zip'
]

# Bank List
BANK_LIST = {
    'sbi': 'State Bank of India',
    'hdfc': 'HDFC Bank',
    'icici': 'ICICI Bank',
    'axis': 'Axis Bank',
    'kotak': 'Kotak Mahindra Bank',
    'yes': 'YES Bank',
    'federal': 'Federal Bank',
    'idbi': 'IDBI Bank',
    'bob': 'Bank of Baroda',
    'union': 'Union Bank of India',
    'other': 'Other Bank',
}

# Products
PRODUCTS = {
    'home_loan': 'Home Loan',
    'personal_loan': 'Personal Loan',
    'auto_loan': 'Auto Loan',
    'business_loan': 'Business Loan',
    'education_loan': 'Education Loan',
    'gold_loan': 'Gold Loan',
    'credit_card': 'Credit Card',
    'mortgage': 'Mortgage',
    'fixed_deposit': 'Fixed Deposit',
    'insurance': 'Insurance',
}

# DSA Status
DSA_STATUS = {
    'active': 'Active',
    'inactive': 'Inactive',
    'suspended': 'Suspended',
    'banned': 'Banned',
}

# Activity Types
ACTIVITY_TYPES = {
    'create': 'Create',
    'update': 'Update',
    'delete': 'Delete',
    'view': 'View',
    'download': 'Download',
    'export': 'Export',
    'login': 'Login',
    'logout': 'Logout',
    'approve': 'Approve',
    'reject': 'Reject',
    'assign': 'Assign',
}

# Lead Quality
LEAD_QUALITY = {
    'hot': 'Hot',
    'warm': 'Warm',
    'cold': 'Cold',
    'dead': 'Dead',
}

LEAD_QUALITY_COLORS = {
    'hot': '#dc3545',       # Red
    'warm': '#ffc107',      # Yellow
    'cold': '#17a2b8',      # Cyan
    'dead': '#6c757d',      # Gray
}

# Lead Sources
LEAD_SOURCES = {
    'website': 'Website',
    'phone_call': 'Phone Call',
    'email': 'Email',
    'referral': 'Referral',
    'advertising': 'Advertising',
    'social_media': 'Social Media',
    'event': 'Event',
    'other': 'Other',
}

# Notification Types
NOTIFICATION_TYPES = {
    'info': 'Information',
    'success': 'Success',
    'warning': 'Warning',
    'error': 'Error',
    'reminder': 'Reminder',
}

# Task Status
TASK_STATUS = {
    'pending': 'Pending',
    'in_progress': 'In Progress',
    'completed': 'Completed',
    'cancelled': 'Cancelled',
    'overdue': 'Overdue',
}

# Task Priority
TASK_PRIORITY = {
    'low': 'Low',
    'medium': 'Medium',
    'high': 'High',
    'urgent': 'Urgent',
}

TASK_PRIORITY_COLORS = {
    'low': '#28a745',       # Green
    'medium': '#ffc107',    # Yellow
    'high': '#ff6b6b',      # Orange-Red
    'urgent': '#dc3545',    # Red
}

# Report Types
REPORT_TYPES = {
    'lead_report': 'Lead Report',
    'commission_report': 'Commission Report',
    'employee_report': 'Employee Report',
    'performance_report': 'Performance Report',
    'bank_report': 'Bank Report',
    'activity_report': 'Activity Report',
}

# Pagination
DEFAULT_PAGE_SIZE = 20
PAGINATION_SIZES = [10, 20, 50, 100]

# Application Settings
APP_SETTINGS = {
    'app_name': 'Banking DSA CRM',
    'app_version': '1.0.0',
    'company_name': 'DSA Management System',
    'timezone': 'Asia/Kolkata',
    'date_format': '%d-%m-%Y',
    'time_format': '%H:%M:%S',
    'datetime_format': '%d-%m-%Y %H:%M:%S',
    'currency': 'INR',
    'currency_symbol': '₹',
}

# Email Settings
EMAIL_TEMPLATES = {
    'welcome': 'Welcome Email',
    'password_reset': 'Password Reset',
    'otp_verification': 'OTP Verification',
    'commission_notification': 'Commission Notification',
    'lead_assignment': 'Lead Assignment',
    'task_reminder': 'Task Reminder',
}

# Session Settings
SESSION_TIMEOUT_MINUTES = 30
REMEMBER_ME_DAYS = 30

# Rate Limiting
RATE_LIMIT_REQUESTS = 100
RATE_LIMIT_WINDOW_SECONDS = 3600  # 1 hour

# Password Policy
PASSWORD_MIN_LENGTH = 8
PASSWORD_EXPIRY_DAYS = 90
PASSWORD_HISTORY_COUNT = 5

"""Email Service for sending emails"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os


class EmailService:
    """Service for sending emails"""
    
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SENDER_EMAIL = os.getenv('SENDER_EMAIL', 'your-email@example.com')
    SENDER_PASSWORD = os.getenv('SENDER_PASSWORD', 'your-app-password')
    
    @staticmethod
    def send_email(recipient, subject, body, html=False, attachment=None):
        """Send email"""
        try:
            message = MIMEMultipart('alternative')
            message['Subject'] = subject
            message['From'] = EmailService.SENDER_EMAIL
            message['To'] = recipient
            
            # Add body
            if html:
                message.attach(MIMEText(body, 'html'))
            else:
                message.attach(MIMEText(body, 'plain'))
            
            # Add attachment if provided
            if attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment)
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename= invoice.pdf')
                message.attach(part)
            
            # Send email
            with smtplib.SMTP(EmailService.SMTP_SERVER, EmailService.SMTP_PORT) as server:
                server.starttls()
                server.login(EmailService.SENDER_EMAIL, EmailService.SENDER_PASSWORD)
                server.send_message(message)
            
            return True
        
        except Exception as e:
            print(f"Email send failed: {str(e)}")
            return False
    
    @staticmethod
    def send_otp_email(recipient_email, otp_code):
        """Send OTP email"""
        subject = "Your OTP Code"
        body = f"""
        Your OTP Code: {otp_code}
        
        This code will expire in 10 minutes.
        Do not share this code with anyone.
        
        If you did not request this code, please ignore this email.
        """
        
        return EmailService.send_email(recipient_email, subject, body)
    
    @staticmethod
    def send_password_reset_email(recipient_email, reset_link):
        """Send password reset email"""
        subject = "Password Reset Request"
        body = f"""
        Click the link below to reset your password:
        {reset_link}
        
        This link will expire in 24 hours.
        
        If you did not request this, please ignore this email.
        """
        
        return EmailService.send_email(recipient_email, subject, body)
    
    @staticmethod
    def send_welcome_email(recipient_email, full_name):
        """Send welcome email"""
        subject = "Welcome to CRM System"
        body = f"""
        Welcome {full_name},
        
        Your account has been created successfully.
        Please log in with your credentials.
        
        If you have any issues, please contact support.
        """
        
        return EmailService.send_email(recipient_email, subject, body)
    
    @staticmethod
    def send_invoice_email(recipient, invoice, pdf_attachment=None):
        """Send invoice via email"""
        subject = f"Invoice {invoice.invoice_number}"
        body = f"""
        Dear Customer,
        
        Please find attached your invoice #{invoice.invoice_number}
        
        Amount: {invoice.total_amount}
        Due Date: {invoice.created_at}
        
        Thank you for your business.
        """
        
        return EmailService.send_email(recipient, subject, body, attachment=pdf_attachment)
    
    @staticmethod
    def send_task_assignment_email(recipient_email, task_title):
        """Send task assignment email"""
        subject = "New Task Assigned"
        body = f"""
        A new task has been assigned to you:
        
        Task: {task_title}
        
        Please log in to view the full details.
        """
        
        return EmailService.send_email(recipient_email, subject, body)

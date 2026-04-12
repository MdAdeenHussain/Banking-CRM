"""LoanAxis CRM — Email Celery Tasks"""
from app.extensions import celery


@celery.task(name="tasks.send_otp_email")
def send_otp_email(user_email, otp):
    """Send OTP email asynchronously."""
    from flask import current_app
    try:
        from flask_mail import Message
        from app.extensions import mail
        msg = Message(subject="LoanAxis CRM — Your Login OTP", recipients=[user_email],
                      body=f"Your one-time code is: {otp}\n\nExpires in 10 minutes.")
        mail.send(msg)
    except Exception as e:
        current_app.logger.error(f"Failed to send OTP: {e}")


@celery.task(name="tasks.send_reset_email")
def send_reset_email(user_email, reset_url):
    """Send password reset email asynchronously."""
    from flask import current_app
    try:
        from flask_mail import Message
        from app.extensions import mail
        msg = Message(subject="LoanAxis CRM — Password Reset", recipients=[user_email],
                      body=f"Reset your password:\n\n{reset_url}\n\nExpires in 1 hour.")
        mail.send(msg)
    except Exception as e:
        current_app.logger.error(f"Failed to send reset email: {e}")

"""
LoanAxis CRM — Auth Forms

WTForms for login, registration, OTP verification, and password reset.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional


class LoginForm(FlaskForm):
    """Login form with email and password."""
    email = StringField("Email", validators=[
        DataRequired(message="Email is required"),
        Email(message="Invalid email address"),
    ])
    password = PasswordField("Password", validators=[
        DataRequired(message="Password is required"),
    ])
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Sign In")


class RegisterForm(FlaskForm):
    """Registration form for the first user (Super Admin)."""
    full_name = StringField("Full Name", validators=[
        DataRequired(message="Full name is required"),
        Length(min=2, max=150),
    ])
    email = StringField("Email", validators=[
        DataRequired(message="Email is required"),
        Email(message="Invalid email address"),
    ])
    mobile = StringField("Mobile", validators=[
        DataRequired(message="Mobile number is required"),
        Length(min=10, max=15),
    ])
    password = PasswordField("Password", validators=[
        DataRequired(message="Password is required"),
        Length(min=8, message="Password must be at least 8 characters"),
    ])
    confirm_password = PasswordField("Confirm Password", validators=[
        DataRequired(message="Please confirm your password"),
        EqualTo("password", message="Passwords must match"),
    ])
    submit = SubmitField("Create Account")


class OTPForm(FlaskForm):
    """6-digit OTP verification form."""
    otp = StringField("OTP Code", validators=[
        DataRequired(message="OTP is required"),
        Length(min=6, max=6, message="OTP must be 6 digits"),
    ])
    submit = SubmitField("Verify OTP")


class ForgotPasswordForm(FlaskForm):
    """Request password reset link."""
    email = StringField("Email", validators=[
        DataRequired(message="Email is required"),
        Email(message="Invalid email address"),
    ])
    submit = SubmitField("Send Reset Link")


class ResetPasswordForm(FlaskForm):
    """Set new password form."""
    password = PasswordField("New Password", validators=[
        DataRequired(message="Password is required"),
        Length(min=8, message="Password must be at least 8 characters"),
    ])
    confirm_password = PasswordField("Confirm New Password", validators=[
        DataRequired(message="Please confirm your password"),
        EqualTo("password", message="Passwords must match"),
    ])
    submit = SubmitField("Reset Password")

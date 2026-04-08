"""Authentication and registration form definitions."""

# =====================================
# SECTION: Imports
# =====================================
from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, SelectField, StringField
from wtforms.validators import DataRequired, Length, Optional


# =====================================
# SECTION: Form Definitions
# =====================================
class LoginForm(FlaskForm):
    """Login form placeholder for session authentication."""

    tenant_slug = StringField("Tenant Slug", validators=[DataRequired(), Length(min=2, max=120)])
    email = StringField("Email", validators=[DataRequired(), Length(max=255)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6, max=128)])
    remember_me = BooleanField("Remember Me")


class TenantRegistrationForm(FlaskForm):
    """Tenant onboarding form."""

    company_name = StringField("Company Name", validators=[DataRequired(), Length(min=2, max=150)])
    slug = StringField("Slug", validators=[DataRequired(), Length(min=2, max=120)])
    admin_name = StringField("Admin Name", validators=[Optional(), Length(max=150)])
    admin_email = StringField("Admin Email", validators=[DataRequired(), Length(max=255)])
    admin_phone = StringField("Admin Phone", validators=[Optional(), Length(max=20)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6, max=128)])


class UserRegistrationForm(FlaskForm):
    """Tenant user registration form."""

    name = StringField("Name", validators=[DataRequired(), Length(min=2, max=150)])
    email = StringField("Email", validators=[DataRequired(), Length(max=255)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6, max=128)])
    role = SelectField(
        "Role",
        choices=[
            ("owner", "Owner"),
            ("branch", "Branch"),
            ("agent", "Agent"),
            ("platform", "Platform"),
        ],
        validators=[DataRequired()],
    )
    phone = StringField("Phone", validators=[Optional(), Length(max=20)])
    tenant_slug = StringField("Tenant Slug", validators=[Optional(), Length(max=120)])

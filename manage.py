"""
LoanAxis CRM — Management CLI Commands

Usage:
    flask seed-demo          # Seed demo data
    flask create-superadmin  # Create a super admin user interactively
    flask reset-db           # Drop and recreate all tables (DEV ONLY)
"""

import click
from flask.cli import with_appcontext

from app import create_app
from app.extensions import db

app = create_app()


@app.cli.command("seed-demo")
@with_appcontext
def seed_demo():
    """Seed the database with demo data for development."""
    from app.models.branch import Branch
    from app.models.bank_partner import BankPartner

    click.echo("🌱 Seeding demo data...")

    # Create demo branches
    branches = [
        Branch(name="Mumbai HQ", city="Mumbai", state="Maharashtra",
               address="Andheri West, Mumbai 400058", is_active=True),
        Branch(name="Delhi NCR", city="New Delhi", state="Delhi",
               address="Connaught Place, New Delhi 110001", is_active=True),
        Branch(name="Bangalore South", city="Bangalore", state="Karnataka",
               address="Koramangala, Bangalore 560034", is_active=True),
    ]
    for branch in branches:
        existing = Branch.query.filter_by(name=branch.name).first()
        if not existing:
            db.session.add(branch)
            click.echo(f"  ✅ Branch: {branch.name}")

    # Create demo bank partners
    banks = [
        BankPartner(name="HDFC Bank", type="Bank",
                    contact_person="Relationship Desk",
                    commission_rate_default_pct=0.50, is_active=True),
        BankPartner(name="ICICI Bank", type="Bank",
                    contact_person="Channel Partner Desk",
                    commission_rate_default_pct=0.45, is_active=True),
        BankPartner(name="SBI", type="Bank",
                    contact_person="DSA Cell",
                    commission_rate_default_pct=0.40, is_active=True),
        BankPartner(name="Axis Bank", type="Bank",
                    contact_person="Partner Relations",
                    commission_rate_default_pct=0.55, is_active=True),
        BankPartner(name="Bajaj Finserv", type="NBFC",
                    contact_person="DSA Support",
                    commission_rate_default_pct=0.75, is_active=True),
        BankPartner(name="Tata Capital", type="NBFC",
                    contact_person="Partner Desk",
                    commission_rate_default_pct=0.65, is_active=True),
    ]
    for bank in banks:
        existing = BankPartner.query.filter_by(name=bank.name).first()
        if not existing:
            db.session.add(bank)
            click.echo(f"  ✅ Bank Partner: {bank.name}")

    db.session.commit()
    click.echo("✅ Demo data seeded successfully!")


@app.cli.command("create-superadmin")
@with_appcontext
def create_superadmin():
    """Create a super admin user interactively."""
    from app.models.user import User

    click.echo("🔐 Create Super Admin Account")
    click.echo("─" * 40)

    full_name = click.prompt("Full Name")
    email = click.prompt("Email")
    mobile = click.prompt("Mobile")
    password = click.prompt("Password", hide_input=True, confirmation_prompt=True)

    existing = User.query.filter_by(email=email).first()
    if existing:
        click.echo(f"❌ User with email {email} already exists!")
        return

    user = User(
        full_name=full_name,
        email=email,
        mobile=mobile,
        role="super_admin",
        is_active=True,
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    click.echo(f"✅ Super Admin created: {full_name} ({email})")
    click.echo(f"   Employee ID: {user.employee_id}")


@app.cli.command("reset-db")
@with_appcontext
def reset_db():
    """Drop and recreate all tables. DEVELOPMENT ONLY."""
    if not click.confirm("⚠️  This will DELETE ALL DATA. Continue?"):
        return
    click.echo("🗑️  Dropping all tables...")
    db.drop_all()
    click.echo("🔨 Creating all tables...")
    db.create_all()
    click.echo("✅ Database reset complete.")


if __name__ == "__main__":
    app.run(debug=True)

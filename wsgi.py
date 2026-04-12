"""
LoanAxis CRM — WSGI Entry Point

Used by Gunicorn in production:
    gunicorn wsgi:app --workers 4 --bind 0.0.0.0:8000
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run()

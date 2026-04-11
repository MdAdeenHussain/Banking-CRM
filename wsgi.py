"""
WSGI Configuration for Production Deployment
Used by Gunicorn, uWSGI, or other WSGI servers
"""

import os
from app import create_app
from app.models.user import db

# Create Flask application instance
app = create_app(os.getenv('FLASK_ENV', 'production'))

# Initialize database
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run()

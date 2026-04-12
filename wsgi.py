"""
WSGI Configuration for Production Deployment
Used by Gunicorn, uWSGI, or other WSGI servers
"""

import os
from app import create_app

# Create Flask application instance
app = create_app(os.getenv('FLASK_ENV', 'production'))

if __name__ == '__main__':
    app.run()

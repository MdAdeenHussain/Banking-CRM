"""
run.py
WSGI entry point for the Flask application.
This file starts the Flask development server or Gunicorn production server.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

from app import create_app

# Create Flask app
app = create_app()

if __name__ == "__main__":
    # Development server
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_ENV") == "development"
    
    app.run(
        host="0.0.0.0",
        port=port,
        debug=debug,
        use_reloader=debug,
    )

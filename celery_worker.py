"""
LoanAxis CRM — Celery Worker Entry Point

Start the worker:
    celery -A celery_worker.celery worker --loglevel=info

Start the beat scheduler:
    celery -A celery_worker.celery beat --loglevel=info

Combined (dev only):
    celery -A celery_worker.celery worker --beat --loglevel=info
"""

from app import create_app
from app.extensions import celery

# Create the Flask app context so Celery tasks can access Flask extensions
flask_app = create_app()

# Push the app context so celery tasks run within it
celery.conf.update(flask_app.config)


class FlaskTask(celery.Task):
    """Ensure every Celery task runs inside the Flask app context."""

    def __call__(self, *args, **kwargs):
        with flask_app.app_context():
            return self.run(*args, **kwargs)


celery.Task = FlaskTask

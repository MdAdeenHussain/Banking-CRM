# Phase 1 production-ready Flask container skeleton
FROM python:3.11-slim

# Prevent Python from buffering logs and writing .pyc files.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependency manifest first for Docker layer caching.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project source.
COPY . .

# Expose Flask/Gunicorn port.
EXPOSE 5000

# Default command uses Gunicorn for production-like runtime.
CMD ["gunicorn", "-b", "0.0.0.0:5000", "run:app"]

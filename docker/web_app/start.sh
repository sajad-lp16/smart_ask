#!/bin/bash

# Create static directory if it doesn't exist
mkdir -p /app/static

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate

# Start server with Gunicorn and Uvicorn workers
echo "Starting server..."
gunicorn web_app.fastapi_app:app \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --reload \
    --access-logfile - \
    --error-logfile - \
    --log-level info

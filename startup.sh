#!/bin/bash

# Azure App Service startup script for Django application

echo "Starting Django application..."

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput

# Run database migrations
python manage.py migrate

# Start Gunicorn server
gunicorn --bind=0.0.0.0:8000 --workers=4 --timeout=600 shop.wsgi:application

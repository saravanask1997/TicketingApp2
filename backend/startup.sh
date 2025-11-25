#!/bin/bash

# Apply database migrations
python manage.py migrate

# Start Gunicorn
gunicorn --bind=0.0.0.0 --workers=4 ticketing_system.wsgi

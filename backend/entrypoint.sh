#!/bin/sh
set -e

echo "=================================================="
echo "===> Django check..."
python manage.py check

echo "===> Running migrations..."
python manage.py migrate --noinput

echo "===> Collecting static files..."
python manage.py collectstatic --noinput

echo "===> Starting Gunicorn..."
exec gunicorn contract_management_BE.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers "${GUNICORN_WORKERS:-3}" \
    --timeout "${GUNICORN_TIMEOUT:-120}" \
    --access-logfile - \
    --error-logfile -

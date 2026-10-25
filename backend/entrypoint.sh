#!/bin/sh
set -e

echo "=================================================="
echo "===> Django check..."
python manage.py check

echo "===> Running migrations..."
python manage.py migrate --noinput

echo "===> Ensuring roles and permissions..."
python manage.py seed_roles

echo "===> Collecting static files..."
python manage.py collectstatic --noinput

# Optionally bootstrap a super admin from environment variables.
# Set DJANGO_SUPERUSER_USERNAME / DJANGO_SUPERUSER_EMAIL /
# DJANGO_SUPERUSER_PASSWORD to enable this (all three required).
if [ -n "${DJANGO_SUPERUSER_USERNAME:-}" ] && [ -n "${DJANGO_SUPERUSER_PASSWORD:-}" ]; then
    echo "===> Ensuring super admin '${DJANGO_SUPERUSER_USERNAME}'..."
    python manage.py create_superadmin --noinput || \
        echo "WARNING: super admin bootstrap skipped/failed (non-fatal)"
fi

echo "===> Starting Gunicorn..."
exec gunicorn contract_management_BE.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers "${GUNICORN_WORKERS:-3}" \
    --timeout "${GUNICORN_TIMEOUT:-120}" \
    --access-logfile - \
    --error-logfile -

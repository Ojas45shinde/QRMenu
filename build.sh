#!/usr/bin/env bash
set -o errexit

echo "==> Installing dependencies..."
pip install -r requirements.txt

echo "==> Collecting static files..."
python manage.py collectstatic --noinput

echo "==> Running migrations..."
python manage.py migrate

echo "==> Creating superuser (if DJANGO_ADMIN_PASSWORD is set)..."
python manage.py create_admin

echo "==> Build complete!"

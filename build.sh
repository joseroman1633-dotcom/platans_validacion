#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python scripts/ensure_jazzmin_sourcemaps.py
python manage.py collectstatic --noinput
python manage.py migrate --noinput
python manage.py createsuperuser --noinput || true
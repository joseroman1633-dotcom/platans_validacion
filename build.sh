#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python scripts/ensure_jazzmin_sourcemaps.py
python manage.py collectstatic --noinput
python manage.py migrate --noinput

python manage.py shell -c "from django.contrib.auth import get_user_model; import os; U=get_user_model(); username=os.environ['DJANGO_SUPERUSER_USERNAME']; email=os.environ.get('DJANGO_SUPERUSER_EMAIL',''); password=os.environ['DJANGO_SUPERUSER_PASSWORD']; user, created = U.objects.get_or_create(username=username, defaults={'email': email, 'is_staff': True, 'is_superuser': True}); user.email=email; user.is_staff=True; user.is_superuser=True; user.set_password(password); user.save(); print(f'Superuser listo: {username}')"
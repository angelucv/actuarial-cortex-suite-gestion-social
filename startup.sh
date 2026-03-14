#!/bin/sh
# Arranque para Hugging Face: migrar, superusuario, datos demo, GeoJSON, luego Gunicorn.
# Salida de arranque silenciada para no saturar los logs del Space.
set -e
python manage.py migrate --noinput >/dev/null 2>&1

python manage.py shell -c "
import os
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin'))
" >/dev/null 2>&1 || true

python manage.py cargar_datos_demo --clear --cantidad 350 >/dev/null 2>&1 || true
python manage.py descargar_geojson_venezuela >/dev/null 2>&1 || true

exec gunicorn --bind 0.0.0.0:7860 --workers 1 --threads 2 config.wsgi:application

#!/bin/sh
# Arranque para Hugging Face: migrar, crear superusuario por defecto, cargar datos demo y GeoJSON, luego Gunicorn.
set -e
python manage.py migrate --noinput

# Crear superusuario si no existe (usuario: admin, contraseña: env DJANGO_SUPERUSER_PASSWORD o "admin")
python manage.py shell -c "
import os
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin'))
" 2>/dev/null || true

# Cargar datos demo y polígonos de estados (si no hay datos o no hay GeoJSON)
python manage.py cargar_datos_demo --clear --cantidad 350 2>/dev/null || true
python manage.py descargar_geojson_venezuela 2>/dev/null || true

exec gunicorn --bind 0.0.0.0:7860 --workers 1 --threads 2 config.wsgi:application

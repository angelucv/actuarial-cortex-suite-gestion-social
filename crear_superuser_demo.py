"""
Script para crear un superusuario de demostración (solo uso local).
Ejecutar: python crear_superuser_demo.py
Usuario: admin / Contraseña: admin (cambiar en producción).
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@ejemplo.local', 'admin')
    print('Superusuario creado: usuario=admin, contraseña=admin')
else:
    print('El usuario "admin" ya existe.')

# Gestión Social — Actuarial Cortex (Django)
# Para Hugging Face Spaces: puerto 7860, bind 0.0.0.0
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=config.settings

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN python manage.py collectstatic --noinput 2>/dev/null || true
RUN python manage.py migrate --noinput

# Hugging Face Spaces expone el puerto 7860. Arranque: superusuario + datos demo + GeoJSON.
EXPOSE 7860
CMD ["sh", "startup.sh"]

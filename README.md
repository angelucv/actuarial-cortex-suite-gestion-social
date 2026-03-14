---
title: Gestión Social — Actuarial Cortex
sdk: docker
app_port: 7860
---

# Gestión Social — Actuarial Cortex (Django)

Aplicativo **Django** con base de datos real y **Django Admin**: carga de datos (import CSV/Excel), listado de casos con filtros, scoring de prioridad y tablero gerencial (KPIs, mapa por estados, vision historica).

**Sitio web:** [Actuarial Cortex](https://actuarial-cortex.pages.dev/) — Hub de conocimiento y tecnologia actuarial. Este aplicativo forma parte de Cortex Suite.

## Rutas

- **`/admin/`** — Iniciar sesión, cargar datos (import/export), listado de solicitudes, filtros, recalcular scoring.
- **`/dashboard/`** — Tablero con KPIs y gráficos (Pareto, estatus, proveedores).

## Como desplegar (Hugging Face Spaces)

1. Crea un **Space** en [huggingface.co/spaces](https://huggingface.co/spaces).
2. Elige **Docker** como SDK.
3. Conecta el repositorio de GitHub de la plataforma Cortex.
4. En **Space settings** → **Space hardware** → **Space directory**: indica la carpeta de este proyecto, por ejemplo `gestion-social-django` (si el repo es `actuarial-cortex-site`, la ruta sería la subcarpeta donde está este `Dockerfile`).
5. El Space construirá la imagen con `Dockerfile` y ejecutará Gunicorn en el puerto **7860**.

## Logos y datos de demostración

- **Logos (Admin y dashboard):** desde la raíz del proyecto ejecute `python copy_logos.py` para copiar los PNG desde `../logo-AC/` a `static/logo/`.
- **Datos simulados:** `python manage.py cargar_datos_demo` (por defecto 150 registros; use `--cantidad 200` para más).

## Como ejecutar en local

```bash
cd gestion-social-django
pip install -r requirements.txt
python manage.py migrate
python copy_logos.py
python manage.py createsuperuser
python manage.py cargar_datos_demo
python manage.py runserver
```

Para producción local con Gunicorn (puerto 7860 como en HF):

```bash
gunicorn --bind 0.0.0.0:7860 config.wsgi:application
```

## Variables de entorno (opcional)

- `DJANGO_SECRET_KEY` — Clave secreta (producción).
- `DJANGO_DEBUG` — `False` en producción.
- `DJANGO_ALLOWED_HOSTS` — Hosts permitidos, separados por coma.

---

[Actuarial Cortex](https://actuarial-cortex.pages.dev/) — Hub de conocimiento y tecnología actuarial.

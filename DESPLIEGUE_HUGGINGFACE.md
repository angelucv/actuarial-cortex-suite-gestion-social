# Despliegue en Hugging Face Spaces — Paso a paso

Sigue estos pasos para subir el proyecto al repositorio de Actuarial Cortex y desplegarlo en Hugging Face.

---

## Paso 1: Preparar el repositorio (Git)

Si el código está en tu máquina pero **no** está en un repo de “actuarial cortex”:

### Opción A — Repositorio nuevo en GitHub (actuarial-cortex)

1. Crea un repositorio en GitHub (por ejemplo `actuarial-cortex` o `actuarial-cortex-site`).
2. En la terminal, entra a la carpeta del proyecto Django:

   ```bash
   cd C:\Users\Angel\actuarial-cortex-site\gestion-social-django
   ```

3. Inicializa Git (si no hay `.git`):

   ```bash
   git init
   ```

4. Añade el remote de GitHub (cambia `TU_USUARIO` y `actuarial-cortex` por tu repo):

   ```bash
   git remote add origin https://github.com/TU_USUARIO/actuarial-cortex.git
   ```

5. Añade todo, haz commit y sube:

   ```bash
   git add .
   git status
   git commit -m "Gestión Social Django: dashboard, mapa por estados, visión histórica"
   git branch -M main
   git push -u origin main
   ```

### Opción B — El repo ya existe (actuarial-cortex-site u otro)

1. Entra a la carpeta **raíz del repositorio** (donde está el `.git`), por ejemplo:

   ```bash
   cd C:\Users\Angel\actuarial-cortex-site
   ```

2. Comprueba el estado y sube los cambios:

   ```bash
   git status
   git add .
   git commit -m "Actualizar Gestión Social: mapa por estados, datos demo desiguales, despliegue HF"
   git push origin main
   ```

Si el proyecto Django está en una subcarpeta (ej. `gestion-social-django`), el push sube toda la repo; en el Paso 3 indicarás esa carpeta en Hugging Face.

---

## Paso 2: Crear el Space en Hugging Face

1. Entra en [huggingface.co/spaces](https://huggingface.co/spaces) e inicia sesión.
2. Pulsa **“Create new Space”**.
3. Rellena:
   - **Name:** por ejemplo `gestion-social` o `actuarial-cortex-gestion`.
   - **License:** el que prefieras (ej. MIT).
   - **SDK:** elige **Docker**.
   - **Visibility:** Public (o Private si lo quieres oculto).
4. Pulsa **“Create Space”**. Se creará un repo vacío en `https://huggingface.co/spaces/TU_USUARIO/gestion-social`.

---

## Paso 3: Subir el código al Space

Tienes dos formas: **solo la carpeta Django** como raíz del Space, o **todo el repo** y decirle a HF qué carpeta usar.

### Opción 1 — Space = solo esta carpeta (recomendado)

El Space usará solo el contenido de `gestion-social-django` (Dockerfile, `manage.py`, etc.) como raíz.

1. En tu PC, entra a la carpeta del proyecto Django:

   ```bash
   cd C:\Users\Angel\actuarial-cortex-site\gestion-social-django
   ```

2. Añade el remote del Space (sustituye `TU_USUARIO` y `gestion-social` por tu Space):

   ```bash
   git remote add hf https://huggingface.co/spaces/TU_USUARIO/gestion-social
   ```

   Si ya tenías `git init` aquí, haz commit (si hay cambios) y push:

   ```bash
   git add .
   git commit -m "Deploy Gestión Social to Hugging Face"
   git push hf main
   ```

   Si esta carpeta **no** es un repo Git:

   ```bash
   git init
   git add .
   git commit -m "Gestión Social — deploy HF"
   git remote add hf https://huggingface.co/spaces/TU_USUARIO/gestion-social
   git push hf main
   ```

3. Hugging Face construirá la imagen con el **Dockerfile** y arrancará la app en el puerto **7860**.

### Opción 2 — Repo completo en GitHub y HF clona ese repo

1. En **Settings** del Space → **Repository** (o al crear), conecta el Space a tu repo de GitHub (si HF lo ofrece).
2. En **Settings** del Space → **Space configuration** (o “Space directory” / “Root directory”), pon la **subcarpeta** donde está el Django, por ejemplo: `gestion-social-django`.
3. Guarda. HF usará esa carpeta como raíz para el Dockerfile.

Si en vez de GitHub subes por Git a HF directamente, clona el Space, copia dentro la carpeta `gestion-social-django` (solo su contenido como raíz del repo del Space), haz commit y push al Space.

---

## Paso 4: Variables de entorno (opcional)

En el Space: **Settings** → **Variables and secrets**:

- `DJANGO_SECRET_KEY`: una clave segura en producción.
- `DJANGO_DEBUG`: `False` en producción.
- `DJANGO_ALLOWED_HOSTS`: `*.hf.space` o el dominio que te den.

No es obligatorio para una demo; el `Dockerfile` y `config.settings` ya están preparados.

---

## Paso 5: Primera ejecución y datos de demo

1. Tras el **build**, el Space abrirá la app. La URL será algo como:
   `https://TU_USUARIO-gestion-social.hf.space`
2. Entra a **`/admin/`**, inicia sesión con el superusuario.  
   Si no existe, hay que crearlo en build time (ver más abajo) o usar un comando que cree superusuario y cargue datos al arrancar.
3. Para tener datos de demo sin tocar el Admin, puedes ejecutar en el contenedor (o en un script de arranque):
   - `python manage.py cargar_datos_demo --clear`
   - `python manage.py descargar_geojson_venezuela`

Si quieres, en el **Dockerfile** se puede añadir un script de arranque que cree superusuario por defecto y cargue datos demo la primera vez.

---

## Resumen de comandos (copiar/pegar)

Ajusta `TU_USUARIO` y el nombre del Space.

```bash
cd C:\Users\Angel\actuarial-cortex-site\gestion-social-django
git init
git add .
git commit -m "Deploy Gestión Social a Hugging Face"
git remote add hf https://huggingface.co/spaces/TU_USUARIO/gestion-social
git push hf main
```

Después, en Hugging Face:

- Crear el Space con **SDK: Docker**.
- Si usas “Create with repo”, el push anterior ya habrá subido el código; si no, repite el `git remote add hf` y `git push hf main` desde esta carpeta.

---

## Rutas de la aplicación

- **`/`** o **`/admin/`** — Admin (login, carga de datos, listados).
- **`/dashboard/`** — Tablero (KPIs, gráficos, mapa por estados, visión histórica).

El `README.md` del proyecto ya incluye el bloque YAML (`title`, `sdk: docker`, `app_port: 7860`) que Hugging Face necesita para el Space Docker.

# Subir a GitHub (CVEA / Actuarial Cortex) y desplegar en Hugging Face

Flujo: **primero** cargar el proyecto en tu repositorio de GitHub (como parte de CVEA / Actuarial Cortex) y **después** hacer que Hugging Face use ese repo para desplegar el Space.

---

## Resumen del flujo

1. **GitHub** = origen del código (repo CVEA / actuarial cortex).
2. **Hugging Face Space** = despliegue: se sincroniza con GitHub (manual la primera vez; luego con GitHub Actions).
3. Cada **push a `main`** en GitHub puede actualizar automáticamente el Space.

---

## Paso 1: Tener el código en GitHub

Puedes hacerlo de dos maneras.

### Opción A — Dentro del repo `cvea-platform` (o el repo “CVEA cortex” que uses)

Si quieres que Gestión Social viva **dentro** del mismo repo que ya usas (por ejemplo `cvea-platform`):

1. Copia la carpeta del proyecto Django dentro del repo, por ejemplo:
   - `cvea-platform/actuarial-cortex/gestion-social-django/`  
   o
   - `cvea-platform/gestion-social-django/`

2. Desde la raíz del repo (donde está el `.git`):

   ```bash
   cd C:\Users\Angel\cvea-platform
   git add actuarial-cortex/gestion-social-django
   # o:  git add gestion-social-django
   git status
   git commit -m "Añadir Gestión Social (Django) para despliegue en Hugging Face"
   git push origin main
   ```

3. Más adelante, en Hugging Face, tendrás que indicar la **carpeta** donde está el Dockerfile (Paso 4).

### Opción B — Repo nuevo solo para Gestión Social

Si prefieres un repo **solo** para esta app (por ejemplo `actuarial-cortex` o `cvea-cortex-gestion-social`):

1. Crea un repo nuevo en GitHub (vacío, con o sin README).
2. En la carpeta del proyecto Django:

   ```bash
   cd C:\Users\Angel\actuarial-cortex-site\gestion-social-django
   git init
   git add .
   git commit -m "Gestión Social Django — CVEA / Actuarial Cortex"
   git remote add origin https://github.com/TU_USUARIO/actuarial-cortex.git
   git branch -M main
   git push -u origin main
   ```

3. En Hugging Face no hará falta indicar subcarpeta: la raíz del Space será la raíz del repo.

---

## Paso 2: Crear el Space en Hugging Face

1. Entra en [huggingface.co/spaces](https://huggingface.co/spaces) e inicia sesión.
2. **Create new Space**.
3. Configuración:
   - **Name:** por ejemplo `gestion-social` o `actuarial-cortex-gestion`.
   - **SDK:** **Docker**.
   - **Visibility:** Public (o Private).
4. Crear el Space. Quedará vacío; en el siguiente paso lo llenarás desde GitHub.

---

## Paso 3: Primera sincronización (GitHub → Hugging Face)

Hugging Face no “conecta” el Space a GitHub como un enlace en vivo: tú subes el contenido del repo al Space (por Git). La primera vez lo haces a mano; luego puedes automatizarlo con GitHub Actions.

Desde la **raíz del repositorio que subiste a GitHub** (el que contiene el código de Gestión Social):

```bash
# Si usaste Opción A (app dentro de cvea-platform):
cd C:\Users\Angel\cvea-platform

# Si usaste Opción B (repo solo Django):
cd C:\Users\Angel\actuarial-cortex-site\gestion-social-django
```

Añade el Space como remote y envía el contenido (sustituye `TU_USUARIO_HF` y `gestion-social` por tu usuario y nombre del Space):

```bash
git remote add hf https://huggingface.co/spaces/TU_USUARIO_HF/gestion-social
git push --force hf main
```

Si el remote `hf` ya existe: `git remote remove hf` y vuelve a añadirlo, o usa `git push --force hf main` directamente.

Con esto, el Space ya tiene el código. Si el repo es solo la app (Opción B), el build debería arrancar solo. Si el repo es grande y la app está en una subcarpeta (Opción A), sigue el Paso 4.

---

## Paso 4: Indicar la carpeta del proyecto (solo Opción A)

Si el Dockerfile está en una **subcarpeta** (por ejemplo `gestion-social-django` o `actuarial-cortex/gestion-social-django`):

1. En Hugging Face, abre tu Space.
2. **Settings** (engranaje).
3. Busca **“Space directory”** / **“Root directory”** / **“Working directory”**.
4. Escribe la ruta desde la raíz del repo hasta la carpeta donde está el `Dockerfile`, por ejemplo:
   - `gestion-social-django`
   - o `actuarial-cortex/gestion-social-django`
5. Guardar. El Space reconstruirá usando esa carpeta como raíz.

---

## Paso 5: Automatizar con GitHub Actions (cada push a `main`)

Para que cada vez que hagas **push a `main`** en GitHub se actualice el Space en Hugging Face:

1. **Token de Hugging Face**  
   En [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens), crea un token con permiso **Write** (para poder hacer push al Space).

2. **Secret en GitHub**  
   En el repo de GitHub: **Settings → Secrets and variables → Actions → New repository secret**  
   - Nombre: `HF_TOKEN`  
   - Valor: el token que creaste.

3. **Workflow en el repo**  
   En el mismo repo que subiste (cvea-platform o el repo solo Django), crea el fichero:

   - **Si la app está en una subcarpeta (Opción A):**  
     `cvea-platform/.github/workflows/sync-gestion-social-hf.yml`
   - **Si el repo es solo la app (Opción B):**  
     `actuarial-cortex/.github/workflows/sync-gestion-social-hf.yml`  
     (o la ruta equivalente en tu repo).

   Contenido del workflow (sustituye `TU_USUARIO_HF` y `gestion-social`):

   ```yaml
   name: Sync to Hugging Face Space
   on:
     push:
       branches: [main]
     workflow_dispatch:

   jobs:
     sync-to-hf:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
           with:
             fetch-depth: 0
             lfs: true
         - name: Push to Hugging Face Space
           env:
             HF_TOKEN: ${{ secrets.HF_TOKEN }}
           run: |
             git push https://TU_USUARIO_HF:$HF_TOKEN@huggingface.co/spaces/TU_USUARIO_HF/gestion-social main
   ```

4. Haz commit y push de este fichero a `main`. A partir de ahí, cada push a `main` sincronizará el Space.

---

## Resumen

| Paso | Dónde | Qué hacer |
|------|--------|-----------|
| 1 | GitHub | Subir el código (dentro de cvea-platform o en un repo nuevo). |
| 2 | Hugging Face | Crear Space con SDK Docker. |
| 3 | Local / Git | Añadir remote `hf` y `git push --force hf main` (primera vez). |
| 4 | Hugging Face | Si la app está en subcarpeta, poner **Space directory** en Settings. |
| 5 | GitHub | Añadir secret `HF_TOKEN` y workflow de sync; cada push a `main` actualiza el Space. |

Rutas útiles una vez desplegado:

- **Admin:** `https://TU_USUARIO_HF-gestion-social.hf.space/admin/` (usuario `admin`, contraseña por defecto `admin`).
- **Dashboard:** `https://TU_USUARIO_HF-gestion-social.hf.space/dashboard/`

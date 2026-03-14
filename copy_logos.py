"""
Copia los logos de Actuarial Cortex desde ../logo-AC/ a static/logo/
para que aparezcan en Admin y Dashboard. Ejecutar desde la raíz del proyecto Django.
"""
import shutil
from pathlib import Path

BASE = Path(__file__).resolve().parent
src = BASE.parent / "logo-AC"
dst = BASE / "static" / "logo"
dst.mkdir(parents=True, exist_ok=True)
if src.exists():
    for f in src.glob("*.png"):
        shutil.copy2(f, dst / f.name)
    print("Logos copiados a static/logo/")
else:
    print("No se encontró ../logo-AC/. Copie manualmente los PNG a static/logo/")

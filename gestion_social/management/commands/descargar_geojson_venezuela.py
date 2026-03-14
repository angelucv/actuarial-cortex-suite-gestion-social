"""
Descarga los polígonos reales de los estados de Venezuela (Natural Earth Admin 1)
y los guarda en static/geojson/venezuela_estados.geojson para que el mapa por estados
muestre las fronteras reales de cada estado, no recuadros aproximados.

Uso: python manage.py descargar_geojson_venezuela
"""
import json
import os
import urllib.request
from django.core.management.base import BaseCommand

# Natural Earth Admin 1 (states/provinces) - filtrar por Venezuela
NE_ADMIN1_URL = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_admin_1_states_provinces.geojson"


class Command(BaseCommand):
    help = 'Descarga polígonos reales de estados de Venezuela (Natural Earth) a static/geojson/venezuela_estados.geojson'

    def handle(self, *args, **options):
        out_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'static', 'geojson')
        out_path = os.path.join(out_dir, 'venezuela_estados.geojson')
        os.makedirs(out_dir, exist_ok=True)

        self.stdout.write('Descargando Natural Earth Admin 1...')
        try:
            with urllib.request.urlopen(NE_ADMIN1_URL, timeout=60) as resp:
                data = json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error al descargar: {e}'))
            return

        # Filtrar solo Venezuela (ADM0_A3 = VEN)
        features = []
        for f in data.get('features', []):
            props = f.get('properties') or {}
            if props.get('ADM0_A3') != 'VEN' and props.get('adm0_a3') != 'VEN':
                continue
            name = (props.get('NAME') or props.get('name') or '').strip()
            if not name:
                continue
            props['name'] = name.upper()
            f['properties'] = props
            features.append(f)

        out_geojson = {'type': 'FeatureCollection', 'features': features}
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(out_geojson, f, ensure_ascii=False, indent=0)

        self.stdout.write(self.style.SUCCESS(
            f'Guardados {len(features)} estados en {out_path}. Recargue el mapa por estados en el dashboard.'
        ))
        if len(features) < 20:
            self.stdout.write(self.style.WARNING(
                'Si los nombres no coinciden con sus datos, edite "name" en el GeoJSON o normalice en la vista.'
            ))

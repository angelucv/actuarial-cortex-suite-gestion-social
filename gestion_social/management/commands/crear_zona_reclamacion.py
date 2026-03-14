"""
Genera el archivo GeoJSON de la zona en reclamación (Guayana Esequiba) para el mapa por estados.
Si no tiene un límite oficial, este comando escribe un polígono de referencia (aproximado)
con más puntos que el usado por defecto en la aplicación.

Para la forma EXACTA: use el límite del IGVSB o convierta el mapa oficial a GeoJSON
y guárdelo como static/geojson/zona_reclamacion.geojson (este comando no lo sobrescribirá
si ya existe, a menos que use --overwrite).

Uso:
  python manage.py crear_zona_reclamacion
  python manage.py crear_zona_reclamacion --overwrite
"""
import json
import os
from django.core.management.base import BaseCommand

# Polígono de referencia Guayana Esequiba (~30 puntos), contorno del territorio reclamado.
COORDS_REFERENCIA = [
    [-60.10, 8.55], [-59.50, 8.20], [-59.00, 7.80], [-58.50, 7.30], [-58.40, 6.80],
    [-58.50, 6.30], [-58.60, 5.80], [-58.70, 5.30], [-58.55, 4.80], [-58.60, 4.30],
    [-58.40, 3.80], [-58.30, 3.30], [-58.20, 2.80], [-58.35, 2.30], [-58.60, 1.80],
    [-58.50, 1.40], [-59.00, 1.60], [-59.50, 1.90], [-60.00, 2.20], [-60.30, 2.80],
    [-60.00, 3.40], [-59.80, 3.90], [-60.20, 4.40], [-60.70, 5.00], [-61.00, 5.50],
    [-61.30, 6.10], [-61.00, 6.70], [-60.50, 7.30], [-60.10, 8.00], [-60.10, 8.55],
]


class Command(BaseCommand):
    help = 'Crea static/geojson/zona_reclamacion.geojson con un polígono de referencia para el mapa por estados'

    def add_arguments(self, parser):
        parser.add_argument('--overwrite', action='store_true', help='Sobrescribir el archivo si ya existe')

    def handle(self, *args, **options):
        out_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'static', 'geojson')
        out_path = os.path.join(out_dir, 'zona_reclamacion.geojson')
        os.makedirs(out_dir, exist_ok=True)

        if os.path.exists(out_path) and not options.get('overwrite'):
            self.stdout.write(self.style.WARNING(
                f'Ya existe {out_path}. Use --overwrite para reemplazarlo con el polígono de referencia.'
            ))
            return

        geojson = {
            'type': 'FeatureCollection',
            'features': [{
                'type': 'Feature',
                'properties': {'name': 'Guayana Esequiba (Zona en Reclamación)', 'nombre': 'Guayana Esequiba (Zona en Reclamación)'},
                'geometry': {'type': 'Polygon', 'coordinates': [COORDS_REFERENCIA]},
            }]
        }
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(geojson, f, ensure_ascii=False, indent=2)

        self.stdout.write(self.style.SUCCESS(
            f'Guardado {out_path}. Recargue el mapa por estados para ver la zona en gris.'
        ))
        self.stdout.write('Para la forma exacta oficial, sustituya este archivo por un GeoJSON del IGVSB o del mapa oficial.')

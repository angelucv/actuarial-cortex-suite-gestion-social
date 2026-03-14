Zona en reclamación (Guayana Esequiba) – Mapa por estado
========================================================

Para que el mapa por estados muestre la forma de la zona en reclamación en gris,
el archivo debe llamarse exactamente:

  zona_reclamacion.geojson

y estar en esta misma carpeta:
  gestion_social/static/geojson/zona_reclamacion.geojson


OPCIÓN 1 – Polígono de referencia (rápido)
-----------------------------------------
Ejecute en la raíz del proyecto:

  python manage.py crear_zona_reclamacion

Esto crea un GeoJSON con un polígono aproximado (más detallado que el usado
si no hay archivo). Si ya existe el archivo, no se sobrescribe; use
--overwrite para reemplazarlo.


OPCIÓN 2 – Forma exacta (límite oficial)
-----------------------------------------
Para usar el límite oficial venezolano de la zona en reclamación:

1) Obtener el límite oficial
   - IGVSB (Instituto Geográfico de Venezuela Simón Bolívar):
     https://igvsb.gob.ve/
     Mapas oficiales en PDF/vectorial; puede incluir el polígono de la zona.
   - Mapa oficial (ej. “Venezuela con Guayana Esequiba”):
     https://commons.wikimedia.org/wiki/File:Venezuela_Guyana_Essequibo_dispute_map.svg

2) Convertir a GeoJSON
   - Con QGIS: cargar el mapa (georreferenciado o con coordenadas), digitalizar
     el polígono de la zona en reclamación, capa → Exportar → Guardar como →
     GeoJSON.
   - Con GDAL (ogr2ogr): si tiene un shapefile (.shp) del límite:
     ogr2ogr -f GeoJSON zona_reclamacion.geojson limite_esequibo.shp
   - Si solo tiene SVG/PNG: georreferenciar en QGIS y luego digitalizar el
     polígono y exportar a GeoJSON.

3) Guardar aquí
   - Guarde el resultado como: zona_reclamacion.geojson
   - Colóquelo en: gestion_social/static/geojson/zona_reclamacion.geojson

Formatos válidos del archivo:
  - FeatureCollection con una o más features (geometry: Polygon o MultiPolygon)
  - Una sola Feature con geometry Polygon o MultiPolygon
  - Un objeto con "type": "Polygon" o "MultiPolygon" y "coordinates" en la raíz

Si no existe este archivo, la aplicación usa un polígono aproximado interno.

"""
Asigna estados de Venezuela (aleatorios) a las solicitudes existentes para el mapa.
Uso: python manage.py asignar_estados_demo
"""
import random
from django.core.management.base import BaseCommand
from gestion_social.models import Solicitud


ESTADOS_VE = [
    'MIRANDA', 'ZULIA', 'CARABOBO', 'DISTRITO CAPITAL', 'LARA', 'ARAGUA',
    'BOLÍVAR', 'ANZOÁTEGUI', 'TÁCHIRA', 'MERIDA', 'MONAGAS', 'SUCRE',
    'FALCÓN', 'PORTUGUESA', 'GUÁRICO', 'YARACUY', 'BARINAS', 'NUEVA ESPARTA',
    'APURE', 'VARGAS', 'COJEDES', 'TRUJILLO', 'AMAZONAS', 'DELTA AMACURO',
]


class Command(BaseCommand):
    help = 'Asigna un estado (entidad federal) aleatorio a cada solicitud existente para el mapa.'

    def handle(self, *args, **options):
        qs = Solicitud.objects.all()
        total = qs.count()
        if total == 0:
            self.stdout.write(self.style.WARNING('No hay solicitudes. Ejecute antes: python manage.py cargar_datos_demo'))
            return
        actualizados = 0
        for sol in qs:
            sol.estado = random.choice(ESTADOS_VE)
            sol.save(update_fields=['estado'])
            actualizados += 1
        self.stdout.write(self.style.SUCCESS(f'Se asignó estado a {actualizados} solicitudes. Recargue el mapa en el dashboard.'))

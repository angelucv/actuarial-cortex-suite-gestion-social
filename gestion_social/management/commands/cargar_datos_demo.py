"""
Carga datos simulados de solicitudes para demostración.
Las fechas se reparten en los últimos 24 meses para que la Visión histórica muestre series temporales.
Uso: python manage.py cargar_datos_demo
"""
import random
from datetime import timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from gestion_social.models import Solicitud

MESES_NOMBRES = [
    'ENERO', 'FEBRERO', 'MARZO', 'ABRIL', 'MAYO', 'JUNIO',
    'JULIO', 'AGOSTO', 'SEPTIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE',
]


class Command(BaseCommand):
    help = 'Carga solicitudes de demostración con scoring variado y fechas repartidas en el tiempo.'

    def add_arguments(self, parser):
        parser.add_argument('--cantidad', type=int, default=350, help='Número de registros a crear (default 350)')
        parser.add_argument('--meses-atras', type=int, default=24, help='Repartir fechas en los últimos N meses (default 24)')
        parser.add_argument('--clear', action='store_true', help='Borrar todas las solicitudes antes de cargar (para ver solo la nueva distribución)')

    def handle(self, *args, **options):
        n = options['cantidad']
        meses_atras = max(6, min(60, options['meses_atras']))
        if options.get('clear') and Solicitud.objects.exists():
            deleted = Solicitud.objects.count()
            Solicitud.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'Se borraron {deleted} solicitudes.'))
        if Solicitud.objects.exists() and not options.get('clear'):
            self.stdout.write(self.style.WARNING('Ya existen solicitudes. Use --clear para borrar primero y ver una distribución más irregular.'))
        especialidades = [
            'MEDICINA GENERAL', 'PEDIATRÍA', 'TRAUMATOLOGÍA', 'CARDIOLOGÍA', 'DERMATOLOGÍA',
            'OFTALMOLOGÍA', 'GINECOLOGÍA', 'ONCOLOGÍA', 'NEUROLOGÍA', 'OTROS'
        ]
        estatus = ['APROBADO', 'PENDIENTE', 'EN TRÁMITE', 'PAGADO', 'RECHAZADO']
        proveedores = ['CLÍNICA CENTRAL', 'LAB. DIAGNÓSTICO', 'FARMACIA RED', 'CONSULTORIO NORTE', 'INSTITUTO ESPECIALIZADO']
        estados_ve = ['MIRANDA', 'ZULIA', 'CARABOBO', 'DISTRITO CAPITAL', 'LARA', 'ARAGUA', 'BOLÍVAR', 'ANZOÁTEGUI', 'TÁCHIRA', 'MERIDA', 'MONAGAS', 'SUCRE', 'FALCÓN', 'PORTUGUESA', 'GUÁRICO', 'YARACUY', 'BARINAS', 'NUEVA ESPARTA', 'APURE', 'VARGAS', 'COJEDES', 'TRUJILLO', 'AMAZONAS', 'DELTA AMACURO']
        # Pesos muy desiguales por estado: pocos estados concentran la mayoría (mapa con diferencias visibles)
        # Primeros 5–6 estados "calientes", el resto con mucho menos peso
        pesos_estados = [12.0, 10.0, 9.0, 8.0, 7.0, 6.0]
        pesos_estados += [2.0] * 4
        pesos_estados += [1.0] * 6
        pesos_estados += [0.4] * (len(estados_ve) - len(pesos_estados))
        pesos_estados = pesos_estados[:len(estados_ve)]
        total_peso_est = sum(pesos_estados)
        probs_estados = [p / total_peso_est for p in pesos_estados]

        # Distribución MUY irregular: pocos meses con pico alto, el resto en valle (evita línea plana)
        pesos_meses = [0.08 + random.uniform(0, 0.12) for _ in range(meses_atras)]  # base baja
        num_picos = random.randint(4, 7)
        indices_pico = random.sample(range(meses_atras), min(num_picos, meses_atras))
        for i in indices_pico:
            pesos_meses[i] = random.uniform(6.0, 14.0)  # picos muy marcados
        total_peso = max(sum(pesos_meses), 1e-6)
        probs_meses = [p / total_peso for p in pesos_meses]

        creados = 0
        for i in range(1, n + 1):
            nro = f"C-{i:05d}"
            if Solicitud.objects.filter(nro_caso=nro).exists():
                continue
            monto = round(Decimal(random.lognormvariate(8, 1.2)), 2)
            monto = max(Decimal('100'), min(monto, Decimal('50000')))
            # Mes elegido de forma aleatoria según pesos (distribución irregular)
            indice_mes = random.choices(range(meses_atras), weights=probs_meses, k=1)[0]
            # Día aleatorio dentro de ese mes (no solo el 1)
            dias_dentro_mes = random.randint(0, 28)
            dias_atras = indice_mes * 30 + dias_dentro_mes
            fecha_pasada = timezone.now() - timedelta(days=dias_atras)
            mes_nombre = MESES_NOMBRES[fecha_pasada.month - 1]
            obj = Solicitud.objects.create(
                nro_caso=nro,
                especialidad=random.choices(especialidades, weights=[22, 18, 14, 10, 8, 8, 6, 5, 4, 5])[0],
                estatus=random.choices(estatus, weights=[35, 20, 15, 20, 10])[0],
                proveedor=random.choices(proveedores, weights=[25, 20, 20, 18, 17])[0],
                monto_usd=monto,
                mes=mes_nombre,
                estado=random.choices(estados_ve, weights=probs_estados, k=1)[0],
                beneficiario_nombre=f"BENEF-{i}",
                beneficiario_cedula=f"V-{10000000 + i}",
                fecha_recepcion=fecha_pasada.date(),
            )
            # Asignar creado_en en el pasado para que la serie temporal use períodos variados
            Solicitud.objects.filter(pk=obj.pk).update(creado_en=fecha_pasada, actualizado_en=fecha_pasada)
            creados += 1
        self.stdout.write(self.style.SUCCESS(
            f'Se crearon {creados} solicitudes de demostración con fechas repartidas en los últimos {meses_atras} meses.'
        ))

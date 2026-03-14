from django.contrib import admin
from django.contrib.auth import get_user_model
from import_export import resources, fields
from import_export.widgets import DateWidget
from import_export.admin import ImportExportModelAdmin
from .models import Solicitud
from .scoring import calcular_prioridad


class MisCasosFilter(admin.SimpleListFilter):
    title = 'asignación'
    parameter_name = 'miscasos'

    def lookups(self, request, model_admin):
        return (('mios', 'Mis casos'),)

    def queryset(self, request, queryset):
        if self.value() == 'mios':
            return queryset.filter(asignado_a=request.user)
        return queryset


class SolicitudResource(resources.ModelResource):
    nro_caso = fields.Field(attribute='nro_caso', column_name='NRO DE CASO')
    fecha_recepcion = fields.Field(attribute='fecha_recepcion', column_name='FECHA DE RECEPCIÓN', widget=DateWidget(format='%Y-%m-%d'))
    solicitante_nombre = fields.Field(attribute='solicitante_nombre', column_name='SOLICITANTE')
    solicitante_cedula = fields.Field(attribute='solicitante_cedula', column_name='CÉDULA DEL SOLICITANTE')
    beneficiario_nombre = fields.Field(attribute='beneficiario_nombre', column_name='BENEFICIARIO')
    beneficiario_cedula = fields.Field(attribute='beneficiario_cedula', column_name='CÉDULA DEL BENEFICIARIO')
    tipo_solicitud = fields.Field(attribute='tipo_solicitud', column_name='TIPO DE SOLICITUD')
    especialidad = fields.Field(attribute='especialidad', column_name='ESPECIALIDAD')
    descripcion_caso = fields.Field(attribute='descripcion_caso', column_name='DESCRIPCIÓN DEL CASO ')
    atendido_por = fields.Field(attribute='atendido_por', column_name='ATENDIDO POR')
    estatus = fields.Field(attribute='estatus', column_name='ESTATUS DE GESTION')
    proveedor = fields.Field(attribute='proveedor', column_name='PROVEEDOR')
    monto_usd = fields.Field(attribute='monto_usd', column_name='MONTO  PAGADO $')
    monto_bs = fields.Field(attribute='monto_bs', column_name='MONTO PAGADO  BS')
    tasa_bcv = fields.Field(attribute='tasa_bcv', column_name='TASA BCV DEL DIA')
    partida = fields.Field(attribute='partida', column_name='PARTIDA')
    mes = fields.Field(attribute='mes', column_name='MES')

    class Meta:
        model = Solicitud
        import_id_fields = ('nro_caso',)
        exclude = ('id',)

    def before_save_instance(self, instance, *args, **kwargs):
        puntos, nivel = calcular_prioridad(instance)
        instance.score_prioridad = puntos
        instance.nivel_prioridad = nivel


@admin.action(description='📊 Recalcular Scoring Manualmente')
def ejecutar_scoring(modeladmin, request, queryset):
    count = 0
    for solicitud in queryset:
        puntos, nivel = calcular_prioridad(solicitud)
        solicitud.score_prioridad = puntos
        solicitud.nivel_prioridad = nivel
        solicitud.save()
        count += 1
    modeladmin.message_user(request, f"Scoring recalculado para {count} casos.")


@admin.register(Solicitud)
class SolicitudAdmin(ImportExportModelAdmin):
    resource_class = SolicitudResource
    list_display = ('nro_caso', 'especialidad', 'monto_usd', 'score_prioridad', 'nivel_prioridad', 'asignado_a')
    list_filter = (MisCasosFilter, 'nivel_prioridad', 'asignado_a', 'mes', 'estatus')
    search_fields = ('nro_caso', 'beneficiario_cedula', 'beneficiario_nombre')
    actions = [ejecutar_scoring]
    list_select_related = ('asignado_a',)
    fieldsets = (
        (None, {'fields': ('nro_caso', 'fecha_recepcion', 'estatus', 'especialidad', 'proveedor', 'estado', 'monto_usd', 'monto_bs', 'tasa_bcv')}),
        ('Solicitante / Beneficiario', {'fields': ('solicitante_nombre', 'solicitante_cedula', 'beneficiario_nombre', 'beneficiario_cedula', 'tipo_solicitud', 'descripcion_caso', 'atendido_por')}),
        ('Seguimiento', {'fields': ('notas', 'asignado_a'), 'description': 'Notas internas y asignación del caso.'}),
        ('Presupuesto', {'fields': ('partida', 'mes')}),
        ('Scoring', {'fields': ('score_prioridad', 'nivel_prioridad')}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('asignado_a')

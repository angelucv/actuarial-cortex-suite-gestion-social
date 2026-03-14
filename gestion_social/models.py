from django.db import models
from django.conf import settings
from .scoring import calcular_prioridad


class Solicitud(models.Model):
    nro_caso = models.CharField(max_length=50, verbose_name="Nro Caso", unique=True)
    fecha_recepcion = models.DateField(verbose_name="Fecha Recepción", null=True, blank=True)
    solicitante_nombre = models.CharField(max_length=200, verbose_name="Solicitante", blank=True, null=True)
    solicitante_cedula = models.CharField(max_length=20, verbose_name="Cédula Solicitante", blank=True, null=True)
    beneficiario_nombre = models.CharField(max_length=200, verbose_name="Beneficiario", blank=True, null=True)
    beneficiario_cedula = models.CharField(max_length=20, verbose_name="Cédula Beneficiario", blank=True, null=True)
    tipo_solicitud = models.CharField(max_length=100, verbose_name="Tipo Solicitud", blank=True, null=True)
    especialidad = models.CharField(max_length=100, verbose_name="Especialidad", blank=True, null=True)
    descripcion_caso = models.TextField(verbose_name="Descripción", blank=True, null=True)
    atendido_por = models.CharField(max_length=100, verbose_name="Atendido Por", blank=True, null=True)
    estatus = models.CharField(max_length=100, verbose_name="Estatus", default='PENDIENTE')
    proveedor = models.CharField(max_length=200, verbose_name="Proveedor", blank=True, null=True)
    monto_usd = models.DecimalField(max_digits=20, decimal_places=2, verbose_name="Monto USD", null=True, blank=True, default=0)
    monto_bs = models.DecimalField(max_digits=25, decimal_places=2, verbose_name="Monto Bs", null=True, blank=True, default=0)
    tasa_bcv = models.DecimalField(max_digits=10, decimal_places=4, verbose_name="Tasa BCV", null=True, blank=True, default=0)
    partida = models.CharField(max_length=150, verbose_name="Partida", blank=True, null=True)
    mes = models.CharField(max_length=50, verbose_name="Mes", blank=True, null=True)
    estado = models.CharField(max_length=100, verbose_name="Estado (entidad federal)", blank=True, null=True, help_text="Estado de Venezuela donde se atiende el caso.")
    score_prioridad = models.IntegerField(verbose_name="Score Riesgo", default=0)
    nivel_prioridad = models.CharField(max_length=20, verbose_name="Nivel", default="BAJO")
    notas = models.TextField(verbose_name="Notas internas", blank=True, null=True, help_text="Comentarios o seguimiento del caso (solo uso interno).")
    asignado_a = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="solicitudes_asignadas",
        verbose_name="Asignado a",
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        puntos, nivel = calcular_prioridad(self)
        self.score_prioridad = puntos
        self.nivel_prioridad = nivel
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nro_caso} - {self.nivel_prioridad}"

    class Meta:
        verbose_name = "Solicitud GRS"
        verbose_name_plural = "Solicitudes GRS"

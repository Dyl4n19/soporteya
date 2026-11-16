from django.conf import settings
from django.db import models

from .categoria_model import CategoriaModel
from .empresa_model import EmpresaModel
from .tecnico_model import TecnicoModel


class TicketModel(models.Model):
    PRIORIDADES = [(x, x.title()) for x in ("BAJA", "MEDIA", "ALTA", "CRITICA")]
    ESTADOS = [(x, x.replace("_", " ").title()) for x in ("ABIERTO", "ASIGNADO", "EN_PROGRESO", "RESUELTO", "CERRADO")]

    id_ticket = models.AutoField(primary_key=True)
    empresa = models.ForeignKey(EmpresaModel, models.PROTECT, db_column="id_empresa", related_name="tickets")
    categoria = models.ForeignKey(CategoriaModel, models.PROTECT, db_column="id_categoria", related_name="tickets")
    tecnico = models.ForeignKey(TecnicoModel, models.PROTECT, db_column="id_tecnico", related_name="tickets", null=True, blank=True)
    titulo = models.CharField(max_length=150)
    descripcion = models.TextField()
    prioridad = models.CharField(max_length=10, choices=PRIORIDADES, default="MEDIA")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_cierre = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(max_length=15, choices=ESTADOS, default="ABIERTO")

    class Meta:
        app_label = "soporte"
        db_table = "TICKETS"
        managed = settings.BUSINESS_MODELS_MANAGED
        ordering = ["-fecha_creacion"]

    def __str__(self):
        return f"#{self.pk} {self.titulo}"


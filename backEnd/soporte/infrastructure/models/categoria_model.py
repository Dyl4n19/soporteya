from django.conf import settings
from django.db import models


class CategoriaModel(models.Model):
    id_categoria = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=80, unique=True)
    horas_sla = models.PositiveIntegerField()
    activo = models.BooleanField(default=True)

    class Meta:
        app_label = "soporte"
        db_table = "CATEGORIAS_TICKET"
        managed = settings.BUSINESS_MODELS_MANAGED
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


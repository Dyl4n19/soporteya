from django.conf import settings
from django.db import models


class TecnicoModel(models.Model):
    id_tecnico = models.AutoField(primary_key=True)
    rut = models.CharField(max_length=12, unique=True)
    nombre = models.CharField(max_length=120)
    email = models.EmailField(max_length=150, unique=True)
    activo = models.BooleanField(default=True)

    class Meta:
        app_label = "soporte"
        db_table = "TECNICOS"
        managed = settings.BUSINESS_MODELS_MANAGED
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


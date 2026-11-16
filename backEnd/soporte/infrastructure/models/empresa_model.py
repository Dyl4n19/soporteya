from django.conf import settings
from django.db import models


class EmpresaModel(models.Model):
    id_empresa = models.AutoField(primary_key=True)
    rut = models.CharField(max_length=12, unique=True)
    razon_social = models.CharField(max_length=120)
    plan = models.CharField(max_length=10, choices=[("BASICO", "Básico"), ("PREMIUM", "Premium")])
    activo = models.BooleanField(default=True)

    class Meta:
        app_label = "soporte"
        db_table = "EMPRESAS"
        managed = settings.BUSINESS_MODELS_MANAGED
        ordering = ["razon_social"]

    def __str__(self):
        return self.razon_social


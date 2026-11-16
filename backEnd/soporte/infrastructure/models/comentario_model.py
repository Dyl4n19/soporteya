from django.conf import settings
from django.db import models

from .ticket_model import TicketModel


class ComentarioModel(models.Model):
    id_comentario = models.AutoField(primary_key=True)
    ticket = models.ForeignKey(TicketModel, models.CASCADE, db_column="id_ticket", related_name="comentarios")
    numero = models.PositiveIntegerField()
    fecha = models.DateTimeField(auto_now_add=True)
    autor = models.CharField(max_length=120)
    texto = models.TextField()

    class Meta:
        app_label = "soporte"
        db_table = "COMENTARIOS_TICKET"
        managed = settings.BUSINESS_MODELS_MANAGED
        constraints = [models.UniqueConstraint(fields=["ticket", "numero"], name="pk_comentarios_ticket")]
        ordering = ["numero"]

    def __str__(self):
        return f"#{self.ticket_id}.{self.numero}"


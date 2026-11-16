from django.db.models import Avg, DurationField, ExpressionWrapper, F
from django.utils import timezone

from soporte.infrastructure.models import TicketModel
from .base import DjangoBaseRepository


class DjangoTicketRepository(DjangoBaseRepository):
    model = TicketModel

    def overdue(self):
        now = timezone.now()
        rows = TicketModel.objects.exclude(estado__in=["RESUELTO", "CERRADO"]).select_related("categoria", "empresa", "tecnico")
        return [t for t in rows if (now - t.fecha_creacion).total_seconds() > t.categoria.horas_sla * 3600]

    def average_resolution_by_technician(self):
        duration = ExpressionWrapper(F("fecha_cierre") - F("fecha_creacion"), output_field=DurationField())
        return (TicketModel.objects.filter(fecha_cierre__isnull=False, tecnico__isnull=False)
                .values("tecnico_id", "tecnico__nombre").annotate(promedio=Avg(duration)).order_by("tecnico__nombre"))


from django.db.models import Avg, DurationField, ExpressionWrapper, F
from django.utils import timezone

from soporte.domain.entities import Ticket
from soporte.domain.entities.ticket import PromedioResolucionTecnico
from soporte.infrastructure.models import TicketModel
from .base import DjangoBaseRepository


class DjangoTicketRepository(DjangoBaseRepository[Ticket]):
    model = TicketModel
    entity_type = Ticket
    field_mapping = {"id_empresa": "empresa_id", "id_categoria": "categoria_id", "id_tecnico": "tecnico_id"}

    def overdue(self) -> list[Ticket]:
        now = timezone.now()
        rows = TicketModel.objects.using(self.database).exclude(estado__in=["RESUELTO", "CERRADO"]).select_related("categoria")
        return [self.to_entity(t) for t in rows
                if (now - t.fecha_creacion).total_seconds() > t.categoria.horas_sla * 3600]

    def average_resolution_by_technician(self) -> list[PromedioResolucionTecnico]:
        duration = ExpressionWrapper(F("fecha_cierre") - F("fecha_creacion"), output_field=DurationField())
        rows = (TicketModel.objects.using(self.database).filter(fecha_cierre__isnull=False, tecnico__isnull=False)
                .values("tecnico_id", "tecnico__nombre").annotate(promedio=Avg(duration)).order_by("tecnico__nombre"))
        return [PromedioResolucionTecnico(
            id_tecnico=row["tecnico_id"], tecnico=row["tecnico__nombre"],
            horas_promedio=round(row["promedio"].total_seconds() / 3600, 2),
        ) for row in rows]


from soporte.application.exceptions import NotFoundError
from soporte.domain.entities import Ticket
from soporte.domain.entities.ticket import PromedioResolucionTecnico
from soporte.infrastructure.models import TicketModel
from .base import DjangoBaseRepository


class DjangoTicketRepository(DjangoBaseRepository[Ticket]):
    model = TicketModel
    entity_type = Ticket
    field_mapping = {"id_empresa": "empresa_id", "id_categoria": "categoria_id", "id_tecnico": "tecnico_id"}
    search_fields = ("titulo", "descripcion", "empresa__razon_social")
    filter_fields = ("estado", "prioridad", "categoria_id", "tecnico_id", "tecnico_email")
    filter_mapping = {"tecnico_email": "tecnico__email__iexact"}
    ordering_fields = ("id_ticket", "titulo", "prioridad", "estado", "fecha_creacion", "fecha_cierre")

    def lock(self, pk: int) -> Ticket:
        try:
            instance = self.model.objects.using(self.database).select_for_update().get(pk=pk)
        except self.model.DoesNotExist as exc:
            raise NotFoundError("Registro no encontrado") from exc
        return self.to_entity(instance)

    def average_resolution_by_technician(self) -> list[PromedioResolucionTecnico]:
        rows = (TicketModel.objects.using(self.database).filter(fecha_cierre__isnull=False, tecnico__isnull=False)
                .select_related("tecnico"))
        totals = {}
        for row in rows:
            item = totals.setdefault(row.tecnico_id, {"nombre": row.tecnico.nombre, "segundos": 0, "cantidad": 0})
            item["segundos"] += (row.fecha_cierre - row.fecha_creacion).total_seconds()
            item["cantidad"] += 1
        return sorted([
            PromedioResolucionTecnico(id_tecnico=pk, tecnico=item["nombre"],
                                      horas_promedio=round(item["segundos"] / item["cantidad"] / 3600, 2))
            for pk, item in totals.items()
        ], key=lambda item: item.tecnico)


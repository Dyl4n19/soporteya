from django.db import transaction
from django.db.models import Max

from soporte.application.exceptions import NotFoundError
from soporte.domain.entities import Comentario
from soporte.infrastructure.models import ComentarioModel, TicketModel


class DjangoComentarioRepository:
    def to_entity(self, instance) -> Comentario:
        return Comentario(id_ticket=instance.ticket_id, numero=instance.numero,
                          autor=instance.autor, texto=instance.texto, fecha=instance.fecha)

    def for_ticket(self, ticket_id: int) -> list[Comentario]:
        return [self.to_entity(instance) for instance in
                ComentarioModel.objects.using("negocio").filter(ticket_id=ticket_id)]

    def add(self, ticket_id: int, autor: str, texto: str) -> Comentario:
        with transaction.atomic(using="negocio"):
            try:
                TicketModel.objects.using("negocio").select_for_update().get(pk=ticket_id)
            except TicketModel.DoesNotExist as exc:
                raise NotFoundError("Ticket no encontrado") from exc
            rows = ComentarioModel.objects.using("negocio").filter(ticket_id=ticket_id)
            ultimo = rows.aggregate(n=Max("numero"))["n"] or 0
            instance = ComentarioModel.objects.using("negocio").create(
                ticket_id=ticket_id, numero=ultimo + 1, autor=autor, texto=texto,
            )
            return self.to_entity(instance)


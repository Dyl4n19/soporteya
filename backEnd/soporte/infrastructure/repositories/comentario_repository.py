from django.db import transaction
from django.db.models import Max, Q

from soporte.application.exceptions import NotFoundError
from soporte.domain.entities import Comentario
from soporte.infrastructure.models import ComentarioModel, TicketModel


class DjangoComentarioRepository:
    def to_entity(self, instance) -> Comentario:
        return Comentario(id_ticket=instance.ticket_id, numero=instance.numero,
                          autor=instance.autor, texto=instance.texto, fecha=instance.fecha)

    def for_ticket(self, ticket_id: int, *, search: str = "", filters: dict | None = None,
                   ordering: str | None = None) -> list[Comentario]:
        rows = ComentarioModel.objects.using("negocio").filter(ticket_id=ticket_id)
        for field, value in (filters or {}).items():
            if field in {"autor", "numero"}:
                rows = rows.filter(**{field: value})
        for term in search.split():
            rows = rows.filter(Q(autor__icontains=term) | Q(texto__icontains=term))
        fields = [field.strip() for field in (ordering or "numero").split(",")
                  if field.strip().removeprefix("-") in {"numero", "fecha", "autor"}]
        if not any(field.removeprefix("-") == "numero" for field in fields):
            fields.append("numero")
        return [self.to_entity(instance) for instance in rows.order_by(*fields)]

    def _get_instance(self, ticket_id: int, numero: int):
        try:
            return ComentarioModel.objects.using("negocio").get(ticket_id=ticket_id, numero=numero)
        except ComentarioModel.DoesNotExist as exc:
            raise NotFoundError("Comentario no encontrado") from exc

    def get(self, ticket_id: int, numero: int) -> Comentario:
        return self.to_entity(self._get_instance(ticket_id, numero))

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

    def update(self, ticket_id: int, numero: int, texto: str) -> Comentario:
        instance = self._get_instance(ticket_id, numero)
        instance.texto = texto
        instance.save(using="negocio", update_fields=["texto"])
        return self.to_entity(instance)

    def delete(self, ticket_id: int, numero: int) -> None:
        self._get_instance(ticket_id, numero).delete(using="negocio")


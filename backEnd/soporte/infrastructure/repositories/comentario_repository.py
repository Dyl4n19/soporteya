from django.db.models import Max

from soporte.infrastructure.models import ComentarioModel


class DjangoComentarioRepository:
    def for_ticket(self, ticket_id):
        return ComentarioModel.objects.filter(ticket_id=ticket_id)

    def add(self, ticket_id, autor, texto):
        ultimo = ComentarioModel.objects.filter(ticket_id=ticket_id).aggregate(n=Max("numero"))["n"] or 0
        return ComentarioModel.objects.create(ticket_id=ticket_id, numero=ultimo + 1, autor=autor, texto=texto)


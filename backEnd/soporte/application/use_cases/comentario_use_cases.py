from soporte.application.exceptions import RuleViolationError
from soporte.domain.entities import Comentario
from soporte.domain.ports import ComentarioRepositoryPort, TicketRepositoryPort


class ComentarioUseCases:
    def __init__(self, repository: ComentarioRepositoryPort, ticket_repository: TicketRepositoryPort):
        self.repository = repository
        self.ticket_repository = ticket_repository

    def agregar(self, ticket_id: int, autor: str, texto: str) -> Comentario:
        ticket = self.ticket_repository.get(ticket_id)
        if ticket.estado == "CERRADO":
            raise RuleViolationError("No se pueden agregar comentarios a un ticket cerrado", "estado")
        return self.repository.add(ticket_id, autor, texto)


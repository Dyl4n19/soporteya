from soporte.application.exceptions import RuleViolationError


class ComentarioUseCases:
    def __init__(self, repository, ticket_repository):
        self.repository = repository
        self.ticket_repository = ticket_repository

    def agregar(self, ticket_id, autor, texto):
        ticket = self.ticket_repository.get(ticket_id)
        if ticket.estado == "CERRADO":
            raise RuleViolationError("No se pueden agregar comentarios a un ticket cerrado", "estado")
        return self.repository.add(ticket_id, autor, texto)


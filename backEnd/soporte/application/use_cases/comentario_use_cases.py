from soporte.application.exceptions import RuleViolationError
from soporte.domain.entities import Comentario
from soporte.domain.ports import ComentarioRepositoryPort, TicketRepositoryPort, UnitOfWorkPort


class ComentarioUseCases:
    def __init__(self, repository: ComentarioRepositoryPort, ticket_repository: TicketRepositoryPort,
                 unit_of_work: UnitOfWorkPort):
        self.repository = repository
        self.ticket_repository = ticket_repository
        self.unit_of_work = unit_of_work

    @staticmethod
    def validar_texto(texto: str) -> None:
        if not isinstance(texto, str) or not 2 <= len(texto.strip()) <= 4000:
            raise RuleViolationError("El comentario debe tener entre 2 y 4000 caracteres", "texto")

    def listar(self, ticket_id: int, *, search: str = "", filters: dict | None = None,
               ordering: str | None = None) -> list[Comentario]:
        self.ticket_repository.get(ticket_id)
        return self.repository.for_ticket(ticket_id, search=search, filters=filters, ordering=ordering)

    def obtener(self, ticket_id: int, numero: int) -> Comentario:
        self.ticket_repository.get(ticket_id)
        return self.repository.get(ticket_id, numero)

    def crear(self, ticket_id: int, autor: str, texto: str) -> Comentario:
        return self.agregar(ticket_id, autor, texto)

    def agregar(self, ticket_id: int, autor: str, texto: str) -> Comentario:
        self.validar_texto(texto)
        with self.unit_of_work.atomic():
            ticket = self.ticket_repository.lock(ticket_id)
            if ticket.estado == "CERRADO":
                raise RuleViolationError("No se pueden agregar comentarios a un ticket cerrado", "estado")
            return self.repository.add(ticket_id, autor, texto.strip())

    def actualizar(self, ticket_id: int, numero: int, texto: str) -> Comentario:
        self.validar_texto(texto)
        with self.unit_of_work.atomic():
            ticket = self.ticket_repository.lock(ticket_id)
            if ticket.estado == "CERRADO":
                raise RuleViolationError("No se pueden editar comentarios de un ticket cerrado", "estado")
            return self.repository.update(ticket_id, numero, texto.strip())

    def eliminar(self, ticket_id: int, numero: int) -> None:
        with self.unit_of_work.atomic():
            ticket = self.ticket_repository.lock(ticket_id)
            self.repository.get(ticket_id, numero)
            if ticket.estado == "CERRADO":
                raise RuleViolationError("No se pueden eliminar comentarios de un ticket cerrado", "estado")
            if ticket.estado == "RESUELTO" and len(self.repository.for_ticket(ticket_id)) == 1:
                raise RuleViolationError("Un ticket resuelto debe conservar al menos un comentario", "texto")
            self.repository.delete(ticket_id, numero)


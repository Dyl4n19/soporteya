from typing import Protocol

from soporte.domain.entities import Comentario


class ComentarioRepositoryPort(Protocol):
    def for_ticket(self, ticket_id: int) -> list[Comentario]: ...

    def add(self, ticket_id: int, autor: str, texto: str) -> Comentario: ...


from typing import Protocol

from soporte.domain.entities import Comentario


class ComentarioRepositoryPort(Protocol):
    def for_ticket(self, ticket_id: int, *, search: str = "", filters: dict | None = None,
                   ordering: str | None = None) -> list[Comentario]: ...

    def get(self, ticket_id: int, numero: int) -> Comentario: ...

    def add(self, ticket_id: int, autor: str, texto: str) -> Comentario: ...

    def update(self, ticket_id: int, numero: int, texto: str) -> Comentario: ...

    def delete(self, ticket_id: int, numero: int) -> None: ...


from typing import Protocol


class ComentarioRepositoryPort(Protocol):
    def for_ticket(self, ticket_id: int): ...
    def add(self, ticket_id: int, autor: str, texto: str): ...


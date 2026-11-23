from typing import Protocol

from soporte.domain.entities import Ticket
from soporte.domain.entities.ticket import PromedioResolucionTecnico
from .base import RepositoryPort


class TicketRepositoryPort(RepositoryPort[Ticket], Protocol):
    def overdue(self) -> list[Ticket]: ...

    def average_resolution_by_technician(self) -> list[PromedioResolucionTecnico]: ...


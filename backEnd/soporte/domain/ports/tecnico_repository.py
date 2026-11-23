from typing import Protocol

from soporte.domain.entities import Tecnico
from .base import RepositoryPort


class TecnicoRepositoryPort(RepositoryPort[Tecnico], Protocol):
    pass


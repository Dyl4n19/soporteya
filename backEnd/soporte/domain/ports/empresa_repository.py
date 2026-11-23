from typing import Protocol

from soporte.domain.entities import Empresa
from .base import RepositoryPort


class EmpresaRepositoryPort(RepositoryPort[Empresa], Protocol):
    pass


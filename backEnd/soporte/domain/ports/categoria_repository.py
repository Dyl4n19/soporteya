from typing import Protocol

from soporte.domain.entities import Categoria
from .base import RepositoryPort


class CategoriaRepositoryPort(RepositoryPort[Categoria], Protocol):
    pass


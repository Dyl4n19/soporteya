from collections.abc import Mapping

from soporte.application.exceptions import RuleViolationError
from soporte.domain.entities import Categoria
from soporte.domain.ports import CategoriaRepositoryPort
from .base import CrudUseCases


class CategoriaUseCases(CrudUseCases[Categoria]):
    required_text_fields = ("nombre",)

    def __init__(self, repository: CategoriaRepositoryPort):
        super().__init__(repository)

    def validar(self, data: Mapping[str, object]) -> None:
        super().validar(data)
        hours = data.get("horas_sla")
        if type(hours) is not int or not 1 <= hours <= 8760:
            raise RuleViolationError("Las horas de SLA deben estar entre 1 y 8760", "horas_sla")


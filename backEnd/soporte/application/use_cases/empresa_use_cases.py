from collections.abc import Mapping

from soporte.application.exceptions import RuleViolationError
from soporte.domain.entities import Empresa
from soporte.domain.ports import EmpresaRepositoryPort
from .base import CrudUseCases


class EmpresaUseCases(CrudUseCases[Empresa]):
    required_text_fields = ("rut", "razon_social")

    def __init__(self, repository: EmpresaRepositoryPort):
        super().__init__(repository)

    def validar(self, data: Mapping[str, object]) -> None:
        super().validar(data)
        if data.get("plan", "BASICO") not in {"BASICO", "PREMIUM"}:
            raise RuleViolationError("El plan debe ser BASICO o PREMIUM", "plan")


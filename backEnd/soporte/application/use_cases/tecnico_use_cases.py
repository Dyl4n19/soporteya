from collections.abc import Mapping

from soporte.application.exceptions import RuleViolationError
from soporte.domain.entities import Tecnico
from soporte.domain.ports import TecnicoRepositoryPort
from .base import CrudUseCases


class TecnicoUseCases(CrudUseCases[Tecnico]):
    required_text_fields = ("rut", "nombre", "email")

    def __init__(self, repository: TecnicoRepositoryPort):
        super().__init__(repository)

    def validar(self, data: Mapping[str, object]) -> None:
        super().validar(data)
        email = data["email"]
        if email.count("@") != 1 or not all(email.split("@")):
            raise RuleViolationError("Debe ingresar un correo electrónico válido", "email")


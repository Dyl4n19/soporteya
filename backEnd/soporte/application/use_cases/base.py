from collections.abc import Mapping
from dataclasses import asdict
from typing import Generic

from soporte.application.exceptions import RuleViolationError
from soporte.domain.ports.base import Entity, RepositoryPort


class CrudUseCases(Generic[Entity]):
    required_text_fields: tuple[str, ...] = ()

    def __init__(self, repository: RepositoryPort[Entity]):
        self.repository = repository

    def listar(self, *, search: str = "", filters: Mapping[str, object] | None = None,
               ordering: str | None = None) -> list[Entity]:
        return self.repository.list(search=search, filters=filters, ordering=ordering)

    def obtener(self, pk: int) -> Entity:
        return self.repository.get(pk)

    def crear(self, data: Mapping[str, object]) -> Entity:
        values = dict(data)
        self.validar(values)
        return self.repository.save(values)

    def actualizar(self, pk: int, data: Mapping[str, object]) -> Entity:
        instance = self.obtener(pk)
        values = dict(data)
        self.validar(asdict(instance) | values)
        return self.repository.save(values, pk)

    def eliminar(self, pk: int) -> None:
        self.repository.delete(pk)

    def validar(self, data: Mapping[str, object]) -> None:
        for field in self.required_text_fields:
            value = data.get(field)
            if not isinstance(value, str) or not value.strip():
                raise RuleViolationError("Este campo no puede estar vacío", field)
        if "activo" in data and not isinstance(data["activo"], bool):
            raise RuleViolationError("El estado activo debe ser verdadero o falso", "activo")


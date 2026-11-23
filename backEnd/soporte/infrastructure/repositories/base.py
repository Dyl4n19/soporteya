from collections.abc import Mapping
from dataclasses import fields
from typing import Generic

from django.db import IntegrityError, transaction
from django.db.models import Q

from soporte.application.exceptions import DuplicateError, InUseError, NotFoundError
from soporte.domain.ports.base import Entity


class DjangoBaseRepository(Generic[Entity]):
    model = None
    entity_type = None
    field_mapping: dict[str, str] = {}
    search_fields: tuple[str, ...] = ()
    filter_fields: tuple[str, ...] = ()
    ordering_fields: tuple[str, ...] = ()
    unique_fields: tuple[str, ...] = ()
    database = "negocio"

    def to_entity(self, instance) -> Entity:
        return self.entity_type(**{
            field.name: getattr(instance, self.field_mapping.get(field.name, field.name))
            for field in fields(self.entity_type)
        })

    def list(self, *, search: str = "", filters: Mapping[str, object] | None = None,
             ordering: str | None = None) -> list[Entity]:
        queryset = self.model.objects.using(self.database).all()
        for field, value in (filters or {}).items():
            if field in self.filter_fields:
                queryset = queryset.filter(**{field: value})
        for term in search.split():
            if self.search_fields:
                conditions = Q()
                for field in self.search_fields:
                    conditions |= Q(**{f"{field}__icontains": term})
                queryset = queryset.filter(conditions)
        if ordering:
            allowed = [field for field in ordering.split(",")
                       if field.removeprefix("-") in self.ordering_fields]
            if allowed:
                queryset = queryset.order_by(*allowed)
        return [self.to_entity(instance) for instance in queryset]

    def _get_instance(self, pk: int):
        try:
            return self.model.objects.using(self.database).get(pk=pk)
        except self.model.DoesNotExist as exc:
            raise NotFoundError("Registro no encontrado") from exc

    def get(self, pk: int) -> Entity:
        return self.to_entity(self._get_instance(pk))

    def save(self, data: Mapping[str, object], pk: int | None = None) -> Entity:
        values = {self.field_mapping.get(field, field): value for field, value in data.items()}
        try:
            with transaction.atomic(using=self.database):
                instance = self._get_instance(pk) if pk is not None else None
                for field in self.unique_fields:
                    if field not in values:
                        continue
                    duplicates = self.model.objects.using(self.database).filter(**{field: values[field]})
                    if pk is not None:
                        duplicates = duplicates.exclude(pk=pk)
                    if duplicates.exists():
                        raise DuplicateError("Ya existe un registro con este valor", field)
                if instance is None:
                    instance = self.model.objects.using(self.database).create(**values)
                else:
                    for field, value in values.items():
                        setattr(instance, field, value)
                    instance.save(using=self.database)
                return self.to_entity(instance)
        except IntegrityError as exc:
            raise DuplicateError("El registro contiene un valor duplicado o inválido") from exc

    def delete(self, pk: int) -> None:
        try:
            with transaction.atomic(using=self.database):
                self._get_instance(pk).delete(using=self.database)
        except IntegrityError as exc:
            raise InUseError("No se puede eliminar porque el registro está en uso") from exc


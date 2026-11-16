from django.db import IntegrityError

from soporte.application.exceptions import DuplicateError, InUseError, NotFoundError


class DjangoBaseRepository:
    model = None

    def get(self, pk):
        try:
            return self.model.objects.get(pk=pk)
        except self.model.DoesNotExist as exc:
            raise NotFoundError("Registro no encontrado") from exc

    def save(self, data, instance=None):
        try:
            if instance is None:
                return self.model.objects.create(**data)
            for field, value in data.items():
                setattr(instance, field, value)
            instance.save()
            return instance
        except IntegrityError as exc:
            raise DuplicateError("El registro contiene un valor duplicado o inválido") from exc

    def delete(self, instance):
        try:
            instance.delete()
        except IntegrityError as exc:
            raise InUseError("No se puede eliminar porque el registro está en uso") from exc


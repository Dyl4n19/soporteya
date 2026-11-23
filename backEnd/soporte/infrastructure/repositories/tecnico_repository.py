from soporte.domain.entities import Tecnico
from soporte.infrastructure.models import TecnicoModel
from .base import DjangoBaseRepository


class DjangoTecnicoRepository(DjangoBaseRepository[Tecnico]):
    model = TecnicoModel
    entity_type = Tecnico
    search_fields = ("rut", "nombre", "email")
    filter_fields = ("activo",)
    ordering_fields = ("id_tecnico", "rut", "nombre", "email", "activo")
    unique_fields = ("rut", "email")


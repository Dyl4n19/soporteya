from soporte.domain.entities import Categoria
from soporte.infrastructure.models import CategoriaModel
from .base import DjangoBaseRepository


class DjangoCategoriaRepository(DjangoBaseRepository[Categoria]):
    model = CategoriaModel
    entity_type = Categoria
    search_fields = ("nombre",)
    filter_fields = ("activo",)
    ordering_fields = ("id_categoria", "nombre", "horas_sla", "activo")
    unique_fields = ("nombre",)


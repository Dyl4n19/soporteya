from soporte.domain.entities import Empresa
from soporte.infrastructure.models import EmpresaModel
from .base import DjangoBaseRepository


class DjangoEmpresaRepository(DjangoBaseRepository[Empresa]):
    model = EmpresaModel
    entity_type = Empresa
    search_fields = ("rut", "razon_social")
    filter_fields = ("plan", "activo")
    ordering_fields = ("id_empresa", "rut", "razon_social", "plan", "activo")
    unique_fields = ("rut",)


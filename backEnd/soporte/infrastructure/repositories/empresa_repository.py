from soporte.infrastructure.models import EmpresaModel
from .base import DjangoBaseRepository


class DjangoEmpresaRepository(DjangoBaseRepository):
    model = EmpresaModel


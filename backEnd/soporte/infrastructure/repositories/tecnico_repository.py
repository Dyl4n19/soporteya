from soporte.infrastructure.models import TecnicoModel
from .base import DjangoBaseRepository


class DjangoTecnicoRepository(DjangoBaseRepository):
    model = TecnicoModel


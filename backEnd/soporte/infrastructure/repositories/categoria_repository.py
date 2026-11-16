from soporte.infrastructure.models import CategoriaModel
from .base import DjangoBaseRepository


class DjangoCategoriaRepository(DjangoBaseRepository):
    model = CategoriaModel


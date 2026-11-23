from .categoria_repository import CategoriaRepositoryPort
from .comentario_repository import ComentarioRepositoryPort
from .empresa_repository import EmpresaRepositoryPort
from .tecnico_repository import TecnicoRepositoryPort
from .ticket_repository import TicketRepositoryPort
from .unit_of_work import UnitOfWorkPort

__all__ = ["EmpresaRepositoryPort", "CategoriaRepositoryPort", "TecnicoRepositoryPort", "TicketRepositoryPort", "ComentarioRepositoryPort", "UnitOfWorkPort"]


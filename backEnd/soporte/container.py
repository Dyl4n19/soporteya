from soporte.application.use_cases import CategoriaUseCases, ComentarioUseCases, EmpresaUseCases, TecnicoUseCases, TicketUseCases
from soporte.domain.ports import (CategoriaRepositoryPort, ComentarioRepositoryPort,
                                 EmpresaRepositoryPort, TecnicoRepositoryPort, TicketRepositoryPort, UnitOfWorkPort)
from soporte.infrastructure.repositories import DjangoCategoriaRepository, DjangoComentarioRepository, DjangoEmpresaRepository, DjangoTecnicoRepository, DjangoTicketRepository
from soporte.infrastructure.unit_of_work import DjangoUnitOfWork

empresa_repository: EmpresaRepositoryPort = DjangoEmpresaRepository()
categoria_repository: CategoriaRepositoryPort = DjangoCategoriaRepository()
tecnico_repository: TecnicoRepositoryPort = DjangoTecnicoRepository()
ticket_repository: TicketRepositoryPort = DjangoTicketRepository()
comentario_repository: ComentarioRepositoryPort = DjangoComentarioRepository()
unit_of_work: UnitOfWorkPort = DjangoUnitOfWork()

empresas = EmpresaUseCases(empresa_repository)
categorias = CategoriaUseCases(categoria_repository)
tecnicos = TecnicoUseCases(tecnico_repository)
tickets = TicketUseCases(ticket_repository, empresa_repository, tecnico_repository, comentario_repository, categoria_repository, unit_of_work)
comentarios = ComentarioUseCases(comentario_repository, ticket_repository, unit_of_work)


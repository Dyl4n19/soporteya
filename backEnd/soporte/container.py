from soporte.application.use_cases import CategoriaUseCases, ComentarioUseCases, EmpresaUseCases, TecnicoUseCases, TicketUseCases
from soporte.infrastructure.repositories import DjangoCategoriaRepository, DjangoComentarioRepository, DjangoEmpresaRepository, DjangoTecnicoRepository, DjangoTicketRepository

empresa_repository = DjangoEmpresaRepository()
categoria_repository = DjangoCategoriaRepository()
tecnico_repository = DjangoTecnicoRepository()
ticket_repository = DjangoTicketRepository()
comentario_repository = DjangoComentarioRepository()

empresas = EmpresaUseCases(empresa_repository)
categorias = CategoriaUseCases(categoria_repository)
tecnicos = TecnicoUseCases(tecnico_repository)
tickets = TicketUseCases(ticket_repository, empresa_repository, tecnico_repository, comentario_repository)
comentarios = ComentarioUseCases(comentario_repository, ticket_repository)


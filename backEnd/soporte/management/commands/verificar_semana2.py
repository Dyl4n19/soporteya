from uuid import uuid4

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError, transaction

from soporte.application.exceptions import NotFoundError
from soporte.container import categorias, comentario_repository, empresas, tecnicos, ticket_repository
from soporte.domain.entities import Categoria, Comentario, Empresa, Tecnico, Ticket


class Command(BaseCommand):
    help = "Verifica la estructura de semana 2 y consulta las cinco tablas sin modificar datos"

    def add_arguments(self, parser):
        parser.add_argument("--crud", action="store_true",
                            help="Prueba los tres CRUD con registros temporales y revierte la transacción")

    def handle(self, *args, **options):
        self.stdout.write(f"Base de negocio: {settings.BUSINESS_DB_ENGINE}")
        masters = [("EMPRESAS", empresas, Empresa), ("CATEGORIAS_TICKET", categorias, Categoria),
                   ("TECNICOS", tecnicos, Tecnico)]
        try:
            for name, use_cases, entity_type in masters:
                for operation in ("listar", "obtener", "crear", "actualizar", "eliminar"):
                    if not callable(getattr(use_cases, operation, None)):
                        raise CommandError(f"Falta el caso de uso {operation} de {name}")
                rows = use_cases.listar()
                self.check_entities(name, rows, entity_type)
            tickets = ticket_repository.list()
            self.check_entities("TICKETS", tickets, Ticket)
            comments = [comment for ticket in tickets
                        for comment in comentario_repository.for_ticket(ticket.id_ticket)]
            self.check_entities("COMENTARIOS_TICKET", comments, Comentario)
            if options["crud"]:
                self.check_crud()
        except DatabaseError as exc:
            raise CommandError("No se pudo consultar la base de negocio. Revise la conexión y las tablas.") from exc
        self.stdout.write(self.style.SUCCESS("Semana 2: cinco tablas consultadas y tres CRUD conectados a casos de uso."))
        self.stdout.write("Para comprobar escrituras, duplicados, eliminaciones y permisos: python -m pytest -q")

    def check_entities(self, name, rows, entity_type):
        if not all(isinstance(row, entity_type) for row in rows):
            raise CommandError(f"El repositorio de {name} no devuelve entidades de dominio")
        self.stdout.write(self.style.SUCCESS(f"OK {name}: {len(rows)} registros; entidad {entity_type.__name__}"))

    def check_crud(self):
        token = uuid4().hex[:12]
        number = f"{uuid4().int % 1000000:06d}"
        samples = [
            ("EMPRESAS", empresas, "id_empresa", {
                "rut": f"90.{number[:3]}.{number[3:]}-1", "razon_social": f"S2 {token}",
                "plan": "BASICO", "activo": True,
            }, {"razon_social": f"S2 editada {token}"}),
            ("CATEGORIAS_TICKET", categorias, "id_categoria", {
                "nombre": f"S2 {token}", "horas_sla": 4, "activo": True,
            }, {"horas_sla": 8}),
            ("TECNICOS", tecnicos, "id_tecnico", {
                "rut": f"91.{number[:3]}.{number[3:]}-1", "nombre": f"S2 {token}",
                "email": f"s2-{token}@example.invalid", "activo": True,
            }, {"nombre": f"S2 editado {token}"}),
        ]
        with transaction.atomic(using="negocio"):
            for name, use_cases, id_field, data, changes in samples:
                entity = use_cases.crear(data)
                pk = getattr(entity, id_field)
                if use_cases.obtener(pk) != entity:
                    raise CommandError(f"No se pudo recuperar el registro temporal de {name}")
                updated = use_cases.actualizar(pk, changes)
                if any(getattr(updated, field) != value for field, value in changes.items()):
                    raise CommandError(f"No se pudo actualizar el registro temporal de {name}")
                use_cases.eliminar(pk)
                try:
                    use_cases.obtener(pk)
                except NotFoundError:
                    self.stdout.write(self.style.SUCCESS(f"OK CRUD {name}: crear, obtener, actualizar y eliminar"))
                else:
                    raise CommandError(f"No se pudo eliminar el registro temporal de {name}")
            transaction.set_rollback(True, using="negocio")
        self.stdout.write("Prueba CRUD terminada con transacción revertida y registros existentes conservados.")

from datetime import timedelta
from unittest.mock import patch
from uuid import uuid4

from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from soporte.application.exceptions import BusinessError, NotFoundError, RuleViolationError
from soporte.container import categorias, comentario_repository, comentarios, empresas, tecnicos, tickets


class Command(BaseCommand):
    help = "Verifica roles y semana 3; --crud demuestra operaciones y rollback con datos temporales"

    def add_arguments(self, parser):
        parser.add_argument("--crud", action="store_true")

    def handle(self, *args, **options):
        if not User.objects.filter(is_superuser=True, is_active=True).exists():
            raise CommandError("Falta un superusuario. Ejecute python manage.py setup_demo")
        for role in ("SUPERVISOR", "TECNICO"):
            group = Group.objects.filter(name=role).first()
            if not group or not group.permissions.exists() or not group.user_set.filter(is_active=True).exists():
                raise CommandError(f"El rol {role} no está preparado. Ejecute python manage.py setup_demo")
            self.stdout.write(self.style.SUCCESS(f"OK rol {role}: permisos y usuario activo"))
        call_command("verificar_semana2", crud=options["crud"], stdout=self.stdout)
        if options["crud"]:
            self.check_ticket_and_details()
        self.stdout.write(self.style.SUCCESS("Semana 3 verificada. Para sesiones, CSRF, admin y permisos: python -m pytest -q"))

    def reject(self, label, operation):
        try:
            operation()
        except BusinessError:
            self.stdout.write(self.style.SUCCESS(f"OK rechazo: {label}"))
        else:
            raise CommandError(f"Se aceptó una operación que debía rechazarse: {label}")

    def check_ticket_and_details(self):
        token = uuid4().hex[:10]
        number = f"{uuid4().int % 1000000:06d}"
        before = len(tickets.listar())
        with transaction.atomic(using="negocio"):
            company = empresas.crear({"rut": f"92.{number[:3]}.{number[3:]}-1",
                                      "razon_social": f"Validacion S3 {token}", "plan": "PREMIUM"})
            category = categorias.crear({"nombre": f"Validacion S3 {token}", "horas_sla": 4})
            technician = tecnicos.crear({"rut": f"93.{number[:3]}.{number[3:]}-1", "nombre": "Tecnico validacion S3",
                                       "email": f"s3-{token}@example.invalid", "activo": True})
            data = {"empresa_id": company.id_empresa, "categoria_id": category.id_categoria, "tecnico_id": None,
                    "titulo": f"Validacion transaccional S3 {token}", "descripcion": "Registro temporal para verificar semana 3",
                    "prioridad": "BAJA", "comentarios": [{"texto": "Solicitud recibida"}, {"texto": "Diagnostico inicial"}]}
            ticket = tickets.crear(data, "Verificacion S3")
            pk = ticket.id_ticket
            if ticket.prioridad != "ALTA" or len(comentarios.listar(pk)) != 2:
                raise CommandError("Falló la creación principal con detalle o la regla R2")
            self.stdout.write(self.style.SUCCESS("OK ticket con dos comentarios en una transacción; R2 aplica ALTA"))
            self.reject("R2: rebajar prioridad PREMIUM", lambda: tickets.actualizar(pk, {"prioridad": "BAJA"}))
            comentarios.actualizar(pk, 1, "Diagnostico actualizado")
            comentarios.eliminar(pk, 2)
            if comentarios.obtener(pk, 1).texto != "Diagnostico actualizado":
                raise CommandError("Falló el CRUD de comentarios")
            self.stdout.write(self.style.SUCCESS("OK CRUD comentarios con clave ticket + número"))
            self.reject("R1: asignar sin técnico", lambda: tickets.cambiar_estado(pk, "ASIGNADO"))
            tecnicos.actualizar(technician.id_tecnico, {"activo": False})
            self.reject("R1: técnico inactivo", lambda: tickets.actualizar(pk, {"tecnico_id": technician.id_tecnico}))
            tecnicos.actualizar(technician.id_tecnico, {"activo": True})
            if not tickets.esta_vencido(ticket, 4, ticket.fecha_creacion + timedelta(hours=5)):
                raise CommandError("Falló la regla R3")
            if tickets.esta_vencido(ticket, 4, ticket.fecha_creacion + timedelta(hours=4)):
                raise CommandError("La regla R3 marcó vencido antes de superar el SLA")
            self.stdout.write(self.style.SUCCESS("OK R3: cálculo del SLA en el caso de uso"))
            without_details = tickets.crear(data | {"tecnico_id": technician.id_tecnico, "comentarios": []}, "Verificacion S3")
            tickets.cambiar_estado(without_details.id_ticket, "EN_PROGRESO")
            self.reject("R1: resolver sin comentarios", lambda: tickets.cambiar_estado(without_details.id_ticket, "RESUELTO"))
            self.reject("eliminar fuera del estado inicial", lambda: tickets.eliminar(without_details.id_ticket))
            tickets.actualizar(pk, {"titulo": f"Ticket editado {token}", "tecnico_id": technician.id_tecnico})
            for state in ("EN_PROGRESO", "RESUELTO", "EN_PROGRESO", "RESUELTO", "CERRADO"):
                tickets.cambiar_estado(pk, state)
            self.reject("reabrir un ticket cerrado", lambda: tickets.cambiar_estado(pk, "EN_PROGRESO"))
            tickets.reporte()
            disposable = tickets.crear(data, "Verificacion S3")
            tickets.eliminar(disposable.id_ticket)
            try:
                comentarios.obtener(disposable.id_ticket, 1)
            except NotFoundError:
                self.stdout.write(self.style.SUCCESS("OK eliminación de ticket abierto y su detalle"))
            else:
                raise CommandError("Quedaron detalles de un ticket eliminado")
            count = len(tickets.listar())
            original = comentario_repository.add
            calls = []

            def fail_second(*args):
                calls.append(args)
                if len(calls) == 2:
                    raise RuleViolationError("Fallo controlado en el segundo comentario")
                return original(*args)

            with patch.object(comentario_repository, "add", side_effect=fail_second):
                self.reject("fallo en segunda línea", lambda: tickets.crear(data, "Verificacion S3"))
            if len(calls) != 2 or len(tickets.listar()) != count:
                raise CommandError("Falló la reversión del registro principal")
            self.stdout.write(self.style.SUCCESS("OK rollback: no queda ticket parcial al fallar su segundo comentario"))
            transaction.set_rollback(True, using="negocio")
        if len(tickets.listar()) != before:
            raise CommandError("No se conservaron los registros originales")
        self.stdout.write(self.style.SUCCESS("Verificación transaccional terminada; datos temporales revertidos."))

import json
from datetime import datetime, timezone

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import connections, router

from soporte.infrastructure.models import CategoriaModel, ComentarioModel, EmpresaModel, TecnicoModel, TicketModel


class Command(BaseCommand):
    help = "Consulta el esquema Oracle propio y verifica configuración de semana 1 sin modificar datos"

    def add_arguments(self, parser):
        parser.add_argument("--json", action="store_true")

    def handle(self, *args, **options):
        if connections["negocio"].vendor != "oracle":
            raise CommandError("Esta comprobación requiere BUSINESS_DB_ENGINE=oracle")
        models = [CategoriaModel, ComentarioModel, EmpresaModel, TecnicoModel, TicketModel]
        names = [model._meta.db_table for model in models]
        placeholders = ", ".join(["%s"] * len(names))
        with connections["negocio"].cursor() as cursor:
            cursor.execute(f"SELECT table_name FROM user_tables WHERE table_name IN ({placeholders}) ORDER BY table_name", names)
            tables = [row[0] for row in cursor.fetchall()]
            cursor.execute(f"SELECT constraint_type, COUNT(*) FROM user_constraints WHERE table_name IN ({placeholders}) "
                           "AND (constraint_type <> 'C' OR constraint_name LIKE 'CK_%%') GROUP BY constraint_type", names)
            constraints = dict(cursor.fetchall())
            cursor.execute("SELECT column_name FROM user_cons_columns WHERE constraint_name = %s ORDER BY position",
                           ["PK_COMENTARIOS_TICKET"])
            detail_key = [row[0] for row in cursor.fetchall()]
            cursor.execute("SELECT CASE WHEN SYS_CONTEXT('USERENV','SESSION_USER') = "
                           "SYS_CONTEXT('USERENV','CURRENT_SCHEMA') THEN 1 ELSE 0 END FROM dual")
            own_schema = bool(cursor.fetchone()[0])
        if set(tables) != set(names) or not own_schema:
            raise CommandError("No se encontraron las cinco tablas en el esquema personal")
        if detail_key != ["ID_TICKET", "NUMERO"]:
            raise CommandError("La clave del detalle no coincide con el modelo")
        if router.db_for_read(EmpresaModel) != "negocio" or router.db_for_read(User) != "default":
            raise CommandError("El router no está separando las bases correctamente")
        report = {
            "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "database": "Oracle FreeSQL", "own_schema": own_schema,
            "tables": [{"name": name, "rows": next(model.objects.count() for model in models
                        if model._meta.db_table == name)} for name in tables],
            "constraints": constraints, "detail_primary_key": detail_key,
            "business_route": router.db_for_read(EmpresaModel), "auth_route": router.db_for_read(User),
            "read_only": True,
        }
        if options["json"]:
            self.stdout.write(json.dumps(report, ensure_ascii=False, indent=2))
            return
        for row in report["tables"]:
            self.stdout.write(self.style.SUCCESS(f"OK {row['name']}: {row['rows']} registros en el esquema propio"))
        self.stdout.write(f"PK: {constraints.get('P', 0)}; FK: {constraints.get('R', 0)}; "
                          f"UNIQUE: {constraints.get('U', 0)}; CHECK explícitos: {constraints.get('C', 0)}")
        self.stdout.write("PK detalle: ID_TICKET + NUMERO; SQLite para Django y Oracle para negocio.")
        self.stdout.write(self.style.SUCCESS("Conexión y estructura de semana 1 verificadas por consultas de solo lectura."))
        self.stdout.write("La inscripción, sección y número de grupo se confirman con el docente en el Anexo A.")

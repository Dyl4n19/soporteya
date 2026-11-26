import subprocess
import sys
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Comprueba la API REST; --postman ejecuta la colección completa con bases de prueba aisladas"

    def add_arguments(self, parser):
        parser.add_argument("--postman", action="store_true")
        parser.add_argument("--evidencia", type=Path)

    def handle(self, *args, **options):
        if options["evidencia"] and not options["postman"]:
            raise CommandError("--evidencia requiere --postman")
        command = [sys.executable, "-m", "pytest", "-q", "-c", str(settings.BASE_DIR / "pytest.ini"),
                   "--ds=soporteya_project.test_settings"]
        if options["postman"]:
            command.append("--postman")
        if options["evidencia"]:
            command.append(f"--api-evidence={options['evidencia'].resolve()}")
        self.stdout.write("Verificando API, CORS, serializers, rutas, permisos, consultas y reporte.")
        self.stdout.write("Las dos bases de prueba son temporales; Oracle y las bases locales se conservan.")
        self.stdout.flush()
        result = subprocess.run(command, cwd=settings.BASE_DIR)
        if result.returncode:
            raise CommandError("Falló la verificación de semana 5")
        self.stdout.write(self.style.SUCCESS("Semana 5 verificada correctamente."))

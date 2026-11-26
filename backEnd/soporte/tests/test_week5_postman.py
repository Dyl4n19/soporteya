import json
import shutil
import subprocess
from datetime import datetime, timedelta, timezone
from io import StringIO
from pathlib import Path

import pytest
from django.core.management import call_command

from soporte.infrastructure.models import CategoriaModel, EmpresaModel, TecnicoModel, TicketModel


@pytest.mark.postman
@pytest.mark.django_db(transaction=True, databases=["default", "negocio"])
def test_coleccion_postman_por_http_con_cookie_y_csrf(request, live_server, tmp_path):
    if not request.config.getoption("--postman"):
        pytest.skip("Usar python manage.py verificar_semana5 --postman")
    runner = shutil.which("pnpm")
    assert runner, "Instalar pnpm y Node.js para ejecutar Newman"
    call_command("setup_demo", stdout=StringIO())
    TecnicoModel.objects.create(rut="15.111.111-1", nombre="Camila Rojas", email="camila.rojas@soporteya.cl")
    company = EmpresaModel.objects.create(rut="81.111.111-1", razon_social="Fixture SLA", plan="BASICO")
    category = CategoriaModel.objects.create(nombre="Fixture SLA", horas_sla=4)
    overdue = TicketModel.objects.create(empresa=company, categoria=category, titulo="Ticket vencido de prueba",
                                       descripcion="Incidente antiguo para probar R3", prioridad="MEDIA")
    TicketModel.objects.filter(pk=overdue.pk).update(fecha_creacion=datetime.now(timezone.utc) - timedelta(hours=5))
    project = Path(__file__).resolve().parents[3]
    full_report = tmp_path / "newman.json"
    command = [runner, "dlx", "newman@6.2.1", "run", str(project / "docs" / "postman_collection.json"),
               "--env-var", f"baseUrl={live_server.url}/api", "--env-var", f"fixtureVencidoId={overdue.pk}",
               "--reporters", "json", "--reporter-json-export", str(full_report),
               "--timeout-request", "10000", "--timeout-script", "10000"]
    completed = subprocess.run(command, cwd=project, capture_output=True, text=True, encoding="utf-8",
                               errors="replace", timeout=180)
    assert full_report.exists(), f"Newman no generó el informe: {completed.stderr[-1000:]}"
    report = json.loads(full_report.read_text(encoding="utf-8"))
    run = report["run"]
    failures = [{"request": failure.get("source", {}).get("name", ""),
                 "test": failure.get("error", {}).get("test", failure.get("error", {}).get("name", ""))}
                for failure in run["failures"]]
    assert not failures, json.dumps(failures, ensure_ascii=False)
    assert completed.returncode == 0
    assert run["stats"]["requests"]["total"] == 95
    assert run["stats"]["assertions"]["total"] > 250
    evidence = request.config.getoption("--api-evidence")
    if evidence:
        destination = Path(evidence).resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)
        summary = {
            "fecha_utc": datetime.now(timezone.utc).isoformat(),
            "herramienta": "Newman 6.2.1",
            "coleccion": "docs/postman_collection.json",
            "entorno": "Servidor Django real por HTTP; dos bases SQLite de prueba en memoria",
            "base_real_modificada": False,
            "solicitudes": run["stats"]["requests"],
            "aserciones": run["stats"]["assertions"],
            "fallos": failures,
            "duracion_ms": run["timings"]["completed"] - run["timings"]["started"],
            "resultados": [{"nombre": execution["item"]["name"], "metodo": execution["request"]["method"],
                            "codigo_http": execution.get("response", {}).get("code"),
                            "pruebas": [assertion["assertion"] for assertion in execution.get("assertions", [])]}
                           for execution in run["executions"]],
        }
        destination.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

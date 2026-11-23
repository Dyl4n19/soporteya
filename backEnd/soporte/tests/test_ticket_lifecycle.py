from datetime import timedelta

import pytest
from django.utils import timezone

from soporte.container import comentario_repository, ticket_repository
from soporte.domain.entities import Comentario, Ticket
from soporte.infrastructure.models import CategoriaModel, EmpresaModel, TecnicoModel, TicketModel


pytestmark = pytest.mark.django_db(databases=["default", "negocio"])


@pytest.fixture
def ticket_data():
    empresa = EmpresaModel.objects.create(rut="76.123.456-1", razon_social="Empresa", plan="BASICO")
    categoria = CategoriaModel.objects.create(nombre="Red", horas_sla=4)
    tecnico = TecnicoModel.objects.create(rut="15.123.456-1", nombre="Tecnico", email="tecnico@test.cl")
    return {"empresa_id": empresa.pk, "categoria_id": categoria.pk, "tecnico_id": tecnico.pk,
            "titulo": "Sin conexion de red", "descripcion": "La oficina esta sin conexion", "prioridad": "MEDIA"}


def test_ciclo_de_ticket_comentarios_y_cierre(api, ticket_data):
    response = api.post("/api/tickets/", ticket_data, format="json")
    assert response.status_code == 201
    assert response.data["estado"] == "ASIGNADO"
    pk = response.data["id_ticket"]
    assert isinstance(ticket_repository.get(pk), Ticket)
    url = f"/api/tickets/{pk}/"
    assert api.post(f"{url}estado/", {"estado": "CERRADO"}, format="json").status_code == 409
    assert api.post(f"{url}estado/", {"estado": "EN_PROGRESO"}, format="json").status_code == 200
    response = api.post(f"{url}estado/", {"estado": "RESUELTO"}, format="json")
    assert response.status_code == 409
    assert response.data["message"] == "Debe existir al menos un comentario antes de resolver"
    assert TicketModel.objects.get(pk=pk).estado == "EN_PROGRESO"
    for number in (1, 2):
        response = api.post(f"{url}comentarios/", {"texto": f"Revision tecnica {number}"}, format="json")
        assert response.status_code == 201
        assert response.data["numero"] == number
    assert all(isinstance(row, Comentario) for row in comentario_repository.for_ticket(pk))
    assert api.post(f"{url}estado/", {"estado": "RESUELTO"}, format="json").status_code == 200
    response = api.post(f"{url}estado/", {"estado": "CERRADO"}, format="json")
    assert response.status_code == 200
    assert response.data["fecha_cierre"] is not None
    assert api.post(f"{url}comentarios/", {"texto": "Otro comentario"}, format="json").status_code == 409
    assert api.delete(url).status_code == 409


def test_solo_elimina_ticket_abierto(api, ticket_data):
    ticket_data["tecnico_id"] = None
    response = api.post("/api/tickets/", ticket_data, format="json")
    pk = response.data["id_ticket"]
    assert api.delete(f"/api/tickets/{pk}/").status_code == 204
    assert not TicketModel.objects.filter(pk=pk).exists()


def test_categoria_inexistente_se_informa_sin_crear_ticket(api, ticket_data):
    response = api.post("/api/tickets/", ticket_data | {"categoria_id": 99999}, format="json")
    assert response.status_code == 404
    assert TicketModel.objects.count() == 0


def test_reporte_identifica_vencidos_y_promedio_de_cierre(api, ticket_data):
    created = api.post("/api/tickets/", ticket_data, format="json")
    late_id = created.data["id_ticket"]
    created = api.post("/api/tickets/", ticket_data | {"titulo": "Caso resuelto"}, format="json")
    closed_id = created.data["id_ticket"]
    now = timezone.now()
    TicketModel.objects.filter(pk=late_id).update(fecha_creacion=now - timedelta(hours=5))
    TicketModel.objects.filter(pk=closed_id).update(estado="CERRADO", fecha_creacion=now - timedelta(hours=3),
                                                   fecha_cierre=now - timedelta(hours=1))
    response = api.get("/api/reportes/soporte/")
    assert response.status_code == 200
    assert [row["id_ticket"] for row in response.data["tickets_vencidos"]] == [late_id]
    assert response.data["tickets_vencidos"][0]["empresa"] == "Empresa"
    assert response.data["tickets_vencidos"][0]["horas_sla"] == 4
    assert response.data["promedio_resolucion_por_tecnico"] == [
        {"id_tecnico": ticket_data["tecnico_id"], "tecnico": "Tecnico", "horas_promedio": 2.0},
    ]

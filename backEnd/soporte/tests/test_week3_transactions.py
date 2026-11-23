from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from soporte.application.exceptions import RuleViolationError
from soporte.application.use_cases.ticket_use_cases import TicketUseCases
from soporte.container import comentario_repository, tickets
from soporte.domain.entities import Ticket
from soporte.infrastructure.models import ComentarioModel, EmpresaModel, TecnicoModel, TicketModel


pytestmark = pytest.mark.django_db(databases=["default", "negocio"])


def test_crea_ticket_con_dos_comentarios_en_una_operacion(api, business_data):
    response = api.post("/api/tickets/", business_data | {"comentarios": [
        {"texto": "Se recibe la solicitud"}, {"texto": "Se revisa el equipo afectado"},
    ]}, format="json")
    assert response.status_code == 201
    assert TicketModel.objects.count() == 1
    assert ComentarioModel.objects.count() == 2
    assert [row["numero"] for row in response.data["comentarios"]] == [1, 2]
    assert {row["autor"] for row in response.data["comentarios"]} == {"supervisor"}
    assert all(row["id_ticket"] == response.data["id_ticket"] for row in response.data["comentarios"])


def test_si_falla_segundo_detalle_se_revierten_ticket_y_primer_detalle(api, business_data):
    original_add = comentario_repository.add
    calls = []

    def fail_second(*args):
        calls.append(args)
        if len(calls) == 2:
            raise RuleViolationError("Fallo controlado del segundo detalle", "comentarios")
        return original_add(*args)

    with patch.object(comentario_repository, "add", side_effect=fail_second):
        response = api.post("/api/tickets/", business_data | {"comentarios": [
            {"texto": "Primer comentario"}, {"texto": "Segundo comentario"},
        ]}, format="json")
    assert response.status_code == 409
    assert len(calls) == 2
    assert TicketModel.objects.count() == 0
    assert ComentarioModel.objects.count() == 0


def test_actualizacion_con_transicion_invalida_revierte_cabecera_y_detalle(api, business_data):
    created = api.post("/api/tickets/", business_data | {"tecnico_id": None}, format="json")
    pk = created.data["id_ticket"]
    response = api.patch(f"/api/tickets/{pk}/", {
        "titulo": "Titulo que no debe guardarse", "estado": "CERRADO",
        "comentarios": [{"texto": "Detalle que tampoco debe guardarse"}],
    }, format="json")
    assert response.status_code == 409
    stored = TicketModel.objects.get(pk=pk)
    assert stored.titulo == business_data["titulo"]
    assert stored.estado == "ABIERTO"
    assert stored.comentarios.count() == 0


def test_crud_de_ticket_abierto_y_eliminacion_de_su_detalle(api, business_data):
    data = business_data | {"tecnico_id": None, "comentarios": [{"texto": "Comentario inicial"}]}
    response = api.post("/api/tickets/", data, format="json")
    pk = response.data["id_ticket"]
    url = f"/api/tickets/{pk}/"
    assert api.get(url).status_code == 200
    assert api.get("/api/tickets/").data["count"] == 1
    response = api.put(url, business_data | {"tecnico_id": None, "titulo": "Ticket actualizado"}, format="json")
    assert response.status_code == 200
    assert response.data["titulo"] == "Ticket actualizado"
    assert api.delete(url).status_code == 204
    assert TicketModel.objects.count() == 0
    assert ComentarioModel.objects.count() == 0
    assert api.get(url).status_code == 404


def test_asignacion_activa_y_reapertura_sin_saltar_estados(api, business_data):
    response = api.post("/api/tickets/", business_data | {
        "tecnico_id": None, "comentarios": [{"texto": "Se recibe el caso"}],
    }, format="json")
    url = f"/api/tickets/{response.data['id_ticket']}/"
    assert api.patch(url, {"estado": "ASIGNADO"}, format="json").status_code == 409
    response = api.patch(url, {"tecnico_id": business_data["tecnico_id"], "estado": "ASIGNADO"}, format="json")
    assert response.status_code == 200
    for state in ["EN_PROGRESO", "RESUELTO", "EN_PROGRESO", "RESUELTO", "CERRADO"]:
        response = api.patch(url, {"estado": state}, format="json")
        assert response.status_code == 200
        assert response.data["estado"] == state
        assert bool(response.data["fecha_cierre"]) == (state == "CERRADO")
    assert api.patch(url, {"estado": "EN_PROGRESO"}, format="json").status_code == 409
    assert api.patch(url, {"titulo": "No editable cerrado"}, format="json").status_code == 409


def test_r1_no_asigna_tecnico_que_paso_a_inactivo(api, business_data):
    response = api.post("/api/tickets/", business_data | {"tecnico_id": None}, format="json")
    pk = response.data["id_ticket"]
    TecnicoModel.objects.filter(pk=business_data["tecnico_id"]).update(activo=False)
    response = api.patch(f"/api/tickets/{pk}/", {"tecnico_id": business_data["tecnico_id"]}, format="json")
    assert response.status_code == 409
    assert response.data["field"] == "tecnico_id"
    assert TicketModel.objects.get(pk=pk).tecnico_id is None


def test_r2_no_permite_bajar_prioridad_de_ticket_premium(api, business_data):
    EmpresaModel.objects.filter(pk=business_data["empresa_id"]).update(plan="PREMIUM")
    response = api.post("/api/tickets/", business_data | {"tecnico_id": None, "prioridad": "BAJA"}, format="json")
    assert response.status_code == 201
    assert response.data["prioridad"] == "ALTA"
    pk = response.data["id_ticket"]
    response = api.patch(f"/api/tickets/{pk}/", {"prioridad": "MEDIA"}, format="json")
    assert response.status_code == 409
    assert response.data["field"] == "prioridad"
    assert TicketModel.objects.get(pk=pk).prioridad == "ALTA"


@pytest.mark.parametrize("state", ["ABIERTO", "ASIGNADO", "EN_PROGRESO", "RESUELTO", "CERRADO"])
@pytest.mark.parametrize("seconds", [14399, 14400, 14401])
def test_r3_solo_vencido_despues_del_limite_y_sin_resolver(state, seconds):
    now = datetime(2026, 11, 23, 12, tzinfo=timezone.utc)
    ticket = Ticket(1, 1, 1, "Falla de red", "Falla en la oficina", "MEDIA", estado=state,
                    fecha_creacion=now - timedelta(seconds=seconds))
    expected = seconds > 14400 and state not in {"RESUELTO", "CERRADO"}
    assert TicketUseCases.esta_vencido(ticket, 4, now) is expected


def test_crud_completo_de_comentarios_con_identidad_compuesta(api, business_data):
    first = api.post("/api/tickets/", business_data | {"tecnico_id": None}, format="json")
    second = api.post("/api/tickets/", business_data | {"tecnico_id": None}, format="json")
    first_id, second_id = first.data["id_ticket"], second.data["id_ticket"]
    url = f"/api/tickets/{first_id}/comentarios/"
    assert api.post(url, {"texto": "Texto original"}, format="json").status_code == 201
    assert api.post(f"/api/tickets/{second_id}/comentarios/", {"texto": "Otro ticket"}, format="json").status_code == 201
    assert len(api.get(url).data) == 1
    original = api.get(f"{url}1/").data
    assert original["id_ticket"] == first_id
    for method in ("put", "patch"):
        response = getattr(api, method)(f"{url}1/", {"texto": f"Editado con {method}"}, format="json")
        assert response.status_code == 200
        assert response.data["autor"] == original["autor"]
        assert response.data["fecha"] == original["fecha"]
    assert api.get(f"/api/tickets/{second_id}/comentarios/1/").data["texto"] == "Otro ticket"
    assert api.delete(f"{url}1/").status_code == 204
    assert api.get(f"{url}1/").status_code == 404
    assert ComentarioModel.objects.filter(ticket_id=second_id).count() == 1


def test_no_borra_ultimo_comentario_resuelto_y_cerrado_no_se_modifica(api, business_data):
    created = api.post("/api/tickets/", business_data | {"comentarios": [{"texto": "Reparacion realizada"}]}, format="json")
    url = f"/api/tickets/{created.data['id_ticket']}/"
    for state in ("EN_PROGRESO", "RESUELTO"):
        assert api.patch(url, {"estado": state}, format="json").status_code == 200
    assert api.delete(f"{url}comentarios/1/").status_code == 409
    assert api.patch(url, {"estado": "CERRADO"}, format="json").status_code == 200
    assert api.post(f"{url}comentarios/", {"texto": "No debe agregarse"}, format="json").status_code == 409
    assert api.put(f"{url}comentarios/1/", {"texto": "No debe editarse"}, format="json").status_code == 409
    assert api.delete(f"{url}comentarios/1/").status_code == 409


def test_detalle_invalido_y_recurso_inexistente_no_producen_500(api, business_data):
    response = api.post("/api/tickets/", business_data | {"comentarios": [{"texto": "x"}]}, format="json")
    assert response.status_code == 400
    assert TicketModel.objects.count() == 0
    assert api.get("/api/tickets/99999/comentarios/").status_code == 404
    assert api.patch("/api/tickets/99999/", {"estado": "RESUELTO"}, format="json").status_code == 404


def test_promedio_agrupa_cierres_por_tecnico_y_excluye_abiertos(api, business_data):
    now = datetime.now(timezone.utc)
    other = TecnicoModel.objects.create(rut="16.000.001-1", nombre="Otro tecnico", email="otro@test.cl")
    for technician_id, hours in [(business_data["tecnico_id"], 1), (business_data["tecnico_id"], 3), (other.pk, 6)]:
        ticket = TicketModel.objects.create(empresa_id=business_data["empresa_id"], categoria_id=business_data["categoria_id"],
                                           tecnico_id=technician_id, titulo="Caso para promedio", descripcion="Caso finalizado")
        TicketModel.objects.filter(pk=ticket.pk).update(estado="CERRADO", fecha_creacion=now - timedelta(hours=hours), fecha_cierre=now)
    assert api.post("/api/tickets/", business_data, format="json").status_code == 201
    response = api.get("/api/reportes/soporte/")
    assert response.status_code == 200
    averages = {row["id_tecnico"]: row["horas_promedio"] for row in response.data["promedio_resolucion_por_tecnico"]}
    assert averages == {business_data["tecnico_id"]: 2.0, other.pk: 6.0}

import json
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.conf import settings
from django.utils import timezone
from rest_framework.test import APIClient

from soporte.container import tickets
from soporte.infrastructure.models import ComentarioModel, EmpresaModel, TecnicoModel, TicketModel


pytestmark = pytest.mark.django_db(databases=["default", "negocio"])


def assert_error(response, code, field=None):
    assert response.status_code == code
    assert response["Content-Type"].startswith("application/json")
    assert set(response.json()) == {"message", "field"}
    assert isinstance(response.json()["message"], str)
    assert response.json()["message"]
    assert response.json()["field"] == field


def test_cors_permite_origen_frontend_con_cookie_y_preflight():
    client = APIClient()
    origin = settings.CORS_ALLOWED_ORIGINS[0]
    response = client.options("/api/tickets/", HTTP_ORIGIN=origin,
                              HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
                              HTTP_ACCESS_CONTROL_REQUEST_HEADERS="content-type,x-csrftoken")
    assert response.status_code == 200
    assert response["Access-Control-Allow-Origin"] == origin
    assert response["Access-Control-Allow-Credentials"] == "true"
    assert "POST" in response["Access-Control-Allow-Methods"]
    assert "x-csrftoken" in response["Access-Control-Allow-Headers"]
    response = client.get("/api/tickets/", HTTP_ORIGIN=origin)
    assert_error(response, 401)
    assert response["Access-Control-Allow-Origin"] == origin


def test_cors_no_habilita_origen_ajeno_ni_administrador():
    client = APIClient()
    response = client.options("/api/tickets/", HTTP_ORIGIN="https://ajeno.example",
                              HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST")
    assert "Access-Control-Allow-Origin" not in response
    response = client.get("/admin/login/", HTTP_ORIGIN=settings.CORS_ALLOWED_ORIGINS[0])
    assert "Access-Control-Allow-Origin" not in response


@pytest.mark.parametrize("method,path", [
    ("get", "/api/ruta-inexistente/"), ("post", "/api/tickets"),
    ("get", "/api/tickets/1/comentarios/no-numerico/"),
])
def test_rutas_inexistentes_siempre_entregan_json(method, path):
    assert_error(getattr(APIClient(enforce_csrf_checks=True), method)(path), 404)


def test_metodo_formato_y_json_invalidos(api):
    assert_error(api.post("/api/auth/me/", {}, format="json"), 405)
    assert_error(api.post("/api/categorias/", "{", content_type="application/json"), 400)
    assert_error(api.post("/api/categorias/", "texto", content_type="text/plain"), 415)
    assert_error(api.get("/api/tickets/", HTTP_ACCEPT="text/html"), 406)


@pytest.mark.parametrize("payload", [[], [1], "texto", 25, None])
def test_login_rechaza_cuerpos_que_no_son_objetos(payload):
    client = APIClient(enforce_csrf_checks=True)
    csrf = client.get("/api/auth/csrf/").data["csrfToken"]
    response = client.post("/api/auth/login/", json.dumps(payload), content_type="application/json",
                           HTTP_X_CSRFTOKEN=csrf)
    assert_error(response, 400)


@pytest.mark.parametrize("method", ["put", "patch"])
def test_ticket_rechaza_lista_en_actualizacion(api, business_data, method):
    pk = api.post("/api/tickets/", business_data, format="json").data["id_ticket"]
    response = getattr(api, method)(f"/api/tickets/{pk}/", [{"estado": "EN_PROGRESO"}], format="json")
    assert_error(response, 400)


def test_campos_desconocidos_y_autor_no_pueden_escribirse(api, business_data):
    response = api.post("/api/empresas/", {"rut": "84.444.444-4", "razon_social": "Empresa",
                        "plan": "BASICO", "id_empresa": 999}, format="json")
    assert_error(response, 400, "id_empresa")
    assert not EmpresaModel.objects.filter(rut="84.444.444-4").exists()
    response = api.post("/api/tickets/", business_data | {"comentarios": [
        {"texto": "Comentario valido"}, {"texto": "Otro comentario", "autor": "suplantado"},
    ]}, format="json")
    assert_error(response, 400, "comentarios.1.autor")
    assert TicketModel.objects.count() == 0
    assert ComentarioModel.objects.count() == 0


def test_error_de_detalle_indica_indice_y_campo_y_no_guarda_ticket(api, business_data):
    response = api.post("/api/tickets/", business_data | {"comentarios": [
        {"texto": "Comentario valido"}, {"texto": "x"},
    ]}, format="json")
    assert_error(response, 400, "comentarios.1.texto")
    assert "{" not in response.data["message"]
    assert TicketModel.objects.count() == 0


@pytest.mark.parametrize("resource,model,fields", [
    ("empresas", EmpresaModel, {"razon_social": "Empresa demo", "plan": "BASICO"}),
    ("tecnicos", TecnicoModel, {"nombre": "Técnico demo", "email": "demo@example.invalid"}),
])
def test_formato_de_rut_y_duplicados_con_distinta_escritura(api, resource, model, fields):
    endpoint = f"/api/{resource}/"
    for invalid in ("sin-formato", "12.34.5678-K", "12345678-X", "123456789-1"):
        assert_error(api.post(endpoint, fields | {"rut": invalid}, format="json"), 400, "rut")
    created = api.post(endpoint, fields | {"rut": "12345670-k"}, format="json")
    assert created.status_code == 201
    assert created.data["rut"] == "12.345.670-K"
    assert_error(api.post(endpoint, fields | {"rut": "12.345.670-K"}, format="json"), 409, "rut")
    model.objects.filter(rut="12.345.670-K").update(rut="12345670-k")
    assert_error(api.post(endpoint, fields | {"rut": "12.345.670-K"}, format="json"), 409, "rut")
    assert model.objects.count() == 1


def test_comentario_sin_texto_en_patch_no_deja_cambios_parciales(api, business_data):
    created = api.post("/api/tickets/", business_data | {"tecnico_id": None}, format="json").data
    url = f"/api/tickets/{created['id_ticket']}/"
    response = api.patch(url, {"titulo": "Cambio sin guardar", "comentarios": [{"texto": "Completo"}, {}]}, format="json")
    assert_error(response, 400, "comentarios.1.texto")
    assert api.get(url).data == created


def test_r3_contraste_de_vencimiento_usa_sla_y_revierte_los_cambios(api, business_data):
    created = api.post("/api/tickets/", business_data | {"tecnico_id": None}, format="json").data
    url = f"/api/tickets/{created['id_ticket']}/"
    assert created["vencido"] is False
    assert_error(api.patch(url, {"titulo": "Cambio sin guardar", "vencido": True}, format="json"), 409, "vencido")
    assert api.get(url).data["titulo"] == created["titulo"]
    TicketModel.objects.filter(pk=created["id_ticket"]).update(fecha_creacion=timezone.now() - timedelta(hours=5))
    assert api.get(url).data["vencido"] is True
    assert_error(api.patch(url, {"vencido": False}, format="json"), 409, "vencido")
    response = api.patch(url, {"tecnico_id": business_data["tecnico_id"], "vencido": True}, format="json")
    assert response.status_code == 200 and response.data["estado"] == "ASIGNADO"
    assert api.patch(url, {"estado": "EN_PROGRESO"}, format="json").status_code == 200
    response = api.patch(url, {"estado": "RESUELTO", "vencido": False, "comentarios": [{"texto": "Resuelto"}]}, format="json")
    assert response.status_code == 200 and response.data["vencido"] is False


def test_comentarios_busqueda_filtros_orden_y_pagina_sin_mezclar_tickets(api, business_data):
    first = api.post("/api/tickets/", business_data, format="json").data["id_ticket"]
    second = api.post("/api/tickets/", business_data, format="json").data["id_ticket"]
    for ticket, number, author, text in [
        (first, 1, "Ana", "Diagnostico de red"), (first, 2, "Ana", "Diagnostico de correo"),
        (first, 3, "Luis", "Diagnostico de red"), (second, 1, "Ana", "Diagnostico de red"),
    ]:
        ComentarioModel.objects.create(ticket_id=ticket, numero=number, autor=author, texto=text)
    url = f"/api/tickets/{first}/comentarios/"
    response = api.get(url, {"search": "diagnostico", "autor": "Ana", "ordering": "-numero",
                             "page_size": 1, "page": 2})
    assert response.status_code == 200
    assert response.data["count"] == 2
    assert response.data["previous"] is not None
    assert response.data["next"] is None
    assert [row["numero"] for row in response.data["results"]] == [1]
    assert all(row["id_ticket"] == first for row in response.data["results"])
    assert [row["numero"] for row in api.get(url, {"search": "red Ana"}).data["results"]] == [1]
    assert api.get(url, {"numero": 3}).data["results"][0]["autor"] == "Luis"
    assert api.get(url, {"ordering": "texto; DROP TABLE COMENTARIO"}).status_code == 200
    assert api.get(url, {"ordering": "--numero"}).status_code == 200
    assert_error(api.get(url, {"numero": "no"}), 400, "numero")


@pytest.mark.parametrize("resource", ["empresas", "categorias", "tecnicos", "tickets", "comentarios"])
@pytest.mark.parametrize("size", ["0", "-1", "101", "abc", "1.5"])
def test_tamanos_de_pagina_invalidos_no_se_ignoran(api, business_data, resource, size):
    url = f"/api/{resource}/"
    if resource == "comentarios":
        pk = api.post("/api/tickets/", business_data, format="json").data["id_ticket"]
        url = f"/api/tickets/{pk}/comentarios/"
    assert_error(api.get(url, {"page_size": size}), 400, "page_size")


def test_tickets_busqueda_filtro_y_pagina_dos_con_detalle_anidado(api, business_data):
    ids = []
    for title in ("Falla correo primera", "Falla correo segunda", "Falla red tercera"):
        response = api.post("/api/tickets/", business_data | {
            "titulo": title, "comentarios": [{"texto": "Diagnostico inicial"}],
        }, format="json")
        ids.append(response.data["id_ticket"])
    response = api.get("/api/tickets/", {"search": "correo", "estado": "ASIGNADO", "prioridad": "MEDIA",
                       "categoria_id": business_data["categoria_id"], "tecnico_id": business_data["tecnico_id"],
                       "ordering": "id_ticket", "page": 2, "page_size": 1})
    assert response.status_code == 200
    assert response.data["count"] == 2
    assert response.data["results"][0]["id_ticket"] == ids[1]
    assert response.data["results"][0]["comentarios"][0]["numero"] == 1
    assert_error(api.get("/api/tickets/", {"page": 99}), 404)
    assert_error(api.get("/api/tickets/", {"estado": "INVENTADO"}), 400, "estado")


def test_reporte_separa_vencidos_y_calcula_promedio_numerico(api, business_data):
    now = timezone.now()
    base = {"empresa_id": business_data["empresa_id"], "categoria_id": business_data["categoria_id"],
            "tecnico_id": business_data["tecnico_id"], "titulo": "Reporte de prueba",
            "descripcion": "Incidente para comprobar reporte", "prioridad": "ALTA"}
    overdue = TicketModel.objects.create(**base, estado="EN_PROGRESO")
    closed = TicketModel.objects.create(**base, estado="CERRADO", fecha_cierre=now - timedelta(hours=1))
    resolved = TicketModel.objects.create(**base, estado="RESUELTO")
    TicketModel.objects.create(**base, estado="ABIERTO")
    TicketModel.objects.filter(pk__in=[overdue.pk, resolved.pk]).update(fecha_creacion=now - timedelta(hours=5))
    TicketModel.objects.filter(pk=closed.pk).update(fecha_creacion=now - timedelta(hours=3))
    response = api.get("/api/reportes/soporte/")
    assert response.status_code == 200
    assert [row["id_ticket"] for row in response.data["tickets_vencidos"]] == [overdue.pk]
    average = response.data["promedio_resolucion_por_tecnico"][0]
    assert average["id_tecnico"] == business_data["tecnico_id"]
    assert average["horas_promedio"] == 2.0
    assert isinstance(response.data["tickets_vencidos"][0]["fecha_creacion"], str)


def test_error_inesperado_entrega_json_sin_detalles_internos(api, caplog):
    with patch.object(tickets, "reporte", side_effect=RuntimeError("detalle interno de prueba")):
        response = api.get("/api/reportes/soporte/")
    assert_error(response, 500)
    assert "detalle interno" not in response.content.decode()
    assert "Error inesperado en la API" in caplog.text

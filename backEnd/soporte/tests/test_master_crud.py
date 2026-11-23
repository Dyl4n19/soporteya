from unittest.mock import patch

import pytest
from django.contrib.auth.models import Group, User
from rest_framework.test import APIClient

from soporte.application.exceptions import RuleViolationError
from soporte.container import categorias, empresas, tecnicos
from soporte.domain.entities import Categoria, Empresa, Tecnico
from soporte.infrastructure.models import CategoriaModel, EmpresaModel, TecnicoModel, TicketModel


pytestmark = pytest.mark.django_db(databases=["default", "negocio"])

MASTERS = {
    "empresas": {
        "model": EmpresaModel, "entity": Empresa, "service": empresas, "id": "id_empresa",
        "name": "razon_social", "unique": ("rut",),
        "payload": lambda n: {"rut": f"76.000.{n:03d}-1", "razon_social": f"Empresa prueba {n}",
                              "plan": "BASICO", "activo": True},
        "invalid": {"plan": "DESCONOCIDO"}, "invalid_field": "plan",
    },
    "categorias": {
        "model": CategoriaModel, "entity": Categoria, "service": categorias, "id": "id_categoria",
        "name": "nombre", "unique": ("nombre",),
        "payload": lambda n: {"nombre": f"Categoria prueba {n}", "horas_sla": 8, "activo": True},
        "invalid": {"horas_sla": 0}, "invalid_field": "horas_sla",
    },
    "tecnicos": {
        "model": TecnicoModel, "entity": Tecnico, "service": tecnicos, "id": "id_tecnico",
        "name": "nombre", "unique": ("rut", "email"),
        "payload": lambda n: {"rut": f"15.000.{n:03d}-1", "nombre": f"Tecnico prueba {n}",
                              "email": f"tecnico{n}@test.cl", "activo": True},
        "invalid": {"email": "sin-correo"}, "invalid_field": "email",
    },
}


@pytest.fixture(params=MASTERS)
def master(request):
    return request.param, MASTERS[request.param]


def test_crud_completo_de_maestra(api, master):
    route, case = master
    url = f"/api/{route}/"
    payload = case["payload"](1)
    response = api.post(url, payload, format="json")
    assert response.status_code == 201
    pk = response.data[case["id"]]
    detail = f"{url}{pk}/"
    assert case["model"].objects.filter(pk=pk).exists()
    entity = case["service"].obtener(pk)
    assert isinstance(entity, case["entity"])

    response = api.get(url)
    assert response.status_code == 200
    assert response.data["count"] == 1
    assert response.data["results"][0][case["id"]] == pk
    assert api.get(detail).data[case["name"]] == payload[case["name"]]

    changed = payload | {case["name"]: "Nombre actualizado"}
    response = api.put(detail, changed, format="json")
    assert response.status_code == 200
    assert response.data[case["name"]] == "Nombre actualizado"
    response = api.patch(detail, {"activo": False}, format="json")
    assert response.status_code == 200
    assert response.data["activo"] is False
    assert response.data[case["name"]] == "Nombre actualizado"
    instance = case["model"].objects.get(pk=pk)
    assert instance.activo is False
    assert getattr(instance, case["name"]) == "Nombre actualizado"

    assert api.delete(detail).status_code == 204
    assert not case["model"].objects.filter(pk=pk).exists()
    assert api.get(detail).status_code == 404


@pytest.mark.parametrize("method", ["post", "put", "patch"])
def test_escrituras_de_api_pasan_por_casos_de_uso(api, master, method):
    route, case = master
    payload = case["payload"](1)
    url = f"/api/{route}/"
    operation = "crear"
    if method != "post":
        created = api.post(url, payload, format="json")
        url += f"{created.data[case['id']]}/"
        operation = "actualizar"
    with patch.object(case["service"], operation, side_effect=RuleViolationError("Regla de prueba", case["name"])):
        response = getattr(api, method)(url, payload, format="json")
    assert response.status_code == 409
    assert response.data == {"message": "Regla de prueba", "field": case["name"]}
    if method == "post":
        assert case["model"].objects.count() == 0


@pytest.mark.parametrize("method", ["post", "patch"])
@pytest.mark.parametrize("route,field", [(route, field) for route, case in MASTERS.items()
                                         for field in case["unique"]])
def test_duplicados_no_crean_ni_alteran_registros(api, route, field, method):
    case = MASTERS[route]
    url = f"/api/{route}/"
    first = case["payload"](1)
    second = case["payload"](2)
    assert api.post(url, first, format="json").status_code == 201
    if method == "patch":
        response = api.post(url, second, format="json")
        pk = response.data[case["id"]]
        response = api.patch(f"{url}{pk}/", {field: first[field]}, format="json")
        assert getattr(case["model"].objects.get(pk=pk), field) == second[field]
        expected_count = 2
    else:
        response = api.post(url, second | {field: first[field]}, format="json")
        expected_count = 1
    assert response.status_code == 409
    assert response.data["field"] == field
    assert set(response.data) == {"message", "field"}
    assert api.get(url).data["count"] == expected_count


@pytest.mark.parametrize("method", ["get", "put", "patch", "delete"])
def test_registro_inexistente_devuelve_404(api, master, method):
    route, case = master
    response = getattr(api, method)(f"/api/{route}/99999/", case["payload"](1), format="json")
    assert response.status_code == 404
    assert response.data == {"message": "Registro no encontrado", "field": None}


def test_identificador_invalido_devuelve_404(api, master):
    route, _ = master
    assert api.get(f"/api/{route}/no-es-numero/").status_code == 404


def test_no_elimina_maestra_con_ticket_asociado(api, master):
    route, case = master
    empresa = EmpresaModel.objects.create(rut="76.123.456-1", razon_social="Empresa", plan="BASICO")
    categoria = CategoriaModel.objects.create(nombre="Red", horas_sla=4)
    tecnico = TecnicoModel.objects.create(rut="15.123.456-1", nombre="Tecnico", email="tecnico@test.cl")
    TicketModel.objects.create(empresa=empresa, categoria=categoria, tecnico=tecnico,
                               titulo="Ticket de prueba", descripcion="Falla en la red de la oficina")
    instance = {"empresas": empresa, "categorias": categoria, "tecnicos": tecnico}[route]
    response = api.delete(f"/api/{route}/{instance.pk}/")
    assert response.status_code == 409
    assert response.data["message"] == "No se puede eliminar porque el registro está en uso"
    assert case["model"].objects.filter(pk=instance.pk).exists()


def test_validacion_http_no_guarda_datos_invalidos(api, master):
    route, case = master
    response = api.post(f"/api/{route}/", case["payload"](1) | case["invalid"], format="json")
    assert response.status_code == 400
    assert response.data["field"] == case["invalid_field"]
    assert case["model"].objects.count() == 0


def test_reglas_de_maestras_tambien_se_aplican_fuera_de_http(master):
    _, case = master
    with pytest.raises(RuleViolationError) as error:
        case["service"].crear(case["payload"](1) | case["invalid"])
    assert error.value.field == case["invalid_field"]
    assert case["model"].objects.count() == 0


def test_consulta_filtra_busca_ordena_y_pagina(api, master):
    route, case = master
    url = f"/api/{route}/"
    ids = []
    for n in range(1, 4):
        response = api.post(url, case["payload"](n), format="json")
        assert response.status_code == 201
        ids.append(response.data[case["id"]])
    assert api.patch(f"{url}{ids[1]}/", {"activo": False}, format="json").status_code == 200
    response = api.get(url, {"activo": "false"})
    assert response.data["count"] == 1
    assert response.data["results"][0][case["id"]] == ids[1]
    response = api.get(url, {"search": case["payload"](2)[case["name"]]})
    assert response.data["count"] == 1
    assert response.data["results"][0][case["id"]] == ids[1]
    response = api.get(url, {"ordering": f"-{case['id']}"})
    assert [row[case["id"]] for row in response.data["results"]] == ids[::-1]
    response = api.get(url, {"page_size": 1, "page": 2, "ordering": case["id"]})
    assert response.data["count"] == 3
    assert [row[case["id"]] for row in response.data["results"]] == [ids[1]]
    assert response.data["next"] is not None
    assert response.data["previous"] is not None


def test_paginacion_permite_listar_mas_de_diez_maestras(api):
    CategoriaModel.objects.bulk_create([CategoriaModel(nombre=f"Categoria {n:02d}", horas_sla=4)
                                      for n in range(12)])
    assert len(api.get("/api/categorias/").data["results"]) == 10
    response = api.get("/api/categorias/?page_size=100")
    assert response.data["count"] == 12
    assert len(response.data["results"]) == 12


def test_filtra_empresas_por_plan(api):
    for n, plan in enumerate(["BASICO", "PREMIUM"], start=1):
        assert api.post("/api/empresas/", MASTERS["empresas"]["payload"](n) | {"plan": plan},
                        format="json").status_code == 201
    response = api.get("/api/empresas/?plan=PREMIUM")
    assert response.data["count"] == 1
    assert response.data["results"][0]["plan"] == "PREMIUM"


def test_anonimo_no_puede_consultar_maestras(master):
    route, _ = master
    assert APIClient().get(f"/api/{route}/").status_code == 401


def test_tecnico_solo_puede_consultar_maestras(api, master):
    route, case = master
    url = f"/api/{route}/"
    payload = case["payload"](1)
    created = api.post(url, payload, format="json")
    detail = f"{url}{created.data[case['id']]}/"
    user = User.objects.create_user("tecnico", password="test12345")
    user.groups.add(Group.objects.create(name="TECNICO"))
    api.force_authenticate(user)
    assert api.get(url).status_code == 200
    assert api.get(detail).status_code == 200
    assert api.post(url, case["payload"](2), format="json").status_code == 403
    assert api.put(detail, payload, format="json").status_code == 403
    assert api.patch(detail, {"activo": False}, format="json").status_code == 403
    assert api.delete(detail).status_code == 403
    assert case["model"].objects.count() == 1
    assert case["model"].objects.get().activo is True

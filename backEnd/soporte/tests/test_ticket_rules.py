import pytest
from django.contrib.auth.models import Group, User
from rest_framework.test import APIClient

from soporte.infrastructure.models import CategoriaModel, EmpresaModel, TecnicoModel


@pytest.fixture
def api(db):
    user = User.objects.create_user("supervisor", password="test12345", email="supervisor@test.cl")
    user.groups.add(Group.objects.create(name="SUPERVISOR"))
    client = APIClient()
    client.force_authenticate(user)
    return client


@pytest.mark.django_db(databases=["default", "negocio"])
def test_empresa_premium_fuerza_prioridad_alta(api):
    empresa = EmpresaModel.objects.create(rut="1-9", razon_social="Premium", plan="PREMIUM")
    categoria = CategoriaModel.objects.create(nombre="Red", horas_sla=4)
    response = api.post("/api/tickets/", {"empresa_id": empresa.pk, "categoria_id": categoria.pk,
        "titulo": "Falla de conexión", "descripcion": "La oficina está sin conexión", "prioridad": "BAJA"}, format="json")
    assert response.status_code == 201
    assert response.data["prioridad"] == "ALTA"


@pytest.mark.django_db(databases=["default", "negocio"])
def test_no_asigna_tecnico_inactivo(api):
    empresa = EmpresaModel.objects.create(rut="2-7", razon_social="Básica", plan="BASICO")
    categoria = CategoriaModel.objects.create(nombre="Acceso", horas_sla=4)
    tecnico = TecnicoModel.objects.create(rut="3-5", nombre="Inactivo", email="inactivo@test.cl", activo=False)
    response = api.post("/api/tickets/", {"empresa_id": empresa.pk, "categoria_id": categoria.pk,
        "tecnico_id": tecnico.pk, "titulo": "Cuenta bloqueada", "descripcion": "No es posible iniciar sesión", "prioridad": "MEDIA"}, format="json")
    assert response.status_code == 409


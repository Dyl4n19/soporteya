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


@pytest.fixture
def business_data():
    company = EmpresaModel.objects.create(rut="76.123.456-1", razon_social="Empresa S3", plan="BASICO")
    category = CategoriaModel.objects.create(nombre="Red S3", horas_sla=4)
    technician = TecnicoModel.objects.create(rut="15.123.456-1", nombre="Tecnico S3", email="s3@test.cl")
    return {"empresa_id": company.pk, "categoria_id": category.pk, "tecnico_id": technician.pk,
            "titulo": "Falla de red oficina", "descripcion": "Los equipos no pueden acceder a la red",
            "prioridad": "MEDIA"}

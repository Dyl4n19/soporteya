from io import StringIO

import pytest
from django.core.management import call_command

from soporte.infrastructure.models import CategoriaModel, EmpresaModel, TecnicoModel


@pytest.mark.django_db(databases=["default", "negocio"])
def test_verificacion_crud_conserva_datos_existentes():
    EmpresaModel.objects.create(rut="76.123.456-1", razon_social="Empresa original", plan="BASICO")
    CategoriaModel.objects.create(nombre="Categoria original", horas_sla=4)
    TecnicoModel.objects.create(rut="15.123.456-1", nombre="Tecnico original", email="original@test.cl")
    models = [EmpresaModel, CategoriaModel, TecnicoModel]
    before = {model: list(model.objects.values()) for model in models}
    output = StringIO()
    call_command("verificar_semana2", crud=True, stdout=output)
    for model in models:
        assert list(model.objects.values()) == before[model]
    assert output.getvalue().count("OK CRUD") == 3
    assert "transacción revertida" in output.getvalue()

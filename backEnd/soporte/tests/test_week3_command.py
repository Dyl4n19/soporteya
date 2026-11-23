from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from soporte.infrastructure.models import CategoriaModel, ComentarioModel, EmpresaModel, TecnicoModel, TicketModel


pytestmark = pytest.mark.django_db(databases=["default", "negocio"])


def test_comando_semana3_exige_roles_preparados():
    with pytest.raises(CommandError, match="superusuario"):
        call_command("verificar_semana3", stdout=StringIO())


def test_comando_semana3_prueba_transacciones_y_conserva_cinco_tablas(business_data):
    call_command("setup_demo", stdout=StringIO())
    ticket = TicketModel.objects.create(empresa_id=business_data["empresa_id"], categoria_id=business_data["categoria_id"],
                                       titulo=business_data["titulo"], descripcion=business_data["descripcion"])
    ComentarioModel.objects.create(ticket=ticket, numero=1, autor="Autor original", texto="Datos originales")
    models = [EmpresaModel, CategoriaModel, TecnicoModel, TicketModel, ComentarioModel]
    before = {model: list(model.objects.values()) for model in models}
    output = StringIO()
    call_command("verificar_semana3", crud=True, stdout=output)
    for model in models:
        assert list(model.objects.values()) == before[model]
    assert "OK rollback" in output.getvalue()
    assert "OK R3" in output.getvalue()

from io import StringIO

import pytest
from django.contrib import admin
from django.contrib.auth.models import User
from django.core.management import call_command

from soporte.infrastructure.models import CategoriaModel, ComentarioModel, EmpresaModel, TecnicoModel, TicketModel


pytestmark = pytest.mark.django_db(databases=["default", "negocio"])


@pytest.fixture
def admin_client(client):
    call_command("setup_demo", stdout=StringIO())
    client.force_login(User.objects.get(username="admin"))
    return client


@pytest.mark.parametrize("model", [EmpresaModel, CategoriaModel, TecnicoModel, TicketModel, ComentarioModel])
def test_admin_cinco_entidades_con_busqueda_y_filtros(admin_client, model):
    registered = admin.site._registry[model]
    assert registered.search_fields
    assert registered.list_filter
    response = admin_client.get(f"/admin/soporte/{model._meta.model_name}/")
    assert response.status_code == 200


def ticket_form_data(business_data):
    return {"empresa": business_data["empresa_id"], "categoria": business_data["categoria_id"],
            "tecnico": "", "titulo": business_data["titulo"], "descripcion": business_data["descripcion"],
            "prioridad": "MEDIA", "comentarios-TOTAL_FORMS": "2", "comentarios-INITIAL_FORMS": "0",
            "comentarios-MIN_NUM_FORMS": "0", "comentarios-MAX_NUM_FORMS": "1000",
            "comentarios-0-texto": "Solicitud recibida", "comentarios-1-texto": "Primera revision", "_save": "Guardar"}


def test_admin_crea_ticket_y_detalle_por_casos_de_uso(admin_client, business_data):
    response = admin_client.post("/admin/soporte/ticketmodel/add/", ticket_form_data(business_data))
    assert response.status_code == 302
    assert TicketModel.objects.count() == 1
    assert ComentarioModel.objects.count() == 2
    assert list(ComentarioModel.objects.values_list("numero", flat=True)) == [1, 2]


def test_admin_informa_r1_sin_guardar_datos_invalidos(admin_client, business_data):
    TecnicoModel.objects.filter(pk=business_data["tecnico_id"]).update(activo=False)
    data = ticket_form_data(business_data) | {"tecnico": business_data["tecnico_id"]}
    response = admin_client.post("/admin/soporte/ticketmodel/add/", data)
    assert response.status_code == 200
    assert "activo" in str(response.context["adminform"].form.errors)
    assert TicketModel.objects.count() == 0
    assert ComentarioModel.objects.count() == 0


def test_admin_no_saltea_estados_y_permiso_de_borrado(admin_client, business_data):
    ticket = TicketModel.objects.create(empresa_id=business_data["empresa_id"], categoria_id=business_data["categoria_id"],
                                       titulo=business_data["titulo"], descripcion=business_data["descripcion"])
    response = admin_client.post("/admin/soporte/ticketmodel/", {"action": "resolver", "_selected_action": [ticket.pk]})
    assert response.status_code == 302
    ticket.refresh_from_db()
    assert ticket.estado == "ABIERTO"
    assert "estado" in admin.site._registry[TicketModel].readonly_fields


def test_admin_comentario_genera_numero_y_autor(admin_client, business_data):
    ticket = TicketModel.objects.create(empresa_id=business_data["empresa_id"], categoria_id=business_data["categoria_id"],
                                       titulo=business_data["titulo"], descripcion=business_data["descripcion"])
    response = admin_client.post("/admin/soporte/comentariomodel/add/", {
        "ticket": ticket.pk, "texto": "Comentario desde el administrador", "_save": "Guardar",
    })
    assert response.status_code == 302
    stored = ComentarioModel.objects.get()
    assert stored.numero == 1
    assert stored.autor == "Administrador"


def test_admin_busqueda_y_filtro_real(admin_client):
    EmpresaModel.objects.create(rut="76.001.001-1", razon_social="Andina SpA", plan="PREMIUM")
    EmpresaModel.objects.create(rut="76.002.002-1", razon_social="Austral Ltda", plan="BASICO")
    response = admin_client.get("/admin/soporte/empresamodel/", {"q": "Andina", "plan__exact": "PREMIUM"})
    assert response.status_code == 200
    assert [row.razon_social for row in response.context["cl"].result_list] == ["Andina SpA"]

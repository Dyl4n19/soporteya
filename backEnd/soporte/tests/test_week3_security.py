from io import StringIO

import pytest
from django.conf import settings
from django.contrib.auth.models import Group, User
from django.core.management import call_command
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from soporte.infrastructure.models import TecnicoModel


pytestmark = pytest.mark.django_db(databases=["default", "negocio"])


@pytest.fixture
def credentials():
    user = User.objects.create_user("sesion", password="ClaveS3!2026", email="sesion@test.cl")
    user.groups.add(Group.objects.create(name="SUPERVISOR"))
    return {"username": user.username, "password": "ClaveS3!2026"}


def csrf(client):
    response = client.get("/api/auth/csrf/")
    assert response.status_code == 200
    return response.data["csrfToken"]


def login(client, credentials):
    return client.post("/api/auth/login/", credentials, format="json", HTTP_X_CSRFTOKEN=csrf(client))


@pytest.mark.parametrize("url", ["/api/empresas/", "/api/categorias/", "/api/tecnicos/", "/api/tickets/",
                                  "/api/tickets/1/comentarios/", "/api/auth/me/", "/api/reportes/soporte/"])
def test_api_sin_autenticar_responde_401(url):
    assert APIClient(enforce_csrf_checks=True).get(url).status_code == 401


def test_login_exige_csrf_incluso_sin_sesion(credentials):
    client = APIClient(enforce_csrf_checks=True)
    assert client.post("/api/auth/login/", credentials, format="json").status_code == 403
    csrf(client)
    assert client.post("/api/auth/login/", credentials, format="json").status_code == 403
    assert Token.objects.count() == 0


def test_contrasena_incorrecta_no_entrega_token(credentials):
    client = APIClient(enforce_csrf_checks=True)
    response = login(client, credentials | {"password": "Equivocada"})
    assert response.status_code == 400
    assert settings.TOKEN_COOKIE_NAME not in response.cookies
    assert Token.objects.count() == 0


def test_cookie_httponly_me_csrf_logout_y_revocacion(credentials):
    client = APIClient(enforce_csrf_checks=True)
    before = csrf(client)
    response = client.post("/api/auth/login/", credentials, format="json", HTTP_X_CSRFTOKEN=before)
    assert response.status_code == 200
    token_cookie = response.cookies[settings.TOKEN_COOKIE_NAME]
    assert token_cookie["httponly"] is True
    assert token_cookie["samesite"] == "Lax"
    assert "token" not in response.data
    old_token = token_cookie.value
    assert client.get("/api/auth/me/").data["username"] == "sesion"
    assert client.get("/api/auth/me/").data["role"] == "SUPERVISOR"
    assert client.cookies[settings.CSRF_COOKIE_NAME].value != before
    payload = {"nombre": "Categoria segura", "horas_sla": 4, "activo": True}
    assert client.post("/api/categorias/", payload, format="json").status_code == 403
    response = client.post("/api/categorias/", payload, format="json", HTTP_X_CSRFTOKEN=client.cookies[settings.CSRF_COOKIE_NAME].value)
    assert response.status_code == 201
    assert client.post("/api/auth/logout/").status_code == 403
    assert client.get("/api/auth/me/").status_code == 200
    response = client.post("/api/auth/logout/", HTTP_X_CSRFTOKEN=client.cookies[settings.CSRF_COOKIE_NAME].value)
    assert response.status_code == 204
    assert response.cookies[settings.TOKEN_COOKIE_NAME]["max-age"] == 0
    assert Token.objects.count() == 0
    assert client.get("/api/tickets/").status_code == 401
    client.cookies[settings.TOKEN_COOKIE_NAME] = old_token
    assert client.get("/api/auth/me/").status_code == 401


def test_origen_no_confiable_es_rechazado_en_login(credentials):
    client = APIClient(enforce_csrf_checks=True)
    token = csrf(client)
    response = client.post("/api/auth/login/", credentials, format="json", HTTP_X_CSRFTOKEN=token,
                           HTTP_ORIGIN="https://sitio-ajeno.example")
    assert response.status_code == 403


def test_cookie_invalida_no_bloquea_un_nuevo_login(credentials):
    client = APIClient(enforce_csrf_checks=True)
    client.cookies[settings.TOKEN_COOKIE_NAME] = "token-invalido"
    assert client.get("/api/tickets/").status_code == 401
    assert login(client, credentials).status_code == 200
    assert client.get("/api/auth/me/").status_code == 200


def test_cookie_secure_es_configurable(credentials, settings):
    settings.TOKEN_COOKIE_SECURE = True
    response = login(APIClient(enforce_csrf_checks=True), credentials)
    assert response.status_code == 200
    assert response.cookies[settings.TOKEN_COOKIE_NAME]["secure"] is True


def test_encabezado_token_no_permite_eludir_cookie_y_csrf(credentials):
    client = APIClient(enforce_csrf_checks=True)
    user = User.objects.get(username=credentials["username"])
    token = Token.objects.create(user=user)
    payload = {"nombre": "Sin omitir CSRF", "horas_sla": 4}
    assert client.post("/api/categorias/", payload, format="json", HTTP_AUTHORIZATION=f"Token {token.key}").status_code == 401
    assert login(client, credentials).status_code == 200
    assert client.post("/api/categorias/", payload, format="json", HTTP_AUTHORIZATION=f"Token {token.key}").status_code == 403


def test_tecnico_solo_ve_avanza_y_comenta_sus_tickets(api, business_data):
    own = api.post("/api/tickets/", business_data, format="json").data["id_ticket"]
    other_tech = TecnicoModel.objects.create(rut="16.123.456-1", nombre="Otro", email="otro@test.cl")
    other = api.post("/api/tickets/", business_data | {"tecnico_id": other_tech.pk}, format="json").data["id_ticket"]
    user = User.objects.create_user("tecnico", password="clave", email="s3@test.cl")
    user.groups.add(Group.objects.create(name="TECNICO"))
    api.force_authenticate(user)
    assert [row["id_ticket"] for row in api.get("/api/tickets/").data["results"]] == [own]
    assert api.get(f"/api/tickets/{other}/").status_code == 404
    assert api.get(f"/api/tickets/{other}/comentarios/").status_code == 404
    assert api.post(f"/api/tickets/{other}/estado/", {"estado": "EN_PROGRESO"}, format="json").status_code == 404
    assert api.post("/api/tickets/", business_data, format="json").status_code == 403
    assert api.patch(f"/api/tickets/{own}/", {"titulo": "No autorizado"}, format="json").status_code == 403
    assert api.put(f"/api/tickets/{own}/", {"estado": "EN_PROGRESO"}, format="json").status_code == 200
    url = f"/api/tickets/{own}/comentarios/"
    assert api.post(url, {"texto": "Diagnostico del tecnico"}, format="json").status_code == 201
    assert api.get(f"{url}1/").status_code == 200
    assert api.put(f"{url}1/", {"texto": "No autorizado"}, format="json").status_code == 403
    assert api.delete(f"{url}1/").status_code == 403
    assert api.delete(f"/api/tickets/{own}/").status_code == 403
    assert api.get("/api/reportes/soporte/").status_code == 403


def test_usuario_sin_rol_no_accede_al_negocio(api):
    user = User.objects.create_user("sinrol", password="clave")
    api.force_authenticate(user)
    assert api.get("/api/tickets/").status_code == 403
    assert api.get("/api/empresas/").status_code == 403


def test_setup_demo_crea_superusuario_y_dos_roles_sin_reiniciar_claves():
    output = StringIO()
    call_command("setup_demo", stdout=output)
    admin = User.objects.get(username="admin")
    lead = User.objects.get(username="supervisor")
    tech = User.objects.get(username="tecnico")
    assert admin.is_superuser and admin.is_staff
    assert lead.is_staff and not lead.is_superuser
    assert not tech.is_superuser and not tech.is_staff
    assert lead.groups.filter(name="SUPERVISOR").exists()
    assert tech.groups.filter(name="TECNICO").exists()
    assert lead.has_perm("soporte.delete_ticketmodel")
    assert tech.has_perm("soporte.add_comentariomodel")
    assert not tech.has_perm("soporte.delete_ticketmodel")
    assert not tech.has_perm("soporte.add_ticketmodel")
    assert admin.check_password("CambiarAdmin123!")
    lead.set_password("ClavePersonalConservada!2026")
    lead.save()
    call_command("setup_demo", stdout=output)
    lead.refresh_from_db()
    assert lead.check_password("ClavePersonalConservada!2026")
    assert User.objects.count() == 3

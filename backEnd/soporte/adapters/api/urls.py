from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter

from .views import CategoriaViewSet, ComentarioViewSet, EmpresaViewSet, TecnicoViewSet, TicketViewSet, api_not_found, csrf_view, login_view, logout_view, me_view, reporte_view

router = DefaultRouter()
router.register("empresas", EmpresaViewSet, basename="empresamodel")
router.register("categorias", CategoriaViewSet, basename="categoriamodel")
router.register("tecnicos", TecnicoViewSet, basename="tecnicomodel")
router.register("tickets", TicketViewSet, basename="ticket")

urlpatterns = [
    path("tickets/<int:ticket_pk>/comentarios/", ComentarioViewSet.as_view({"get": "list", "post": "create"}),
         name="comentario-list"),
    path("tickets/<int:ticket_pk>/comentarios/<int:numero>/",
         ComentarioViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}),
         name="comentario-detail"),
    path("auth/csrf/", csrf_view),
    path("auth/login/", login_view),
    path("auth/me/", me_view),
    path("auth/logout/", logout_view),
    path("reportes/soporte/", reporte_view),
    path("", include(router.urls)),
    re_path(r"^.*$", api_not_found),
]


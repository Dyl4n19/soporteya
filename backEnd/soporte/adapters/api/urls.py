from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CategoriaViewSet, EmpresaViewSet, TecnicoViewSet, TicketViewSet, csrf_view, login_view, logout_view, me_view, reporte_view

router = DefaultRouter()
router.register("empresas", EmpresaViewSet)
router.register("categorias", CategoriaViewSet)
router.register("tecnicos", TecnicoViewSet)
router.register("tickets", TicketViewSet, basename="ticket")

urlpatterns = [
    path("auth/csrf/", csrf_view),
    path("auth/login/", login_view),
    path("auth/me/", me_view),
    path("auth/logout/", logout_view),
    path("reportes/soporte/", reporte_view),
    path("", include(router.urls)),
]


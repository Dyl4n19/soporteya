from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token
from rest_framework import mixins, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from soporte.adapters.api.permissions import IsSupervisorOrReadOnly, TicketRolePermission, user_role
from soporte.adapters.api.serializers import (CategoriaInputSerializer, CategoriaOutputSerializer,
    ComentarioInputSerializer, EmpresaInputSerializer, EmpresaOutputSerializer, EstadoInputSerializer,
    TecnicoInputSerializer, TecnicoOutputSerializer, TicketInputSerializer, TicketOutputSerializer)
from soporte.container import comentarios, tickets
from soporte.infrastructure.models import CategoriaModel, EmpresaModel, TecnicoModel, TicketModel


class MasterViewSet(viewsets.ModelViewSet):
    permission_classes = [IsSupervisorOrReadOnly]
    input_serializer_class = None
    output_serializer_class = None

    def get_serializer_class(self):
        return self.output_serializer_class if self.action in {"list", "retrieve"} else self.input_serializer_class

    def create(self, request, *args, **kwargs):
        serializer = self.input_serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response(self.output_serializer_class(instance).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.input_serializer_class(instance, data=request.data, partial=kwargs.get("partial", False))
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response(self.output_serializer_class(instance).data)


class EmpresaViewSet(MasterViewSet):
    queryset = EmpresaModel.objects.all()
    input_serializer_class = EmpresaInputSerializer
    output_serializer_class = EmpresaOutputSerializer
    search_fields = ["rut", "razon_social"]
    filterset_fields = ["plan", "activo"]


class CategoriaViewSet(MasterViewSet):
    queryset = CategoriaModel.objects.all()
    input_serializer_class = CategoriaInputSerializer
    output_serializer_class = CategoriaOutputSerializer
    search_fields = ["nombre"]
    filterset_fields = ["activo"]


class TecnicoViewSet(MasterViewSet):
    queryset = TecnicoModel.objects.all()
    input_serializer_class = TecnicoInputSerializer
    output_serializer_class = TecnicoOutputSerializer
    search_fields = ["rut", "nombre", "email"]
    filterset_fields = ["activo"]


class TicketViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin,
                    mixins.DestroyModelMixin, viewsets.GenericViewSet):
    permission_classes = [TicketRolePermission]
    serializer_class = TicketOutputSerializer
    search_fields = ["titulo", "descripcion", "empresa__razon_social"]
    filterset_fields = ["estado", "prioridad", "categoria_id", "tecnico_id"]

    def get_queryset(self):
        qs = TicketModel.objects.select_related("empresa", "categoria", "tecnico").prefetch_related("comentarios")
        if user_role(self.request.user) == "TECNICO":
            qs = qs.filter(tecnico__email__iexact=self.request.user.email)
        return qs

    def create(self, request, *args, **kwargs):
        serializer = TicketInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ticket = tickets.crear(dict(serializer.validated_data))
        ticket = self.get_queryset().get(pk=ticket.pk)
        return Response(TicketOutputSerializer(ticket).data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        tickets.eliminar(self.get_object().pk)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"], url_path="comentarios")
    def agregar_comentario(self, request, pk=None):
        self.get_object()
        serializer = ComentarioInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comentario = comentarios.agregar(int(pk), request.user.get_full_name() or request.user.username, serializer.validated_data["texto"])
        return Response({"numero": comentario.numero, "autor": comentario.autor, "texto": comentario.texto}, status=201)

    @action(detail=True, methods=["post"], url_path="estado")
    def cambiar_estado(self, request, pk=None):
        self.get_object()
        serializer = EstadoInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ticket = tickets.cambiar_estado(int(pk), serializer.validated_data["estado"])
        ticket = self.get_queryset().get(pk=ticket.pk)
        return Response(TicketOutputSerializer(ticket).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def csrf_view(request):
    return Response({"csrfToken": get_token(request)})


@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    username = request.data.get("username", "")
    password = request.data.get("password", "")
    user = authenticate(request, username=username, password=password)
    if not user:
        return Response({"message": "Credenciales incorrectas", "field": "username"}, status=400)
    login(request, user)
    token, _ = Token.objects.get_or_create(user=user)
    response = Response({"username": user.username, "name": user.get_full_name(), "role": user_role(user)})
    response.set_cookie(settings.TOKEN_COOKIE_NAME, token.key, httponly=True,
                        secure=settings.TOKEN_COOKIE_SECURE, samesite=settings.TOKEN_COOKIE_SAMESITE)
    return response


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me_view(request):
    return Response({"username": request.user.username, "name": request.user.get_full_name(), "email": request.user.email, "role": user_role(request.user)})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    Token.objects.filter(user=request.user).delete()
    logout(request)
    response = Response(status=204)
    response.delete_cookie(settings.TOKEN_COOKIE_NAME)
    return response


@api_view(["GET"])
def reporte_view(request):
    vencidos, promedios = tickets.reporte()
    return Response({
        "tickets_vencidos": [{"id_ticket": t.pk, "titulo": t.titulo, "empresa": t.empresa.razon_social,
                               "estado": t.estado, "horas_sla": t.categoria.horas_sla,
                               "fecha_creacion": t.fecha_creacion} for t in vencidos],
        "promedio_resolucion_por_tecnico": [{"id_tecnico": x["tecnico_id"], "tecnico": x["tecnico__nombre"],
                                               "horas_promedio": round(x["promedio"].total_seconds() / 3600, 2)} for x in promedios],
    })


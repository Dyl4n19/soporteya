from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.db import transaction
from django.middleware.csrf import get_token
from rest_framework import mixins, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from soporte.adapters.api.permissions import IsSupervisorOrReadOnly, TicketRolePermission, user_role
from soporte.adapters.api.serializers import (CategoriaInputSerializer, CategoriaOutputSerializer,
    ComentarioInputSerializer, EmpresaInputSerializer, EmpresaOutputSerializer, EstadoInputSerializer,
    MasterQuerySerializer, TecnicoInputSerializer, TecnicoOutputSerializer, TicketInputSerializer, TicketOutputSerializer)
from soporte.application.exceptions import NotFoundError
from soporte.container import categorias, comentarios, empresas, tecnicos, tickets
from soporte.infrastructure.models import TicketModel


class MasterPagination(PageNumberPagination):
    page_size_query_param = "page_size"
    max_page_size = 100


class MasterViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated, IsSupervisorOrReadOnly]
    pagination_class = MasterPagination
    input_serializer_class = None
    output_serializer_class = None
    use_cases = None
    filter_fields = ("activo",)

    def get_serializer_class(self):
        return self.output_serializer_class if self.action in {"list", "retrieve"} else self.input_serializer_class

    def get_pk(self):
        try:
            return int(self.kwargs["pk"])
        except (ValueError, TypeError) as exc:
            raise NotFoundError("Registro no encontrado") from exc

    def get_object(self):
        instance = self.use_cases.obtener(self.get_pk())
        self.check_object_permissions(self.request, instance)
        return instance

    def list(self, request, *args, **kwargs):
        query = MasterQuerySerializer(data=request.query_params.dict())
        query.is_valid(raise_exception=True)
        params = query.validated_data
        filters = {field: params[field] for field in self.filter_fields
                   if field in params and params[field] != ""}
        instances = self.use_cases.listar(search=params["search"], filters=filters,
                                         ordering=params.get("ordering"))
        page = self.paginate_queryset(instances)
        if page is not None:
            return self.get_paginated_response(self.output_serializer_class(page, many=True).data)
        return Response(self.output_serializer_class(instances, many=True).data)

    def retrieve(self, request, *args, **kwargs):
        return Response(self.output_serializer_class(self.get_object()).data)

    def create(self, request, *args, **kwargs):
        serializer = self.input_serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = self.use_cases.crear(dict(serializer.validated_data))
        return Response(self.output_serializer_class(instance).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.input_serializer_class(instance, data=request.data, partial=kwargs.get("partial", False))
        serializer.is_valid(raise_exception=True)
        instance = self.use_cases.actualizar(self.get_pk(), dict(serializer.validated_data))
        return Response(self.output_serializer_class(instance).data)

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        self.get_object()
        self.use_cases.eliminar(self.get_pk())
        return Response(status=status.HTTP_204_NO_CONTENT)


class EmpresaViewSet(MasterViewSet):
    use_cases = empresas
    input_serializer_class = EmpresaInputSerializer
    output_serializer_class = EmpresaOutputSerializer
    filter_fields = ("plan", "activo")


class CategoriaViewSet(MasterViewSet):
    use_cases = categorias
    input_serializer_class = CategoriaInputSerializer
    output_serializer_class = CategoriaOutputSerializer


class TecnicoViewSet(MasterViewSet):
    use_cases = tecnicos
    input_serializer_class = TecnicoInputSerializer
    output_serializer_class = TecnicoOutputSerializer


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
        ticket = self.get_queryset().get(pk=ticket.id_ticket)
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
    @transaction.atomic(using="negocio")
    def cambiar_estado(self, request, pk=None):
        self.get_object()
        serializer = EstadoInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ticket = tickets.cambiar_estado(int(pk), serializer.validated_data["estado"])
        ticket = self.get_queryset().get(pk=ticket.id_ticket)
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
    return Response(tickets.reporte())


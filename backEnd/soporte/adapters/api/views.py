from collections.abc import Mapping

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import action, api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from soporte.adapters.api.pagination import ApiPagination
from soporte.adapters.api.permissions import ComentarioRolePermission, IsSupervisor, TicketRolePermission, user_role
from soporte.adapters.api.serializers import (CategoriaInputSerializer, CategoriaOutputSerializer,
    ComentarioInputSerializer, EmpresaInputSerializer, EmpresaOutputSerializer, EstadoInputSerializer,
    ComentarioOutputSerializer, ComentarioQuerySerializer, LoginInputSerializer, MasterQuerySerializer,
    ReporteSerializer, TecnicoInputSerializer, TecnicoOutputSerializer,
    TicketInputSerializer, TicketOutputSerializer, TicketQuerySerializer, TicketUpdateSerializer)
from soporte.application.exceptions import NotFoundError
from soporte.container import categorias, comentarios, empresas, tecnicos, tickets


class MasterViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated, IsSupervisor]
    pagination_class = ApiPagination
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


def ticket_for_user(user, pk):
    try:
        ticket = tickets.obtener(int(pk))
    except (ValueError, TypeError) as error:
        raise NotFoundError("Registro no encontrado") from error
    if user_role(user) == "TECNICO":
        if not ticket.id_tecnico or tecnicos.obtener(ticket.id_tecnico).email.casefold() != user.email.casefold():
            raise NotFoundError("Registro no encontrado")
    return ticket


class TicketViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated, TicketRolePermission]
    pagination_class = ApiPagination
    serializer_class = TicketOutputSerializer

    def get_object(self):
        return ticket_for_user(self.request.user, self.kwargs["pk"])

    def output(self, ticket):
        return TicketOutputSerializer(tickets.detalles([ticket])[0]).data

    def list(self, request, *args, **kwargs):
        query = TicketQuerySerializer(data=request.query_params.dict())
        query.is_valid(raise_exception=True)
        params = query.validated_data
        filters = {field: params[field] for field in ("estado", "prioridad", "categoria_id", "tecnico_id")
                   if field in params and params[field] != ""}
        if user_role(request.user) == "TECNICO":
            filters["tecnico_email"] = request.user.email
        rows = tickets.listar(search=params["search"], filters=filters, ordering=params.get("ordering"))
        page = self.paginate_queryset(rows)
        data = TicketOutputSerializer(tickets.detalles(page if page is not None else rows), many=True).data
        return self.get_paginated_response(data) if page is not None else Response(data)

    def retrieve(self, request, *args, **kwargs):
        return Response(self.output(self.get_object()))

    def create(self, request, *args, **kwargs):
        serializer = TicketInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ticket = tickets.crear(dict(serializer.validated_data), request.user.get_full_name() or request.user.username)
        return Response(self.output(ticket), status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = TicketUpdateSerializer(data=request.data,
                                            partial=kwargs.get("partial", False) or (
                                                isinstance(request.data, Mapping) and set(request.data) == {"estado"}))
        serializer.is_valid(raise_exception=True)
        ticket = tickets.actualizar(instance.id_ticket, dict(serializer.validated_data),
                                   request.user.get_full_name() or request.user.username)
        return Response(self.output(ticket))

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        tickets.eliminar(self.get_object().id_ticket)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"], url_path="estado")
    def cambiar_estado(self, request, pk=None):
        self.get_object()
        serializer = EstadoInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ticket = tickets.cambiar_estado(int(pk), serializer.validated_data["estado"])
        return Response(self.output(ticket))


class ComentarioViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated, ComentarioRolePermission]
    serializer_class = ComentarioOutputSerializer
    pagination_class = ApiPagination

    def get_ticket(self):
        return ticket_for_user(self.request.user, self.kwargs["ticket_pk"])

    def list(self, request, *args, **kwargs):
        parent = self.get_ticket()
        query = ComentarioQuerySerializer(data=request.query_params.dict())
        query.is_valid(raise_exception=True)
        params = query.validated_data
        filters = {field: params[field] for field in ("autor", "numero") if params.get(field) not in (None, "")}
        rows = comentarios.listar(parent.id_ticket, search=params["search"], filters=filters,
                                 ordering=params.get("ordering"))
        page = self.paginate_queryset(rows)
        data = ComentarioOutputSerializer(page if page is not None else rows, many=True).data
        return self.get_paginated_response(data) if page is not None else Response(data)

    def retrieve(self, request, *args, **kwargs):
        parent = self.get_ticket()
        return Response(ComentarioOutputSerializer(comentarios.obtener(parent.id_ticket, self.kwargs["numero"])).data)

    def create(self, request, *args, **kwargs):
        parent = self.get_ticket()
        serializer = ComentarioInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = comentarios.crear(parent.id_ticket, request.user.get_full_name() or request.user.username,
                                    serializer.validated_data["texto"])
        return Response(ComentarioOutputSerializer(comment).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        parent = self.get_ticket()
        serializer = ComentarioInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = comentarios.actualizar(parent.id_ticket, self.kwargs["numero"], serializer.validated_data["texto"])
        return Response(ComentarioOutputSerializer(comment).data)

    def partial_update(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        parent = self.get_ticket()
        comentarios.eliminar(parent.id_ticket, self.kwargs["numero"])
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def csrf_view(request):
    return Response({"csrfToken": get_token(request)})


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def login_view(request):
    SessionAuthentication().enforce_csrf(request)
    serializer = LoginInputSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = authenticate(request, **serializer.validated_data)
    if not user:
        return Response({"message": "Credenciales incorrectas", "field": "username"}, status=400)
    login(request, user)
    token, _ = Token.objects.get_or_create(user=user)
    response = Response({"username": user.username, "name": user.get_full_name(), "role": user_role(user),
                         "csrfToken": get_token(request)})
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
@permission_classes([IsAuthenticated, IsSupervisor])
def reporte_view(request):
    return Response(ReporteSerializer(tickets.reporte()).data)


@csrf_exempt
def api_not_found(request):
    return JsonResponse({"message": "Ruta de API no encontrada", "field": None}, status=404)


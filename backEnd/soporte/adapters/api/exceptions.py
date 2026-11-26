import logging

from django.db import IntegrityError
from rest_framework.response import Response
from rest_framework.views import exception_handler, set_rollback

from soporte.application.exceptions import BusinessError, NotFoundError


logger = logging.getLogger(__name__)


def first_error(data, path=""):
    if isinstance(data, dict):
        for key, value in data.items():
            location = path if key in {"detail", "non_field_errors"} else ".".join(filter(None, [path, str(key)]))
            if value:
                return first_error(value, location)
    elif isinstance(data, (list, tuple)):
        for index, value in enumerate(data):
            if value:
                location = f"{path}.{index}" if isinstance(value, (dict, list, tuple)) else path
                return first_error(value, location)
    elif data:
        return path or None, str(data)
    return path or None, "Solicitud inválida"


def uniform_exception_handler(exc, context):
    if isinstance(exc, BusinessError):
        set_rollback()
        status_code = 404 if isinstance(exc, NotFoundError) else 409
        return Response({"message": exc.message, "field": exc.field}, status=status_code)
    if isinstance(exc, IntegrityError):
        set_rollback()
        return Response({"message": "Conflicto con los datos existentes", "field": None}, status=409)
    response = exception_handler(exc, context)
    if response is None:
        set_rollback()
        logger.error("Error inesperado en la API", exc_info=(type(exc), exc, exc.__traceback__))
        return Response({"message": "Error interno del servidor", "field": None}, status=500)
    field, message = first_error(response.data)
    response.data = {"message": message, "field": field}
    return response


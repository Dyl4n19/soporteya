from django.db import IntegrityError
from rest_framework.response import Response
from rest_framework.views import exception_handler

from soporte.application.exceptions import BusinessError


def uniform_exception_handler(exc, context):
    if isinstance(exc, BusinessError):
        return Response({"message": exc.message, "field": exc.field}, status=exc.status_code)
    if isinstance(exc, IntegrityError):
        return Response({"message": "Conflicto con los datos existentes", "field": None}, status=409)
    response = exception_handler(exc, context)
    if response is None:
        return None
    data = response.data
    if isinstance(data, dict):
        field = next((key for key in data if key not in {"detail", "non_field_errors"}), None)
        raw = data.get(field) if field else data.get("detail") or data.get("non_field_errors")
        if isinstance(raw, (list, tuple)):
            raw = raw[0] if raw else "Solicitud inválida"
        message = str(raw or "Solicitud inválida")
    else:
        field, message = None, str(data)
    response.data = {"message": message, "field": field}
    return response


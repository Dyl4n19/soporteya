from collections.abc import Mapping

from rest_framework.permissions import SAFE_METHODS, BasePermission


def user_role(user):
    if not user or not user.is_authenticated or not user.is_active:
        return "SIN_ROL"
    if user.is_superuser:
        return "SUPERVISOR"
    groups = set(user.groups.values_list("name", flat=True))
    return next((role for role in ("SUPERVISOR", "TECNICO") if role in groups), "SIN_ROL")


class IsSupervisorOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        role = user_role(request.user)
        return role == "SUPERVISOR" or (role == "TECNICO" and request.method in SAFE_METHODS)


class IsSupervisor(BasePermission):
    def has_permission(self, request, view):
        return user_role(request.user) == "SUPERVISOR"


class TicketRolePermission(BasePermission):
    def has_permission(self, request, view):
        role = user_role(request.user)
        if role == "SUPERVISOR":
            return True
        if role != "TECNICO":
            return False
        if view.action in {"list", "retrieve", "cambiar_estado"}:
            return True
        return (view.action in {"update", "partial_update"} and isinstance(request.data, Mapping) and bool(request.data)
                and set(request.data) == {"estado"})


class ComentarioRolePermission(BasePermission):
    def has_permission(self, request, view):
        role = user_role(request.user)
        return role == "SUPERVISOR" or (role == "TECNICO" and view.action in {"list", "retrieve", "create"})


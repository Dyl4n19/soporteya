from rest_framework.permissions import BasePermission


def user_role(user):
    if user.is_superuser:
        return "SUPERVISOR"
    group = user.groups.values_list("name", flat=True).first()
    return (group or "SIN_ROL").upper()


class IsSupervisorOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in {"GET", "HEAD", "OPTIONS"} or user_role(request.user) == "SUPERVISOR"


class TicketRolePermission(BasePermission):
    def has_permission(self, request, view):
        if view.action == "destroy":
            return user_role(request.user) == "SUPERVISOR"
        return True


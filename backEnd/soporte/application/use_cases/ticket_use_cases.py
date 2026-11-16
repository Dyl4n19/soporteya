from django.db import transaction
from django.utils import timezone

from soporte.application.exceptions import InvalidStateError, RuleViolationError


TRANSICIONES = {
    "ABIERTO": {"ASIGNADO"},
    "ASIGNADO": {"EN_PROGRESO"},
    "EN_PROGRESO": {"RESUELTO"},
    "RESUELTO": {"CERRADO", "EN_PROGRESO"},
    "CERRADO": set(),
}


class TicketUseCases:
    def __init__(self, ticket_repository, empresa_repository, tecnico_repository, comentario_repository):
        self.tickets = ticket_repository
        self.empresas = empresa_repository
        self.tecnicos = tecnico_repository
        self.comentarios = comentario_repository

    def crear(self, data):
        empresa = self.empresas.get(data["empresa_id"])
        if empresa.plan == "PREMIUM" and data.get("prioridad") in {"BAJA", "MEDIA", None}:
            data["prioridad"] = "ALTA"
        if data.get("tecnico_id"):
            tecnico = self.tecnicos.get(data["tecnico_id"])
            if not tecnico.activo:
                raise RuleViolationError("El técnico asignado debe estar activo", "tecnico_id")
            data["estado"] = "ASIGNADO"
        return self.tickets.save(data)

    @transaction.atomic(using="negocio")
    def cambiar_estado(self, ticket_id, nuevo_estado):
        ticket = self.tickets.get(ticket_id)
        if nuevo_estado not in TRANSICIONES[ticket.estado]:
            raise InvalidStateError(f"No se permite pasar de {ticket.estado} a {nuevo_estado}", "estado")
        if nuevo_estado == "ASIGNADO":
            if not ticket.tecnico_id:
                raise RuleViolationError("Debe asignar un técnico", "tecnico_id")
            if not ticket.tecnico.activo:
                raise RuleViolationError("El técnico asignado debe estar activo", "tecnico_id")
        if nuevo_estado == "RESUELTO" and not self.comentarios.for_ticket(ticket_id).exists():
            raise RuleViolationError("Debe existir al menos un comentario antes de resolver", "estado")
        ticket.estado = nuevo_estado
        ticket.fecha_cierre = timezone.now() if nuevo_estado == "CERRADO" else None
        ticket.save(update_fields=["estado", "fecha_cierre"])
        return ticket

    def eliminar(self, ticket_id):
        ticket = self.tickets.get(ticket_id)
        if ticket.estado != "ABIERTO":
            raise RuleViolationError("Solo se puede eliminar un ticket abierto", "estado")
        self.tickets.delete(ticket)

    def reporte(self):
        vencidos = self.tickets.overdue()
        promedios = self.tickets.average_resolution_by_technician()
        return vencidos, promedios


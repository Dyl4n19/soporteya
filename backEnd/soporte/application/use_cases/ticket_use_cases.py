from collections.abc import Mapping
from dataclasses import asdict
from datetime import datetime, timezone

from soporte.application.exceptions import InvalidStateError, RuleViolationError
from soporte.domain.entities import Ticket
from soporte.domain.ports import (CategoriaRepositoryPort, ComentarioRepositoryPort,
                                 EmpresaRepositoryPort, TecnicoRepositoryPort, TicketRepositoryPort)


TRANSICIONES = {
    "ABIERTO": {"ASIGNADO"},
    "ASIGNADO": {"EN_PROGRESO"},
    "EN_PROGRESO": {"RESUELTO"},
    "RESUELTO": {"CERRADO", "EN_PROGRESO"},
    "CERRADO": set(),
}


class TicketUseCases:
    def __init__(self, ticket_repository: TicketRepositoryPort, empresa_repository: EmpresaRepositoryPort,
                 tecnico_repository: TecnicoRepositoryPort, comentario_repository: ComentarioRepositoryPort,
                 categoria_repository: CategoriaRepositoryPort):
        self.tickets = ticket_repository
        self.empresas = empresa_repository
        self.tecnicos = tecnico_repository
        self.comentarios = comentario_repository
        self.categorias = categoria_repository

    def crear(self, data: Mapping[str, object]) -> Ticket:
        data = dict(data)
        empresa = self.empresas.get(data["empresa_id"])
        self.categorias.get(data["categoria_id"])
        if empresa.plan == "PREMIUM" and data.get("prioridad") in {"BAJA", "MEDIA", None}:
            data["prioridad"] = "ALTA"
        if data.get("tecnico_id"):
            tecnico = self.tecnicos.get(data["tecnico_id"])
            if not tecnico.activo:
                raise RuleViolationError("El técnico asignado debe estar activo", "tecnico_id")
            data["estado"] = "ASIGNADO"
        return self.tickets.save(data)

    def cambiar_estado(self, ticket_id: int, nuevo_estado: str) -> Ticket:
        ticket = self.tickets.get(ticket_id)
        if nuevo_estado not in TRANSICIONES.get(ticket.estado, set()):
            raise InvalidStateError(f"No se permite pasar de {ticket.estado} a {nuevo_estado}", "estado")
        if nuevo_estado == "ASIGNADO":
            if not ticket.id_tecnico:
                raise RuleViolationError("Debe asignar un técnico", "tecnico_id")
            if not self.tecnicos.get(ticket.id_tecnico).activo:
                raise RuleViolationError("El técnico asignado debe estar activo", "tecnico_id")
        if nuevo_estado == "RESUELTO" and not self.comentarios.for_ticket(ticket_id):
            raise RuleViolationError("Debe existir al menos un comentario antes de resolver", "estado")
        return self.tickets.save({
            "estado": nuevo_estado,
            "fecha_cierre": datetime.now(timezone.utc) if nuevo_estado == "CERRADO" else None,
        }, ticket_id)

    def eliminar(self, ticket_id: int) -> None:
        ticket = self.tickets.get(ticket_id)
        if ticket.estado != "ABIERTO":
            raise RuleViolationError("Solo se puede eliminar un ticket abierto", "estado")
        self.tickets.delete(ticket_id)

    def reporte(self):
        vencidos = self.tickets.overdue()
        empresas = {empresa.id_empresa: empresa for empresa in self.empresas.list()}
        categorias = {categoria.id_categoria: categoria for categoria in self.categorias.list()}
        return {
            "tickets_vencidos": [{
                "id_ticket": ticket.id_ticket, "titulo": ticket.titulo,
                "empresa": empresas[ticket.id_empresa].razon_social, "estado": ticket.estado,
                "horas_sla": categorias[ticket.id_categoria].horas_sla,
                "fecha_creacion": ticket.fecha_creacion,
            } for ticket in vencidos],
            "promedio_resolucion_por_tecnico": [
                asdict(promedio) for promedio in self.tickets.average_resolution_by_technician()
            ],
        }


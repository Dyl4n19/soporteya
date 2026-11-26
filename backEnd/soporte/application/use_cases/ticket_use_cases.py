from collections.abc import Mapping
from dataclasses import asdict
from datetime import datetime, timezone

from soporte.application.exceptions import InvalidStateError, RuleViolationError
from soporte.application.use_cases.comentario_use_cases import ComentarioUseCases
from soporte.domain.entities import Ticket
from soporte.domain.ports import (CategoriaRepositoryPort, ComentarioRepositoryPort,
                                 EmpresaRepositoryPort, TecnicoRepositoryPort, TicketRepositoryPort, UnitOfWorkPort)


TRANSICIONES = {
    "ABIERTO": {"ASIGNADO"},
    "ASIGNADO": {"EN_PROGRESO"},
    "EN_PROGRESO": {"RESUELTO"},
    "RESUELTO": {"CERRADO", "EN_PROGRESO"},
    "CERRADO": set(),
}


class TicketUseCases:
    editable_fields = {"empresa_id", "categoria_id", "tecnico_id", "titulo", "descripcion", "prioridad"}

    def __init__(self, ticket_repository: TicketRepositoryPort, empresa_repository: EmpresaRepositoryPort,
                 tecnico_repository: TecnicoRepositoryPort, comentario_repository: ComentarioRepositoryPort,
                 categoria_repository: CategoriaRepositoryPort, unit_of_work: UnitOfWorkPort):
        self.tickets = ticket_repository
        self.empresas = empresa_repository
        self.tecnicos = tecnico_repository
        self.comentarios = comentario_repository
        self.categorias = categoria_repository
        self.unit_of_work = unit_of_work

    def listar(self, **query) -> list[Ticket]:
        return self.tickets.list(**query)

    def obtener(self, ticket_id: int) -> Ticket:
        return self.tickets.get(ticket_id)

    def detalles(self, rows: list[Ticket]) -> list[dict]:
        if not rows:
            return []
        companies = {row.id_empresa: row for row in self.empresas.list()}
        categories = {row.id_categoria: row for row in self.categorias.list()}
        technicians = {row.id_tecnico: row for row in self.tecnicos.list()}
        ahora = datetime.now(timezone.utc)
        result = []
        for ticket in rows:
            data = asdict(ticket)
            data["empresa_id"] = data.pop("id_empresa")
            data["categoria_id"] = data.pop("id_categoria")
            data["tecnico_id"] = data.pop("id_tecnico")
            data["empresa_nombre"] = companies[ticket.id_empresa].razon_social
            data["categoria_nombre"] = categories[ticket.id_categoria].nombre
            data["horas_sla"] = categories[ticket.id_categoria].horas_sla
            data["vencido"] = self.esta_vencido(ticket, data["horas_sla"], ahora)
            data["tecnico_nombre"] = technicians[ticket.id_tecnico].nombre if ticket.id_tecnico else None
            data["comentarios"] = [asdict(comment) for comment in self.comentarios.for_ticket(ticket.id_ticket)]
            result.append(data)
        return result

    def validar_datos(self, data: Mapping[str, object], *, editing: bool = False) -> dict:
        values = dict(data)
        for field, limit in (("titulo", 150), ("descripcion", None)):
            value = values.get(field)
            minimum = 5 if field == "titulo" else 10
            if not isinstance(value, str) or len(value.strip()) < minimum or (limit and len(value) > limit):
                raise RuleViolationError(f"El campo {field} no tiene una longitud válida", field)
        empresa = self.empresas.get(values["empresa_id"])
        self.categorias.get(values["categoria_id"])
        priority = values.get("prioridad", "MEDIA")
        if priority not in {"BAJA", "MEDIA", "ALTA", "CRITICA"}:
            raise RuleViolationError("Prioridad inválida", "prioridad")
        if empresa.plan == "PREMIUM" and priority in {"BAJA", "MEDIA"}:
            if editing:
                raise RuleViolationError("Una empresa PREMIUM requiere prioridad ALTA o CRITICA", "prioridad")
            priority = "ALTA"
        values["prioridad"] = priority
        if values.get("tecnico_id") is not None:
            if not self.tecnicos.get(values["tecnico_id"]).activo:
                raise RuleViolationError("El técnico asignado debe estar activo", "tecnico_id")
        return values

    def crear(self, data: Mapping[str, object], autor: str = "Sistema") -> Ticket:
        values = dict(data)
        details = values.pop("comentarios", [])
        values = self.validar_datos(values)
        values["estado"] = "ASIGNADO" if values.get("tecnico_id") is not None else "ABIERTO"
        with self.unit_of_work.atomic():
            ticket = self.tickets.save(values)
            for detail in details:
                ComentarioUseCases.validar_texto(detail["texto"])
                self.comentarios.add(ticket.id_ticket, autor, detail["texto"].strip())
            return ticket

    def validar_edicion(self, ticket: Ticket, data: Mapping[str, object]) -> dict:
        current = {
            "empresa_id": ticket.id_empresa, "categoria_id": ticket.id_categoria,
            "tecnico_id": ticket.id_tecnico, "titulo": ticket.titulo,
            "descripcion": ticket.descripcion, "prioridad": ticket.prioridad,
        }
        changes = {field: value for field, value in data.items()
                   if field in self.editable_fields and current[field] != value}
        if not changes:
            return {}
        if ticket.estado != "ABIERTO":
            raise RuleViolationError("Solo se editan los datos de un ticket abierto", "estado")
        combined = current | changes
        if "prioridad" not in changes and self.empresas.get(combined["empresa_id"]).plan == "PREMIUM":
            if combined["prioridad"] in {"BAJA", "MEDIA"}:
                combined["prioridad"] = "ALTA"
                changes["prioridad"] = "ALTA"
        self.validar_datos(combined, editing=True)
        return changes

    def actualizar(self, ticket_id: int, data: Mapping[str, object], autor: str = "Sistema") -> Ticket:
        with self.unit_of_work.atomic():
            ticket = self.tickets.lock(ticket_id)
            changes = self.validar_edicion(ticket, data)
            if changes:
                ticket = self.tickets.save(changes, ticket_id)
            for detail in data.get("comentarios", []):
                if ticket.estado == "CERRADO":
                    raise RuleViolationError("No se pueden agregar comentarios a un ticket cerrado", "estado")
                ComentarioUseCases.validar_texto(detail["texto"])
                self.comentarios.add(ticket_id, autor, detail["texto"].strip())
            next_state = data.get("estado")
            if next_state is None and ticket.estado == "ABIERTO" and ticket.id_tecnico is not None:
                next_state = "ASIGNADO"
            if next_state is not None and next_state != ticket.estado:
                self.validar_transicion(ticket, next_state)
                ticket = self.tickets.save({
                    "estado": next_state,
                    "fecha_cierre": datetime.now(timezone.utc) if next_state == "CERRADO" else None,
                }, ticket_id)
            if "vencido" in data:
                horas_sla = self.categorias.get(ticket.id_categoria).horas_sla
                if data["vencido"] != self.esta_vencido(ticket, horas_sla, datetime.now(timezone.utc)):
                    raise RuleViolationError("El vencimiento indicado no coincide con el SLA calculado del ticket", "vencido")
            return ticket

    def validar_transicion(self, ticket: Ticket, nuevo_estado: str) -> None:
        if nuevo_estado not in TRANSICIONES.get(ticket.estado, set()):
            raise InvalidStateError(f"No se permite pasar de {ticket.estado} a {nuevo_estado}", "estado")
        if nuevo_estado == "ASIGNADO":
            if not ticket.id_tecnico:
                raise RuleViolationError("Debe asignar un técnico", "tecnico_id")
            if not self.tecnicos.get(ticket.id_tecnico).activo:
                raise RuleViolationError("El técnico asignado debe estar activo", "tecnico_id")
        if nuevo_estado == "RESUELTO" and not self.comentarios.for_ticket(ticket.id_ticket):
            raise RuleViolationError("Debe existir al menos un comentario antes de resolver", "estado")

    def cambiar_estado(self, ticket_id: int, nuevo_estado: str) -> Ticket:
        return self.actualizar(ticket_id, {"estado": nuevo_estado})

    def eliminar(self, ticket_id: int) -> None:
        with self.unit_of_work.atomic():
            ticket = self.tickets.lock(ticket_id)
            if ticket.estado != "ABIERTO":
                raise RuleViolationError("Solo se puede eliminar un ticket abierto", "estado")
            self.tickets.delete(ticket_id)

    @staticmethod
    def esta_vencido(ticket: Ticket, horas_sla: int, ahora: datetime) -> bool:
        return (ticket.estado not in {"RESUELTO", "CERRADO"} and ticket.fecha_creacion is not None
                and (ahora - ticket.fecha_creacion).total_seconds() > horas_sla * 3600)

    def vencidos(self, ahora: datetime | None = None) -> list[Ticket]:
        ahora = ahora or datetime.now(timezone.utc)
        categorias = {categoria.id_categoria: categoria for categoria in self.categorias.list()}
        return [ticket for ticket in self.tickets.list()
                if self.esta_vencido(ticket, categorias[ticket.id_categoria].horas_sla, ahora)]

    def reporte(self):
        empresas = {empresa.id_empresa: empresa for empresa in self.empresas.list()}
        categorias = {categoria.id_categoria: categoria for categoria in self.categorias.list()}
        return {
            "tickets_vencidos": [{
                "id_ticket": ticket.id_ticket, "titulo": ticket.titulo,
                "empresa": empresas[ticket.id_empresa].razon_social, "estado": ticket.estado,
                "horas_sla": categorias[ticket.id_categoria].horas_sla,
                "fecha_creacion": ticket.fecha_creacion,
            } for ticket in self.vencidos()],
            "promedio_resolucion_por_tecnico": [
                asdict(promedio) for promedio in self.tickets.average_resolution_by_technician()
            ],
        }


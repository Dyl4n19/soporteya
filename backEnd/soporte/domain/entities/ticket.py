from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class Ticket:
    id_ticket: int | None
    id_empresa: int
    id_categoria: int
    titulo: str
    descripcion: str
    prioridad: str
    estado: str = "ABIERTO"
    id_tecnico: int | None = None
    fecha_creacion: datetime | None = None
    fecha_cierre: datetime | None = None


@dataclass(slots=True)
class PromedioResolucionTecnico:
    id_tecnico: int
    tecnico: str
    horas_promedio: float


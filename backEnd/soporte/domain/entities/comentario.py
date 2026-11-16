from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class Comentario:
    id_ticket: int
    numero: int
    autor: str
    texto: str
    fecha: datetime | None = None


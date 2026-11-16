from dataclasses import dataclass


@dataclass(slots=True)
class Categoria:
    id_categoria: int | None
    nombre: str
    horas_sla: int
    activo: bool = True


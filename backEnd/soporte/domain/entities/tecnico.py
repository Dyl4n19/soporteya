from dataclasses import dataclass


@dataclass(slots=True)
class Tecnico:
    id_tecnico: int | None
    rut: str
    nombre: str
    email: str
    activo: bool = True


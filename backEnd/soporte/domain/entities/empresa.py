from dataclasses import dataclass


@dataclass(slots=True)
class Empresa:
    id_empresa: int | None
    rut: str
    razon_social: str
    plan: str = "BASICO"
    activo: bool = True


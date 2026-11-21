"""Persistencia del proyecto y estado compartido entre módulos."""

import json
from dataclasses import asdict, dataclass, field


@dataclass
class Proyecto:
    nombre: str = "Sin título"
    trafico: dict | None = None
    subrasante: dict | None = None
    flexible: dict | None = None
    clima: dict | None = None


def guardar_proyecto(proyecto: Proyecto, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(asdict(proyecto), f, indent=2, ensure_ascii=False)


def cargar_proyecto(path: str) -> Proyecto:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return Proyecto(**data)

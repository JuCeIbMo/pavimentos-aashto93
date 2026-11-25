"""Configuraciones de ejes para agregar rápido un vehículo en el módulo 1.

No se inventan pesos: solo se da la disposición de ejes y las cargas quedan vacías
para completarlas desde el enunciado, el pesaje o la norma de pesos y dimensiones.
"""

from __future__ import annotations

CONFIGURACIONES = [
    ("2 ejes simples", ["simple", "simple"]),
    ("Simple + tándem", ["simple", "tandem"]),
    ("Simple + trídem", ["simple", "tridem"]),
    ("Simple + simple + tándem", ["simple", "simple", "tandem"]),
    ("Simple + tándem + tándem", ["simple", "tandem", "tandem"]),
    ("Simple + tándem + trídem", ["simple", "tandem", "tridem"]),
    ("1 eje simple", ["simple"]),
]

NOMBRE_EJE = {"simple": "Simple", "tandem": "Tándem", "tridem": "Trídem"}


def opciones() -> list[tuple[str, dict]]:
    """Opciones para el selector «Agregar vehículo»: (etiqueta, plantilla)."""
    out = []
    for nombre, tipos in CONFIGURACIONES:
        out.append((nombre,
                    {"nombre": "Vehículo", "pesado": False, "ejes": [[t, 0.0] for t in tipos], "unidad": None,
                     "fuente": None}))
    return out

"""Vehículos para agregar rápido en el módulo 1.

No se inventan pesos: las cargas por eje salen de una fuente citada (la tabla de
vehículos del Práctico 3 de la cátedra) o se dejan en cero para que el usuario las
complete desde su enunciado, pesaje o norma de pesos y dimensiones.
"""

from __future__ import annotations

FUENTE_PRACTICO3 = "Práctico 3 de la cátedra Carreteras II (tabla de vehículos, cargas en toneladas)"

# (nombre, pesado, ejes en toneladas) — tal cual la tabla del práctico
PRACTICO3 = [
    ("Automóvil, jeep y vagoneta", False, [["simple", 1], ["simple", 1]]),
    ("Camioneta hasta 2 t", False, [["simple", 1], ["simple", 2]]),
    ("Minibús", False, [["simple", 1], ["simple", 2]]),
    ("Bus 12-21 asientos", True, [["simple", 1], ["simple", 4]]),
    ("Bus 21-35 asientos", True, [["simple", 2], ["simple", 11]]),
    ("Bus 35 asientos o más", True, [["simple", 7], ["tandem", 18]]),
    ("Camión mediano hasta 6 t", True, [["simple", 7], ["simple", 11]]),
    ("Camión grande 2 ejes", True, [["simple", 7], ["tridem", 25]]),
    ("Camión grande 3 ejes", True, [["simple", 7], ["simple", 7], ["tandem", 18]]),
    ("Semirremolque", True, [["simple", 7], ["tridem", 25], ["tandem", 18]]),
    ("Camión con remolque", True, [["simple", 7], ["simple", 11], ["tridem", 25], ["tandem", 18]]),
]

# configuraciones sin cargas: el usuario escribe los pesos
CONFIGURACIONES = [
    ("2 ejes simples", ["simple", "simple"]),
    ("Simple + tándem", ["simple", "tandem"]),
    ("Simple + trídem", ["simple", "tridem"]),
    ("Simple + simple + tándem", ["simple", "simple", "tandem"]),
    ("Simple + tándem + tándem", ["simple", "tandem", "tandem"]),
    ("Simple + tándem + trídem", ["simple", "tandem", "tridem"]),
    ("Un eje simple (a completar)", ["simple"]),
]

NOMBRE_EJE = {"simple": "Simple", "tandem": "Tándem", "tridem": "Trídem"}


def opciones() -> list[tuple[str, dict]]:
    """Opciones para el selector «Agregar vehículo»: (etiqueta, plantilla)."""
    out = []
    for nombre, pesado, ejes in PRACTICO3:
        desc = " + ".join(f"{NOMBRE_EJE[t].lower()} {c:g} t" for t, c in ejes)
        out.append((f"📘 {nombre} · {desc}",
                    {"nombre": nombre, "pesado": pesado, "ejes": ejes, "unidad": "t", "fuente": FUENTE_PRACTICO3}))
    for nombre, tipos in CONFIGURACIONES:
        out.append((f"⚙️ {nombre} · cargas a completar",
                    {"nombre": "Vehículo", "pesado": False, "ejes": [[t, 0.0] for t in tipos], "unidad": None,
                     "fuente": None}))
    return out

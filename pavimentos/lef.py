"""Carga de las tablas LEF (AASHTO '93, apéndice D) y lookup con interpolación bilineal."""

import json
import os

from math import isclose


class DatosInvalidos(ValueError):
    """Dato de entrada fuera de rango o inválido."""


RUTA_DEFECTO = os.path.join(os.path.dirname(__file__), "..", "data", "lef.json")

CARGAS_MIN = 2.0
CARGAS_MAX = 90.0  # simple: hasta 50 kip; tándem y trídem: hasta 90 kip (tablas D)
SN_MIN = 1
SN_MAX = 6
PTS = ("2.0", "2.5", "3.0")
TIPOS = ("simple", "tandem", "tridem")


def cargar_lef(ruta: str = RUTA_DEFECTO) -> dict:
    """Carga las matrices LEF desde JSON."""
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def _interp(x: float, x0: float, x1: float, y0: float, y1: float) -> float:
    return y0 + (y1 - y0) * (x - x0) / (x1 - x0)


def _ubicar(x: float, xs: list[float]) -> tuple[int, float]:
    """Índice i tal que xs[i] <= x <= xs[i+1], y la fracción dentro del tramo."""
    if x <= xs[0]:
        return 0, 0.0
    if x >= xs[-1]:
        return len(xs) - 2, 1.0
    for i in range(len(xs) - 1):
        if xs[i] <= x <= xs[i + 1]:
            return i, (x - xs[i]) / (xs[i + 1] - xs[i])
    return len(xs) - 2, 1.0


def lef_eje(tablas: dict, tipo_eje: str, pt: float, carga_kip: float, sn: float) -> float:
    """LEF de un eje por lookup en las tablas, con interpolación bilineal en (carga, SN)."""
    if tipo_eje not in TIPOS:
        raise DatosInvalidos(f"Tipo de eje desconocido: {tipo_eje}")
    pt_s = f"{pt:.1f}"
    if pt_s not in PTS:
        raise DatosInvalidos(f"pt fuera de rango: {pt}")
    if not (SN_MIN <= sn <= SN_MAX):
        raise DatosInvalidos(f"SN fuera de [1, 6]: {sn}")
    bloque = tablas["flexible"][tipo_eje][pt_s]
    cargas = bloque["cargas"]
    if not (cargas[0] <= carga_kip <= cargas[-1]):
        raise DatosInvalidos(
            f"Carga de eje {tipo_eje} fuera de la tabla AASHTO [{cargas[0]:g}, {cargas[-1]:g}] kip: {carga_kip:.1f} kip")
    sns = bloque["sn"]
    lef = bloque["lef"]

    ci, fc = _ubicar(carga_kip, cargas)
    sj = int(sn) - 1
    fs = sn - int(sn)
    if sj >= len(sns) - 1:
        sj = len(sns) - 2
        fs = 1.0

    v00 = lef[sj][ci]
    v01 = lef[sj][ci + 1]
    v10 = lef[sj + 1][ci]
    v11 = lef[sj + 1][ci + 1]

    abajo = _interp(fc, 0.0, 1.0, v00, v01)
    arriba = _interp(fc, 0.0, 1.0, v10, v11)
    return _interp(fs, 0.0, 1.0, abajo, arriba)

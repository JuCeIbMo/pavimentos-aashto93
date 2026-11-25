"""Validación del paquete contra ejercicios resueltos (cátedra y bibliografía).

Cada ejercicio vive en `data/validacion/NN_nombre.json` con:
- `fuente`: título, tipo y referencia bibliográfica.
- `proyecto`: un `ProyectoFlexible` completo (se puede cargar en la app).
- `esperados`: valores de la fuente con su tolerancia. `tipo = "informativo"` marca
  comparaciones que se muestran, pero que no cuentan como falla (p. ej. errores de la fuente).
"""

from __future__ import annotations

import glob
import json
import os

from pavimentos.modelo import ProyectoFlexible
from pavimentos.resolver import resolver

CARPETA = os.path.join(os.path.dirname(__file__), "..", "data", "validacion")


def obtener(res: dict, clave: str):
    """Lee `a.b.0.c` dentro del resultado del resolver."""
    x = res
    for parte in clave.split("."):
        if x is None:
            return None
        if isinstance(x, list):
            x = x[int(parte)]
        else:
            x = x.get(parte)
    return x


def listar() -> list[dict]:
    """Ejercicios disponibles, ordenados por nombre de archivo."""
    out = []
    for ruta in sorted(glob.glob(os.path.join(CARPETA, "[0-9][0-9]_*.json"))):
        with open(ruta, encoding="utf-8") as f:
            d = json.load(f)
        d["id"] = os.path.splitext(os.path.basename(ruta))[0]
        out.append(d)
    return out


def comparar(ejercicio: dict) -> dict:
    proyecto = ProyectoFlexible.from_dict(ejercicio["proyecto"])
    res = resolver(proyecto)
    filas = []
    for e in ejercicio["esperados"]:
        app = obtener(res, e["clave"])
        ref = e["valor"]
        if app is None:
            dif, ok = None, False
        else:
            dif = (app - ref) / ref if ref else app - ref
            ok = abs(dif) <= e.get("tol_rel", 0.01) + 1e-12
        filas.append({**e, "app": app, "dif_rel": dif, "cumple": ok})
    exactos = [f for f in filas if f.get("tipo", "exacto") != "informativo"]
    return {
        "id": ejercicio.get("id"),
        "fuente": ejercicio["fuente"],
        "proyecto": proyecto,
        "resultado": res,
        "filas": filas,
        "aprobado": all(f["cumple"] for f in exactos),
        "n_ok": sum(f["cumple"] for f in exactos),
        "n_total": len(exactos),
    }


def validar_todo() -> list[dict]:
    return [comparar(e) for e in listar()]

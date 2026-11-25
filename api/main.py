"""API HTTP del paquete: expone el motor de cálculo (`pavimentos`) a la interfaz web.

La interfaz (React, carpeta `web/`) guarda el proyecto como JSON y, en cada cambio,
lo manda a `/api/resolver`. Toda la lógica de ingeniería vive en `pavimentos/`;
este archivo solo traduce JSON ↔ objetos de Python.
"""

from __future__ import annotations

import math
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from pavimentos import catalogo
from pavimentos.ambiental import delta_psi_helada, delta_psi_hinchamiento
from pavimentos.exportar_excel import generar_excel
from pavimentos.exportar_pdf import generar_pdf
from pavimentos.modelo import ProyectoFlexible
from pavimentos.referencias import ECUACIONES, REFERENCIAS
from pavimentos.resolver import MINIMOS_AASHTO, limpiar, resolver
from pavimentos.sensibilidad import VARIABLES, barrido, comparar_escenarios, rango_por_defecto, tornado, valor_actual
from pavimentos.validacion import listar, validar_todo

RAIZ = Path(__file__).resolve().parent.parent

app = FastAPI(title="Pavimentos AASHTO 93", version="1.0")


# ----------------------------------------------------------------------------- utilidades
def _json_seguro(x: Any) -> Any:
    """Reemplaza NaN/inf (no válidos en JSON) y tuplas."""
    if isinstance(x, float):
        return None if (math.isnan(x) or math.isinf(x)) else x
    if isinstance(x, dict):
        return {k: _json_seguro(v) for k, v in x.items() if not callable(v)}
    if isinstance(x, (list, tuple)):
        return [_json_seguro(v) for v in x]
    return x


def _proyecto(d: dict) -> ProyectoFlexible:
    try:
        return ProyectoFlexible.from_dict(d)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(422, f"Proyecto inválido: {e}") from e


def _archivo(nombre: str) -> str:
    base = re.sub(r"[^\w\- ]", "", nombre or "").strip().replace(" ", "_") or "proyecto"
    return base[:60]


def _adjunto(nombre: str, ext: str) -> dict:
    """Content-Disposition con nombre ASCII de respaldo y nombre UTF-8 (RFC 6266)."""
    from urllib.parse import quote
    import unicodedata
    base = _archivo(nombre)
    ascii_ = unicodedata.normalize("NFKD", base).encode("ascii", "ignore").decode() or "proyecto"
    return {"Content-Disposition": f'attachment; filename="{ascii_}.{ext}"; filename*=UTF-8\'\'{quote(base)}.{ext}'}


class ConProyecto(BaseModel):
    proyecto: dict


class PedidoBarrido(BaseModel):
    proyecto: dict
    variable: str
    desde: float | None = None
    hasta: float | None = None
    n: int = 31


class PedidoTornado(BaseModel):
    proyecto: dict
    variacion: float = 0.2
    metrica: str = "sn"


class Escenario(BaseModel):
    nombre: str
    cambios: dict[str, float] = {}


class PedidoEscenarios(BaseModel):
    proyecto: dict
    escenarios: list[Escenario]


class PedidoCurvaClima(BaseModel):
    proyecto: dict
    t_max: float | None = None


# ----------------------------------------------------------------------------- proyecto
@app.get("/api/proyecto/nuevo")
def proyecto_nuevo():
    return ProyectoFlexible().to_dict()


@app.get("/api/proyecto/inicial")
def proyecto_inicial():
    """Proyecto con datos de ejemplo para no empezar en blanco."""
    ruta = RAIZ / "data" / "proyecto_inicial.json"
    if ruta.exists():
        return ProyectoFlexible.from_json(ruta.read_text(encoding="utf-8")).to_dict()
    return ProyectoFlexible().to_dict()


@app.post("/api/resolver")
def api_resolver(body: ConProyecto):
    return _json_seguro(limpiar(resolver(_proyecto(body.proyecto))))


@app.get("/api/ejemplos")
def ejemplos():
    return [{"id": e["id"], "fuente": e["fuente"],
             "proyecto": ProyectoFlexible.from_dict(e["proyecto"]).to_dict()} for e in listar()]


@app.get("/api/catalogo")
def api_catalogo():
    return {"opciones": [{"etiqueta": et, **pl} for et, pl in catalogo.opciones()]}


@app.get("/api/referencias")
def referencias():
    return {"referencias": REFERENCIAS, "ecuaciones": ECUACIONES,
            "minimos_aashto": [{"w_max": w if math.isfinite(w) else None, "carpeta": c, "base": b}
                               for w, c, b in MINIMOS_AASHTO]}


# ----------------------------------------------------------------------------- exportación
@app.post("/api/exportar/pdf")
def exportar_pdf(body: ConProyecto):
    p = _proyecto(body.proyecto)
    res = resolver(p)
    if not res.get("capas"):
        raise HTTPException(400, "Completá el diseño antes de exportar.")
    return Response(generar_pdf(p, res), media_type="application/pdf",
                    headers=_adjunto(p.nombre, "pdf"))


@app.post("/api/exportar/excel")
def exportar_excel(body: ConProyecto):
    p = _proyecto(body.proyecto)
    res = resolver(p)
    if not res.get("capas"):
        raise HTTPException(400, "Completá el diseño antes de exportar.")
    return Response(generar_excel(p, res),
                    media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers=_adjunto(p.nombre, "xlsx"))


# ----------------------------------------------------------------------------- validación
@lru_cache(maxsize=1)
def _validacion():
    out = []
    for v in validar_todo():
        out.append(_json_seguro({**{k: v[k] for k in ("id", "fuente", "filas", "aprobado", "n_ok", "n_total")},
                                 "proyecto": v["proyecto"].to_dict()}))
    return out


@app.get("/api/validacion")
def validacion():
    return _validacion()


# ----------------------------------------------------------------------------- sensibilidad
@app.get("/api/sensibilidad/variables")
def variables():
    return [{"clave": v.clave, "etiqueta": v.etiqueta, "unidad": v.unidad, "minimo": v.minimo,
             "maximo": v.maximo, "explicacion": v.explicacion} for v in VARIABLES.values()]


@app.post("/api/sensibilidad/barrido")
def api_barrido(body: PedidoBarrido):
    if body.variable not in VARIABLES:
        raise HTTPException(422, "Variable desconocida.")
    p = _proyecto(body.proyecto)
    x0 = valor_actual(p, body.variable)
    if x0 is None:
        raise HTTPException(400, "Completá el diseño primero.")
    defecto = rango_por_defecto(p, body.variable, body.n)
    lo = body.desde if body.desde is not None else defecto[0]
    hi = body.hasta if body.hasta is not None else defecto[-1]
    if hi <= lo:
        raise HTTPException(422, "«Hasta» debe ser mayor que «Desde».")
    n = max(5, min(body.n, 61))
    if body.variable == "w18":
        a, b = math.log10(lo), math.log10(hi)
        xs = [10 ** (a + (b - a) * i / (n - 1)) for i in range(n)]
    else:
        xs = [lo + (hi - lo) * i / (n - 1) for i in range(n)]
    puntos = [x for x in barrido(p, body.variable, xs) if x.get("sn_requerido") is not None]
    return _json_seguro({"x0": x0, "desde": lo, "hasta": hi, "puntos": puntos})


@app.post("/api/sensibilidad/tornado")
def api_tornado(body: PedidoTornado):
    return _json_seguro(tornado(_proyecto(body.proyecto), body.variacion, body.metrica))


@app.post("/api/sensibilidad/escenarios")
def api_escenarios(body: PedidoEscenarios):
    p = _proyecto(body.proyecto)
    lista = [("Proyecto actual", p)]
    for e in body.escenarios:
        q = p.copia()
        for clave, v in e.cambios.items():
            if clave in VARIABLES:
                VARIABLES[clave].escribir(q, v)
        lista.append((e.nombre, q))
    return _json_seguro(comparar_escenarios(lista))


@app.post("/api/clima/curva")
def curva_clima(body: PedidoCurvaClima):
    c = _proyecto(body.proyecto).clima
    t_max = body.t_max or 30.0
    out = []
    for i in range(61):
        t = t_max * i / 60
        sw = delta_psi_hinchamiento(c.vr, c.ps, c.theta, t) if c.hinchamiento else 0.0
        fh = delta_psi_helada(c.helada.pf, c.helada.dpsi_max, c.helada.phi, t) if c.helada else 0.0
        out.append({"t": t, "sw": sw, "fh": fh, "total": sw + fh})
    return out


# ----------------------------------------------------------------------------- interfaz compilada
WEB = os.path.join(os.path.dirname(__file__), "..", "web", "dist")
if os.path.isdir(WEB):
    app.mount("/assets", StaticFiles(directory=os.path.join(WEB, "assets")), name="assets")

    @app.get("/{ruta:path}", include_in_schema=False)
    def spa(ruta: str):
        archivo = os.path.join(WEB, ruta)
        if ruta and os.path.isfile(archivo):
            return FileResponse(archivo)
        return FileResponse(os.path.join(WEB, "index.html"))

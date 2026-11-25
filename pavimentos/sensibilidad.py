"""Análisis de sensibilidad y comparación de escenarios.

Todo se apoya en `resolver`: se copia el proyecto, se cambia una variable y se
vuelve a resolver la cadena completa. Así la sensibilidad respeta los mismos
mínimos, redondeos y ajustes climáticos que el diseño real.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from pavimentos.modelo import ProyectoFlexible
from pavimentos.resolver import resolver


@dataclass(frozen=True)
class Variable:
    clave: str
    etiqueta: str
    unidad: str
    minimo: float
    maximo: float
    leer: Callable[[ProyectoFlexible, dict], float]
    escribir: Callable[[ProyectoFlexible, float], None]
    explicacion: str


def _set_w18(p: ProyectoFlexible, v: float):
    p.diseno.fuente_w18, p.diseno.w18_dato = "dato", v


def _set_mr(p: ProyectoFlexible, v: float):
    p.diseno.fuente_mr, p.diseno.mr_dato = "dato", v


def _set_m(p: ProyectoFlexible, v: float):
    p.diseno.base.m = v
    p.diseno.subbase.m = v


def _set_pt(p: ProyectoFlexible, v: float):
    p.diseno.pt = v


VARIABLES: dict[str, Variable] = {v.clave: v for v in [
    Variable("w18", "Tránsito W18", "ESAL", 5e4, 1e8,
             lambda p, r: r["diseno"]["w18"], _set_w18,
             "Más repeticiones de carga exigen más estructura, pero el SN crece con el logaritmo de W18: "
             "duplicar el tránsito no duplica el espesor."),
    Variable("mr", "M_R efectivo de la subrasante", "psi", 1000, 40000,
             lambda p, r: r["diseno"]["mr"], _set_mr,
             "Una subrasante más rígida soporta más: es la variable con más peso en el SN total."),
    Variable("r_pct", "Confiabilidad R", "%", 50, 99.9,
             lambda p, r: p.diseno.r_pct, lambda p, v: setattr(p.diseno, "r_pct", v),
             "Subir R reduce el riesgo de falla anticipada, pero el costo crece rápido por encima del 95 %."),
    Variable("so", "Desviación estándar So", "—", 0.30, 0.55,
             lambda p, r: p.diseno.so, lambda p, v: setattr(p.diseno, "so", v),
             "Mide la incertidumbre del tránsito y del comportamiento; multiplica a Z_R."),
    Variable("pt", "Serviciabilidad terminal pt", "—", 1.5, 3.0,
             lambda p, r: p.diseno.pt, _set_pt,
             "Un pt más alto (vía más importante) deja menos ΔPSI disponible y exige más SN."),
    Variable("m", "Coeficiente de drenaje m₂ = m₃", "—", 0.4, 1.4,
             lambda p, r: p.diseno.base.m, _set_m,
             "Un buen drenaje (m > 1) hace rendir más a base y subbase; uno malo (m < 1) obliga a engrosarlas."),
]}


def _metricas(res: dict) -> dict:
    if not res.get("capas"):
        return {"ok": False}
    c = res["capas"]
    return {
        "ok": res["ok"],
        "sn_requerido": res["diseno"]["sn_requerido"],
        "sn_total": c["sn_total"],
        "d1": c["capas"][0]["d"], "d2": c["capas"][1]["d"], "d3": c["capas"][2]["d"],
        "espesor_total": c["espesor_total"],
        "unidad": c["unidad"],
        "periodo": (res.get("clima") or {}).get("periodo"),
    }


def valor_actual(p: ProyectoFlexible, clave: str) -> float | None:
    res = resolver(p)
    if not res.get("diseno"):
        return None
    return VARIABLES[clave].leer(p, res)


def barrido(p: ProyectoFlexible, clave: str, valores: list[float]) -> list[dict]:
    """Resuelve el proyecto para cada valor de la variable."""
    var = VARIABLES[clave]
    out = []
    for x in valores:
        q = p.copia()
        var.escribir(q, x)
        out.append({"x": x, **_metricas(resolver(q))})
    return out


def rango_por_defecto(p: ProyectoFlexible, clave: str, n: int = 25) -> list[float]:
    var = VARIABLES[clave]
    base = valor_actual(p, clave)
    if clave == "w18":
        lo, hi = max(var.minimo, base / 5), min(var.maximo, base * 5)
        import math
        a, b = math.log10(lo), math.log10(hi)
        return [10 ** (a + (b - a) * i / (n - 1)) for i in range(n)]
    if clave == "mr":
        lo, hi = max(var.minimo, base * 0.4), min(var.maximo, base * 2.5)
    else:
        lo, hi = var.minimo, var.maximo
        if clave == "r_pct":
            lo, hi = 50.0, 99.9
    return [lo + (hi - lo) * i / (n - 1) for i in range(n)]


def tornado(p: ProyectoFlexible, variacion: float = 0.20, metrica: str = "sn") -> list[dict]:
    """Cuánto cambia el SN requerido (`metrica="sn"`) o el espesor total (`"espesor"`)
    si cada variable baja o sube un ±`variacion`.

    Para R se varía la probabilidad de falla (100 − R), que es lo que tiene sentido físico.
    """
    base_res = resolver(p)
    if not base_res.get("capas"):
        return []
    sn0 = base_res["diseno"]["sn_requerido"]
    filas = []
    for clave, var in VARIABLES.items():
        x0 = var.leer(p, base_res)
        if clave == "r_pct":
            falla = 100 - x0
            lo, hi = 100 - falla * (1 + variacion), 100 - falla * (1 - variacion)
        else:
            lo, hi = x0 * (1 - variacion), x0 * (1 + variacion)
        lo = min(max(lo, var.minimo), var.maximo)
        hi = min(max(hi, var.minimo), var.maximo)
        r_lo, r_hi = barrido(p, clave, [lo, hi])
        if not (r_lo.get("ok") or r_lo.get("sn_requerido")) or not r_hi.get("sn_requerido"):
            continue
        filas.append({
            "clave": clave, "etiqueta": var.etiqueta, "x0": x0, "x_lo": lo, "x_hi": hi,
            "sn_lo": r_lo["sn_requerido"], "sn_hi": r_hi["sn_requerido"],
            "esp_lo": r_lo["espesor_total"], "esp_hi": r_hi["espesor_total"],
            "rango_sn": abs(r_hi["sn_requerido"] - r_lo["sn_requerido"]),
            "rango_esp": abs(r_hi["espesor_total"] - r_lo["espesor_total"]),
        })
    clave_orden = "rango_sn" if metrica == "sn" else "rango_esp"
    filas.sort(key=lambda f: f[clave_orden], reverse=True)
    esp0 = base_res["capas"]["espesor_total"]
    return [{**f, "sn_base": sn0, "esp_base": esp0, "unidad": base_res["capas"]["unidad"]} for f in filas]


def comparar_escenarios(escenarios: list[tuple[str, ProyectoFlexible]]) -> list[dict]:
    """Resuelve cada escenario y devuelve una fila comparable por escenario."""
    out = []
    for nombre, q in escenarios:
        res = resolver(q)
        fila = {"escenario": nombre, **_metricas(res)}
        if res.get("diseno"):
            d = res["diseno"]
            fila.update({"w18": d["w18"], "mr": d["mr"], "r_pct": d["r_pct"], "so": d["so"],
                         "dpsi": d["dpsi"], "sn_adoptado": d["sn_adoptado"]})
        fila["avisos"] = [a["texto"] for a in res["avisos"] if a["nivel"] == "error"]
        out.append(fila)
    return out

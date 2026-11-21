"""Módulo 1 — Tránsito y ESAL (AASHTO '93)."""

from pavimentos.lef import lef_eje
from pavimentos.unidades import t_a_kip


def factor_crecimiento(r: float, n: float) -> float:
    """Factor de crecimiento compuesto ((1+r)^n - 1)/r; con r=0 devuelve n."""
    if r == 0:
        return n
    return ((1 + r) ** n - 1) / r


def factor_camion(vehiculo: dict, tablas: dict, pt: float, sn: float) -> float:
    """Factor de camión = suma de LEF de los ejes del vehículo."""
    return sum(lef_eje(tablas, tipo, pt, t_a_kip(carga_t), sn) for tipo, carga_t in vehiculo["ejes"])


def esal_vehiculo(vehiculo: dict, n: float, fd: float, fc: float,
                  tablas: dict, pt: float, sn: float) -> dict:
    """ESAL de un vehículo: {"fc", "esal1", "w"}."""
    fcam = factor_camion(vehiculo, tablas, pt, sn)
    esal1 = vehiculo["tpda"] * fcam * 365.0 * fd * fc
    return {"fc": fcam, "esal1": esal1, "w": esal1 * factor_crecimiento(vehiculo["r"], n)}


def esal_total(vehiculos: list[dict], n: float, fd: float, fc: float,
               tablas: dict, pt: float, sn: float) -> dict:
    """ESAL totales y desglose por vehículo."""
    total_w = 0.0
    total_esal1 = 0.0
    tpda_total = 0.0
    tpda_pesado = 0.0
    por_vehiculo = []
    for v in vehiculos:
        r = esal_vehiculo(v, n, fd, fc, tablas, pt, sn)
        total_w += r["w"]
        total_esal1 += r["esal1"]
        tpda_total += v["tpda"]
        if v.get("pesado"):
            tpda_pesado += v["tpda"]
        por_vehiculo.append({"nombre": v["nombre"], **r})
    pesados_pct = 100.0 * tpda_pesado / tpda_total if tpda_total else 0.0
    return {
        "total_w": total_w,
        "total_esal1": total_esal1,
        "tpda_total": tpda_total,
        "pesados_pct": pesados_pct,
        "por_vehiculo": por_vehiculo,
    }


def w_t(vehiculos: list[dict], t: float, fd: float, fc: float,
        tablas: dict, pt: float, sn: float) -> float:
    """ESAL acumulados en t años (admite t no entero)."""
    total = 0.0
    for v in vehiculos:
        fcam = factor_camion(v, tablas, pt, sn)
        esal1 = v["tpda"] * fcam * 365.0 * fd * fc
        total += esal1 * factor_crecimiento(v["r"], t)
    return total

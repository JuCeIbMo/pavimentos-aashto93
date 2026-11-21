"""Módulo 4 — Diseño de pavimentos flexibles (AASHTO '93)."""

import math
from statistics import NormalDist

from pavimentos.unidades import cm_a_pulg, pulg_a_cm


def zr_de_r(r_pct: float) -> float:
    """Desviación normal estandarizada para la confiabilidad R (%)."""
    return -NormalDist().inv_cdf(r_pct / 100.0)


def r_etapa(r_global_pct: float, n_etapas: int) -> float:
    """Confiabilidad por etapa para estrategia por etapas: R_etapa = R^(1/n)."""
    return (r_global_pct / 100.0) ** (1.0 / n_etapas) * 100.0


def log_w18(sn: float, zr: float, so: float, delta_psi: float, mr: float) -> float:
    """Ecuación de diseño AASHTO '93 (flexibles): log10(W18)."""
    return (
        zr * so
        + 9.36 * math.log10(sn + 1.0)
        - 0.20
        + math.log10(delta_psi / (4.2 - 1.5)) / (0.40 + 1094.0 / (sn + 1.0) ** 5.19)
        + 2.32 * math.log10(mr)
        - 8.07
    )


def sn_requerido(w18: float, zr: float, so: float, delta_psi: float, mr: float) -> float:
    """Número estructural requerido por bisección en [0.5, 10]."""
    objetivo = math.log10(w18)
    lo, hi = 0.5, 10.0
    for _ in range(100):
        mid = (lo + hi) / 2.0
        if log_w18(mid, zr, so, delta_psi, mr) < objetivo:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def coef_a1(e_ca: float) -> float:
    return 0.17 * math.log(e_ca) - 1.7754


def coef_a2(e_b: float) -> float:
    return 0.249 * math.log10(e_b) - 0.977


def coef_a3(e_sb: float) -> float:
    return 0.227 * math.log10(e_sb) - 0.839


def _redondear_arriba(x: float, paso: float) -> float:
    return math.ceil(x / paso - 1e-9) * paso


def disenar_capas(w18, zr, so, delta_psi, mr, e_b, e_sb, a1, a2, a3,
                  m2=1.0, m3=1.0, min_ca_cm=0.0, min_base_cm=0.0,
                  min_subbase_cm=0.0, redondeo_cm=0.5) -> dict:
    """Diseño por capas: SN1/SN2/SN3 y espesores en cm con mínimos."""
    sn1 = sn_requerido(w18, zr, so, delta_psi, e_b)
    sn2 = sn_requerido(w18, zr, so, delta_psi, e_sb)
    sn3 = sn_requerido(w18, zr, so, delta_psi, mr)

    d1_cm = max(_redondear_arriba(pulg_a_cm(sn1 / a1), redondeo_cm), min_ca_cm)
    sn1_aporte = a1 * cm_a_pulg(d1_cm)

    d2_cm = max(_redondear_arriba(pulg_a_cm((sn2 - sn1_aporte) / (a2 * m2)), redondeo_cm), min_base_cm)
    sn2_aporte = a2 * m2 * cm_a_pulg(d2_cm)

    d3_cm = max(_redondear_arriba(pulg_a_cm((sn3 - sn1_aporte - sn2_aporte) / (a3 * m3)), redondeo_cm), min_subbase_cm)
    sn3_aporte = a3 * m3 * cm_a_pulg(d3_cm)

    sn_total = sn1_aporte + sn2_aporte + sn3_aporte
    return {
        "sn1": sn1, "sn2": sn2, "sn3": sn3,
        "d1_cm": d1_cm, "d2_cm": d2_cm, "d3_cm": d3_cm,
        "d1_pulg": cm_a_pulg(d1_cm), "d2_pulg": cm_a_pulg(d2_cm), "d3_pulg": cm_a_pulg(d3_cm),
        "sn_total": sn_total,
        "cumple": sn_total >= sn3,
    }

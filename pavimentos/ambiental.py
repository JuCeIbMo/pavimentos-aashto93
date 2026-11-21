"""Módulo 6 — Ajuste de vida útil por condiciones ambientales (AASHTO '93, apéndice G)."""

import math

from pavimentos.flexible import log_w18


class DatosInvalidos(ValueError):
    """Dato de entrada fuera de rango o inválido."""


def delta_psi_hinchamiento(vr: float, ps: float, theta: float, t: float) -> float:
    """Pérdida de serviciabilidad por hinchamiento de suelos expansivos."""
    return 0.00335 * vr * ps * (1.0 - math.exp(-theta * t))


def delta_psi_helada(pf: float, dpsi_max: float, phi: float, t: float, coef: float = 0.02) -> float:
    """Pérdida de serviciabilidad por helada. El coeficiente 0.02 está pendiente de verificar."""
    return 0.01 * pf * dpsi_max * (1.0 - math.exp(-coef * phi * t))


def _invertir_w_t(w_t_fn, w_objetivo, t_hi):
    """t tal que w_t_fn(t) == w_objetivo, por bisección en [0, t_hi]."""
    lo, hi = 0.0, t_hi
    for _ in range(100):
        mid = (lo + hi) / 2.0
        if w_t_fn(mid) < w_objetivo:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def periodo_desempeno(sn, mr, delta_psi_total, zr, so, vr, ps, theta, t_inicial,
                      w_t_fn, helada=None) -> dict:
    """Período de desempeño por iteración del efecto ambiental.

    `helada` (opcional): {"pf", "dpsi_max", "phi", "coef"}.
    `w_t_fn`: callable t -> ESAL acumulados (monótono creciente).
    """
    t = t_inicial
    iteraciones = []
    for _ in range(10):
        dpsi_sw = delta_psi_hinchamiento(vr, ps, theta, t)
        dpsi_fh = 0.0
        if helada is not None:
            dpsi_fh = delta_psi_helada(
                helada["pf"], helada["dpsi_max"], helada["phi"], t,
                helada.get("coef", 0.02))
        dpsi_tr = delta_psi_total - dpsi_sw - dpsi_fh
        if dpsi_tr <= 0:
            raise DatosInvalidos(
                f"El ambiente consume toda la serviciabilidad (ΔPSI_TR = {dpsi_tr:.3f} ≤ 0).")
        w_adm = 10.0 ** log_w18(sn, zr, so, dpsi_tr, mr)
        t_calc = _invertir_w_t(w_t_fn, w_adm, 2 * t_inicial)
        iteraciones.append({"t": t, "dpsi_sw": dpsi_sw, "dpsi_fh": dpsi_fh,
                            "dpsi_tr": dpsi_tr, "w_adm": w_adm, "t_calc": t_calc})
        if abs(t - t_calc) < 1.0:
            periodo = (t + t_calc) / 2.0
            return {"periodo": periodo, "w_adm": w_adm, "iteraciones": iteraciones,
                    "dpsi_sw": dpsi_sw, "dpsi_tr": dpsi_tr, "dpsi_fh": dpsi_fh}
        t = (t + t_calc) / 2.0
    return {"periodo": t, "w_adm": iteraciones[-1]["w_adm"], "iteraciones": iteraciones,
            "dpsi_sw": iteraciones[-1]["dpsi_sw"], "dpsi_tr": iteraciones[-1]["dpsi_tr"],
            "dpsi_fh": iteraciones[-1]["dpsi_fh"]}

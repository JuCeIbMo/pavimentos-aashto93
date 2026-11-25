"""Módulo 4 — Diseño de pavimentos flexibles (AASHTO '93)."""

import math
from statistics import NormalDist

from pavimentos.unidades import cm_a_pulg, pulg_a_cm


def zr_de_r(r_pct: float) -> float:
    """Desviación normal estandarizada ZR para la confiabilidad R (%).

    Idea: el comportamiento real del pavimento se dispersa alrededor de lo que
    predice la ecuación, y esa dispersión sigue una distribución normal. Pedir
    una confiabilidad R es pedir que la probabilidad de que el pavimento dure
    lo previsto sea R. ZR es el punto de la normal estándar (media 0,
    desviación 1) que deja por encima un área igual a R.

    Es el mismo número de la tabla de ZR del apunte (R = 90 % -> ZR = -1,282;
    R = 95 % -> -1,645), pero calculado exacto en vez de leído.
    """
    # NormalDist() sin argumentos es la normal estándar: media 0, desviación 1.
    # Viene en la biblioteca estándar de Python (módulo statistics), no hace
    # falta instalar nada.
    normal = NormalDist()

    # inv_cdf(p) es la inversa de la función de distribución acumulada:
    # devuelve el valor z tal que P(Z <= z) = p.
    #   R = 90 %  ->  p = 0,90  ->  z = +1,2816
    # La tabla AASHTO usa ZR negativo (el área R queda a la derecha de ZR),
    # por eso se cambia el signo: ZR = -1,2816.
    # ZR negativo hace que el término ZR*So de la ecuación reste, así que hace
    # falta más SN para el mismo W18: ese es el margen de seguridad.
    p = r_pct / 100.0
    return -normal.inv_cdf(p)


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
    """Número estructural requerido, por bisección en [0,5; 10].

    Problema: la ecuación AASHTO da log(W18) en función del SN, pero el SN
    aparece dos veces (en log(SN+1) y en (SN+1)^5,19) y no se puede despejar.
    Lo que sí se puede es evaluarla: dado un SN, log_w18() dice cuántos ejes
    aguanta. Buscamos el SN para el que eso es igual al W18 de diseño.

    Por qué funciona la bisección: cuanto mayor es el SN, más ejes aguanta
    (la función crece siempre). Entonces, si un SN aguanta menos que W18, la
    respuesta está por encima; si aguanta más, está por debajo. Cada vuelta
    parte el intervalo por la mitad y se queda con la mitad donde está la
    respuesta. Es lo mismo que hacer "prueba y error" a mano o leer el ábaco,
    pero ordenado.
    """
    # Lo que tiene que dar la ecuación: log10 del W18 de diseño.
    objetivo = math.log10(w18)

    # Intervalo inicial [lo, hi]. Ningún pavimento real necesita SN fuera de
    # 0,5 a 10, así que la respuesta está adentro.
    lo, hi = 0.5, 10.0

    # Cada vuelta divide el intervalo por 2. Tras 100 vueltas el ancho es
    # 9,5 / 2^100, mucho menos que cualquier precisión que importe.
    # (Con unas 20 vueltas ya alcanza para 4 decimales.)
    for _ in range(100):
        mid = (lo + hi) / 2.0                         # SN de prueba: el medio
        aguanta = log_w18(mid, zr, so, delta_psi, mr)  # log de los ejes que aguanta ese SN
        if aguanta < objetivo:
            # Se queda corto: el SN buscado es mayor. Descartamos la mitad de abajo.
            lo = mid
        else:
            # Sobra: el SN buscado es menor o igual. Descartamos la mitad de arriba.
            hi = mid

    # lo y hi ya son prácticamente iguales: el medio es el SN requerido.
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

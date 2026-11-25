"""Módulo 6 — Ajuste de la vida útil por condiciones climáticas (hinchamiento y helada)."""

import math

import altair as alt
import pandas as pd
import streamlit as st

from pavimentos.ambiental import delta_psi_helada, delta_psi_hinchamiento
from pavimentos.formato import entero, num
from pavimentos.modelo import Helada

from .componentes import avisos, concepto, decisiones, ecuacion, encabezado, fila_metricas, seccion
from .estado import k, proyecto

CONCEPTO = """
El tránsito no es lo único que gasta la serviciabilidad. Una **arcilla expansiva** que se hincha, o
una subrasante que sufre **levantamiento por congelamiento**, deforman la superficie aunque no pase
ningún camión. Esa pérdida (ΔPSI<sub>SW</sub> + ΔPSI<sub>FH</sub>) se le **resta** al ΔPSI de diseño, y al
tránsito le queda menos margen: el pavimento dura menos.

El procedimiento (AASHTO 93, Parte II, 3.1.4) es iterativo:
1. Se supone un período de desempeño t (p. ej. el de diseño).
2. Se calcula la pérdida ambiental a esa edad y el ΔPSI que queda para el tránsito.
3. Con la ecuación AASHTO se obtiene cuánto tránsito admite la estructura.
4. Se busca en qué año se acumula ese tránsito. Si difiere del t supuesto en más de 1 año, se repite.

El resultado indica **a qué edad hará falta una rehabilitación** (recapado) con el SN elegido.
"""

AYUDA = {
    "vr": "Levantamiento vertical potencial (pulg): cuánto podría subir la superficie si la arcilla se hincha por completo.",
    "ps": "Probabilidad de hinchamiento (%): porcentaje del tramo con suelo expansivo.",
    "theta": "Tasa de hinchamiento (0,04–0,20): qué tan rápido ocurre. Depende de la permeabilidad y de las fisuras del suelo.",
    "pf": "Probabilidad de levantamiento por helada (%): porcentaje del tramo afectado.",
    "dpsi_max": "Pérdida máxima de serviciabilidad por helada (figura G.7, según drenaje y profundidad de congelamiento).",
    "phi": "Tasa de levantamiento por helada (mm/día), según el tipo de suelo (figura G.6).",
}


def render(res: dict):
    p = proyecto()
    c = p.clima
    encabezado("Ajuste de la vida útil por clima",
               "Suelos expansivos y heladas: cuánto acortan la vida del pavimento.", badge="06")
    concepto("¿Cómo afecta el clima a la vida útil?", CONCEPTO)

    c.activo = st.toggle("Considerar efectos ambientales en el diseño", value=c.activo, key=k("cl_on"),
                         help="Si se activa, los espesores se diseñan con el tránsito admisible y el ΔPSI remanente.")
    if not c.activo:
        st.info("El diseño actual no considera efectos ambientales. Activá el interruptor si la subrasante es "
                "expansiva o susceptible a la helada.")
        return

    seccion("Hinchamiento (suelos expansivos)")
    c.hinchamiento = st.checkbox("Incluir hinchamiento", value=c.hinchamiento, key=k("cl_sw"))
    if c.hinchamiento:
        cc = st.columns(3)
        c.vr = cc[0].number_input("V_R (pulg)", 0.0, 10.0, float(c.vr), 0.1, key=k("cl_vr"), help=AYUDA["vr"])
        c.ps = cc[1].number_input("P_S (%)", 0.0, 100.0, float(c.ps), 1.0, key=k("cl_ps"), help=AYUDA["ps"])
        c.theta = cc[2].number_input("θ", 0.0, 0.3, float(c.theta), 0.005, format="%.3f", key=k("cl_th"),
                                     help=AYUDA["theta"])

    seccion("Levantamiento por helada")
    usar = st.checkbox("Incluir helada", value=c.helada is not None, key=k("cl_fh"))
    if usar:
        h = c.helada or Helada()
        cc = st.columns(3)
        h.pf = cc[0].number_input("P_F (%)", 0.0, 100.0, float(h.pf), 1.0, key=k("cl_pf"), help=AYUDA["pf"])
        h.dpsi_max = cc[1].number_input("ΔPSI_MAX", 0.0, 3.0, float(h.dpsi_max), 0.1, key=k("cl_dm"), help=AYUDA["dpsi_max"])
        h.phi = cc[2].number_input("φ (mm/día)", 0.0, 30.0, float(h.phi), 0.5, key=k("cl_phi"), help=AYUDA["phi"])
        c.helada = h
    else:
        c.helada = None

    avisos(res, "clima")
    cl = res.get("clima")
    if not cl:
        return
    seccion("Resultados")
    fila_metricas([
        {"etiqueta": "Período de desempeño", "valor": f"{num(cl['periodo'], 1)} años",
         "sub": f"objetivo: {num(cl['t_objetivo'], 0)} años"},
        {"etiqueta": "ΔPSI ambiental", "valor": num(cl["dpsi_sw"] + cl["dpsi_fh"], 3), "sub": "hinchamiento + helada"},
        {"etiqueta": "ΔPSI para el tránsito", "valor": num(cl["dpsi_tr"], 3), "sub": "ΔPSI_TR"},
        {"etiqueta": "W admisible", "valor": entero(cl["w_adm"]), "sub": "ESAL hasta la rehabilitación"},
    ])
    it = pd.DataFrame([{"t supuesto": i["t"], "ΔPSI_SW": i["dpsi_sw"], "ΔPSI_FH": i["dpsi_fh"], "ΔPSI_TR": i["dpsi_tr"],
                        "W admisible": i["w_adm"], "t calculado": i["t_calc"],
                        "|Δt|": abs(i["t"] - i["t_calc"])} for i in cl["iteraciones"]])
    c1, c2 = st.columns([1.2, 1])
    with c1:
        st.markdown("**Iteraciones** (converge cuando |Δt| < 1 año)")
        st.dataframe(it, hide_index=True, width="stretch", column_config={
            "W admisible": st.column_config.NumberColumn(format="%.0f"),
            **{x: st.column_config.NumberColumn(format="%.3f") for x in ("ΔPSI_SW", "ΔPSI_FH", "ΔPSI_TR")},
            **{x: st.column_config.NumberColumn(format="%.2f") for x in ("t supuesto", "t calculado", "|Δt|")}})
    with c2:
        tmax = max(20.0, cl["t_objetivo"] * 1.5)
        filas = []
        for i in range(0, 41):
            t = tmax * i / 40
            sw = delta_psi_hinchamiento(c.vr, c.ps, c.theta, t) if c.hinchamiento else 0.0
            fh = delta_psi_helada(c.helada.pf, c.helada.dpsi_max, c.helada.phi, t) if c.helada else 0.0
            filas.append({"t (años)": t, "ΔPSI": sw, "Efecto": "Hinchamiento"})
            filas.append({"t (años)": t, "ΔPSI": fh, "Efecto": "Helada"})
            filas.append({"t (años)": t, "ΔPSI": sw + fh, "Efecto": "Total ambiental"})
        ch = alt.Chart(pd.DataFrame(filas)).mark_line().encode(
            x="t (años):Q", y=alt.Y("ΔPSI:Q", title="Pérdida de serviciabilidad"),
            color=alt.Color("Efecto:N", scale=alt.Scale(range=["#9CA3AF", "#C98A00", "#1F2937"])),
        ).properties(height=230, title="Pérdida ambiental de serviciabilidad en el tiempo")
        regla = alt.Chart(pd.DataFrame({"t": [cl["periodo"]]})).mark_rule(strokeDash=[4, 3]).encode(x="t:Q")
        st.altair_chart(ch + regla, use_container_width=True)
    decisiones(res, "clima")
    if not math.isclose(cl["periodo"], cl["t_objetivo"], abs_tol=0.05) and cl["periodo"] < cl["t_objetivo"]:
        st.caption("💡 Para alcanzar el período objetivo sin rehabilitación, aumentá el SN (más espesor) o mejorá "
                   "la subrasante (estabilización, reemplazo del suelo expansivo).")

    with st.expander("📐 Procedimiento y ecuaciones"):
        ecuacion("hinchamiento")
        ecuacion("helada")
        ecuacion("periodo")

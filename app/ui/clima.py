"""Página del módulo 6 — Clima y período de desempeño."""

import streamlit as st

from pavimentos.ambiental import DatosInvalidos, periodo_desempeno
from pavimentos.flexible import r_etapa, zr_de_r
from pavimentos.lef import cargar_lef
from pavimentos.trafico import w_t

from .componentes import aviso, cargar_practico3, tarjeta


def render():
    st.header("Módulo 6 · Ajuste de vida útil por clima")
    st.caption("Evalúa el hinchamiento (y opcionalmente helada) sobre el período de desempeño.")

    col = st.columns(4)
    sn = col[0].number_input("SN adoptado", 0.5, 10.0, 3.1, step=0.1)
    mr = col[1].number_input("M_R subrasante (psi)", 1000.0, None, 10222.0)
    r_global = col[2].number_input("R (%)", 50.0, 99.9, 85.0)
    etapas = col[3].number_input("Etapas", 1, 3, 2)

    so = st.number_input("So", 0.0, 1.0, 0.49, step=0.01)
    dpsi = st.number_input("ΔPSI total", 0.0, 4.0, 2.2, step=0.1)

    st.subheader("Hinchamiento")
    c1, c2, c3 = st.columns(3)
    vr = c1.number_input("VR (pulg)", 0.0, None, 2.0, step=0.1)
    ps = c2.number_input("PS (%)", 0.0, 100.0, 60.0, step=1.0)
    theta = c3.number_input("θ (tasa)", 0.0, 0.3, 0.1, step=0.01)

    usar_helada = st.checkbox("Incluir helada", value=False)
    helada = None
    if usar_helada:
        c4, c5, c6 = st.columns(3)
        pf = c4.number_input("PF (%)", 0.0, 100.0, 50.0)
        dpsi_max = c5.number_input("ΔPSI máx helada", 0.0, 2.0, 1.0, step=0.1)
        phi = c6.number_input("φ (mm/día)", 0.0, None, 20.0)
        helada = {"pf": pf, "dpsi_max": dpsi_max, "phi": phi, "coef": 0.02}

    if st.button("Calcular período", type="primary"):
        try:
            tablas = cargar_lef()
            preset = cargar_practico3()
            w_t_fn = lambda t: w_t(preset["vehiculos"], t, preset["fd"], preset["fc"],
                                   tablas, preset["pt"], preset["sn"])
            zr = zr_de_r(r_etapa(r_global, etapas)) if etapas > 1 else zr_de_r(r_global)
            r = periodo_desempeno(sn, mr, dpsi, zr, so, vr, ps, theta, 15, w_t_fn, helada)
            tarjeta("Período de desempeño", f"{r['periodo']:.1f} años")
            tarjeta("ΔPSI ambiental", f"{r['dpsi_sw'] + r['dpsi_fh']:.3f}")
            tarjeta("ΔPSI remanente (tráfico)", f"{r['dpsi_tr']:.3f}")
            tarjeta("W admisible", f"{r['w_adm']:,.0f}".replace(",", "."))
            st.session_state["clima_resultado"] = r
            with st.expander("Procedimiento e iteraciones"):
                st.latex(r"\Delta PSI_{SW} = 0.00335\, V_R\, P_S\,(1-e^{-\theta t})")
                for it in r["iteraciones"]:
                    st.write(f"t={it['t']:.2f} → ΔPSI_SW={it['dpsi_sw']:.3f}, "
                             f"W_adm={it['w_adm']:,.0f}, t_calc={it['t_calc']:.2f}")
        except DatosInvalidos as e:
            aviso(str(e), "error")

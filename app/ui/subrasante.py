"""Página del módulo 2 — Módulo resiliente efectivo."""

import streamlit as st

from pavimentos.resiliente import DatosInvalidos, mr_de_cbr, mr_efectivo

from .componentes import aviso, tarjeta


def render():
    st.header("Módulo 2 · Módulo resiliente efectivo de la subrasante")
    st.caption("Períodos por mes. Los meses deben sumar 12. CBR < 7.2 → 1500·CBR; 7.2–20 → 3000·CBR^0.65.")

    if "periodos" not in st.session_state:
        st.session_state["periodos"] = [
            {"nombre": "Ene-Mar", "meses": 3, "cbr": 4.7},
            {"nombre": "Abr", "meses": 1, "cbr": 6.7},
            {"nombre": "May/Nov/Dic", "meses": 3, "cbr": 8.4},
            {"nombre": "Jun-Oct", "meses": 5, "cbr": 13.1},
        ]

    rows = st.data_editor(
        [{"nombre": p["nombre"], "meses": p["meses"], "cbr": p["cbr"]}
         for p in st.session_state["periodos"]],
        num_rows="dynamic", width="stretch", key="periodos_editor",
        column_config={"nombre": "Período", "meses": "Meses", "cbr": "CBR (%)"},
    )

    if st.button("Calcular M_R efectivo", type="primary"):
        try:
            periodos = [{"nombre": r["nombre"], "meses": int(r["meses"]), "mr": mr_de_cbr(float(r["cbr"]))}
                        for r in rows]
            res = mr_efectivo(periodos)
            tarjeta("M_R efectivo", f"{res['mr_efectivo']:,.0f} psi".replace(",", "."))
            tarjeta("Daño relativo promedio ūf", f"{res['uf_bar']:.4f}")
            st.session_state["subrasante_resultado"] = res
            with st.expander("Procedimiento"):
                st.latex(r"u_f = 1.18\times10^{8}\, M_R^{-2.32}")
                st.latex(r"M_{R,ef} = \left(\bar u_f / 1.18\times10^{8}\right)^{-1/2.32}")
        except DatosInvalidos as e:
            aviso(str(e), "error")

"""Página del módulo 2 — Módulo resiliente efectivo."""

import streamlit as st

from pavimentos.resiliente import DatosInvalidos, mr_de_cbr, mr_efectivo

from .componentes import aviso, encabezado, fila_metricas


def render():
    encabezado("Módulo resiliente efectivo de la subrasante",
               "M_R por período, ponderado por daño relativo a lo largo del año.",
               badge="02")
    st.caption("Los meses deben sumar 12. CBR < 7.2 → 1500·CBR; 7.2–20 → 3000·CBR^0.65.")

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
            fila_metricas([
                {"etiqueta": "M_R efectivo", "valor": f"{res['mr_efectivo']:,.0f} psi".replace(",", "."),
                 "sub": "módulo resiliente promedio"},
                {"etiqueta": "Daño relativo promedio ūf", "valor": f"{res['uf_bar']:.4f}",
                 "sub": "ponderado por meses"},
            ])
            st.session_state["subrasante_resultado"] = res
            with st.expander("Procedimiento"):
                st.latex(r"u_f = 1.18\times10^{8}\, M_R^{-2.32}")
                st.latex(r"M_{R,ef} = \left(\bar u_f / 1.18\times10^{8}\right)^{-1/2.32}")
        except DatosInvalidos as e:
            aviso(str(e), "error")

"""Página del módulo 1 — Tránsito y ESAL."""

import streamlit as st

from pavimentos.lef import DatosInvalidos, cargar_lef
from pavimentos.trafico import esal_total

from .componentes import aviso, cargar_practico3, ejes_a_str, str_a_ejes, tabla, tarjeta


def _a_vehiculos(rows) -> list:
    out = []
    for r in rows:
        try:
            ejes = str_a_ejes(r["ejes"])
        except Exception:
            aviso(f"Ejes mal formados en '{r.get('nombre', '?')}'.", "warn")
            continue
        out.append({
            "nombre": r["nombre"],
            "tpda": float(r["tpda"]),
            "r": float(r["r"]) / 100.0,
            "pesado": bool(r["pesado"]),
            "ejes": ejes,
        })
    return out


def render():
    st.header("Módulo 1 · Cálculo de ejes equivalentes (ESAL)")
    tablas = cargar_lef()

    c1, c2, c3, c4 = st.columns(4)
    n = c1.number_input("Período de diseño (años)", 1, 50, 15)
    fd = c2.number_input("Distribución direccional Fd", 0.1, 1.0, 0.5, step=0.1)
    fc = c3.number_input("Factor de carril Fc", 0.1, 1.0, 1.0, step=0.05)
    sn = c4.number_input("SN supuesto (para LEF)", 1.0, 6.0, 3.0, step=0.1)

    pt = st.selectbox("Serviciabilidad terminal pt", [2.0, 2.5, 3.0], index=0)

    st.divider()
    if st.button("Cargar composición del práctico 3"):
        st.session_state["vehiculos"] = cargar_practico3()["vehiculos"]

    vehiculos = st.session_state.get("vehiculos")
    if vehiculos:
        rows = [{
            "nombre": v["nombre"],
            "tpda": v["tpda"],
            "r": v["r"] * 100,
            "pesado": v["pesado"],
            "ejes": ejes_a_str(v["ejes"]),
        } for v in vehiculos]
        edited = st.data_editor(
            rows, num_rows="dynamic", width="stretch",
            key="veh_editor", column_config={
                "nombre": "Vehículo", "tpda": "TPDA", "r": "Crec. %",
                "pesado": "Pesado", "ejes": "Ejes (tipo carga; ...)",
            })
        if st.button("Calcular ESAL", type="primary"):
            vehiculos = _a_vehiculos(edited)
            st.session_state["vehiculos"] = vehiculos
            try:
                r = esal_total(vehiculos, n, fd, fc, tablas, pt, sn)
                tarjeta("W18 (ESAL de diseño)", f"{r['total_w']:,.0f}".replace(",", "."))
                tarjeta("log W18", f"{__import__('math').log10(r['total_w']):.3f}")
                tarjeta("Vehículos pesados", f"{r['pesados_pct']:.1f} %")
                st.session_state["trafico_resultado"] = r
                tabla(r["por_vehiculo"],
                      ["nombre", "fc", "esal1", "w"])
                with st.expander("Procedimiento"):
                    st.latex(r"ESAL_1 = TPDA \cdot FC \cdot 365 \cdot F_d \cdot F_c")
                    st.latex(r"W = ESAL_1 \cdot \dfrac{(1+r)^n - 1}{r}")
            except DatosInvalidos as e:
                aviso(str(e), "error")
    else:
        st.info("Cargá la composición vehicular (o usá el preset) para empezar.")

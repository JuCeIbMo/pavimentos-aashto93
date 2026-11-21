"""Página del módulo 4 — Diseño de pavimentos flexibles."""

import math

import streamlit as st

from pavimentos.flexible import coef_a1, coef_a2, coef_a3, disenar_capas, r_etapa, zr_de_r
from pavimentos.unidades import kg_cm2_a_psi

from .componentes import aviso, encabezado, fila_metricas, seccion, tabla


def render():
    encabezado("Diseño de pavimentos flexibles",
               "Número estructural requerido y espesores de carpeta, base y subbase.",
               badge="04")

    col = st.columns(4)
    w18 = col[0].number_input("W18 (ESAL)", 0.0, None, 890521.0, step=1000.0, format="%.0f")
    r_global = col[1].number_input("Confiabilidad R (%)", 50.0, 99.9, 85.0, step=0.5)
    etapas = col[2].number_input("Etapas", 1, 3, 2)
    so = col[3].number_input("Desviación So", 0.0, 1.0, 0.49, step=0.01)

    col2 = st.columns(2)
    p0 = col2[0].number_input("p0 (inicial)", 4.0, 4.6, 4.2, step=0.1)
    pt = col2[1].number_input("pt (terminal)", 1.5, 3.0, 2.0, step=0.1)
    mr = st.number_input("M_R efectivo de subrasante (psi)", 1000.0, None, 10222.0, step=100.0)

    st.divider()
    seccion("Materiales", "Módulos y coeficientes de capa derivados de E y CBR.")
    col3 = st.columns(3)
    e_ca_kg = col3[0].number_input("E concreto asfáltico (kg/cm²)", 1000.0, None, 29880.0)
    cbr_base = col3[1].number_input("CBR base (%)", 0.0, 100.0, 80.0)
    cbr_sb = col3[2].number_input("CBR subbase (%)", 0.0, 100.0, 40.0)

    e_ca = kg_cm2_a_psi(e_ca_kg)
    e_b = 9380 * math.log(cbr_base) - 12960
    e_sb = 4326 * math.log(cbr_sb) + 241
    a1, a2, a3 = coef_a1(e_ca), coef_a2(e_b), coef_a3(e_sb)

    col4 = st.columns(3)
    m2 = col4[0].number_input("m2 (drenaje base)", 0.4, 1.4, 1.0, step=0.05)
    m3 = col4[1].number_input("m3 (drenaje subbase)", 0.4, 1.4, 1.0, step=0.05)
    tabla_min = col4[2].selectbox("Tabla de mínimos", ["métrica (cm)", "AASHTO (pulg)"])
    min_ca, min_base, min_sb = (7.5, 15.0, 10.0) if tabla_min.startswith("mét") else (7.6, 15.2, 10.2)

    if st.button("Diseñar", type="primary"):
        zr = zr_de_r(r_etapa(r_global, etapas)) if etapas > 1 else zr_de_r(r_global)
        delta_psi = p0 - pt
        try:
            r = disenar_capas(w18, zr, so, delta_psi, mr, e_b, e_sb, a1, a2, a3,
                              m2, m3, min_ca, min_base, min_sb)
            fila_metricas([
                {"etiqueta": "SN requerido", "valor": f"{r['sn3']:.2f}",
                 "sub": "sobre subrasante"},
                {"etiqueta": "Estructura", "valor": f"{r['d1_cm']:.0f} / {r['d2_cm']:.0f} / {r['d3_cm']:.0f}",
                 "sub": "carpeta / base / subbase (cm)"},
            ])
            ok = "✔ cumple" if r["cumple"] else "✘ no cumple"
            st.write(f"**Verificación:** SN aportado {r['sn_total']:.2f} vs SN requerido {r['sn3']:.2f} → {ok}")
            tabla([
                {"Capa": "Concreto asfáltico", "SN": r["sn1"], "Espesor (cm)": r["d1_cm"], "Espesor (pulg)": round(r["d1_pulg"], 2)},
                {"Capa": "Base granular", "SN": r["sn2"], "Espesor (cm)": r["d2_cm"], "Espesor (pulg)": round(r["d2_pulg"], 2)},
                {"Capa": "Subbase granular", "SN": r["sn3"], "Espesor (cm)": r["d3_cm"], "Espesor (pulg)": round(r["d3_pulg"], 2)},
            ])
            st.caption(f"a1={a1:.3f}  a2={a2:.3f}  a3={a3:.3f}  ZR={zr:.3f}  ΔPSI={delta_psi:.2f}")
            st.session_state["flexible_resultado"] = r
            with st.expander("Procedimiento"):
                st.latex(r"\log W_{18} = Z_R S_o + 9.36\log(SN+1) - 0.20 + "
                         r"\frac{\log(\Delta PSI/2.7)}{0.40 + 1094/(SN+1)^{5.19}} + 2.32\log M_R - 8.07")
                st.latex(r"SN = a_1 D_1 + a_2 m_2 D_2 + a_3 m_3 D_3")
        except Exception as e:  # noqa: BLE001
            aviso(str(e), "error")

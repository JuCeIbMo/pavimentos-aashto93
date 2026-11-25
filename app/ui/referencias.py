"""Bibliografía y fuente de cada ecuación implementada."""

import streamlit as st

from pavimentos.referencias import ECUACIONES, REFERENCIAS

from .componentes import encabezado, seccion

GRUPOS = [
    ("Módulo 1 · Tránsito", ["lef", "crecimiento", "esal"]),
    ("Módulo 2 · Subrasante", ["mr_cbr", "danio", "mr_ef"]),
    ("Módulo 4 · Diseño flexible", ["zr", "aashto", "e_cbr", "coef", "sn", "capas"]),
    ("Módulo 6 · Clima", ["hinchamiento", "helada", "periodo"]),
]


def render(res: dict):
    encabezado("Referencias y ecuaciones",
               "Bibliografía y fuente de cada ecuación implementada en el paquete.", badge="📖")
    seccion("Bibliografía")
    for _, texto in REFERENCIAS.items():
        st.markdown(f"- {texto}")

    seccion("Ecuaciones implementadas", "Cada ecuación con su fuente y lo que representa.")
    for titulo, claves in GRUPOS:
        st.markdown(f"#### {titulo}")
        for c in claves:
            e = ECUACIONES[c]
            st.latex(e["latex"])
            st.caption(f"📖 {e['fuente']} — {e['explica']}")

    seccion("Herramientas")
    st.markdown("- Python 3, Streamlit (interfaz), Typst (memoria PDF), openpyxl (libro Excel), "
                "matplotlib y Altair (gráficos).\n"
                "- Tablas LEF: AASHTO 93, Apéndice D (tablas D.1–D.9), digitalizadas e interpoladas en carga y SN.")

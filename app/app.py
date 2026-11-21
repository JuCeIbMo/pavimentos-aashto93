"""Aplicación Streamlit — Paquete computacional de diseño de pavimentos flexibles (AASHTO '93)."""

import streamlit as st

from pavimentos.proyecto import Proyecto

from ui import clima, flexibles, subrasante, trafico, validacion

st.set_page_config(page_title="Pavimentos AASHTO '93", page_icon="🛣️", layout="wide")


def main():
    st.session_state.setdefault("proyecto", Proyecto())

    st.sidebar.title("Pavimentos AASHTO '93")
    st.sidebar.caption("Diseño de pavimentos flexibles")
    pagina = st.sidebar.radio(
        "Módulo",
        ["Inicio", "1 · Tránsito", "2 · Subrasante", "4 · Flexibles",
         "6 · Clima", "Validación", "7 · Marshall"],
    )

    if pagina == "Inicio":
        st.title("🛣️ Paquete computacional de diseño de pavimentos")
        st.write("Método AASHTO 1993 · pavimentos flexibles.")
        st.write("**Flujo:** 1 Tránsito → 2 Subrasante → 4 Flexibles → 6 Clima.")
        st.info("El módulo 7 (Marshall) está reservado y se integrará más adelante.")
    elif pagina == "1 · Tránsito":
        trafico.render()
    elif pagina == "2 · Subrasante":
        subrasante.render()
    elif pagina == "4 · Flexibles":
        flexibles.render()
    elif pagina == "6 · Clima":
        clima.render()
    elif pagina == "Validación":
        validacion.render()
    elif pagina == "7 · Marshall":
        st.header("Módulo 7 · Diseño de mezclas Marshall")
        st.info("Espacio reservado. Se implementará más adelante.")


if __name__ == "__main__":
    main()

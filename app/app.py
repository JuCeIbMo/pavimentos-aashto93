"""Aplicación Streamlit — Paquete computacional de diseño de pavimentos flexibles (AASHTO '93)."""

import json
from dataclasses import asdict

import streamlit as st

from pavimentos.proyecto import Proyecto, cargar_proyecto, guardar_proyecto
from pavimentos.reporte import generar_reporte_html

from ui import clima, flexibles, subrasante, trafico, validacion

st.set_page_config(page_title="Pavimentos AASHTO '93", page_icon="🛣️", layout="wide")


def _resultados() -> dict:
    """Arma el dict de resultados desde lo que cada página guardó en session_state."""
    out = {}
    if st.session_state.get("trafico_resultado"):
        r = st.session_state["trafico_resultado"]
        out["Tránsito (ESAL)"] = {
            "W18": r.get("total_w"),
            "ESAL primer año": r.get("total_esal1"),
            "Vehículos pesados (%)": r.get("pesados_pct"),
            "TPDA total": r.get("tpda_total"),
        }
    if st.session_state.get("subrasante_resultado"):
        r = st.session_state["subrasante_resultado"]
        out["Subrasante"] = {"M_R efectivo (psi)": r.get("mr_efectivo"),
                             "Daño relativo promedio": r.get("uf_bar")}
    if st.session_state.get("flexible_resultado"):
        r = st.session_state["flexible_resultado"]
        out["Diseño flexible"] = {
            "SN requerido": r.get("sn3"),
            "Carpeta (cm)": r.get("d1_cm"),
            "Base (cm)": r.get("d2_cm"),
            "Subbase (cm)": r.get("d3_cm"),
            "SN aportado": r.get("sn_total"),
            "Cumple": "sí" if r.get("cumple") else "no",
        }
    if st.session_state.get("clima_resultado"):
        r = st.session_state["clima_resultado"]
        out["Clima"] = {"Período de desempeño (años)": r.get("periodo"),
                        "ΔPSI ambiental": r.get("dpsi_sw"),
                        "ΔPSI remanente": r.get("dpsi_tr"),
                        "W admisible": r.get("w_adm")}
    return out


def _sidebar_exportar():
    st.sidebar.divider()
    st.sidebar.subheader("Reporte y exportación")

    proyecto = st.session_state["proyecto"]
    resultados = _resultados()

    if resultados:
        html = generar_reporte_html(proyecto, resultados)
        st.sidebar.download_button("Descargar reporte (HTML)", html,
                                   file_name="reporte_pavimento.html", mime="text/html")
    else:
        st.sidebar.caption("Calculá algún módulo para poder generar el reporte.")

    st.sidebar.download_button(
        "Guardar proyecto (.json)",
        json.dumps(asdict(proyecto), indent=2, ensure_ascii=False),
        file_name="proyecto.json", mime="application/json")

    subido = st.sidebar.file_uploader("Cargar proyecto (.json)", type=["json"])
    if subido is not None:
        try:
            data = json.loads(subido.read())
            st.session_state["proyecto"] = Proyecto(**data)
            st.sidebar.success("Proyecto cargado.")
        except Exception as e:  # noqa: BLE001
            st.sidebar.error(f"No se pudo cargar: {e}")


def main():
    st.session_state.setdefault("proyecto", Proyecto())

    st.sidebar.title("Pavimentos AASHTO '93")
    st.sidebar.caption("Diseño de pavimentos flexibles")
    pagina = st.sidebar.radio(
        "Módulo",
        ["Inicio", "1 · Tránsito", "2 · Subrasante", "4 · Flexibles",
         "6 · Clima", "Validación", "7 · Marshall"],
    )
    _sidebar_exportar()

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

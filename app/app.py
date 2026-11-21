"""Aplicación Streamlit — Paquete computacional de diseño de pavimentos flexibles (AASHTO '93)."""

import json
from dataclasses import asdict

import streamlit as st

from pavimentos.proyecto import Proyecto, cargar_proyecto
from pavimentos.reporte import generar_reporte_html

from ui import clima, flexibles, subrasante, trafico, validacion
from ui.componentes import seccion
from ui.theme import aplicar_tema

st.set_page_config(page_title="Pavimentos AASHTO '93", page_icon="🛣️", layout="wide")
aplicar_tema()

PAGINAS = ["Inicio", "1 · Tránsito", "2 · Subrasante", "4 · Flexibles",
           "6 · Clima", "Validación", "7 · Marshall"]

_MODULOS = [
    ("1 · Tránsito", "01", "Cálculo de ejes equivalentes",
     "TPDA, factor de camión y ESAL acumulados (W18) con crecimiento compuesto."),
    ("2 · Subrasante", "02", "Módulo resiliente efectivo",
     "M_R por período y daño relativo ponderado a lo largo del año."),
    ("4 · Flexibles", "04", "Número estructural y capas",
     "SN requerido y espesores de carpeta, base y subbase con mínimos."),
    ("6 · Clima", "06", "Vida útil por clima",
     "Ajuste del período de desempeño por hinchamiento y helada."),
]


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


def _sidebar():
    st.sidebar.markdown(
        """<div class="brand">
             <div class="brand-mark">🛣️</div>
             <div><div class="brand-name">PAVIMENTOS</div>
             <div class="brand-sub">AASHTO '93 · Flexibles</div></div>
           </div>""",
        unsafe_allow_html=True,
    )
    pagina = st.sidebar.radio("Módulo", PAGINAS, key="pagina_actual")

    st.sidebar.divider()
    st.sidebar.subheader("Reporte y exportación")
    proyecto = st.session_state["proyecto"]
    resultados = _resultados()

    if resultados:
        html = generar_reporte_html(proyecto, resultados)
        st.sidebar.download_button("⬇ Descargar reporte (HTML)", html,
                                   file_name="reporte_pavimento.html", mime="text/html")
    else:
        st.sidebar.caption("Calculá un módulo para generar el reporte.")

    st.sidebar.download_button(
        "💾 Guardar proyecto (.json)",
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

    return pagina


def _ir_a(pagina: str):
    st.session_state["pagina_actual"] = pagina
    st.rerun()


def _inicio():
    st.markdown(
        """<div class="hero">
             <div class="hero-kicker">Diseño de pavimentos · Método AASHTO 1993</div>
             <h1>Pavimentos flexibles, de punta a punta.</h1>
             <p>Tránsito, subrasante, número estructural y clima en un solo flujo de
             cálculo. Cargá tus datos, validá contra el Práctico 3 y exportá el reporte.</p>
             <div class="road-line"></div>
             <div class="hero-chips">
               <span class="chip">4 módulos de cálculo</span>
               <span class="chip">Validado · Práctico 3</span>
               <span class="chip">Reporte imprimible</span>
             </div>
           </div>""",
        unsafe_allow_html=True,
    )

    cols = st.columns(4)
    for i, (pagina, num, titulo, desc) in enumerate(_MODULOS):
        with cols[i]:
            st.markdown(
                f"""<div class="step-num">PASO {num}</div>
                    <div class="step-title">{titulo}</div>
                    <div class="step-desc">{desc}</div>""",
                unsafe_allow_html=True,
            )
            st.button("Abrir módulo", key=f"abrir_{i}", use_container_width=True,
                      on_click=_ir_a, args=(pagina,))

    st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)
    seccion("Flujo de trabajo",
            "Los resultados de cada módulo alimentan al siguiente. Arrancá por Tránsito o cargá "
            "el preset del Práctico 3 para ver todo resuelto.")


def main():
    st.session_state.setdefault("proyecto", Proyecto())
    pagina = _sidebar()

    if pagina == "Inicio":
        _inicio()
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
        st.markdown('<div class="page-head"><div class="page-badge">07</div>'
                    '<div><h1 class="page-title">Diseño de mezclas Marshall</h1>'
                    '<p class="page-sub">Módulo reservado.</p></div></div>',
                    unsafe_allow_html=True)
        st.info("Espacio reservado. Se implementará más adelante.")


if __name__ == "__main__":
    main()

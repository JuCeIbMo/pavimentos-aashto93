"""Paquete computacional de diseño de pavimentos flexibles — AASHTO 1993 (Streamlit)."""

import re

import streamlit as st

from pavimentos.exportar_excel import generar_excel
from pavimentos.exportar_pdf import generar_pdf
from pavimentos.formato import entero, num
from pavimentos.modelo import ProyectoFlexible
from pavimentos.validacion import listar

from ui import clima, flexibles, referencias, sensibilidad, subrasante, trafico, validacion
from ui.componentes import encabezado, seccion
from ui.estado import k, proyecto, reemplazar, resultado
from ui.theme import aplicar_tema

st.set_page_config(page_title="Pavimentos AASHTO '93", page_icon="🛣️", layout="wide")
aplicar_tema()

PAGINAS = {
    "Inicio": None,
    "1 · Tránsito": trafico.render,
    "2 · Subrasante": subrasante.render,
    "4 · Diseño flexible": flexibles.render,
    "6 · Clima": clima.render,
    "Sensibilidad y escenarios": sensibilidad.render,
    "Validación": validacion.render,
    "Referencias": referencias.render,
}


def _archivo(nombre: str) -> str:
    base = re.sub(r"[^\w\- ]", "", nombre).strip().replace(" ", "_") or "proyecto"
    return base[:60]


def _estado_modulos(res: dict) -> list[tuple[str, str, bool, str]]:
    tr, sub, di, ca, cl = (res.get(x) for x in ("transito", "subrasante", "diseno", "capas", "clima"))
    p = proyecto()
    return [
        ("1 · Tránsito", "Ejes equivalentes", bool(tr),
         f"W18 = {entero(tr['w18'])}" if tr else "Falta la composición vehicular"),
        ("2 · Subrasante", "M_R efectivo", bool(sub),
         f"M_R = {entero(sub['mr_efectivo'])} psi" if sub else "Faltan los períodos"),
        ("4 · Diseño flexible", "SN y espesores", bool(ca),
         (f"{num(ca['capas'][0]['d'], 1)} / {num(ca['capas'][1]['d'], 1)} / {num(ca['capas'][2]['d'], 1)} {ca['unidad']}"
          if ca else "Completá los datos")),
        ("6 · Clima", "Vida útil por clima", bool(cl) or not p.clima.activo,
         f"{num(cl['periodo'], 1)} años" if cl else ("No considerado" if not p.clima.activo else "Revisar")),
    ]


def _sidebar(res: dict) -> str:
    st.sidebar.markdown(
        """<div class="brand"><div class="brand-mark">🛣️</div>
             <div><div class="brand-name">PAVIMENTOS</div>
             <div class="brand-sub">AASHTO '93 · Flexibles</div></div></div>""",
        unsafe_allow_html=True)
    if "pagina_actual" not in st.session_state:
        st.session_state["pagina_actual"] = "Inicio"
    pagina = st.sidebar.radio("Navegación", list(PAGINAS), key="pagina_actual", label_visibility="collapsed")

    p = proyecto()
    st.sidebar.divider()
    estado = "✅ Diseño completo" if res["ok"] else ("⚠️ Hay errores" if any(
        a["nivel"] == "error" for a in res["avisos"]) else "⏳ Diseño incompleto")
    st.sidebar.caption(f"**{p.nombre}** · {estado}")

    st.sidebar.subheader("Exportar resolución")
    if st.sidebar.button("📄 Preparar memoria de cálculo (PDF)", width="stretch", disabled=not res.get("capas")):
        with st.spinner("Generando PDF…"):
            st.session_state["pdf_bytes"] = generar_pdf(p, res)
    if st.session_state.get("pdf_bytes"):
        st.sidebar.download_button("⬇ Descargar PDF", st.session_state["pdf_bytes"],
                                   file_name=f"{_archivo(p.nombre)}.pdf", mime="application/pdf", width="stretch")
    if st.sidebar.button("📊 Preparar libro Excel (fórmulas vivas)", width="stretch", disabled=not res.get("capas")):
        st.session_state["xlsx_bytes"] = generar_excel(p, res)
    if st.session_state.get("xlsx_bytes"):
        st.sidebar.download_button(
            "⬇ Descargar Excel", st.session_state["xlsx_bytes"], file_name=f"{_archivo(p.nombre)}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", width="stretch")
    if not res.get("capas"):
        st.sidebar.caption("Completá el diseño para exportar.")

    st.sidebar.subheader("Proyecto")
    st.sidebar.download_button("💾 Guardar proyecto (.json)", p.to_json(), file_name=f"{_archivo(p.nombre)}.json",
                               mime="application/json", width="stretch")
    subido = st.sidebar.file_uploader("Abrir proyecto (.json)", type=["json"], key=f"up_{st.session_state.get('ver', 0)}")
    if subido is not None:
        try:
            reemplazar(ProyectoFlexible.from_json(subido.read().decode("utf-8")))
            st.rerun()
        except Exception as e:  # noqa: BLE001
            st.sidebar.error(f"No se pudo abrir: {e}")
    return pagina


def _ir(pagina: str):
    st.session_state["pagina_actual"] = pagina


def _inicio(res: dict):
    st.markdown(
        """<div class="hero">
             <div class="hero-kicker">Diseño de pavimentos flexibles · Método AASHTO 1993</div>
             <h1>Del tránsito a los espesores, con cada decisión explicada.</h1>
             <p>Cargá los datos módulo por módulo: los resultados se recalculan solos y alimentan al
             módulo siguiente. Al final, exportá la memoria de cálculo en PDF o el libro Excel con
             fórmulas vivas.</p>
             <div class="road-line"></div>
             <div class="hero-chips">
               <span class="chip">Módulos 1 · 2 · 4 · 6 conectados</span>
               <span class="chip">Validado con 4 ejercicios</span>
               <span class="chip">PDF y Excel</span>
               <span class="chip">Sensibilidad y escenarios</span>
             </div>
           </div>""", unsafe_allow_html=True)

    p = proyecto()
    seccion("Datos del proyecto")
    c = st.columns([1.4, 1, 1])
    p.nombre = c[0].text_input("Nombre del proyecto", p.nombre, key=k("p_nom"))
    p.autor = c[1].text_input("Autor / proyectista", p.autor, key=k("p_aut"))
    p.ubicacion = c[2].text_input("Ubicación", p.ubicacion, key=k("p_ubi"))
    p.descripcion = st.text_area("Descripción", p.descripcion, key=k("p_desc"), height=70)

    seccion("Flujo de cálculo", "Cada módulo toma los resultados del anterior. Hacé clic para abrirlo.")
    cols = st.columns(4)
    for col, (pag, titulo, ok, detalle) in zip(cols, _estado_modulos(res)):
        with col, st.container(border=True):
            st.markdown(f"<div class='step-num'>{pag.split(' · ')[0].zfill(2)} · {'✅' if ok else '⏳'}</div>"
                        f"<div class='step-title'>{titulo}</div><div class='step-desc'>{detalle}</div>",
                        unsafe_allow_html=True)
            st.button("Abrir", key=f"ir_{pag}", on_click=_ir, args=(pag,), width="stretch")

    seccion("Empezar desde un ejemplo", "Cargá un ejercicio validado y recorrelo módulo por módulo.")
    ejemplos = listar()
    cols = st.columns(len(ejemplos) + 1)
    for col, e in zip(cols, ejemplos):
        with col, st.container(border=True):
            st.markdown(f"**{e['fuente']['titulo']}**")
            st.caption(e["fuente"]["tipo"])
            if st.button("Cargar", key=f"ej_{e['id']}", width="stretch"):
                reemplazar(ProyectoFlexible.from_dict(e["proyecto"]))
                st.rerun()
    with cols[-1], st.container(border=True):
        st.markdown("**Proyecto en blanco**")
        st.caption("Empezar de cero")
        if st.button("Nuevo", key="nuevo", width="stretch"):
            reemplazar(ProyectoFlexible())
            st.rerun()


def main():
    p = proyecto()  # noqa: F841 (inicializa el estado)
    res_previo = resultado()
    pagina = _sidebar(res_previo)
    if pagina == "Inicio":
        _inicio(res_previo)
    else:
        # cada página escribe en el proyecto; se resuelve de nuevo con los datos recién editados
        PAGINAS[pagina](res_previo)
        nuevo = resultado()
        if nuevo != res_previo and _cambio_relevante(res_previo, nuevo):
            st.session_state.pop("pdf_bytes", None)
            st.session_state.pop("xlsx_bytes", None)
            st.rerun()


def _cambio_relevante(a: dict, b: dict) -> bool:
    from pavimentos.resolver import limpiar
    return repr(limpiar(a)) != repr(limpiar(b))


if __name__ == "__main__":
    main()

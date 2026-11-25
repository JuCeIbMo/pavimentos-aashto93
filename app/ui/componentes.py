"""Componentes reutilizables de la interfaz Streamlit."""

import streamlit as st

from pavimentos.formato import num
from pavimentos.referencias import ECUACIONES


# --------------------------------------------------------------------------- #
#  Bloques visuales (dependen del CSS de theme.py)                            #
# --------------------------------------------------------------------------- #
def encabezado(titulo: str, descripcion: str = "", badge: str = ""):
    st.markdown(
        f"""<div class="page-head">
              <div class="page-badge">{badge}</div>
              <div><h1 class="page-title">{titulo}</h1>
              <p class="page-sub">{descripcion}</p></div>
            </div>""",
        unsafe_allow_html=True,
    )


def seccion(titulo: str, descripcion: str = ""):
    st.markdown(
        f"""<div class="section-title">{titulo}</div>
            <div class="section-sub">{descripcion}</div>""",
        unsafe_allow_html=True,
    )


def tarjeta(etiqueta: str, valor: str, sub: str = ""):
    st.markdown(
        f"""<div class="kpi-card">
              <div class="kpi-label">{etiqueta}</div>
              <div class="kpi-value">{valor}</div>
              {f'<div class="kpi-sub">{sub}</div>' if sub else ''}
            </div>""",
        unsafe_allow_html=True,
    )


def fila_metricas(items: list, ncols: int | None = None):
    """Items: lista de dicts {etiqueta, valor, sub} o tuplas (etiqueta, valor[, sub])."""
    n = ncols or len(items)
    cols = st.columns(n)
    for i, it in enumerate(items):
        if isinstance(it, dict):
            et, va, su = it["etiqueta"], it["valor"], it.get("sub", "")
        else:
            et, va = it[0], it[1]
            su = it[2] if len(it) > 2 else ""
        with cols[i % n]:
            tarjeta(et, va, su)


# --------------------------------------------------------------------------- #
#  Componentes funcionales                                                    #
# --------------------------------------------------------------------------- #
def tabla(datos: list[dict], columnas: list[str] | None = None):
    if columnas:
        datos = [{c: d.get(c) for c in columnas} for d in datos]
    st.dataframe(datos, width="stretch", hide_index=True)


def aviso(mensaje: str, tipo: str = "info"):
    if tipo == "error":
        st.error(mensaje)
    elif tipo == "warn":
        st.warning(mensaje)
    else:
        st.info(mensaje)


def ecuacion(clave: str, mostrar_explicacion: bool = True):
    """Ecuación en LaTeX con su fuente bibliográfica y una explicación breve."""
    e = ECUACIONES[clave]
    st.latex(e["latex"])
    texto = f"📖 *Fuente: {e['fuente']}*"
    if mostrar_explicacion:
        texto += f" — {e['explica']}"
    st.caption(texto)


def concepto(titulo: str, texto: str):
    """Bloque didáctico desplegable con la explicación conceptual del módulo."""
    with st.expander(f"💡 {titulo}"):
        st.markdown(texto, unsafe_allow_html=True)


def avisos(res: dict, modulo: str | None = None):
    for a in res.get("avisos", []):
        if modulo is None or a["modulo"] == modulo:
            aviso(a["texto"], a["nivel"])


def decisiones(res: dict, modulo: str | None = None):
    ds = [d for d in res.get("decisiones", []) if modulo is None or d["modulo"] == modulo]
    if ds:
        st.markdown("**Decisiones de diseño**")
        for d in ds:
            st.markdown(f"- {d['texto']}")


_COLORES = ("#374151", "#D6B46B", "#E8DCC0")


def estructura(capas: dict, mr: float | None = None, alto_px: int = 260):
    """Dibujo a escala del paquete estructural (HTML)."""
    total = sum(c["d_cm"] for c in capas["capas"]) or 1
    u = capas["unidad"]
    bloques = []
    for i, c in enumerate(capas["capas"]):
        if c["d_cm"] <= 0:
            continue
        h = max(22, alto_px * c["d_cm"] / total)
        color_txt = "#fff" if i == 0 else "#1F2937"
        m_txt = "" if c["m"] is None else f" · m = {num(c['m'], 2)}"
        bloques.append(
            f"<div style='display:flex;align-items:center;gap:12px'>"
            f"<div style='width:46%;height:{h:.0f}px;background:{_COLORES[i]};border:1px solid #1F2937;"
            f"display:flex;align-items:center;justify-content:center;color:{color_txt};font-weight:700'>"
            f"{num(c['d'], 1)} {u}</div>"
            f"<div style='font-size:.9rem'><b>{c['capa']}</b><br><span style='color:#6B7280'>"
            f"a = {num(c['a'], 3)}{m_txt} · aporta SN {num(c['sn_aporte'], 2)}"
            f"</span></div></div>")
    sub = f"Subrasante · M<sub>R</sub> = {num(mr, 0)} psi" if mr else "Subrasante"
    bloques.append(
        "<div style='display:flex;align-items:center;gap:12px'>"
        "<div style='width:46%;height:26px;border:1px solid #1F2937;background:repeating-linear-gradient("
        "45deg,#fff,#fff 5px,#D1D5DB 5px,#D1D5DB 6px)'></div>"
        f"<div style='font-size:.9rem'>{sub}</div></div>")
    st.markdown("<div style='display:flex;flex-direction:column;gap:0'>" + "".join(bloques) + "</div>",
                unsafe_allow_html=True)
